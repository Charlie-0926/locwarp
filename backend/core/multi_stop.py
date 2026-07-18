"""Multi-stop navigator -- sequential navigation through multiple waypoints."""

from __future__ import annotations

import asyncio
import logging
import math
import random
import time

from models.schemas import Coordinate, MovementMode, SimulationState
from services.location_service import DeviceLostError
from config import resolve_speed_profile, SpeedProfile
from extensions.custom.jump_random_walk import (
    DWELL_MOTION_DURATION_SECONDS,
    DWELL_MOTION_SPEED_MPS,
    DWELL_MOTION_TICK_SECONDS,
    DwellMotionSession,
)

logger = logging.getLogger(__name__)


class MultiStopNavigator:
    """Navigate through a series of waypoints with optional pauses at each stop."""

    def __init__(self, engine):
        self.engine = engine

    async def start(
        self,
        waypoints: list[Coordinate],
        mode: MovementMode,
        stop_duration: float = 0,
        loop: bool = False,
        *,
        start_index: int = 0,
        speed_kmh: float | None = None,
        speed_min_kmh: float | None = None,
        speed_max_kmh: float | None = None,
        pause_enabled: bool = True,
        pause_min: float = 5.0,
        pause_max: float = 20.0,
        straight_line: bool = False,
        route_engine: str | None = None,
        jump_mode: bool = False,
        jump_dwell_motion: bool = False,
        jump_extra_wait: float = 6.0,
        jump_move_seconds: float = DWELL_MOTION_DURATION_SECONDS,
    ) -> None:
        """Navigate through *waypoints* one leg at a time.

        Parameters
        ----------
        waypoints
            Ordered list of stops to visit.
        mode
            Movement speed profile.
        stop_duration
            Seconds to pause at each intermediate stop (0 = no pause).
        loop
            If True, loop back to the start after reaching the last
            waypoint and repeat indefinitely.
        """
        engine = self.engine

        if len(waypoints) < 2:
            raise ValueError("At least 2 waypoints are required for multi-stop")

        requested_start_index = max(0, min(int(start_index or 0), len(waypoints) - 2))

        # Jump mode: teleport point-to-point with all dwell after arrival.
        # Skips OSRM routing and the normal "near first waypoint?"
        # preamble because the user wants to land exactly on each stop, in
        # order, without walking. Honors loop=True to repeat. stop_duration
        # / pause_* are ignored. Post-arrival dwell honours pause + stop.
        if jump_mode:
            engine.jump_dwell_motion = jump_dwell_motion
            engine.jump_extra_wait = max(0.0, float(jump_extra_wait))
            engine.jump_move_seconds = max(0.0, float(jump_move_seconds))
            await _run_jump_multistop(
                engine,
                waypoints,
                loop=loop,
                start_index=requested_start_index,
            )
            return

        if engine.current_position is None:
            raise RuntimeError(
                "Cannot start multi-stop: no current position. Teleport first."
            )

        profile_name = mode.value
        osrm_profile = "foot" if mode in (MovementMode.WALKING, MovementMode.RUNNING) else "car"

        def _pick_profile() -> SpeedProfile:
            # Honor mid-flight apply_speed across legs / laps; otherwise
            # re-pick from the original args (so range mode varies).
            if engine._speed_was_applied and engine._active_speed_profile is not None:
                return engine._active_speed_profile
            return resolve_speed_profile(
                profile_name, speed_kmh, speed_min_kmh, speed_max_kmh,
            )

        # Resume support: when this engine is taking over from a peer
        # that just disconnected, jump straight to the leg they were on
        # so the iPhone doesn't visibly walk back to waypoints[0] first.
        resume_snap = engine._resume_snapshot if engine._resume_snapshot and engine._resume_snapshot.get("kind") == "multi_stop" else None
        engine._resume_snapshot = None

        engine.state = SimulationState.MULTI_STOP
        engine.total_segments = len(waypoints) - 1
        if resume_snap:
            engine.lap_count = int(resume_snap.get("lap_count", 0))
            resume_seg = max(0, min(int(resume_snap.get("segment_index", 0)), len(waypoints) - 2))
            resume_uwn = int(resume_snap.get("user_waypoint_next", 1))
        else:
            engine.lap_count = 0
            resume_seg = requested_start_index
            resume_uwn = requested_start_index + 1
        engine.segment_index = resume_seg
        engine.distance_traveled = 0.0

        # Pre-calculate full route path for display + grand total distance so
        # the UI can show total-trip ETA (like route_loop does) instead of
        # the per-leg ETA, which resets at each stop.
        display_start_index = resume_seg if resume_snap else requested_start_index
        display_waypoints = waypoints[display_start_index:]
        all_wp_tuples = [(wp.lat, wp.lng) for wp in display_waypoints]
        full_total_distance = 0.0
        try:
            full_route = await engine.route_service.get_multi_route(
                all_wp_tuples, profile=osrm_profile,
                force_straight=straight_line,
                engine=route_engine,
            )
            full_total_distance = float(full_route.get("distance") or 0.0)
            await engine._emit("route_path", {
                "coords": [{"lat": pt[0], "lng": pt[1]} for pt in full_route["coords"]],
            })
        except Exception:
            logger.warning("Failed to pre-calculate full multi-stop route for display")

        await engine._emit("state_change", {
            "state": engine.state.value,
            "waypoints": [{"lat": wp.lat, "lng": wp.lng} for wp in waypoints],
            "stop_duration": stop_duration,
            "loop": loop,
            "start_index": display_start_index,
        })

        logger.info(
            "Multi-stop started: %d waypoints, start=%d, stop=%ds, loop=%s [%s]",
            len(waypoints), display_start_index, stop_duration, loop, profile_name,
        )

        # Ensure we start from the selected waypoint's location.
        # If we're not near that waypoint, navigate there first.
        # Skip this preamble entirely on resume — the previous engine
        # was already past wp[0] and we want the iPhone to continue from
        # whichever leg it was on, not walk back to the start.
        if not resume_snap:
            first = waypoints[requested_start_index]
            start_pos = engine.current_position
            start_dist = self._quick_distance(start_pos, first)
            if start_dist > 50:  # more than 50m away, route to the selected waypoint
                route_data = await engine.route_service.get_route(
                    start_pos.lat, start_pos.lng,
                    first.lat, first.lng,
                    profile=osrm_profile,
                    force_straight=straight_line,
                    engine=route_engine,
                )
                coords = [Coordinate(lat=pt[0], lng=pt[1]) for pt in route_data["coords"]]
                if len(coords) >= 2:
                    await engine._move_along_route(coords, _pick_profile())
                    if engine._stop_event.is_set():
                        return

        # Track the named user waypoints so highlight events refer to them
        # (otherwise OSRM densification would emit indices over road points).
        engine._user_waypoints = list(waypoints)
        engine._user_waypoint_next = resume_uwn

        # Track how much of the grand total we have already finished so the
        # offset we hand to _move_along_route reflects the remaining legs
        # after the current one.
        completed_distance = 0.0

        running = True
        first_lap = True
        while running and not engine._stop_event.is_set():
            # On each loop pass (only > 1 if loop=True) restart the highlight
            # at the selected first target so the UI re-highlights correctly.
            if loop and engine._user_waypoint_next >= len(waypoints):
                engine._user_waypoint_next = requested_start_index + 1
            # New lap: reset completed distance so the total-ETA countdown
            # restarts from full trip length.
            completed_distance = 0.0
            # On a resume, the first lap starts at the leg the previous
            # engine was on. Otherwise, keep the user-selected run start.
            leg_start = resume_seg if (first_lap and resume_snap) else requested_start_index
            for i in range(leg_start, len(waypoints) - 1):
                if engine._stop_event.is_set():
                    break

                engine.segment_index = i
                wp_a = waypoints[i]
                wp_b = waypoints[i + 1]

                logger.debug(
                    "Multi-stop leg %d/%d: (%.6f,%.6f) -> (%.6f,%.6f)",
                    i + 1, len(waypoints) - 1,
                    wp_a.lat, wp_a.lng, wp_b.lat, wp_b.lng,
                )

                # On the first leg of a resume, start from the iPhone's
                # actual current GPS instead of routing from wp_a (which
                # would teleport the iPhone back to that earlier waypoint
                # before walking forward).
                leg_origin = (
                    engine.current_position
                    if (first_lap and resume_snap and i == leg_start and engine.current_position)
                    else wp_a
                )

                # Get route for this leg
                route_data = await engine.route_service.get_route(
                    leg_origin.lat, leg_origin.lng,
                    wp_b.lat, wp_b.lng,
                    profile=osrm_profile,
                    force_straight=straight_line,
                    engine=route_engine,
                )

                coords = [Coordinate(lat=pt[0], lng=pt[1]) for pt in route_data["coords"]]
                leg_distance = float(route_data.get("distance") or 0.0)
                engine.distance_remaining = leg_distance
                # Offset for emitted ETA = meters left in future legs after
                # this one. When the grand total from get_multi_route exists,
                # derive future-leg distance from it; otherwise fall back to
                # 0 so ETA at least reflects the current leg (same as pre-fix).
                if full_total_distance > 0:
                    future_legs = max(full_total_distance - completed_distance - leg_distance, 0.0)
                else:
                    future_legs = 0.0
                engine._route_offset_remaining = future_legs

                if len(coords) >= 2:
                    await engine._move_along_route(coords, _pick_profile())

                completed_distance += leg_distance
                engine._route_offset_remaining = 0.0

                if engine._stop_event.is_set():
                    break

                # Arrived at a stop
                await engine._emit("stop_reached", {
                    "index": i + 1,
                    "total": len(waypoints),
                    "lat": wp_b.lat,
                    "lng": wp_b.lng,
                })

                # Pause at the stop. Precedence: explicit stop_duration > per-mode
                # random range (when pause_enabled). Last stop only pauses when looping.
                is_last = i == len(waypoints) - 2
                if stop_duration and stop_duration > 0:
                    this_pause = float(stop_duration)
                elif pause_enabled:
                    lo, hi = sorted((float(pause_min), float(pause_max)))
                    if lo < 0:
                        lo = 0.0
                    this_pause = random.uniform(lo, hi) if hi > 0 else 0.0
                else:
                    this_pause = 0.0
                should_pause = this_pause > 0 and (not is_last or loop)

                if should_pause:
                    logger.info("Multi-stop: pausing %.1fs at stop %d", this_pause, i + 1)
                    await engine._emit("pause_countdown", {
                        "duration_seconds": this_pause,
                        "source": "multi_stop",
                    })
                    try:
                        await asyncio.wait_for(
                            engine._stop_event.wait(),
                            timeout=this_pause,
                        )
                        break
                    except asyncio.TimeoutError:
                        pass
                    await engine._emit("pause_countdown_end", {"source": "multi_stop"})

            first_lap = False
            if not loop or engine._stop_event.is_set():
                running = False
            else:
                engine.lap_count += 1
                await engine._emit("lap_complete", {"lap": engine.lap_count})
                logger.info("Multi-stop lap %d complete", engine.lap_count)

        engine._route_offset_remaining = 0.0
        if engine.state == SimulationState.MULTI_STOP:
            engine.state = SimulationState.IDLE
            await engine._emit("multi_stop_complete", {
                "laps": engine.lap_count,
            })
            await engine._emit("state_change", {"state": engine.state.value})

        logger.info("Multi-stop finished after %d laps", engine.lap_count)

    @staticmethod
    def _quick_distance(a: Coordinate, b: Coordinate) -> float:
        """Rough distance in meters (good enough for threshold checks)."""
        import math
        dlat = math.radians(b.lat - a.lat)
        dlng = math.radians(b.lng - a.lng) * math.cos(math.radians(a.lat))
        return 6_371_000 * math.sqrt(dlat ** 2 + dlng ** 2)


