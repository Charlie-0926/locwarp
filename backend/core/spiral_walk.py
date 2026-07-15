"""Spiral walk handler -- move in an outward Archimedean spiral."""

from __future__ import annotations

import asyncio
import logging
import math

from models.schemas import Coordinate, MovementMode, SimulationState
from services.interpolator import RouteInterpolator
from config import resolve_speed_profile, SpeedProfile

logger = logging.getLogger(__name__)


class SpiralWalkHandler:
    """Generates waypoints for an Archimedean spiral and walks them."""

    def __init__(self, engine):
        self.engine = engine

    async def start(
        self,
        center: Coordinate,
        radius_m: float,
        spacing_m: float,
        mode: MovementMode,
        *,
        speed_kmh: float | None = None,
        speed_min_kmh: float | None = None,
        speed_max_kmh: float | None = None,
        straight_line: bool = True,
        route_engine: str | None = None,
    ) -> None:
        """Begin a spiral walk around *center* up to *radius_m*."""
        engine = self.engine

        if engine.current_position is None:
            raise RuntimeError(
                "Cannot start spiral walk: no current position. Teleport first."
            )

        profile_name = mode.value
        osrm_profile = "foot" if mode in (MovementMode.WALKING, MovementMode.RUNNING) else "car"

        engine.state = SimulationState.SPIRAL
        engine.distance_traveled = 0.0
        engine.lap_count = 0

        await engine._emit("state_change", {
            "state": engine.state.value,
            "center": {"lat": center.lat, "lng": center.lng},
            "radius_m": radius_m,
            "spacing_m": spacing_m,
        })

        logger.info(
            "Spiral walk started: center=(%.6f,%.6f), radius=%.0fm, spacing=%.0fm [%s]",
            center.lat, center.lng, radius_m, spacing_m, profile_name,
        )

        # Generate spiral points
        coords = self._generate_spiral(center, radius_m, spacing_m)
        logger.info("Generated %d waypoints for spiral", len(coords))

        if not coords:
            logger.warning("Spiral generated 0 points, stopping.")
            engine.state = SimulationState.IDLE
            return

        engine._user_waypoints = coords
        engine._user_waypoint_next = 0
        # For spiral we just highlight the whole generated path
        await engine._emit("route_path", {
            "coords": [{"lat": c.lat, "lng": c.lng} for c in coords],
        })

        speed_profile: SpeedProfile
        if engine._speed_was_applied and engine._active_speed_profile is not None:
            speed_profile = engine._active_speed_profile
        else:
            speed_profile = resolve_speed_profile(
                profile_name, speed_kmh, speed_min_kmh, speed_max_kmh,
            )

        # A spiral generates thousands of points spaced ~10m apart to form a
        # continuous geometric curve. Passing this to OSRM (road snapping)
        # would not only destroy the spiral shape but also spam the routing
        # API thousands of times. Spiral must always follow straight lines.
        total_dist = sum(
            RouteInterpolator.haversine(coords[i].lat, coords[i].lng, coords[i+1].lat, coords[i+1].lng)
            for i in range(len(coords) - 1)
        )
        engine.distance_remaining = total_dist
        await engine._move_along_route(coords, speed_profile)

        if engine.state in (SimulationState.SPIRAL, SimulationState.PAUSED):
            engine.state = SimulationState.IDLE
            await engine._emit("state_change", {"state": engine.state.value})

        logger.info("Spiral walk finished")

    def _generate_spiral(self, center: Coordinate, max_radius: float, spacing: float) -> list[Coordinate]:
        """Generate Archimedean spiral points. r = (spacing / (2*pi)) * theta"""
        if spacing <= 0 or max_radius <= 0:
            return []

        points = [center]
        
        b = spacing / (2 * math.pi)
        theta = 0.0
        r = 0.0
        
        # Step distance along the spiral curve
        # We want points dense enough to form a smooth curve, e.g. every 10 meters
        step_dist = 10.0
        
        while r < max_radius:
            # Arc length dS = sqrt(r^2 + b^2) * dTheta
            # So dTheta = step_dist / sqrt(r^2 + b^2)
            dTheta = step_dist / math.sqrt(r*r + b*b)
            theta += dTheta
            r = b * theta
            
            if r > max_radius:
                r = max_radius
                
            lat, lng = RouteInterpolator.move_point(
                center.lat, center.lng,
                bearing_deg=math.degrees(theta) % 360,
                distance_m=r
            )
            points.append(Coordinate(lat=lat, lng=lng))
            
            if r == max_radius:
                break
                
        return points
