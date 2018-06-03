from random import shuffle
from typing import List, Dict, Tuple

from elevate.ButtonPush import ButtonPush
from elevate.Elevator import Elevator
from elevate.Events import ElevatorStop
from elevate.PhysicsCalculator import ElevatorPhysicsCalculator
from elevate.Schedule import ElevatorSchedule
from elevate.strategies.BaseElevatorStrategy import ElevatorStrategy


class BoringElevatorStrategy(ElevatorStrategy):

    def schedule_from_runs(self,
                           already_planned_stops: Dict[Elevator, List[int]],
                           e_to_runs: Dict[Elevator, List[Tuple[str, List[int], List[float]]]],
                           current_time: float):
        plan = {e: [] for e in e_to_runs.keys()}
        final_dirs = {}
        for e in e_to_runs.keys():
            for run in e_to_runs[e]:
                for stop in run[1]:
                    if len(plan[e]) == 0 or plan[e][-1] != stop:
                        # Check to eliminate duplicates here
                        plan[e].append(stop)
            # We add a final direction that we're going if we think that we'll be picking someone up on a floor.
            if len(e_to_runs[e]) > 0 and e_to_runs[e][-1][1][-1] not in already_planned_stops[e]:
                final_dirs[e] = e_to_runs[e][-1][0]

            # All elevators that are not doing anything and are not located on floor 0 are instructed to return there
            # and wait fur further instruction.
            if len(e_to_runs[e]) == 0 and not e.is_stopped:
                plan[e] = [0]

        print("Final set of runs:")
        for e in plan:
            print("Elevator:" + str(e))
            for run in e_to_runs[e]:
                print("    {}".format(run))
        print("Generated Plan")
        for e in plan:
            print(e, plan[e], final_dirs[e] if e in final_dirs else "")
        return ElevatorSchedule(plan, final_dirs, current_time)

    def update_run_times(self, runs: List[Tuple[str, List[int], List[float]]]):
        # We assume that the start time on the first run is accurate and work our way from there.
        if len(runs) == 0 or len(runs[0][1]) == 0:
            return

        prev_time = runs[0][2][0]
        prev_floor = runs[0][1][0]
        for run in runs:
            for i in range(len(run[1])):
                # Find time from prev floor to this floor
                new_floor = run[1][i]
                delta_t = ElevatorPhysicsCalculator.time_to(prev_floor, new_floor)
                new_t = prev_time + delta_t
                run[2][i] = new_t
                prev_time = new_t + ElevatorStop.duration
                prev_floor = new_floor

        print("Updated run times to: {}".format(runs) )

    def insert_button_push(self,
                           button_push: ButtonPush,
                           e_to_runs: Dict[Elevator, List[Tuple[str, List[int], List[float]]]],
                           current_time: float):
        """
        This inserts a button push into a series of runs, either by adding it to a an existing run,
        or by adding a new run if necessary.
        :param current_time: The time at which we are updating the schedule
        :param button_push: the button push to add
        :param e_to_runs: a map from
        :return: None. This updates the runs in place.
        """
        best_time_so_far = 100000000000  # a very large number
        best_run_so_far = None
        insert_at_index = -1
        insert_elevator = None

        elevators = list(e_to_runs.keys())
        shuffle(elevators)  # Shuffle to distribute load more evenly.
        for e in elevators:
            # Can we append to the very beginning?
            if len(e_to_runs[e]) > 0 and \
                    e_to_runs[e][0][0] == button_push.direction and \
                    self.is_floor_in_dir(e.location, button_push.floor, e_to_runs[e][0][0]) and \
                    self.is_floor_in_dir(button_push.floor, e_to_runs[e][0][1][0], e_to_runs[e][0][0]):
                time = ElevatorPhysicsCalculator.time_to(e.location, button_push.floor, e.velocity)
                time += current_time
                if time < best_time_so_far:
                    best_time_so_far = time
                    best_run_so_far = e_to_runs[e][0]
                    insert_at_index = 0
                    insert_elevator = e

            # Or at the very end?
            run_at_end = e_to_runs[e][-1] if len(e_to_runs[e]) > 0 else None
            # Only if there is nothing on this elevator yet -or- the last run goes in a different direction.
            # if it goes in the same direction, it'll be handled lower by appending to the last run.
            # This should ensure that every thing always gets at least one.
            prev_time = run_at_end[2][-1] if run_at_end is not None else current_time
            prev_floor = run_at_end[1][-1] if run_at_end is not None else e.location
            time = prev_time + ElevatorPhysicsCalculator.time_to(prev_floor, button_push.floor)
            new_run = (button_push.direction, [button_push.floor], [time])
            if time < best_time_so_far:
                best_time_so_far = time
                best_run_so_far = new_run
                insert_at_index = -1
                insert_elevator = e

            # Lets see if we can add it to any of the existing runs:
            first_run = True
            for run in e_to_runs[e]:
                (d, stops, times) = run
                # First, we look for way to insert it between stops.
                if d is not None and d == button_push.direction and len(stops) > 1:
                    # Look for a way to squeeze it in.
                    for i, start_floor, end_floor, start_time in \
                            zip(range(0, len(stops) - 1), stops, stops[1:], times):
                        if self.is_floor_in_dir(start_floor, button_push.floor, d) \
                                and self.is_floor_in_dir(button_push.floor, end_floor, d):
                            time = start_time + ElevatorPhysicsCalculator.time_to(start_floor, button_push.floor)
                            if time < best_time_so_far:
                                best_time_so_far = time
                                best_run_so_far = run
                                insert_at_index = i + 1
                                insert_elevator = e

                # Is there a way to add it to the beginning or end of a run?
                if d is not None and d == button_push.direction and len(stops) > 0:
                    if self.is_floor_in_dir(stops[-1], button_push.floor, d):
                        time = times[-1] + ElevatorPhysicsCalculator.time_to(stops[-1], button_push.floor)
                        if time < best_time_so_far:
                            best_time_so_far = time
                            best_run_so_far = run
                            insert_at_index = len(stops)
                            insert_elevator = e

                    # Does it fit on the front of a run?
                    if not first_run and self.is_floor_in_dir(button_push.floor, stops[0], d):
                        time = ElevatorPhysicsCalculator.time_to(e.location, button_push.floor, e.velocity)
                        time += current_time
                        if time < best_time_so_far:
                            best_time_so_far = time
                            best_run_so_far = run
                            insert_at_index = 0
                            insert_elevator = e

                first_run = False

        if insert_at_index == -1:  # Add a run.
            print("Adding run {}".format(best_run_so_far))
            e_to_runs[insert_elevator].append(best_run_so_far)
            # And update the timing on those runs.
        else:
            # Then we are adding to an existing run.
            print("Adding {} to run {} at index {} (t = {})".format(
                button_push, best_run_so_far, insert_at_index, best_time_so_far))
            best_run_so_far[1].insert(insert_at_index, button_push.floor)
            best_run_so_far[2].insert(insert_at_index, best_time_so_far)

        # Last step is to update times on the elevator that was modified.
        self.update_run_times(e_to_runs[insert_elevator])

    def get_plan(self, elevators: List[Elevator], presses: List[ButtonPush], current_time) -> ElevatorSchedule:
        # First, get their current directions
        elevator_directions = self._get_current_directions(elevators)
        elevator_stops = self._get_already_planned_stops(elevators)
        # This gives us timing information for each of the elevators
        schedule = ElevatorSchedule(elevator_stops, {}, current_time)
        elevator_to_stop_times = schedule.elevator_to_time  # This is calculated at creation of a schedule
        # We combine elevator stops, directions, and times to produce a variety of runs.
        # These are stored as a map from elevators to an in-order list of runs.
        e_to_runs = {
            e: [(elevator_directions[e], elevator_stops[e], elevator_to_stop_times[e])]
            if elevator_directions[e] is not None else [] for e in elevators
        }

        for button_push in sorted(presses, key=lambda p: p.time):
            self.insert_button_push(button_push, e_to_runs, current_time)

        # The final step is recombining all of the runs into a schedule.
        return self.schedule_from_runs(elevator_stops, e_to_runs, current_time)