def jump_dwell_seconds(
    motion_enabled: bool,
    extra_wait: float,
    move_seconds: float = DWELL_MOTION_DURATION_SECONDS,
) -> float:
    """Total post-arrival dwell for one ordinary jump stop."""
    return (
        (max(0.0, float(move_seconds)) if motion_enabled else 0.0)
        + max(0.0, float(extra_wait))
    )


def _phase_active_elapsed(
    engine,
    wall_started: float,
    pause_total_started: float,
) -> float:
    """Wall time since phase start minus every paused interval."""
    now = time.monotonic()
    paused = max(
        0.0,
        float(getattr(engine, "_pause_total_seconds", 0.0)) - pause_total_started,
    )
    pause_started = getattr(engine, "_pause_started_monotonic", None)
    if pause_started is not None:
        paused += max(0.0, now - float(pause_started))
    return max(0.0, now - wall_started - paused)


async def _wait_for_pause_stop_or_timeout(engine, timeout: float) -> str:
    """Return timeout, pause_change, or stop without missing a pause race."""
    if engine._stop_event.is_set():
        return "stop"
    if timeout <= 0:
        return "timeout"

    engine._pause_change_event.clear()
    if not engine._pause_event.is_set():
        return "pause_change"

    stop_task = asyncio.create_task(engine._stop_event.wait())
    pause_task = asyncio.create_task(engine._pause_change_event.wait())
    try:
        done, _ = await asyncio.wait(
            {stop_task, pause_task},
            timeout=timeout,
            return_when=asyncio.FIRST_COMPLETED,
        )
        if stop_task in done and engine._stop_event.is_set():
            return "stop"
        if pause_task in done:
            return "pause_change"
        return "timeout"
    finally:
        for task in (stop_task, pause_task):
            if not task.done():
                task.cancel()
        await asyncio.gather(stop_task, pause_task, return_exceptions=True)


