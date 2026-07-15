"""API schema owned by the Spiral extension."""

from pydantic import BaseModel

from models.schemas import Coordinate, MovementMode


class SpiralRequest(BaseModel):
    center: Coordinate
    radius_m: float = 500.0
    spacing_m: float = 20.0
    mode: MovementMode = MovementMode.WALKING
    speed_kmh: float | None = None
    speed_min_kmh: float | None = None
    speed_max_kmh: float | None = None
    straight_line: bool = True
    route_engine: str | None = None
    udid: str | None = None
