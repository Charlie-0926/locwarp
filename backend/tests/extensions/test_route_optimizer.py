from extensions.custom.route_optimizer import optimize_order_2opt


def route_cost(matrix: list[list[float]], order: list[int]) -> float:
    return sum(matrix[start][end] for start, end in zip(order, order[1:]))


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