async def _wait_until_resumed_or_stopped(engine) -> bool:
    """Block while paused; return True if stop wins the race."""
    while not engine._pause_event.is_set():
        if engine._stop_event.is_set():
            return True
        resume_task = asyncio.create_task(engine._pause_event.wait())
        stop_task = asyncio.create_task(engine._stop_event.wait())
        try:
            done, _ = await asyncio.wait(
                {resume_task, stop_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            if stop_task in done and engine._stop_event.is_set():
                return True
        finally:
            for task in (resume_task, stop_task):
                if not task.done():
                    task.cancel()
            await asyncio.gather(resume_task, stop_task, return_exceptions=True)
    return engine._stop_event.is_set()


async def _push_dwell_position(engine, point: Coordinate) -> None:
    """Push a motion point with bounded retries and responsive backoff."""
    for attempt in range(3):
        try:
            await engine._set_position(point.lat, point.lng)
            return
        except (ConnectionError, OSError, asyncio.TimeoutError) as exc:
            logger.warning(
                "jump dwell position push failed (attempt %d/3): %s",
                attempt + 1,
                exc,
            )
        except DeviceLostError:
            engine._stop_event.set()
            raise
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Unexpected jump dwell position push failure")

        if attempt < 2:
            outcome = await _wait_for_pause_stop_or_timeout(
                engine,
                0.25 * (attempt + 1),
            )
            if outcome == "stop":
                raise RuntimeError("Jump dwell stopped after a position push failure")
            if not engine._pause_event.is_set():
                if await _wait_until_resumed_or_stopped(engine):
                    raise RuntimeError("Jump dwell stopped after a position push failure")

    engine._stop_event.set()
    raise RuntimeError("Jump dwell position push failed repeatedly")


async def _emit_dwell_position(
    engine,
    *,
    position: Coordinate,
    speed_mps: float,
    bearing: float | None,
    phase: str,
    is_paused: bool,
    dwell_elapsed: float,
    dwell_total: float,
    future_seconds: float,
    index: int,
    total_waypoints: int,
) -> None:
    remaining = max(0.0, dwell_total - dwell_elapsed)
    engine._current_speed_mps = speed_mps
    payload = {
        "lat": position.lat,
        "lng": position.lng,
        "speed_mps": speed_mps,
        "progress": (index + 1) / max(total_waypoints, 1),
        "segment_index": index,
        "total_segments": total_waypoints,
        "lap_count": engine.lap_count,
        "distance_traveled": 0.0,
        "distance_remaining": 0.0,
        "eta_seconds": future_seconds + remaining,
        "eta_arrival": "",
        "is_paused": is_paused,
        "dwell_phase": phase,
        "dwell_remaining_seconds": remaining,
    }
    if bearing is not None:
        payload["bearing"] = bearing
    await engine._emit("position_update", payload)


async def post_jump_dwell(
    engine,
    *,
    source: str,
    base_wp: Coordinate,
    index: int,
    total_waypoints: int,
    motion_enabled: bool,
    extra_wait: float,
    move_seconds: float = DWELL_MOTION_DURATION_SECONDS,
    future_seconds: float = 0.0,
) -> bool:
    """Run an interruptible idle wait, then fixed-speed straight movement.

    Returns True when stop interrupts the dwell. Settings are passed by value
    so hot apply has a clean next-waypoint boundary.
    """
    idle_seconds = max(0.0, float(extra_wait))
    motion_seconds = max(0.0, float(move_seconds)) if motion_enabled else 0.0
    dwell_total = motion_seconds + idle_seconds
    if dwell_total <= 0:
        return engine._stop_event.is_set()

    await engine._emit("pause_countdown", {
        "duration_seconds": dwell_total,
        "source": source,
        "phase": "post_dwell",
        "motion_seconds": motion_seconds,
        "idle_seconds": idle_seconds,
    })

    try:
        if idle_seconds > 0:
            wall_started = time.monotonic()
            pause_total_started = float(
                getattr(engine, "_pause_total_seconds", 0.0),
            )
            next_keepalive = min(1.0, idle_seconds)
            while True:
                if engine._stop_event.is_set():
                    return True

                idle_elapsed = min(
                    _phase_active_elapsed(engine, wall_started, pause_total_started),
                    idle_seconds,
                )
                position = engine.current_position or base_wp
                if not engine._pause_event.is_set():
                    await _emit_dwell_position(
                        engine,
                        position=position,
                        speed_mps=0.0,
                        bearing=None,
                        phase="idle",
                        is_paused=True,
                        dwell_elapsed=idle_elapsed,
                        dwell_total=dwell_total,
                        future_seconds=future_seconds,
                        index=index,
                        total_waypoints=total_waypoints,
                    )
                    if await _wait_until_resumed_or_stopped(engine):
                        return True
                    continue

                if idle_elapsed + 1e-9 >= next_keepalive or idle_elapsed >= idle_seconds:
                    try:
                        await engine.location_service.set(position.lat, position.lng)
                    except Exception:
                        logger.debug("post_jump_dwell keepalive failed", exc_info=True)
                    await _emit_dwell_position(
                        engine,
                        position=position,
                        speed_mps=0.0,
                        bearing=None,
                        phase="idle",
                        is_paused=False,
                        dwell_elapsed=idle_elapsed,
                        dwell_total=dwell_total,
                        future_seconds=future_seconds,
                        index=index,
                        total_waypoints=total_waypoints,
                    )
                    while next_keepalive <= idle_elapsed + 1e-9:
                        next_keepalive = min(next_keepalive + 1.0, idle_seconds)
                        if next_keepalive == idle_seconds:
                            break
                    if idle_elapsed >= idle_seconds:
                        break
                    continue

                outcome = await _wait_for_pause_stop_or_timeout(
                    engine,
                    max(0.0, next_keepalive - idle_elapsed),
                )
                if outcome == "stop":
                    return True

        if motion_seconds > 0:
            session = DwellMotionSession.create(
                base_wp,
                duration_seconds=motion_seconds,
            )
            wall_started = time.monotonic()
            pause_total_started = float(
                getattr(engine, "_pause_total_seconds", 0.0),
            )
            next_emit = min(DWELL_MOTION_TICK_SECONDS, motion_seconds)

            while True:
                if engine._stop_event.is_set():
                    return True

                motion_elapsed = min(
                    _phase_active_elapsed(engine, wall_started, pause_total_started),
                    motion_seconds,
                )
                if not engine._pause_event.is_set():
                    position = engine.current_position or session.coordinate_at(motion_elapsed)
                    await _emit_dwell_position(
                        engine,
                        position=position,
                        speed_mps=0.0,
                        bearing=session.bearing_deg,
                        phase="moving",
                        is_paused=True,
                        dwell_elapsed=idle_seconds + motion_elapsed,
                        dwell_total=dwell_total,
                        future_seconds=future_seconds,
                        index=index,
                        total_waypoints=total_waypoints,
                    )
                    if await _wait_until_resumed_or_stopped(engine):
                        return True
                    continue

                if motion_elapsed + 1e-9 >= next_emit or motion_elapsed >= motion_seconds:
                    position = session.coordinate_at(motion_elapsed)
                    await _push_dwell_position(engine, position)
                    await _emit_dwell_position(
                        engine,
                        position=position,
                        speed_mps=DWELL_MOTION_SPEED_MPS,
                        bearing=session.bearing_deg,
                        phase="moving",
                        is_paused=False,
                        dwell_elapsed=idle_seconds + motion_elapsed,
                        dwell_total=dwell_total,
                        future_seconds=future_seconds,
                        index=index,
                        total_waypoints=total_waypoints,
                    )
                    while next_emit <= motion_elapsed + 1e-9:
                        next_emit = min(
                            next_emit + DWELL_MOTION_TICK_SECONDS,
                            motion_seconds,
                        )
                        if next_emit == motion_seconds:
                            break
                    if motion_elapsed >= motion_seconds:
                        break
                    continue

                timeout = max(0.0, next_emit - motion_elapsed)
                outcome = await _wait_for_pause_stop_or_timeout(engine, timeout)
                if outcome == "stop":
                    return True

            endpoint = session.coordinate_at(motion_seconds)
            await _emit_dwell_position(
                engine,
                position=endpoint,
                speed_mps=0.0,
                bearing=session.bearing_deg,
                phase="complete",
                is_paused=False,
                dwell_elapsed=dwell_total,
                dwell_total=dwell_total,
                future_seconds=future_seconds,
                index=index,
                total_waypoints=total_waypoints,
            )

        return False
    finally:
        engine._current_speed_mps = 0.0
        await engine._emit("pause_countdown_end", {"source": source})


async def interruptible_wait(engine, seconds: float, *, source: str) -> bool:
    """Generic active-time wait used by non-jump modes such as Flower."""
    duration = max(0.0, float(seconds))
    if duration <= 0:
        return engine._stop_event.is_set()

    await engine._emit("pause_countdown", {
        "duration_seconds": duration,
        "source": source,
    })
    wall_started = time.monotonic()
    pause_total_started = float(getattr(engine, "_pause_total_seconds", 0.0))
    next_keepalive = min(1.0, duration)
    try:
        while True:
            if engine._stop_event.is_set():
                return True
            elapsed = min(
                _phase_active_elapsed(engine, wall_started, pause_total_started),
                duration,
            )
            if not engine._pause_event.is_set():
                if await _wait_until_resumed_or_stopped(engine):
                    return True
                continue
            if elapsed + 1e-9 >= next_keepalive or elapsed >= duration:
                position = engine.current_position
                if position is not None:
                    try:
                        await engine.location_service.set(position.lat, position.lng)
                    except Exception:
                        logger.debug("interruptible_wait keepalive failed", exc_info=True)
                while next_keepalive <= elapsed + 1e-9:
                    next_keepalive = min(next_keepalive + 1.0, duration)
                    if next_keepalive == duration:
                        break
                if elapsed >= duration:
                    return False
                continue
            outcome = await _wait_for_pause_stop_or_timeout(
                engine,
                max(0.0, next_keepalive - elapsed),
            )
            if outcome == "stop":
                return True
    finally:
        await engine._emit("pause_countdown_end", {"source": source})


async def _run_jump_multistop(
    engine,
    waypoints: list[Coordinate],
    *,
    loop: bool,
    start_index: int = 0,
) -> None:
    """Teleport through waypoints with all dwell after each arrival."""
    engine.state = SimulationState.MULTI_STOP
    engine.total_segments = len(waypoints)
    engine.lap_count = 0
    engine.segment_index = start_index
    engine.distance_traveled = 0.0
    engine.distance_remaining = 0.0
    engine._user_waypoints = list(waypoints)
    engine._user_waypoint_next = min(start_index + 1, len(waypoints) - 1)

    await engine._emit("route_path", {
        "coords": [{"lat": wp.lat, "lng": wp.lng} for wp in waypoints[start_index:]],
    })
    await engine._emit("state_change", {
        "state": engine.state.value,
        "waypoints": [{"lat": wp.lat, "lng": wp.lng} for wp in waypoints],
        "stop_duration": 0,
        "loop": loop,
        "start_index": start_index,
    })

    logger.info(
        "Jump multi-stop started: %d waypoints, start=%d, wait=%.1fs, move=%.1fs, loop=%s",
        len(waypoints), start_index, engine.jump_extra_wait,
        engine.jump_move_seconds, loop,
    )

    running = True
    first_iteration = True
    while running and not engine._stop_event.is_set():
        run_start = start_index if first_iteration else 0
        for i in range(run_start, len(waypoints)):
            wp = waypoints[i]
            if engine._stop_event.is_set():
                break

            await engine._set_position(wp.lat, wp.lng)
            engine.segment_index = i
            engine._user_waypoint_next = min(i + 1, len(waypoints))
            motion_enabled = bool(engine.jump_dwell_motion)
            extra_wait = max(0.0, float(engine.jump_extra_wait))
            move_seconds = max(0.0, float(engine.jump_move_seconds))
            dwell_seconds = jump_dwell_seconds(
                motion_enabled,
                extra_wait,
                move_seconds,
            )
            dwell_count = (
                len(waypoints) - i
                if loop
                else max(len(waypoints) - 1 - i, 0)
            )
            eta_secs = dwell_count * dwell_seconds
            await engine._emit("position_update", {
                "lat": wp.lat, "lng": wp.lng,
                "speed_mps": 0.0,
                "progress": (i + 1) / max(len(waypoints), 1),
                "segment_index": i,
                "total_segments": len(waypoints),
                "lap_count": engine.lap_count,
                "distance_traveled": 0.0,
                "distance_remaining": 0.0,
                "eta_seconds": eta_secs,
                "eta_arrival": "",
                "is_paused": False,
                "dwell_phase": "arrival",
            })
            await engine._emit("user_waypoint_advance", {
                "current_index": i,
                "next_index": min(i + 1, len(waypoints) - 1),
            })
            await engine._emit("stop_reached", {
                "index": i + 1,
                "total": len(waypoints),
                "lat": wp.lat, "lng": wp.lng,
            })
            # Skip the post-delay after the very last stop on a non-looping
            # run — the simulation is finished, so the wait would just
            # delay the IDLE transition without serving any purpose.
            is_last = (i == len(waypoints) - 1)
            if is_last and not loop:
                continue
            if await post_jump_dwell(
                engine,
                source="multi_stop",
                base_wp=wp,
                index=i,
                total_waypoints=len(waypoints),
                motion_enabled=motion_enabled,
                extra_wait=extra_wait,
                move_seconds=move_seconds,
                future_seconds=max(dwell_count - 1, 0) * dwell_seconds,
            ):
                break

        if not loop or engine._stop_event.is_set():
            running = False
        else:
            first_iteration = False
            engine.lap_count += 1
            await engine._emit("lap_complete", {"lap": engine.lap_count})
            logger.info("Jump multi-stop lap %d complete", engine.lap_count)

    if engine.state == SimulationState.MULTI_STOP:
        engine.state = SimulationState.IDLE
        await engine._emit("multi_stop_complete", {"laps": engine.lap_count})
        await engine._emit("state_change", {"state": engine.state.value})
    logger.info("Jump multi-stop finished after %d laps", engine.lap_count)
