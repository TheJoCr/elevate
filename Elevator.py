from typing import Set

from elevate.Events import ElevatorStart
from elevate.TravelGoal import TravelGoal


class Elevator:
    __index = 1

    def __init__(self, location=0, is_stopped=True, passenger_goals: Set[TravelGoal] = set(),
                 last_start_event: ElevatorStart = None):
        self.__location = location
        self.__velocity = 0  # Can be + or - depending on the direction
        self.__is_stopped = is_stopped
        self.passenger_goals = passenger_goals
        self.last_start_event = last_start_event
        self.index = Elevator.__index
        Elevator.__index += 1

    def start_and_pick_up(self, new_travel_goals: Set[TravelGoal], start_event: ElevatorStart):
        assert self.is_stopped
        for g in new_travel_goals:
            assert self.location == g.start_floor

        self.velocity = 0
        self.is_stopped = False
        print("Picking up {} travel goal(s) handling {}".format(
            len(new_travel_goals), start_event.button_press_handled
        ))
        for new_travel_goal in new_travel_goals:
            self.passenger_goals.add(new_travel_goal)
        self.last_start_event = start_event

    def stop_and_drop_off(self) -> Set[TravelGoal]:
        """
        Drops off passengers whose goal is this floor and returns the list of their goals
        :return: A set of travel goals that are now satisfied
        """
        assert not self.is_stopped
        self.velocity = 0
        self.is_stopped = True
        completed_goals = set()
        for g in self.passenger_goals:
            if g.end_floor == self.location:
                completed_goals.add(g)
        # print("Dropped off {} people on floor".format(len(completed_goals), self.location))
        for g in completed_goals:
            self.passenger_goals.remove(g)
        return completed_goals

    @property
    def is_stopped(self):
        return self.__is_stopped

    @is_stopped.setter
    def is_stopped(self, is_stopped):
        # We can only set it if we change it
        assert self.__is_stopped is None or self.__is_stopped != is_stopped
        self.__is_stopped = is_stopped

    @property
    def velocity(self):
        return self.__velocity

    @velocity.setter
    def velocity(self, velocity):
        assert abs(velocity) <= 8
        self.__velocity = velocity

    @property
    def location(self):
        return self.__location

    @location.setter
    def location(self, location):
        assert -1 <= location <= 40  # We allow a slight dip bellow to slow down.
        self.__location = location

    def __repr__(self):
        return "{} (P={:.4}, V={:.4}) Stopped={} #on_board={}".format(
            str(self.index), float(self.location), float(self.velocity), self.is_stopped, len(self.passenger_goals))
