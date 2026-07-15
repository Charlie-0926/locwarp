import math

from extensions.custom.jump_random_walk.policy import random_coordinate
from models.schemas import Coordinate


def test_random_coordinate_stays_inside_radius() -> None:
    values = iter((1.0, 0.0))
    center = Coordinate(lat=25.0, lng=121.0)
    point = random_coordinate(center, 20.0, lambda: next(values))

    north_m = (point.lat - center.lat) * 111_320.0
    east_m = (
        (point.lng - center.lng)
        * 111_320.0
        * math.cos(math.radians(center.lat))
    )
    assert math.hypot(north_m, east_m) <= 20.0001
    assert east_m > 19.99
