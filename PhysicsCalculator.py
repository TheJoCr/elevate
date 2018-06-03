import functools
from math import sqrt
from typing import Tuple

from prompt_toolkit.cache import memoized


class ElevatorPhysicsCalculator:
    meters_per_floor = 3.9

    @staticmethod
    def floors_to_meters(floor, meters_per_floor=meters_per_floor):
        return floor * meters_per_floor

    @staticmethod
    def meters_to_floors(meters, meters_per_floor=meters_per_floor):
        return meters / meters_per_floor

    @staticmethod
    @functools.lru_cache(2000)
    def time_to(start, stop, v_initial=0, a=1.2, v_max=8, meters_per_floor=meters_per_floor, ):
        """
        We calculate the amount of time it takes to move from one floor to another by assuming constant acceleration
        to a max velocity, and then constant deceleration at the end.

        These parameters are estimates.

        Meters per floor is about 3.9 in most office buildings:
        http://www.ctbuh.org/TallBuildings/HeightStatistics/HeightCalculator/tabid/1007/language/en-US/Default.aspx

        Acceleration of an elevator appears to be about 1.2 m/s^2 on average. Apparently it starts to be pretty
        uncomfortable around 1.5 m/s^2 per this link:
        https://www.treehugger.com/public-transportation/how-fast-should-elevator-go.html

        Max speed varies tremendously. But we'll estimate here about 8 m/s, though very quick elevators can move much
        faster, with some reaching 20+ m/s (generally only moving up though - down tends to be closer to 10 m/s)

        Note that with these parameters it takes about 7 floors to accelerate to speed and 7 to decelerate.

        :param start: Starting floor (can be a float if between floors)
        :param stop: Ending floor (the final floor)
        :param v_initial: The current speed of the elevator
        :param meters_per_floor: floor-to-floor height of a storey. In an office building, this is about 3.9
        :param v_max: the max speed of the elevator, set to a 'sane' default of 8 m/s
        :param a: the acceleration of the elevator, set to a 'sane' default of 1.2 m/s^2
        :return: the amount of time it will take to get to stop from start
        """
        d_total = (stop - start) * meters_per_floor
        t = ElevatorPhysicsCalculator(d_total, v_initial, a=a, v_max=v_max).delta_t
        # print("Takes {:.5} seconds from {} to {}".format(float(t), start, stop))
        return t

    def __init__(self, total_delta_loc, v_initial, a=1.2, v_max=8):
        if abs(v_initial) > v_max:
            raise ValueError("Cannot have v_initial greater than v_max!")
        self.total_delta_loc = total_delta_loc
        self.v_initial = v_initial
        self.a = abs(a) if total_delta_loc > 0 else -abs(a)
        self.v_max = abs(v_max) if total_delta_loc > 0 else -v_max
        self.achieved_v_max = self.achieved_v_max()
        self.delta_t = self.total_time()

    def achieved_v_max(self):
        if self.total_delta_loc == self.v_initial == 0:
            return 0

        half_v0_2 = .5 * (self.v_initial ** 2)
        if self.v_initial * self.total_delta_loc > 0 and \
                abs(half_v0_2) > abs(self.total_delta_loc * self.a):
            # Then our problem is reversed: we decelerate and then accelerate.
            # print("Delta_P:{}, A:{}, half_v0^2:{}".format(self.total_delta_loc, self.a, half_v0_2))
            pot_v_max_mag = sqrt(half_v0_2 - self.total_delta_loc * self.a)
            sign_v_max = -1 if self.v_initial > 0 else 1  # The opposite of the initial velocity
            self.a = -self.a
            return pot_v_max_mag * sign_v_max

        pot_v_max_mag = sqrt(self.total_delta_loc * self.a + half_v0_2)
        sign_v_max = 1 if self.total_delta_loc >= 0 else -1  # The same as the change in direction
        potential_v_max = sign_v_max * pot_v_max_mag
        # print("Potential v_max of {}".format(potential_v_max))
        achieved_v_max = \
            max(potential_v_max, self.v_max) if sign_v_max < 0 else min(potential_v_max, self.v_max)
        # print("Achieved v_max of {}".format(achieved_v_max))
        return achieved_v_max

    def total_time(self):
        # This is all algebra stuff - see the paper
        # Three terms. The last is an adjustment for the start speed
        #  (with a small adjustment made to the second term as well)
        if self.total_delta_loc == self.achieved_v_max == 0:
            return 0

        t_total = self.total_delta_loc / self.achieved_v_max + \
                  (self.achieved_v_max - self.v_initial) / self.a + \
                  (self.v_initial ** 2) / (2 * self.a * self.achieved_v_max)

        return t_total

    def state_at_t(self, t) -> Tuple[float, float]:
        """
        Gets (Position, Velocity) Tuple
        :param t:
        :return:
        """
        if self.a * self.total_delta_loc < 0:
            if t < .5 * (self.delta_t - (self.v_initial / self.a)):
                # Deceleration - Phase 1
                return self.accelerating_state(t)
            else:
                # Acceleration - Phase 2
                return self.decelerating_state(t)

        accel_end = self.accelerate_end_t()
        if t < accel_end:
            return self.accelerating_state(t)
        accel_end_p = self.accelerate_end_p()
        decel_begin = self.decelerate_begin_t(accel_end)
        if t < decel_begin:
            return self.steady_state(t, accel_end, accel_end_p)
        return self.decelerating_state(t)

    def accelerating_state(self, t) -> Tuple[float, float]:
        v = self.v_initial + self.a * t
        pos = self.v_initial * t + .5 * self.a * (t**2)
        return pos, v

    def accelerate_end_t(self):
        return (self.achieved_v_max - self.v_initial) / self.a

    def accelerate_end_p(self):
        return (self.achieved_v_max**2 - self.v_initial**2) / (2 * self.a)

    def steady_state(self, t, accel_end_t, accel_end_p) -> Tuple[float, float]:
        v = self.achieved_v_max
        pos = accel_end_p + (t - accel_end_t) * v
        return pos, v

    def decelerate_begin_t(self, accel_end_t):
        return self.delta_t - (self.v_max/self.a)

    def decelerate_begin_d(self, accel_end_p, accel_end, decel_begin):
        decel = accel_end_p + (decel_begin - accel_end) * self.achieved_v_max
        # Note: This can also be computed directly:
        # decel = self.total_delta_loc - (self.v_max**2/(2*self.a))
        # if abs(decel1 - decel2) > .0000001:
        #     print("Don't match")
        return decel

    def decelerating_state(self, t) -> Tuple[float, float]:
        v = self.a * (self.delta_t - t)
        pos = self.a * (self.delta_t * t - .5 * (t**2 + self.delta_t**2)) + self.total_delta_loc
        return pos, v

    @staticmethod
    def direction(current_floor, next_floor) -> str:
        return "UP" if next_floor > current_floor else "DOWN"


