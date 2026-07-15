"""Local-only 2-opt enhancement layered on the official route optimizer."""

from services.geo_extras import optimize_order_nearest_neighbor


def _route_total(durations: list[list[float]], order: list[int]) -> float:
    total = 0.0
    for start, end in zip(order, order[1:]):
        duration = durations[start][end]
        if duration is None:
            return float("inf")
        total += duration
    return total


def optimize_order_2opt(
    durations: list[list[float]], keep_first: bool,
) -> list[int]:
    """Improve nearest-neighbour ordering by repeatedly reversing segments."""
    size = len(durations)
    if size <= 2:
        return list(range(size))

    order = optimize_order_nearest_neighbor(durations, keep_first)
    best_cost = _route_total(durations, order)
    improved = True
    while improved:
        improved = False
        start_index = 1 if keep_first else 0
        for left in range(start_index, size - 1):
            for right in range(left + 1, size):
                candidate = order[:]
                candidate[left:right + 1] = reversed(order[left:right + 1])
                candidate_cost = _route_total(durations, candidate)
                if candidate_cost < best_cost - 1e-4:
                    order = candidate
                    best_cost = candidate_cost
                    improved = True
                    break
            if improved:
                break
    return order
