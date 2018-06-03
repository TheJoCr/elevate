from abc import ABC, abstractmethod
from typing import List, Dict

from elevate.Elevator import Elevator
from elevate.Schedule import ElevatorSchedule


class ElevatorStrategy(ABC):

    @abstractmethod
    def get_plan(self, elevators, presses, current_time) -> ElevatorSchedule:
        pass

    def is_floor_in_dir(self, start_floor, end_floor, direction) -> bool:
        if direction == "UP":
            return start_floor < end_floor
        elif direction == "DOWN":
            return end_floor < start_floor
        elif direction is None:
            raise ValueError("Can't evaluate with direction of None!")
        else:
            raise ValueError("Unknown direction:" + direction)

    def _get_current_directions(self, elevators: List[Elevator]):
        elevator_directions = {}
        for e in elevators:
            direction = None
            if e.passenger_goals is None:
                if e.velocity > 0:
                    direction = "UP"
                elif e.velocity < 0:
                    direction = "DOWN"
                else:
                    direction = None
            else:
                for goal in e.passenger_goals:
                    direction = goal.direction()
                    break  # We only need the first one
            elevator_directions[e] = direction
        return elevator_directions

    def _get_already_planned_stops(self, elevators: List[Elevator]) -> Dict[Elevator, List[int]]:
        elevator_stops = {}
        for e in elevators:
            if e.passenger_goals is None:
                elevator_stops[e] = []
            else:
                stops = list(set(g.end_floor for g in e.passenger_goals))
                stops.sort(key=lambda floor: abs(floor - e.location))  # Sort by distance from current floor.
                elevator_stops[e] = stops
        return elevator_stops