if __name__ == "___main__":
    ElevatorPhysicsCalculator.time_to(5, 0)
    ElevatorPhysicsCalculator.time_to(0, 5)
    ElevatorPhysicsCalculator.time_to(5, 10)
    ElevatorPhysicsCalculator.time_to(10, 5)

    ElevatorPhysicsCalculator.time_to(0, 100)
    ElevatorPhysicsCalculator.time_to(100, 0)

    ElevatorPhysicsCalculator.time_to(5, 10, 1)
    ElevatorPhysicsCalculator.time_to(5, 10, 0)
    ElevatorPhysicsCalculator.time_to(5, 10, -1)

    ElevatorPhysicsCalculator.time_to(10, 5, 1)
    ElevatorPhysicsCalculator.time_to(10, 5, 0)
    ElevatorPhysicsCalculator.time_to(10, 5, -1)

    epc = ElevatorPhysicsCalculator(-100, 3, v_max=5)
    total_t = epc.total_time()
    t = 0
    while t < total_t:
        print(epc.state_at_t(t))
        t = t + .4

if __name__ == "__main__":
    # for d in range(20):
    #     epc = ElevatorPhysicsCalculator(d, 5, v_max=5)
    #     print("D = {}, t = {}".format(d, epc.delta_t))
    print(ElevatorPhysicsCalculator.time_to(12, 10))
    epc = ElevatorPhysicsCalculator(-2 * 3.9, 0)
    total_t = epc.total_time()
    print(total_t)
    t = float(0)
    while t <= total_t:
        print("T={:.4} (P,V)={}".format(t, epc.state_at_t(t)))
        t = t + .1



