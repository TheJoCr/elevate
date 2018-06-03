import copy
import math
from copy import copy
from random import choice, random
from typing import Dict, List, Tuple

from elevate.ButtonPush import ButtonPush
from elevate.Elevator import Elevator
from elevate.Schedule import ElevatorSchedule
from elevate.Simulator import ElevatorSimulator
from elevate.TravelBehaviors import TravelBehavior, UpPeakTravelBehavior, UpDownPeakTravelBehavior, \
    DownPeakTravelBehavior, InterfloorTravelBehavior, CompositeTravelBehavior
from elevate.strategies.BaseElevatorStrategy import ElevatorStrategy
from elevate.strategies.BoringElevatorStrategy import BoringElevatorStrategy
from elevate.strategies.PriorBeliefElevatorStrategy import PriorBeliefElevatorStrategy


class SOSAElevatorStrategy(ElevatorStrategy):
    @staticmethod
    def assign_stops_randomly(elevators_to_stops, presses, directions):
        for press in presses:
            e = choice(list(elevators_to_stops.keys()))
            num_stops = len(elevators_to_stops[e])
            i = choice(range(num_stops)) if num_stops > 0 else 0
            if i == num_stops:
                directions[e] = press.direction
            elevators_to_stops[e].insert(i, (press.floor, True))  # true indicates its eligible for reassignment.

    @staticmethod
    def insert_randomly(plan:  Dict[Elevator, List[Tuple[int, bool]]], floor: int):
        e = choice(list(plan.keys()))
        num_stops = len(plan[e])
        i = choice(range(num_stops)) if num_stops > 0 else 0
        plan[e].insert(i, (floor, True))  # true indicates its eligible for reassignment.

    @staticmethod
    def clean_plan(plan: Dict[Elevator, List[int]]):
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

    @staticmethod
    def random_element(plan:  Dict[Elevator, List[Tuple[int, bool]]]) -> Tuple[int, bool]:
        e = choice(list(plan.keys()))
        num_stops = len(plan[e])
        while num_stops == 0:
            e = choice(list(plan.keys()))
            num_stops = len(plan[e])
        return choice(plan[e])

    @staticmethod
    def perturb(plan:  Dict[Elevator, List[Tuple[int, bool]]]):
        """
        Input is a plan where floors are marked with whether or not they are eligible to be perturbed.
        Output is a new plan after perturbing 1 single element
        :param plan:
        :return:
        """
        # Perturbation is 'dumb' in the sense that we just replace things randomly.
        # Select elements at random until we find one eligible for perturbation
        new_plan = copy(plan)
        e = SOSAElevatorStrategy.random_element(new_plan)
        while not e[1]:  # Need to be able to handle the other side as well - change order
            e = SOSAElevatorStrategy.random_element(new_plan)
        # Stick e somewhere else at random:
        SOSAElevatorStrategy.insert_randomly(new_plan, e[0])
        return new_plan

    @staticmethod
    def get_traffic_profile(current_time, duration=600) -> TravelBehavior:
        up_peak = 65 * 60  # just past 8 am
        up_down_peak = 6 * 60 * 60  # 1 pm
        down_peak = 10 * 60 * 60  # 5 pm
        peaks = [up_peak, up_down_peak, down_peak]
        ps = [abs(current_time - p) for p in peaks]
        map(lambda i: 1/i, ps)
        norm_factor = .9 / sum(ps)
        map(lambda i: norm_factor * i, ps)  # normalize to .9 - the rest is interfloor
        ps.append(.1)
        types = [
            UpPeakTravelBehavior(40, current_time, duration),
            UpDownPeakTravelBehavior(40, current_time, duration),
            DownPeakTravelBehavior(40, current_time, duration),
            InterfloorTravelBehavior(40, current_time, duration)]
        return CompositeTravelBehavior(40, dict(zip(types, ps)))

    @staticmethod
    def get_cost_of_plan(elevators, presses, current_time, plan, num_simulations=10):
        # Here, we simulate repeatedly
        travel_behavior = SOSAElevatorStrategy.get_traffic_profile(current_time)
        for _ in range(num_simulations):
            # Based on current_time, generate some basic traffic for the next few minutes
            # Just need to make this actually return some stuff...
            num_people = int(random.gaussian(15, 5))
            simulator = ElevatorSimulator(travel_behavior, PriorBeliefElevatorStrategy(plan))
            # Set up the simulator to look like the 'real' one we're in now.
            simulator.elevators = copy.deepcopy(elevators)
            new_presses = copy.deepcopy(presses)
            # TODO this won't work. We have to actually simulate stops for the pending presses... hmm

            simulator.pending_button_presses = new_presses
            # And run it.
            #
            cost = simulator.run(num_people)
            return cost.avg_wait  # Single objective baby!
        return 0

    @staticmethod
    def p_accept(old_cost, new_cost, t):
        if new_cost < old_cost:
            return 1
        else:
            loss = old_cost - new_cost
            assert loss <= 0
            # exp( (old_cost - new_cost) / t )
            return math.e ** (loss / t)

    def get_plan(self, elevators: List[Elevator], presses: List[ButtonPush], current_time) -> ElevatorSchedule:
        # Each elevator has a set of stops they have to hit, corresponding with the set of people on board.
        e_to_must_stops = self._get_already_planned_stops(elevators)
        e_to_stops = {e: [(s, False) for s in e_to_must_stops[e]] for e in e_to_must_stops}
        final_dirs = {}
        SOSAElevatorStrategy.assign_stops_randomly(e_to_stops, presses, final_dirs)
        old_plan = e_to_stops
        old_cost = SOSAElevatorStrategy.get_cost_of_plan(old_plan)

        # The cooling schedule: Basically how likely are we to accept a worse plan?
        t = 1000
        alpha = .9

        # The number of trials per iteration - this increases over time.
        num_trial_perturbations = 2
        beta = 1.2

        # Exit criteria
        max_nam_iterations = len(presses) * len(elevators)
        i = 0

        while i < max_nam_iterations:
            for _ in range(num_trial_perturbations):
                new_plan = SOSAElevatorStrategy.perturb(old_plan)
                new_cost = SOSAElevatorStrategy.get_cost_of_plan(new_plan)
                if random() < SOSAElevatorStrategy.p_accept(old_cost, new_cost, t):
                    old_plan = new_plan
                    old_cost = new_cost
            t *= alpha
            num_trial_perturbations = int(num_trial_perturbations * beta + .99999999)  # Round up
            i += 1

        SOSAElevatorStrategy.clean_plan(old_plan)
        print("Generated Plan")
        for e in old_plan:
            print(e, old_plan[e], final_dirs[e] if e in final_dirs else "")
        return ElevatorSchedule(old_plan, final_dirs, current_time)