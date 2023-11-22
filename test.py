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


def adjust_constraints(
    constraints, task_to_change, new_start_time, num_tasks, start_hour, end_hour
):
    """
    Adjusts the constraints when a task's start time is changed by the user.
    Only the constraints for the tasks that come after the fixed task are updated.
    """

    new_start_hour = convert_to_24_hour_format(new_start_time)
    updated_task_index = task_to_change
    new_constraints = []

    # Adjust constraints for the remaining tasks relative to the updated task
    for i, (task_i, task_j, duration) in enumerate(constraints):
        if task_i >= updated_task_index:
            # Reindex the tasks relative to the updated task
            new_task_i = task_i - updated_task_index
            new_task_j = task_j - updated_task_index
            new_constraints.append((new_task_i, new_task_j, duration))

    # Adjust the global constraint for the end of the day based on the new start time
    remaining_hours = end_hour - new_start_hour
    new_constraints.insert(
        0, (0, num_tasks - updated_task_index, range(0, remaining_hours + 1))
    )

    return new_constraints


# This is the corrected adjust_constraints function
# Now I will integrate this function back into the main program and run it to ensure it works correctly.


def main():
    constraints, num_tasks = get_user_input()
    last_updated_task = 0
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

    # Run Bellman-Ford for earliest start times
    G_earliest = G.reverse(copy=True)
    print(print_graph(G))
    print("\nCalculating earliest start times...")
    result_earliest = bellman_ford(G_earliest, "x0")
    if result_earliest == (None, None):
        print("Negative cycle detected for earliest start times. No solution exists.")
        return 0
    else:
        distances_earliest, _ = result_earliest

    # Run Bellman-Ford for latest start times
    print("\nCalculating latest start times...")
    result_latest = bellman_ford(G, "x0")
    if result_latest == (None, None):
        print("Negative cycle detected for latest start times. No solution exists.")
        return 0
    else:
        distances_latest, _ = result_latest

    print("\nTotal Duration of Shortest Paths for Earliest Start Times:")
    distances_earliest, _ = result_earliest
    for node in sorted(distances_earliest.keys(), key=lambda x: (len(x), x)):
        if node == "x0":
            continue
        total_duration_earliest = -distances_earliest[
            node
        ]  # Use negative value for earliest start times
        print(f"Total duration to {node} (Earliest): {total_duration_earliest} hour(s)")

    print("\nTotal Duration of Shortest Paths for Latest Start Times:")
    distances_latest, _ = result_latest
    for node in sorted(distances_latest.keys(), key=lambda x: (len(x), x)):
        if node == "x0":
            continue
        total_duration_latest = distances_latest[node]
        print(f"Total duration to {node} (Latest): {total_duration_latest} hour(s)")

    # Display schedules
    print("\nEarliest start times:")
    for node in sorted(distances_earliest.keys(), key=lambda x: (len(x), x)):
        if node == "x0":
            continue
        print(f"{node}: {time_conversion(-distances_earliest[node], start_hour)}")

    print("\nLatest start times:")
    for node in sorted(distances_latest.keys(), key=lambda x: (len(x), x)):
        if node == "x0":
            continue
        print(f"{node}: {time_conversion(distances_latest[node], start_hour)}")

    original_earliest_times = {
        node: -distances_earliest[node] for node in distances_earliest
    }
    original_latest_times = {node: distances_latest[node] for node in distances_latest}

    print("RITEN IS A GOOD BOY", original_earliest_times)
    print("MESSSSSSSSi", original_latest_times)

    # Ask if the user wants to change anything
    while True:
        change_schedule = (
            input("Would you like to change any task in the schedule? (yes/no): ")
            .strip()
            .lower()
        )

        if change_schedule == "no":
            break  # Exit the loop if the user doesn't want to change the schedule

        # Display the range of start times for each task that can be changed
        print("\nYou can change the start times of the following tasks:")
        for i in range(1, num_tasks - last_updated_task + 1):
            task_key = f"x{i}"
            if (
                task_key in original_earliest_times
                and task_key in original_latest_times
            ):
                earliest_start = time_conversion(
                    original_earliest_times[task_key], start_hour
                )
                latest_start = time_conversion(
                    original_latest_times[task_key], start_hour
                )
                print(
                    f"Task {i + last_updated_task}: Earliest start time: {earliest_start}, Latest start time: {latest_start}"
                )

        # Ask which task to change, ensuring it's not a completed task
        task_to_change = int(
            input("Which task number do you want to change? (Enter the task number): ")
        )
        if task_to_change <= last_updated_task:
            print(
                f"Task {task_to_change} has already been started or completed and cannot be changed."
            )
            continue

        # Update the last updated task
        last_updated_task = task_to_change

        # Ask for a new time within this range
        new_time_str = input(
            f"Enter the new start time for Task {task_to_change} (within the range above): "
        )
        new_time_hour = convert_to_24_hour_format(new_time_str)

        # Since the start time for a task has changed, we need to update the constraints and graph
        constraints = adjust_constraints(
            constraints, task_to_change, new_time_str, num_tasks, start_hour, end_hour
        )
        for c in constraints:
            print(format_constraints([c]))
        updated_task_index = task_to_change
        # Rebuild the graph with updated constraints for the uncompleted tasks

        G_updated = build_graph(
            constraints,  # Only use constraints from updated tasks onwards
            num_tasks - updated_task_index,  # Adjust the number of tasks accordingly
            start_hour,
            end_hour,
        )
        print(print_graph(G_updated))
        # Run Bellman-Ford from the updated task considered as the new 'x0'
        print(
            "\nRecalculating times for subsequent tasks starting from the updated task..."
        )

        result_earliest_updated = bellman_ford(G_updated.reverse(copy=True), "x0")

        result_latest_updated = bellman_ford(G_updated, "x0")

        print(result_earliest_updated)
        print(result_latest_updated)

        if (
            result_earliest_updated[0] is not None
            and result_latest_updated[0] is not None
        ):
            original_earliest_times = {
                f"x{i - last_updated_task+1}": dist
                for i, dist in enumerate(
                    result_earliest_updated[0].values(), start=last_updated_task + 1
                )
            }
            original_latest_times = {
                f"x{i - last_updated_task+1}": dist
                for i, dist in enumerate(
                    result_latest_updated[0].values(), start=last_updated_task + 1
                )
            }

        print("hi", original_earliest_times)
        print("bvye", original_latest_times)
        # Check for negative cycles in the updated graph
        if result_earliest_updated[0] is None or result_latest_updated[0] is None:
            print(
                "Negative cycle detected after updating the task. No solution exists."
            )
            return 0

        if result_earliest_updated == (None, None):
            print(
                "Negative cycle detected for earliest start times. No solution exists."
            )
            return 0
        else:
            distances_earliest_updated, _ = result_earliest_updated

        print("\nEarliest start times:")
        for node in sorted(
            distances_earliest_updated.keys(), key=lambda x: (len(x), x)
        ):
            if node == "x0":
                continue
            print(
                f"{node}: {time_conversion(-distances_earliest_updated[node], new_time_hour)}"
            )

        print("\nCalculating latest start times...")
        if result_latest_updated == (None, None):
            print("Negative cycle detected for latest start times. No solution exists.")
            return 0
        else:
            distances_latest_updated, _ = result_latest_updated

        print("\nLatest start times:")
        for node in sorted(distances_latest_updated.keys(), key=lambda x: (len(x), x)):
            if node == "x0":
                continue
            print(
                f"{node}: {time_conversion(distances_latest_updated[node], new_time_hour)}"
            )


if __name__ == "__main__":
    main()
