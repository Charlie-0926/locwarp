import asyncio
import math
import time

import core.multi_stop as multi_stop_module
import core.route_loop as route_loop_module

from extensions.custom.jump_random_walk.policy import (
    DWELL_MOTION_DURATION_SECONDS,
    DWELL_MOTION_SPEED_MPS,
    DwellMotionSession,
)
from extensions.custom.jump_random_walk.schema import ApplyJumpSettingsRequest
from models.schemas import Coordinate
from models.schemas import LoopRequest, MultiStopRequest
from services.interpolator import RouteInterpolator


class _FakeLocationService:
    def __init__(self) -> None:
        self.positions: list[tuple[float, float]] = []

    async def set(self, lat: float, lng: float) -> None:
        self.positions.append((lat, lng))


class _FakeEngine:
    def __init__(self, position: Coordinate) -> None:
        self.location_service = _FakeLocationService()
        self.current_position = position
        self.events: list[tuple[str, dict]] = []
        self.pushed_positions: list[tuple[float, float]] = []
        self._stop_event = asyncio.Event()
        self._pause_event = asyncio.Event()
        self._pause_event.set()
        self._pause_change_event = asyncio.Event()
        self._pause_total_seconds = 0.0
        self._pause_started_monotonic: float | None = None
        self._current_speed_mps = 0.0
        self.jump_dwell_motion = True
        self.jump_extra_wait = 0.0
        self.jump_move_seconds = 4.0
        self.state = None
        self.lap_count = 0
        self.segment_index = 0
        self.total_segments = 0
        self.distance_traveled = 0.0
        self.distance_remaining = 0.0
        self._user_waypoints: list[Coordinate] = []
        self._user_waypoint_next = 0

    async def _set_position(self, lat: float, lng: float) -> None:
        await self.location_service.set(lat, lng)
        self.current_position = Coordinate(lat=lat, lng=lng)
        self.pushed_positions.append((lat, lng))

    async def _emit(self, event_type: str, data: dict) -> None:
        self.events.append((event_type, data))
def test_dwell_motion_uses_one_bearing_and_cumulative_distance() -> None:
    random_calls = 0

    def choose_east() -> float:
        nonlocal random_calls
        random_calls += 1
        return 0.25  # 90 degrees

    origin = Coordinate(lat=25.0, lng=121.0)
    session = DwellMotionSession.create(origin, choose_east)

    for elapsed in (0.5, 1.0, 2.5, 4.0):
        point = session.coordinate_at(elapsed)
        distance = RouteInterpolator.haversine(
            origin.lat, origin.lng, point.lat, point.lng,
        )
        bearing = RouteInterpolator.bearing(
            origin.lat, origin.lng, point.lat, point.lng,
        )
        assert math.isclose(distance, DWELL_MOTION_SPEED_MPS * elapsed, abs_tol=0.001)
        assert math.isclose(bearing, 90.0, abs_tol=0.001)

    assert random_calls == 1


def test_dwell_motion_clamps_position_at_four_seconds() -> None:
    origin = Coordinate(lat=25.0, lng=121.0)
    session = DwellMotionSession.create(origin, lambda: 0.0)
    endpoint = session.coordinate_at(DWELL_MOTION_DURATION_SECONDS)
    after_endpoint = session.coordinate_at(20.0)

    distance = RouteInterpolator.haversine(
        origin.lat, origin.lng, endpoint.lat, endpoint.lng,
    )
    assert math.isclose(
        distance,
        DWELL_MOTION_SPEED_MPS * DWELL_MOTION_DURATION_SECONDS,
        abs_tol=0.001,
    )
    assert endpoint == after_endpoint
    assert session.is_complete(3.999) is False
    assert session.is_complete(4.0) is True


def test_dwell_motion_accepts_custom_duration() -> None:
    origin = Coordinate(lat=25.0, lng=121.0)
    session = DwellMotionSession.create(
        origin,
        lambda: 0.5,
        duration_seconds=2.0,
    )

    endpoint = session.coordinate_at(20.0)
    distance = RouteInterpolator.haversine(
        origin.lat, origin.lng, endpoint.lat, endpoint.lng,
    )
    assert math.isclose(distance, DWELL_MOTION_SPEED_MPS * 2.0, abs_tol=0.001)
    assert session.is_complete(1.999) is False
    assert session.is_complete(2.0) is True


