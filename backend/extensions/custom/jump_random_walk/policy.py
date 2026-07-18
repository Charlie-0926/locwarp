"""Random movement policy used while a jump route is dwelling."""

from __future__ import annotations

import random
from dataclasses import dataclass
from collections.abc import Callable

from models.schemas import Coordinate
from services.interpolator import RouteInterpolator


DWELL_MOTION_SPEED_KMH = 15.0
DWELL_MOTION_SPEED_MPS = DWELL_MOTION_SPEED_KMH / 3.6
DWELL_MOTION_DURATION_SECONDS = 4.0
DWELL_MOTION_TICK_SECONDS = 0.5


@dataclass(frozen=True)
class DwellMotionSession:
    """One post-arrival straight-line movement with a stable bearing."""

    origin: Coordinate
    bearing_deg: float
    speed_mps: float = DWELL_MOTION_SPEED_MPS
    duration_seconds: float = DWELL_MOTION_DURATION_SECONDS

    @classmethod
    def create(
        cls,
        origin: Coordinate,
        random_value: Callable[[], float] = random.random,
        *,
        duration_seconds: float = DWELL_MOTION_DURATION_SECONDS,
    ) -> "DwellMotionSession":
        # random.random() is [0, 1), but modulo also keeps injected test RNGs
        # and custom callers inside the documented bearing range.
        bearing = (float(random_value()) * 360.0) % 360.0
        return cls(
            origin=origin,
            bearing_deg=bearing,
            duration_seconds=max(0.0, float(duration_seconds)),
        )

    def active_elapsed(self, elapsed_seconds: float) -> float:
        return min(max(0.0, float(elapsed_seconds)), self.duration_seconds)

    def distance_at(self, elapsed_seconds: float) -> float:
        return self.speed_mps * self.active_elapsed(elapsed_seconds)

    def coordinate_at(self, elapsed_seconds: float) -> Coordinate:
        lat, lng = RouteInterpolator.move_point(
            self.origin.lat,
            self.origin.lng,
            self.bearing_deg,
            self.distance_at(elapsed_seconds),
        )
        return Coordinate(lat=lat, lng=lng)

    def is_complete(self, elapsed_seconds: float) -> bool:
        return float(elapsed_seconds) >= self.duration_seconds
