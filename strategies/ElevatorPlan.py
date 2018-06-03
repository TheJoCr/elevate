from typing import List

from elevate.ButtonPush import ButtonPush


class ElevatorPlan:
    def __init__(self, handled_presses: List[ButtonPush]):
        self.handled_presses = handled_presses

    def as_runs(self ) -> List[Tuple[str, List[int], List[float]]]:
        if len(stops) == 0:
            return []
        current_run = (ElevatorPhysicsCalculator.direction(current_loc, stops[0]), [], [])
        runs = [current_run]
        i = 1
        while i < len(stops):
            direction = ElevatorPhysicsCalculator.direction(stops[i - 1], stops[i])
            if current_run[0] == direction:
                # Append to current
                current_run[1].append(stops[i])
                current_run[2].append(0)
            else:
                # New run
                current_run = (direction, [stops[i]], [0])
                runs.append(current_run)
            i += 1
        self.update_run_times(runs)
        return runs