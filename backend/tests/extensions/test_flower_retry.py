import asyncio

import core.flower as flower_module
from models.schemas import Coordinate, MovementMode, SimulationState


def test_flower_retries_same_waypoint_after_route_push_failure(monkeypatch) -> None:
    class FakeEngine:
        def __init__(self) -> None:
            self.current_position = Coordinate(lat=25.0, lng=121.0)
            self._stop_event = asyncio.Event()
            self._speed_was_applied = False
            self._active_speed_profile = None
            self._route_push_failed = False
            self.state = SimulationState.IDLE
            self.distance_traveled = 0.0
            self.events: list[tuple[str, dict]] = []
            self.walk_calls = 0

        async def _set_position(self, lat: float, lng: float) -> None:
            self.current_position = Coordinate(lat=lat, lng=lng)

        async def _emit(self, name: str, payload: dict) -> None:
            self.events.append((name, payload))

        async def _move_along_route(self, coords, speed_profile, *, retry_on_push_failure=False) -> None:
            assert retry_on_push_failure
            self.walk_calls += 1
            self._route_push_failed = self.walk_calls == 1

    async def expire_backoff(awaitable, *, timeout):
        awaitable.close()
        raise asyncio.TimeoutError

    monkeypatch.setattr(flower_module.asyncio, "wait_for", expire_backoff)
    engine = FakeEngine()
    asyncio.run(flower_module.FlowerHandler(engine).start(
        [Coordinate(lat=25.001, lng=121.001)], MovementMode.WALKING,
        teleport=True, pre_wait=0, post_wait=0,
    ))

    assert engine.walk_calls == 2
    assert [name for name, _ in engine.events].count("connection_lost") == 1
    assert [name for name, _ in engine.events].count("flower_progress") == 1
    assert engine.state == SimulationState.IDLE
