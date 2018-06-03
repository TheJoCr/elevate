from random import choice
from typing import List

from elevate.ButtonPush import ButtonPush
from elevate.Elevator import Elevator
from elevate.Schedule import ElevatorSchedule
from elevate.strategies.BaseElevatorStrategy import ElevatorStrategy


class RandomElevatorStrategy(ElevatorStrategy):
    def assign_stops_randomly(self, elevators_to_stops, presses):
        directions = {}
        for press in presses:
            e = choice(list(elevators_to_stops.keys()))
            num_stops = len(elevators_to_stops[e])
            i = choice(range(num_stops)) if num_stops > 0 else 0
            if i == num_stops:
                directions[e] = press.direction
            elevators_to_stops[e].insert(i, press.floor)
        return directions

    def get_plan(self, elevators: List[Elevator], presses: List[ButtonPush], current_time) -> ElevatorSchedule:
        # Each elevator has a set of stops they have to hit, corresponding with the set of people on board.
        e_to_must_stops = self._get_already_planned_stops(elevators)
        final_dirs = self.assign_stops_randomly(e_to_must_stops, presses)
        plan = e_to_must_stops
        # Handle when you're doing nothing
        for e in plan:
            if plan[e] == [] and not e.is_stopped:
                plan[e] = [12]
        # Remove duplicates
        for e in plan:
            if len(plan[e]) > 1:
                remove = []
                for i, s1, s2 in zip(range(len(plan[e])), plan[e], plan[e][1:]):
                    if s1 == s2:
                        remove.append(i)
                for r in reversed(remove):
                    del plan[e][r]
        print("Generated Plan")
        for e in plan:
            print(e, plan[e], final_dirs[e] if e in final_dirs else "")
        return ElevatorSchedule(plan, final_dirs, current_time)