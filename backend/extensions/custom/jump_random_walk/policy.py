"""Random movement policy used while a jump route is dwelling."""

from __future__ import annotations

import math
import random
from collections.abc import Callable
from typing import Any

from models.schemas import Coordinate


def random_coordinate(
    center: Coordinate,
    radius_m: float,
    random_value: Callable[[], float] = random.random,
) -> Coordinate:
    """Return a uniformly distributed coordinate inside a radius."""
    radius = max(0.0, float(radius_m)) * math.sqrt(random_value())
    theta = random_value() * 2 * math.pi
    dx = radius * math.cos(theta)
    dy = radius * math.sin(theta)
    dlat = dy / 111_320.0
    cos_lat = max(abs(math.cos(math.radians(center.lat))), 1e-9)
    dlng = dx / (111_320.0 * cos_lat)
    return Coordinate(lat=center.lat + dlat, lng=center.lng + dlng)


async def perform_dwell_step(
    engine: Any,
    base_wp: Coordinate | None,
    *,
    enabled: bool,
    remaining: float,
    elapsed: float,
    total_seconds: float,
    index: int,
    total_waypoints: int,
    pre_delay: float,
    post_delay: float,
    is_pre_delay: bool,
) -> bool:
    """Move once and emit progress; return whether a step was performed."""
    if not enabled or base_wp is None or remaining <= 0:
        return False

    point = random_coordinate(
        base_wp,
        getattr(engine, "jump_random_walk_radius", 10.0),
    )
    await engine._set_position(point.lat, point.lng)
    eta_seconds = (
        (total_waypoints - 1 - index) * (pre_delay + post_delay)
        + (post_delay if is_pre_delay else 0.0)
        + remaining
    )
    await engine._emit("position_update", {
        "lat": point.lat,
        "lng": point.lng,
        "speed_mps": 0.0,
        "progress": (index + (elapsed / max(total_seconds, 1.0))) / max(total_waypoints, 1),
        "segment_index": index,
        "total_segments": total_waypoints,
        "lap_count": engine.lap_count,
        "distance_traveled": 0.0,
        "distance_remaining": 0.0,
        "eta_seconds": eta_seconds,
        "eta_arrival": "",
        "is_paused": False,
    })
    return True