def test_post_jump_dwell_waits_before_custom_duration_motion(monkeypatch) -> None:
    monkeypatch.setattr(multi_stop_module, "DWELL_MOTION_TICK_SECONDS", 0.01)
    origin = Coordinate(lat=25.0, lng=121.0)
    engine = _FakeEngine(origin)

    started = time.monotonic()
    stopped = asyncio.run(multi_stop_module.post_jump_dwell(
        engine,
        source="test",
        base_wp=origin,
        index=0,
        total_waypoints=2,
        motion_enabled=True,
        extra_wait=0.03,
        move_seconds=0.06,
    ))
    elapsed = time.monotonic() - started

    assert stopped is False
    assert elapsed >= 0.08
    countdown = next(data for event, data in engine.events if event == "pause_countdown")
    assert math.isclose(countdown["duration_seconds"], 0.09, abs_tol=0.001)
    dwell_events = [
        data for event, data in engine.events
        if event == "position_update" and data.get("dwell_phase") in {"idle", "moving"}
    ]
    assert dwell_events[0]["dwell_phase"] == "idle"
    assert next(
        data for data in dwell_events if data["dwell_phase"] == "moving"
    )["dwell_remaining_seconds"] <= 0.06
    moving = [
        data for event, data in engine.events
        if event == "position_update" and data.get("dwell_phase") == "moving"
    ]
    assert moving
    assert len({round(data["bearing"], 8) for data in moving}) == 1
    assert all(data["speed_mps"] == DWELL_MOTION_SPEED_MPS for data in moving)
    assert engine._current_speed_mps == 0.0


def test_post_jump_dwell_stop_interrupts_long_idle_wait() -> None:
    async def scenario() -> tuple[bool, float]:
        origin = Coordinate(lat=25.0, lng=121.0)
        engine = _FakeEngine(origin)
        started = time.monotonic()
        task = asyncio.create_task(multi_stop_module.post_jump_dwell(
            engine,
            source="test",
            base_wp=origin,
            index=0,
            total_waypoints=2,
            motion_enabled=False,
            extra_wait=10.0,
        ))
        await asyncio.sleep(0.01)
        engine._stop_event.set()
        engine._pause_change_event.set()
        return await task, time.monotonic() - started

    stopped, elapsed = asyncio.run(scenario())
    assert stopped is True
    assert elapsed < 0.5


def test_post_jump_dwell_pause_freezes_motion(monkeypatch) -> None:
    monkeypatch.setattr(multi_stop_module, "DWELL_MOTION_TICK_SECONDS", 0.01)

    async def scenario() -> tuple[int, int, float]:
        origin = Coordinate(lat=25.0, lng=121.0)
        engine = _FakeEngine(origin)
        started = time.monotonic()
        task = asyncio.create_task(multi_stop_module.post_jump_dwell(
            engine,
            source="test",
            base_wp=origin,
            index=0,
            total_waypoints=2,
            motion_enabled=True,
            extra_wait=0.0,
            move_seconds=0.08,
        ))
        await asyncio.sleep(0.025)
        engine._pause_started_monotonic = time.monotonic()
        engine._pause_event.clear()
        engine._pause_change_event.set()
        await asyncio.sleep(0.02)
        pushes_while_paused = len(engine.pushed_positions)
        await asyncio.sleep(0.04)
        pushes_after_more_pause = len(engine.pushed_positions)
        assert engine._pause_started_monotonic is not None
        engine._pause_total_seconds += (
            time.monotonic() - engine._pause_started_monotonic
        )
        engine._pause_started_monotonic = None
        engine._pause_event.set()
        engine._pause_change_event.set()
        assert await task is False
        return pushes_while_paused, pushes_after_more_pause, time.monotonic() - started

    before, after, elapsed = asyncio.run(scenario())
    assert before == after
    assert elapsed >= 0.13


