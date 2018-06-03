import random
from abc import ABC, abstractmethod
from random import uniform, choice
from typing import Dict

from elevate.TravelGoal import TravelGoal


class TravelBehavior(ABC):

    def __init__(self, num_floors):
        self.num_floors = num_floors

    def random_nonzero_floor(self):
        return random.randint(1, self.num_floors)

    """
    A travel behavior is a class that is good at generating behaviors of people in different situations, e.g. at an
    office building, apartment complex, parking garage, etc.

    This allows us to test different algorithm under different experimental conditions.
    """
    @abstractmethod
    def generate_path(self):
        pass


class OfficeBuildingTravelBehavior(TravelBehavior):
    """
    Times are always in seconds. 0 = 7am
    """
    d_min = 60
    d_hr = 60 * d_min

    t_7am = 0
    t_8am = t_7am + d_hr
    t_12pm = t_7am + 5 * d_hr
    t_5pm = t_7am + 10 * d_hr

    def __init__(self, num_floors, start_t_mean=t_8am, start_t_sd=(35 * d_min), p_lunch=.8,
                 lunch_start_t_mean=(t_12pm + 15 * d_min), lunch_start_t_sd=(25 * d_min),
                 lunch_duration_t_mean=(50 * d_min), lunch_duration_t_sd=(15 * d_min), quittin_t_mean=t_5pm,
                 quittin_t_sd=d_hr, p_trip=.5, trip_t_mean=(30 * d_min), trip_t_sd=(15 * d_min),
                 trip_t_min=(10 * d_min), p_trip_to_0=.6):
        super().__init__(num_floors)
        self.start_t_mean = start_t_mean
        self.start_t_sd = start_t_sd
        self.p_lunch = p_lunch
        self.lunch_start_t_mean = lunch_start_t_mean
        self.lunch_start_t_sd = lunch_start_t_sd
        self.lunch_duration_t_mean = lunch_duration_t_mean
        self.lunch_duration_t_sd = lunch_duration_t_sd
        self.quittin_t_mean = quittin_t_mean
        self.quittin_t_sd = quittin_t_sd
        self.p_trip = p_trip
        self.trip_t_mean = trip_t_mean
        self.trip_t_sd = trip_t_sd
        self.trip_t_min = trip_t_min
        self.p_trip_to_0 = p_trip_to_0

    def start_time(self):
        t = 0
        while t <= 0:
            t = random.gauss(self.start_t_mean, self.start_t_sd)
        return t

    def lunch(self, start_time):
        lunch_start = random.gauss(self.lunch_start_t_mean, self.lunch_start_t_sd)
        lunch_duration = random.gauss(self.lunch_duration_t_mean, self.lunch_duration_t_sd)
        return max(lunch_start, start_time + 150*60), max(lunch_duration, 0)

    def quittin_t(self):
        t = random.gauss(self.quittin_t_mean, self.quittin_t_sd)
        return max(t, 0)

    def trip_duration(self):
        t = random.gauss(self.trip_t_mean, self.trip_t_sd)
        return t if t > self.trip_t_min else self.trip_t_min

    def random_start_time(self):
        return random.gauss(self.start_t_mean, self.start_t_sd)

    def generate_path(self):
        goals = []
        # In the morning, I go to my office floor:
        office_floor = self.random_nonzero_floor()
        start_t = self.start_time()
        goals.append(TravelGoal(self.start_time(), 0, office_floor))
        # At lunch, I go down
        if random.random() < self.p_lunch:
            lunch_start, lunch_duration = self.lunch(start_t)
            goals.append(TravelGoal(lunch_start, office_floor, 0))
            goals.append(TravelGoal(lunch_start + lunch_duration, 0, office_floor))
        # And at the end of the day I leave
        goals.append(TravelGoal(self.quittin_t(), office_floor, 0))

        # In addition, I may go from my office to some other floor at some point in the morning
        if random.random() < self.p_trip:
            trip_duration = self.trip_duration()
            if goals[0].time + self.trip_t_min \
                    < goals[1].time - self.trip_t_min - trip_duration:
                trip_start = random.uniform(goals[0].time + 15*60, goals[1].time - trip_duration )
                floor = 0 if random.random() < self.p_trip_to_0 else self.random_nonzero_floor()
                while floor == office_floor:
                    floor = self.random_nonzero_floor()
                goals.insert(1, TravelGoal(trip_start, office_floor, floor))
                goals.insert(2, TravelGoal(trip_start+trip_duration, floor, office_floor))

        # Or in the afternoon:
        if random.random() < self.p_trip:
            trip_duration = self.trip_duration()
            if goals[-2].time + self.trip_t_min \
                    < goals[-1].time - self.trip_t_min - trip_duration:
                trip_start = random.uniform(goals[-2].time + 15*60, goals[-1].time - trip_duration)
                floor = 0 if random.random() < self.p_trip_to_0 else self.random_nonzero_floor()
                while floor == office_floor:
                    floor = self.random_nonzero_floor()
                goals.insert(-1, TravelGoal(trip_start, office_floor, floor))
                goals.insert(-1, TravelGoal(trip_start + trip_duration, floor, office_floor))

        return goals


class TravelBehaviorType(TravelBehavior):
    def __init__(self, num_floors, start_t, duration):
        super().__init__(num_floors)
        self.start_t = start_t
        self.duration = duration

    def get_t(self):
        return uniform(self.start_t, self.start_t + self.duration)

    @abstractmethod
    def generate_path(self):
        pass


class UpPeakTravelBehavior(TravelBehaviorType):

    def __init__(self, num_floors, start_t, duration):
        super().__init__(num_floors, start_t, duration)

    def generate_path(self):
        # Start at a uniform random time between start_t and duration
        # Go to a random floor from 0
        return [TravelGoal(self.get_t(), 0, self.random_nonzero_floor())]


class DownPeakTravelBehavior(TravelBehaviorType):

    def __init__(self, num_floors, start_t, duration):
        super().__init__(num_floors, start_t, duration)

    def generate_path(self):
        return [TravelGoal(self.get_t(), self.random_nonzero_floor(), 0)]


class UpDownPeakTravelBehavior(TravelBehaviorType):

    def __init__(self, num_floors, start_t, duration):
        super().__init__(num_floors, start_t, duration)

    def generate_path(self):
        if random.random() <= .5:
            return [TravelGoal(self.get_t(), self.random_nonzero_floor(), 0)]
        else:
            return [TravelGoal(self.get_t(), 0, self.random_nonzero_floor())]


class InterfloorTravelBehavior(TravelBehaviorType):

    def __init__(self, num_floors, start_t, duration):
        super().__init__(num_floors, start_t, duration)

    def generate_path(self):
        start = self.random_nonzero_floor()
        end = self.random_nonzero_floor()
        while end != start:
            end = self.random_nonzero_floor()
        return [TravelGoal(self.get_t(), start, end)]


class CompositeTravelBehavior(TravelBehavior):

    def __init__(self, num_floors, behaviors: Dict[TravelBehaviorType, float]):
        super().__init__(num_floors)
        assert .99999 < sum(behaviors.values()) < 1.00001  # make sure that its a proper distribution
        self.behaviors = behaviors

    def generate_path(self):
        r = random.random()
        # This chooses each item with correct probability
        for b, p in self.behaviors.items():
            if r < p:
                return b.generate_path()
            else:
                r -= p
