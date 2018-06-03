from typing import List, Dict, Tuple

from elevate.Elevator import Elevator
from elevate.PhysicsCalculator import ElevatorPhysicsCalculator
from elevate.TravelGoal import TravelGoal


class RunStats:
    def __init__(self, completed_goals: List[TravelGoal], elevator_history: Dict[Elevator, List[Tuple[float, int, int]]]):
        self.avg_wait = 0
        self.avg_total = 0
        self.max_wait = 0
        self.max_total = 0
        for g in completed_goals:
            wait_time, total_time = g.board_time - g.time, g.finish_time - g.time
            self.max_wait = max(wait_time, self.max_wait)
            self.max_total = max(total_time, self.max_total)
            self.avg_wait += wait_time
            self.avg_total += total_time
        self.avg_wait /= len(completed_goals)
        self.avg_total /= len(completed_goals)

        self.total_dist = 0
        for e in elevator_history:
            for h1, h2 in zip(elevator_history[e], elevator_history[e][1:]):
                self.total_dist += abs(h2[1] - h1[1])

        self.total_dist += ElevatorPhysicsCalculator.floors_to_meters(self.total_dist)

    def __repr__(self):
        return "Wait (avg: {} max: {}). Total: (avg: {} max: {}). Dist={}".format(
            self.avg_wait, self.max_wait, self.avg_total, self.max_total, self.total_dist)


if __name__ == '__main__':
    goal1 = TravelGoal(5, 0, 10)
    goal1.board_time = 7
    goal1.finish_time = 15

    goal2 = TravelGoal(10, 10, 0)
    goal2.board_time = 15
    goal2.finish_time = 30

    elevator1 = Elevator()
    elevator1_stops = [
        (0, 1, 1),
        (5, 10, 5),
        (10, 10, 5)
    ]

    elevator2 = Elevator()

    elevator2_stops = [
        (10, 1, 1),
        (5, 10, 5),
        (1, 10, 5)
    ]

    stats = RunStats([goal1, goal2], {elevator1: elevator1_stops, elevator2: elevator2_stops})

    print(stats)
