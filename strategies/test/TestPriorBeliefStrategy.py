import unittest

from elevate.ButtonPush import ButtonPush
from elevate.Elevator import Elevator
from elevate.TravelGoal import TravelGoal
from elevate.strategies.PriorBeliefElevatorStrategy import PriorBeliefElevatorStrategy


class PriorBeliefTest(unittest.TestCase):

    def test_to_runs(self):
        strat = PriorBeliefElevatorStrategy({})
        runs = strat.to_runs([2, 3, 5, 8, 6, 2, 5])
        self.assertEqual(len(runs), 4)

        self.assertEqual(runs[0][1], [])
        self.assertEqual(runs[0][0], "DOWN")

        self.assertEqual(runs[1][1], [2, 3, 5, 8])
        self.assertEqual(runs[1][0], "UP")

        self.assertEqual(runs[2][1], [6, 2])
        self.assertEqual(runs[2][0], "DOWN")

        self.assertEqual(runs[3][1], [5])
        self.assertEqual(runs[3][0], "UP")


    def test_insert(self):
        # Start on floor 0, with passengers on 3 and 6.
        # Ensure that 2, 4, and 8 get added correctly
        # and that 4 down gets added at the end
        # with a prior belief that the best stops are 2 and 4
        e = Elevator()
        e.passenger_goals = [
            TravelGoal(0, 0, 3),
            TravelGoal(0, 0, 6)
        ]
        pending_presses = [
            ButtonPush(2, "UP", 3),
            ButtonPush(8, "UP", 2),
            ButtonPush(4, "UP", 1),
            ButtonPush(4, "DOWN", 0),
        ]
        prior_belief = {
            e: [2, 4]
        }

        schedule = PriorBeliefElevatorStrategy(prior_belief).get_plan([e], pending_presses, 0)

        self.assertEqual(
            schedule.elevator_to_floors[e],
            [2, 3, 4, 6, 8, 4],
            "Stopping at floors in the wrong order!"
        )


if __name__ == '__main__':
    unittest.main()
