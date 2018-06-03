from typing import Dict, List, Tuple

from elevate.ButtonPush import ButtonPush
from elevate.Elevator import Elevator
from elevate.PhysicsCalculator import ElevatorPhysicsCalculator
from elevate.Schedule import ElevatorSchedule
from elevate.strategies.BoringElevatorStrategy import BoringElevatorStrategy


class PriorBeliefElevatorStrategy(BoringElevatorStrategy):
    """
    This class extends the Boring elevator strategy by adding support for a preassigned set of stops that
    are granted preference as if they were stops that the user was already on.

    This is used when simulating how well a strategy proposed by SA will work under unexpected conditions.
    """
    def __init__(self, prior_elevators_to_stops: Dict[Elevator, List[int]]):
        self.prior_elevators_to_stops = prior_elevators_to_stops


    def get_plan(self, elevators: List[Elevator], presses: List[ButtonPush], current_time) -> ElevatorSchedule:
        # First, we construct the runs established from our prior belief.

        return super().get_plan(elevators, presses, current_time)

