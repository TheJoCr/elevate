import unittest
from heapq import heappop

from elevate.ButtonPush import ButtonPush
from elevate.strategies.BoringElevatorStrategy import BoringElevatorStrategy
from elevate.TravelGoal import TravelGoal
from elevate.Elevator import Elevator


class TestBoringSchedule(unittest.TestCase):
    def test_insert(self):
        # Start on floor 0, with passengers on 3 and 6.
        # Ensure that 2, 4, and 8 get added correctly
        # and that 4 down gets added at the end
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

        schedule = BoringElevatorStrategy().get_plan([e], pending_presses, 0)

        self.assertEqual(
            schedule.elevator_to_floors[e],
            [2, 3, 4, 6, 8, 4],
            "Stopping at floors in the wrong order!"
        )

    def test_insert_2_elevators(self):
        # Start on floor 0, with passengers on 3 and 6.
        # Ensure that 2, 4, and 8 get added correctly
        # and that 4 down gets added at the end
        e1 = Elevator()
        e1.passenger_goals = [
            TravelGoal(0, 0, 3),
        ]

        e2 = Elevator(3)  # Going down now (but stopped)
        e2.passenger_goals = [
            TravelGoal(0, 6, 0),
            TravelGoal(0, 4, 1),
        ]

        pending_presses = [
            ButtonPush(2, "UP", 0),
            ButtonPush(8, "UP", 2),
            ButtonPush(4, "UP", 1),
            ButtonPush(4, "DOWN", 0),
        ]

        schedule = BoringElevatorStrategy().get_plan([e1, e2], pending_presses, 0)

        self.assertEqual(
            schedule.elevator_to_floors[e1],
            [2, 3, 4],
            "Stopping at floors in the wrong order!"
        )

        self.assertEqual(
            schedule.elevator_to_floors[e2],
            [1, 0, 8],
            "Stopping at floors in the wrong order!"
        )

    def test_complicated(self):
        # Start on floor 0, with passengers on 3 and 6.
        # Ensure that 2, 4, and 8 get added correctly
        # and that 4 down gets added at the end
        e1 = Elevator()
        e1.passenger_goals = [
            TravelGoal(0, 0, 3),
        ]

        e2 = Elevator(3, True)
        e2.passenger_goals = []

        pending_presses = [
            ButtonPush(2, "UP", 1),
            ButtonPush(8, "UP", 2),
            ButtonPush(4, "UP", 1),
            ButtonPush(4, "DOWN", 9),
            ButtonPush(6, "UP", 2),
            ButtonPush(2, "UP", 1),
            ButtonPush(1, "DOWN", 3),
            ButtonPush(6, "DOWN", 5),
            ButtonPush(8, "UP", 1),
            ButtonPush(2, "DOWN", 6),
        ]

        schedule = BoringElevatorStrategy().get_plan([e1, e2], pending_presses, 0)
        # Not sure if this is right.. Just to make sure that if there are changes I notice them.
        self.assertEqual(
            schedule.elevator_to_floors[e1],
            [3, 6, 8, 6, 2, 1],
            "Stopping at floors in the wrong order!"
        )

        self.assertEqual(
            schedule.elevator_to_floors[e2],
            [2, 8, 2, 4],
            "Stopping at floors in the wrong order!"
        )

    def test_gen_end_events(self):
        e = Elevator(0, True)
        e.passenger_goals = [
        ]
        pending_presses = [
            ButtonPush(2, "DOWN", 0),
        ]

        schedule = BoringElevatorStrategy().get_plan([e], pending_presses, 0)

        self.assertEqual(
            schedule.elevator_to_floors[e],
            [2],
            "Stopping at floors in the wrong order!"
        )

        events = schedule.event_gen_and_apply()
        e1 = heappop(events)
        self.assertEqual(e1.floor, 0)  # Start event on floor 1
        self.assertEqual(e1.button_press_handled.direction, "UP")  # Start event on floor 1

        e2 = heappop(events)
        self.assertEqual(e2.floor, 2)  # End event on floor 2

        e3 = heappop(events)
        self.assertEqual(e3.floor, 2)  # Start event on floor 3
        self.assertEqual(e3.button_press_handled.direction, "DOWN")  # Start event on floor 3

        self.assertEqual(len(events), 0, "Should have exhausted all events!")

    def test_gen_start(self):
        e = Elevator(0, True)
        e.passenger_goals = [
        ]
        pending_presses = [
            ButtonPush(0, "UP", 0),
        ]

        schedule = BoringElevatorStrategy().get_plan([e], pending_presses, 0)

        self.assertEqual(
            schedule.elevator_to_floors[e],
            [0],
            "Stopping at floors in the wrong order!"
        )

        events = schedule.event_gen_and_apply()
        e1 = heappop(events)
        self.assertEqual(e1.floor, 0)

        self.assertEqual(len(events), 0)

    def test_goes_to_zero(self):
        e = Elevator(5, False)
        e.passenger_goals = [
        ]
        pending_presses = [

        ]

        schedule = BoringElevatorStrategy().get_plan([e], pending_presses, 0)

        self.assertEqual(
            schedule.elevator_to_floors[e],
            [0],
            "Stopping at floors in the wrong order!"
        )


if __name__ == '__main__':
    unittest.main()
