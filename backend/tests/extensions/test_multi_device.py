from types import SimpleNamespace

from extensions.custom.multi_device.coordinator import mirror_progress


def tracker(total: float, traveled: float, speed: float, started: float) -> SimpleNamespace:
    return SimpleNamespace(
        total_distance=total,
        traveled=traveled,
        speed_mps=speed,
        start_time=started,
    )


def test_mirror_progress_copies_mutable_tracker_state() -> None:
    primary = SimpleNamespace(
        distance_traveled=12.0,
        distance_remaining=34.0,
        lap_count=2,
        segment_index=3,
        total_segments=8,
        _current_speed_mps=4.5,
        eta_tracker=tracker(100.0, 66.0, 4.5, 10.0),
    )
    follower = SimpleNamespace(
        distance_traveled=0.0,
        distance_remaining=0.0,
        lap_count=0,
        segment_index=0,
        total_segments=0,
        _current_speed_mps=0.0,
        eta_tracker=tracker(0.0, 0.0, 0.0, 0.0),
    )

    mirror_progress(primary, follower)

    assert follower.distance_remaining == 34.0
    assert follower.eta_tracker.total_distance == 100.0
    assert follower.eta_tracker.traveled == 66.0
    assert follower.eta_tracker.speed_mps == 4.5
