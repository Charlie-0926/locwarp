"""Local-only 2-opt enhancement layered on the official route optimizer."""

from services.geo_extras import optimize_order_nearest_neighbor


def optimize_order_2opt(
    durations: list[list[float]], keep_first: bool,
) -> list[int]:
    """Improve nearest-neighbour ordering by repeatedly reversing segments.

    Candidate costs are evaluated from the changed boundary edges and a
    prefix sum of reversed internal-edge costs.  This keeps each evaluation
    O(1), including for asymmetric road-duration matrices.  The route slice
    is copied only when an improving move is accepted.
    """
    size = len(durations)
    if size <= 2:
        return list(range(size))

    order = optimize_order_nearest_neighbor(durations, keep_first)
    route_size = len(order)
    if route_size <= 2:
        return order

    improved = True
    while improved:
        improved = False

        # reversed_internal_delta[i + 1] - reversed_internal_delta[i]
        # is the cost change when edge order[i] -> order[i + 1] is traversed
        # in reverse.  A segment's internal reversal cost is then one prefix
        # subtraction, even when the duration matrix is asymmetric.
        reversed_internal_delta = [0.0] * route_size
        reversed_invalid_edges = [0] * route_size
        for index in range(route_size - 1):
            start = order[index]
            end = order[index + 1]
            forward_duration = durations[start][end]
            reverse_duration = durations[end][start]
            reversed_invalid_edges[index + 1] = reversed_invalid_edges[index]
            if forward_duration is None or reverse_duration is None:
                reversed_internal_delta[index + 1] = (
                    reversed_internal_delta[index]
                )
                reversed_invalid_edges[index + 1] += 1
                continue
            reversed_internal_delta[index + 1] = (
                reversed_internal_delta[index]
                + reverse_duration
                - forward_duration
            )

        start_index = 1 if keep_first else 0
        for left in range(start_index, route_size - 1):
            for right in range(left + 1, route_size):
                if (
                    reversed_invalid_edges[right]
                    - reversed_invalid_edges[left]
                ):
                    continue
                delta = (
                    reversed_internal_delta[right]
                    - reversed_internal_delta[left]
                )
                if left > 0:
                    previous = order[left - 1]
                    first = order[left]
                    last = order[right]
                    new_duration = durations[previous][last]
                    old_duration = durations[previous][first]
                    if new_duration is None or old_duration is None:
                        continue
                    delta += (
                        new_duration
                        - old_duration
                    )
                if right + 1 < route_size:
                    first = order[left]
                    last = order[right]
                    following = order[right + 1]
                    new_duration = durations[first][following]
                    old_duration = durations[last][following]
                    if new_duration is None or old_duration is None:
                        continue
                    delta += (
                        new_duration
                        - old_duration
                    )

                if delta < -1e-4:
                    order[left:right + 1] = reversed(order[left:right + 1])
                    improved = True
                    break
            if improved:
                break
    return order
