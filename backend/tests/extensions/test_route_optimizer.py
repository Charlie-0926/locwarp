from extensions.custom.route_optimizer import optimize_order_2opt
from services.geo_extras import optimize_order_nearest_neighbor


def route_cost(matrix: list[list[float]], order: list[int]) -> float:
    return sum(matrix[start][end] for start, end in zip(order, order[1:]))


def reference_two_opt(
    matrix: list[list[float]], keep_first: bool,
) -> list[int]:
    """Original full-route candidate calculation used as a regression oracle."""
    order = optimize_order_nearest_neighbor(matrix, keep_first)
    best_cost = route_cost(matrix, order)
    improved = True
    while improved:
        improved = False
        start_index = 1 if keep_first else 0
        for left in range(start_index, len(order) - 1):
            for right in range(left + 1, len(order)):
                candidate = order[:]
                candidate[left:right + 1] = reversed(order[left:right + 1])
                candidate_cost = route_cost(matrix, candidate)
                if candidate_cost < best_cost - 1e-4:
                    order = candidate
                    best_cost = candidate_cost
                    improved = True
                    break
            if improved:
                break
    return order


def test_two_opt_returns_valid_route_and_keeps_first() -> None:
    matrix: list[list[float]] = [
        [0.0, 2.0, 9.0, 10.0, 7.0],
        [2.0, 0.0, 6.0, 4.0, 3.0],
        [9.0, 6.0, 0.0, 8.0, 5.0],
        [10.0, 4.0, 8.0, 0.0, 6.0],
        [7.0, 3.0, 5.0, 6.0, 0.0],
    ]
    order = optimize_order_2opt(matrix, keep_first=True)

    assert order[0] == 0
    assert sorted(order) == list(range(len(matrix)))
    assert route_cost(matrix, order) <= route_cost(matrix, list(range(len(matrix))))


def test_two_opt_handles_small_matrices() -> None:
    assert optimize_order_2opt([], keep_first=False) == []
    assert optimize_order_2opt([[0.0]], keep_first=False) == [0]


def test_incremental_cost_matches_original_for_symmetric_matrix() -> None:
    matrix: list[list[float]] = [
        [0.0, 8.0, 5.0, 9.0, 6.0, 7.0],
        [8.0, 0.0, 4.0, 3.0, 8.0, 5.0],
        [5.0, 4.0, 0.0, 7.0, 2.0, 6.0],
        [9.0, 3.0, 7.0, 0.0, 5.0, 4.0],
        [6.0, 8.0, 2.0, 5.0, 0.0, 3.0],
        [7.0, 5.0, 6.0, 4.0, 3.0, 0.0],
    ]

    assert optimize_order_2opt(matrix, True) == reference_two_opt(matrix, True)
    assert optimize_order_2opt(matrix, False) == reference_two_opt(matrix, False)


def test_incremental_cost_matches_original_for_asymmetric_matrix() -> None:
    matrix: list[list[float]] = [
        [0.0, 3.0, 9.0, 8.0, 6.0],
        [7.0, 0.0, 2.0, 5.0, 9.0],
        [4.0, 8.0, 0.0, 3.0, 7.0],
        [6.0, 4.0, 9.0, 0.0, 2.0],
        [5.0, 7.0, 3.0, 8.0, 0.0],
    ]

    assert optimize_order_2opt(matrix, True) == reference_two_opt(matrix, True)
    assert optimize_order_2opt(matrix, False) == reference_two_opt(matrix, False)


def test_incremental_cost_rejects_unreachable_reversed_edges() -> None:
    matrix: list[list[float]] = [
        [0.0, 1.0, 5.0, 8.0],
        [1.0, 0.0, 1.0, 5.0],
        [5.0, None, 0.0, 1.0],  # type: ignore[list-item]
        [8.0, 5.0, 1.0, 0.0],
    ]

    order = optimize_order_2opt(matrix, keep_first=True)

    assert order == [0, 1, 2, 3]
