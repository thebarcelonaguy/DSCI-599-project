import networkx as nx


def get_user_input():
    constraints = []

    num_tasks = int(input("Enter the number of tasks: "))

    for i in range(num_tasks):
        while True:
            duration = input(
                f"Enter the duration (in hours) of task {i + 1} (e.g., '2' or '1-2' for a range): "
            )
            if "-" in duration:
                try:
                    min_duration, max_duration = map(int, duration.split("-"))

                    if min_duration <= max_duration:
                        constraints.append(
                            (i, i + 1, range(min_duration, max_duration + 1))
                        )
                        break
                    else:
                        print(
                            "Invalid duration range. Please ensure the start of the range is less than or equal to the end."
                        )
                except ValueError:
                    print(
                        "Invalid range. Please enter in the correct format (e.g., '1-2')."
                    )
            else:
                try:
                    fixed_duration = int(duration)
                    constraints.append((i, i + 1, fixed_duration))
                    break
                except ValueError:
                    print("Invalid input. Please enter an integer.")

    return constraints, num_tasks


def convert_to_24_hour_format(time_str):
    """
    Converts a time string in the format "hh am/pm" to a 24-hour format.
    """
    time, period = time_str.split()
    hour = int(time)

    if period.lower() == "pm" and hour != 12:
        hour += 12
    elif period.lower() == "am" and hour == 12:
        hour = 0

    return hour


def format_constraints(constraints):
    formatted_constraints = []

    for constraint in constraints:
        task_i, task_j, duration = constraint

        if isinstance(duration, range):
            l = min(duration)
            u = max(duration)
            formatted_constraints.append(f"{l} <= t(x{task_j}) - t(x{task_i}) <= {u}")
        else:
            formatted_constraints.append(
                f"{duration} <= t(x{task_j}) - t(x{task_i}) <= {duration}"
            )

    return formatted_constraints


def build_graph(constraints, num_tasks, start_hour, end_hour):
    G = nx.DiGraph()

    G.add_node("x0")

    G.add_edge("x0", "x1", weight=start_hour)
    total_hours = end_hour - start_hour

    G.add_edge("x0", f"x{num_tasks}", weight=total_hours)

    for xi, xj, duration in constraints:
        if isinstance(duration, range):
            l = min(duration)
            u = max(duration)
        else:
            l = u = duration

        G.add_edge(f"x{xi}", f"x{xj}", weight=u)
        if not (f"x{xi}" == f"x{num_tasks}" and f"x{xj}" == "x0"):
            G.add_edge(f"x{xj}", f"x{xi}", weight=-l)

    return G


def bellman_ford(G, source):
    distances = {node: float("inf") for node in G.nodes()}
    predecessor = {node: None for node in G.nodes()}
    distances[source] = 0

    for _ in range(len(G.nodes()) - 1):
        for u, v, weight in G.edges(data="weight"):
            if distances[u] != float("inf") and distances[u] + weight < distances[v]:
                distances[v] = distances[u] + weight
                predecessor[v] = u

    for u, v, weight in G.edges(data="weight"):
        if distances[u] != float("inf") and distances[u] + weight < distances[v]:
            cycle = [v, u]
            while predecessor[u] not in cycle:
                cycle.append(predecessor[u])
                u = predecessor[u]
            cycle.append(predecessor[u])
            print("Negative cycle detected: ", " -> ".join(cycle))
            return (
                None,
                None,
            )

    return distances, predecessor


def print_graph(G):
    print("\nGraph:")
    print("Nodes:", G.nodes())
    print("Edges:")
    for edge in G.edges(data=True):
        print(f"{edge[0]} -> {edge[1]} (weight: {edge[2]['weight']})")


def time_conversion(hour, start_hour):
    """Converts the hour to a 12-hour format with AM/PM."""
    adjusted_hour = (hour + start_hour) % 24
    if adjusted_hour == 0:
        return "12 AM"
    elif adjusted_hour < 12:
        return f"{adjusted_hour} AM"
    elif adjusted_hour == 12:
        return "12 PM"
    else:
        return f"{adjusted_hour - 12} PM"


def main():
    constraints, num_tasks = get_user_input()
    while True:
        start_time_str = input(
            "Enter the hour you want to start your day (e.g., '5 am'): "
        )
        end_time_str = input(
            "Enter the hour you want to end your day (e.g., '10 pm'): "
        )

        start_hour = convert_to_24_hour_format(start_time_str)
        end_hour = convert_to_24_hour_format(end_time_str)

        if start_hour < end_hour:
            break
        else:
            print(
                "Invalid time range! Please make sure the start time is earlier than the end time. Try again."
            )

    total_hours = end_hour - start_hour

    constraints.append((0, num_tasks, range(0, total_hours + 1)))

    print("\nConstraints:")
    formatted_constraints = format_constraints(constraints)
    for constraint in formatted_constraints:
        print(constraint)

    G = build_graph(constraints, num_tasks, start_hour, end_hour)
    G_earliest = G.reverse(copy=True)

    print_graph(G)

    result = bellman_ford(G_earliest, "x0")
    if result is None:
        print("Negative cycle detected for latest start times. No solution exists.")
    else:
        distances_earliest, _ = result
        print("\nEarliest start times:")
        for node in sorted(distances_earliest.keys(), key=lambda x: (len(x), x)):
            if node == "x0":
                continue
            print(f"{node}: {time_conversion(-distances_earliest[node], start_hour)}")


if __name__ == "__main__":
    main()
