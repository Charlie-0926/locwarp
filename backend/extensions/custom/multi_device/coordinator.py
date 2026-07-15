"""Multi-device lifecycle coordination isolated from the FastAPI bootstrap."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from models.schemas import SimulationState

ACTIVE_FOLLOW_STATES = {
    SimulationState.NAVIGATING,
    SimulationState.LOOPING,
    SimulationState.MULTI_STOP,
    SimulationState.RANDOM_WALK,
    SimulationState.SPIRAL,
    SimulationState.FLOWER,
}


async def auto_sync_new_device(
    app_state: Any,
    new_udid: str,
    logger: logging.Logger,
) -> None:
    """Align a newly connected device and attach it to the active leader."""
    primary_udid = app_state._primary_udid
    if primary_udid is None or primary_udid == new_udid:
        return
    primary_engine = app_state.simulation_engines.get(primary_udid)
    follower_engine = app_state.simulation_engines.get(new_udid)
    if primary_engine is None or follower_engine is None:
        return

    position = primary_engine.current_position
    if position is None:
        logger.info("Auto-sync: primary %s has no position, skipping %s", primary_udid, new_udid)
        return
    try:
        await follower_engine.teleport(position.lat, position.lng)
    except Exception:
        logger.exception("Auto-sync: teleport failed for %s", new_udid)
        return

    primary_state = primary_engine.state
    if primary_state == SimulationState.PAUSED:
        primary_state = getattr(primary_engine, "_paused_from", SimulationState.IDLE)
    if primary_state not in ACTIVE_FOLLOW_STATES:
        return

    follower_engine.state = primary_engine.state
    follower_engine._paused_from = getattr(primary_engine, "_paused_from", None)
    if getattr(primary_engine, "_last_route_path", None):
        follower_engine._last_route_path = list(primary_engine._last_route_path)

    try:
        await follower_engine._emit("state_change", {"state": follower_engine.state.value})
        if follower_engine._last_route_path:
            await follower_engine._emit("route_path", {"coords": follower_engine._last_route_path})
    except Exception:
        logger.debug("Auto-sync: initial state emission failed for %s", new_udid, exc_info=True)

    asyncio.create_task(
        follow_primary_positions(app_state, new_udid, primary_udid, logger),
    )


def mirror_progress(primary_engine: Any, follower_engine: Any) -> None:
    """Copy mutable progress fields without assigning read-only properties."""
    follower_engine.distance_traveled = primary_engine.distance_traveled
    follower_engine.distance_remaining = primary_engine.distance_remaining
    follower_engine.lap_count = primary_engine.lap_count
    follower_engine.segment_index = primary_engine.segment_index
    follower_engine.total_segments = primary_engine.total_segments
    follower_engine._current_speed_mps = primary_engine._current_speed_mps

    follower_tracker = follower_engine.eta_tracker
    primary_tracker = primary_engine.eta_tracker
    follower_tracker.total_distance = primary_tracker.total_distance
    follower_tracker.traveled = primary_tracker.traveled
    follower_tracker.speed_mps = primary_tracker.speed_mps
    follower_tracker.start_time = primary_tracker.start_time


async def follow_primary_positions(
    app_state: Any,
    follower_udid: str,
    primary_udid: str,
    logger: logging.Logger,
    poll_interval: float = 0.5,
) -> None:
    """Mirror leader position and progress until either engine changes."""
    last_position: tuple[float, float] | None = None
    while True:
        if app_state._primary_udid != primary_udid:
            return
        follower_engine = app_state.simulation_engines.get(follower_udid)
        primary_engine = app_state.simulation_engines.get(primary_udid)
        if follower_engine is None or primary_engine is None:
            return
        if follower_engine._stop_event.is_set():
            return

        position = primary_engine.current_position
        current = (position.lat, position.lng) if position is not None else None
        if current is not None and current != last_position:
            try:
                await follower_engine._set_position(*current)
                last_position = current
                await follower_engine._emit("position_update", {
                    "lat": current[0],
                    "lng": current[1],
                })
                mirror_progress(primary_engine, follower_engine)
            except Exception:
                logger.debug("Follower %s update failed", follower_udid, exc_info=True)

        if follower_engine.state != primary_engine.state:
            follower_engine.state = primary_engine.state
            follower_engine._paused_from = getattr(primary_engine, "_paused_from", None)
            await follower_engine._emit("state_change", {"state": follower_engine.state.value})
        await asyncio.sleep(poll_interval)