def test_finite_jump_loop_closes_once_and_stops_exactly_at_start(monkeypatch) -> None:
    dwell_indices: list[int] = []

    async def fake_dwell(*_args, **kwargs) -> bool:
        dwell_indices.append(kwargs["index"])
        return False

    monkeypatch.setattr(route_loop_module, "post_jump_dwell", fake_dwell)
    waypoints = [
        Coordinate(lat=25.0, lng=121.0),
        Coordinate(lat=25.001, lng=121.001),
        Coordinate(lat=25.002, lng=121.002),
    ]
    engine = _FakeEngine(waypoints[0])

    asyncio.run(route_loop_module._run_jump_loop(
        engine,
        waypoints,
        lap_count=1,
        close_loop=True,
    ))

    assert engine.pushed_positions == [
        (waypoints[0].lat, waypoints[0].lng),
        (waypoints[1].lat, waypoints[1].lng),
        (waypoints[2].lat, waypoints[2].lng),
        (waypoints[0].lat, waypoints[0].lng),
    ]
    assert dwell_indices == [0, 1, 2]
    assert engine.current_position == waypoints[0]
    assert len([event for event, _ in engine.events if event == "lap_complete"]) == 1
    assert len([event for event, _ in engine.events if event == "loop_complete"]) == 1


def test_non_looping_jump_multistop_skips_final_post_dwell(monkeypatch) -> None:
    dwell_indices: list[int] = []

    async def fake_dwell(*_args, **kwargs) -> bool:
        dwell_indices.append(kwargs["index"])
        return False

    monkeypatch.setattr(multi_stop_module, "post_jump_dwell", fake_dwell)
    waypoints = [
        Coordinate(lat=25.0, lng=121.0),
        Coordinate(lat=25.001, lng=121.001),
        Coordinate(lat=25.002, lng=121.002),
    ]
    engine = _FakeEngine(waypoints[0])

    asyncio.run(multi_stop_module._run_jump_multistop(
        engine,
        waypoints,
        loop=False,
    ))

    assert dwell_indices == [0, 1]
    assert engine.current_position == waypoints[-1]


def _waypoints() -> list[dict[str, float]]:
    return [
        {"lat": 25.0, "lng": 121.0},
        {"lat": 25.001, "lng": 121.001},
    ]


def test_legacy_route_settings_merge_all_wait_after_arrival() -> None:
    loop = LoopRequest.model_validate({
        "waypoints": _waypoints(),
        "jump_mode": True,
        "jump_random_walk": True,
        "jump_random_walk_radius": 30,
        "jump_pre_delay": 2.5,
        "jump_post_delay": 7.5,
    })
    multi_stop = MultiStopRequest.model_validate({
        "waypoints": _waypoints(),
        "jump_mode": True,
        "jump_random_walk": True,
        "jump_pre_delay": 1,
        "jump_post_delay": 3,
    })

    assert loop.jump_dwell_motion is True
    assert loop.jump_extra_wait == 10.0
    assert loop.jump_move_seconds == 4.0
    assert multi_stop.jump_dwell_motion is True
    assert multi_stop.jump_extra_wait == 4.0
    assert multi_stop.jump_move_seconds == 4.0


def test_new_route_settings_win_over_legacy_values() -> None:
    request = LoopRequest.model_validate({
        "waypoints": _waypoints(),
        "jump_dwell_motion": False,
        "jump_extra_wait": 9,
        "jump_move_seconds": 2.5,
        "jump_random_walk": True,
        "jump_pre_delay": 20,
        "jump_post_delay": 30,
    })

    assert request.jump_dwell_motion is False
    assert request.jump_extra_wait == 9.0
    assert request.jump_move_seconds == 2.5


def test_legacy_hot_apply_does_not_replace_extra_wait() -> None:
    legacy = ApplyJumpSettingsRequest.model_validate({
        "jump_random_walk": True,
        "jump_random_walk_radius": 12,
    })
    current = ApplyJumpSettingsRequest.model_validate({
        "jump_dwell_motion": False,
        "jump_extra_wait": 8,
        "jump_move_seconds": 3,
    })

    assert legacy.resolved_motion_enabled is True
    assert legacy.jump_extra_wait is None
    assert legacy.jump_move_seconds is None
    assert current.resolved_motion_enabled is False
    assert current.jump_extra_wait == 8.0
    assert current.jump_move_seconds == 3.0
