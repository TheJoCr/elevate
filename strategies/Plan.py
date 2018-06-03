from typing import Dict

from elevate.Elevator import Elevator
from elevate.strategies.ElevatorPlan import ElevatorPlan


class Plan:
    def __init__(self, elevator_to_plan: Dict[Elevator, ElevatorPlan]):
        self.elevator_to_plan = elevator_to_plan

    def for_elevator(self, elevator: Elevator):
        return self.elevator_to_plan.get(elevator)
