from heapq import heappush, heappop
from typing import Dict, List

from elevate.Events import ElevatorEvent, ElevatorStop, ElevatorStart
from elevate.PhysicsCalculator import ElevatorPhysicsCalculator
from elevate.ButtonPush import ButtonPush
from elevate.Elevator import Elevator


class ElevatorSchedule:
    def __init__(self,
                 elevator_to_floors: Dict[Elevator, List],
                 elevator_to_final_dir: Dict[Elevator, str],
                 initalization_time):
        # print("Constructing elevator schedule from {}".format(elevator_to_floors))
        self.elevator_to_floors = elevator_to_floors
        self.elevator_to_time = self._find_times(initalization_time)
        self.initialization_time = initalization_time
        # print("Found times: {}".format(self.elevator_to_time))
        print("Planned times")
        for e in elevator_to_floors:
            print(e)
            print("    {}".format(elevator_to_floors[e]))
            print("    {}".format(self.elevator_to_time[e]))

        self.elevator_to_final_dir = elevator_to_final_dir

    def _find_times(self, current_time) -> Dict[Elevator, List[float]]:
        return {e: ElevatorSchedule.find_stop_times(e, self.elevator_to_floors[e], current_time)
                for e in self.elevator_to_floors}

    @staticmethod
    def find_stop_times(elevator: Elevator, floors_to_visit: List[int], current_time) -> List[float]:
        """
        This takes in the current state of an elevator and the list of floors to visit.
        It returns a list of floats that represent the times it will take (relative to the input current_time, or to
        0 if none is supplied).
        :param elevator: the elevator (only used to find current state)
        :param floors_to_visit: the floors to visit
        :param current_time: the time at which this schedule was constructed
        :return: a list of floats representing the amount of time it will take to travel to all those floors.
        """
        next_floor_index = 0
        current_time_acc = current_time
        current_floor = elevator.location

        floor_arrival_times = []
        if len(floors_to_visit) == 0:
            return floor_arrival_times

        if not elevator.is_stopped:
            # Then we need to add a stop to whatever is currently running
            next_floor = floors_to_visit[next_floor_index]
            delta_t = ElevatorPhysicsCalculator.time_to(current_floor, next_floor, elevator.velocity)
            floor_arrival_times.append(current_time_acc + delta_t)

            current_time_acc = current_time_acc + delta_t + ElevatorStop.duration
            current_floor = next_floor
            next_floor_index += 1
        else:
            if elevator.last_start_event is not None:
                # This means we are stopped on a floor and will leave soon - exactly ElevatorStop.duration from the
                # stop event associated with the most recent start event.

                # Make sure that we don't start before the current time.
                current_time_acc = max(current_time_acc,
                                       elevator.last_start_event.stop_event.time + ElevatorStop.duration)
            else:
                next_floor = floors_to_visit[next_floor_index]
                delta_t = ElevatorPhysicsCalculator.time_to(current_floor, next_floor, elevator.velocity)
                floor_arrival_times.append(current_time_acc + delta_t)
                current_time_acc = current_time_acc + delta_t + ElevatorStop.duration
                current_floor = next_floor
                next_floor_index += 1

        while next_floor_index < len(floors_to_visit):
            next_floor = floors_to_visit[next_floor_index]
            # Generate the start and end events from current_floor to next_floor
            delta_t = ElevatorPhysicsCalculator.time_to(next_floor, current_floor)
            floor_arrival_times.append(current_time_acc + delta_t)
            current_time_acc = current_time_acc + delta_t + ElevatorStop.duration
            # And update local state
            current_floor = next_floor
            next_floor_index = next_floor_index + 1

        return floor_arrival_times

    @staticmethod
    def _move_elevator_to_start_floor(elevator, start_floor, current_time, arrival_time) \
            -> List[ElevatorEvent]:
        """
        This method does two things:
        1) Find the set of events needed to move the elevator from its current location to the start floor (in no
        particular order).
        2) Update the elevators own record of events in order that it can be tracked later.
        :param elevator: The elevator object that needs to move to the start floor.
        :param start_floor: We move the elevator to this floor
        :param current_time: The current time (i.e. the time associated with the current state of the elevator)
        :param arrival_time: The time that the elevator is expected to arrive to the new floor.
        :return: A list of events in no particular order. There will be at most one of these - a stop - in the case that
         the elevator is not already in motion. If it's stopped, we return its next start (which may have
         time = current_time, and the stop that will put us on the floor.
        """
        if not elevator.is_stopped:  # The elevator is already in motion - only add an end event.
            # Make sure that we update the last start event of the elevator so we can track it's motion.
            stop_event = ElevatorStop(elevator, arrival_time, start_floor)
            elevator.last_start_event.stop_event = stop_event  # to keep track of things
            elevator.last_start_event.override_elevator_state(current_time, elevator)
            return [stop_event]
        else:  # The elevator is currently stopped.
            if elevator.location == start_floor:
                # Then we are already on the floor - nothing to be done to move us there.
                return []
            start_time = current_time
            if elevator.last_start_event is not None:
                start_time = max(current_time, elevator.last_start_event.stop_event.time + ElevatorStop.duration)
            stop_event = ElevatorStop(elevator, arrival_time, start_floor)
            start_event = ElevatorStart(
                elevator, start_time, elevator.location, stop_event,
                ButtonPush(elevator.location,
                           ElevatorPhysicsCalculator.direction(elevator.location, start_floor)))
            # Don't update the last start event of the elevator in this case - that will be taken care of when we
            # process the newly added start event
            return [start_event, stop_event]

    def _move_elevators_to_start_floor(self):
        event_queue = []
        for elevator in self.elevator_to_floors:
            if len(self.elevator_to_floors[elevator]) > 0:
                starting_events = self._move_elevator_to_start_floor(
                    elevator,
                    self.elevator_to_floors[elevator][0],
                    self.initialization_time,
                    self.elevator_to_time[elevator][0]
                )
                for event in starting_events:
                    heappush(event_queue, event)
        return event_queue

    def event_gen_and_apply(self) -> List[ElevatorEvent]:
        """
        :return: a priority queue (heap) of events that will occur in this building
        """
        event_queue = self._move_elevators_to_start_floor()
        for elevator in self.elevator_to_floors:
            for i in range(1, len(self.elevator_to_floors[elevator])):
                #  Construct events to move from i-1 to 1
                stop_event = ElevatorStop(
                    elevator,
                    self.elevator_to_time[elevator][i],
                    self.elevator_to_floors[elevator][i]
                )
                start_event = ElevatorStart(
                    elevator,
                    self.elevator_to_time[elevator][i - 1] + ElevatorStop.duration,
                    self.elevator_to_floors[elevator][i - 1],
                    stop_event,
                    ButtonPush(
                        self.elevator_to_floors[elevator][i - 1],
                        ElevatorPhysicsCalculator.direction(
                            self.elevator_to_floors[elevator][i - 1],
                            self.elevator_to_floors[elevator][i]
                        )
                    )
                )
                heappush(event_queue, stop_event)
                heappush(event_queue, start_event)
            # We add one last start event without a target at the end.
            if elevator in self.elevator_to_final_dir:
                floor = self.elevator_to_floors[elevator][-1]
                time = self.elevator_to_time[elevator][-1] + ElevatorStop.duration
                heappush(event_queue, ElevatorStart(
                    elevator,
                    time,
                    floor,
                    stop_event=None,
                    button_press_handled=ButtonPush(floor, self.elevator_to_final_dir[elevator])
                ))
        return event_queue

    def update_elevator_state(self, current_time):
        for elevator in self.elevator_to_floors:
            if elevator.is_stopped:
                elevator.velocity = 0
                continue

            start_event = elevator.last_start_event
            stop_event = start_event.stop_event
            if stop_event is None:
                continue

            start_t, start_loc, start_v = start_event.elevator_state
            _, stop_loc = stop_event.time, stop_event.floor

            print("Start_t: {:.6}, start_loc: {:.4}, start_v: {:.4}, stop_loc: {:.4}"
                  .format(float(start_t), float(start_loc), float(start_v), float(stop_loc)))

            delta_t_so_far = current_time - start_t
            total_delta_loc = stop_loc - start_loc
            # need to multiply by 3.9 - number of meters per floor.
            epc = ElevatorPhysicsCalculator(ElevatorPhysicsCalculator.floors_to_meters(total_delta_loc), start_v)
            delta_location_meters, v = epc.state_at_t(delta_t_so_far)
            delta_location = ElevatorPhysicsCalculator.meters_to_floors(delta_location_meters)
            print("delta_t_so_far: {:.6}, delta_loc_total: {:.4}; delta_loc_so_far: {:.4}, V: {:.4}; expected_t_total"
                  .format(float(delta_t_so_far), float(total_delta_loc),
                          float(delta_location), float(v)),
                          ElevatorPhysicsCalculator.time_to(start_loc, stop_loc)
                  )
            elevator.velocity = v
            elevator.location = start_loc + delta_location


if __name__ == "__main__":
    ElevatorPhysicsCalculator.time_to(6, 10)
    ElevatorPhysicsCalculator.time_to(10, 6)
    print(ElevatorPhysicsCalculator(-4*3.9, 0).delta_t)

    # e1 = Elevator(is_stopped=False)
    # e1.last_start_event = ElevatorStart(e1, 0, 0, ElevatorStop(e1, ElevatorPhysicsCalculator.time_to(0, 2), 2))
    # e2 = Elevator(location=10, is_stopped=False)
    # e2.last_start_event = ElevatorStart(e2, .5, 10, ElevatorStop(e1, .5 + ElevatorPhysicsCalculator.time_to(10, 4), 4))
    # e3 = Elevator()
    # stops = {
    #     e1: [5, 2, 8, 1],
    #     e2: [6, 1, 0, 5, 8, 2],
    #     e3: [90],
    # }
    # schedule = ElevatorSchedule(stops, {e1: "DOWN", e2: "UP", e3: "DOWN"}, 1.5)

    e1 = Elevator()

    events = schedule.event_gen_and_apply()
    while len(events) > 0:
        print(heappop(events))

    # schedule.event_gen_and_apply(0)
    # print("Start: T = {}, p = {:.4}, v = {:.4}".format(0, float(e1.location), float(e1.velocity)))
    # print("Start: T = {}, p = {:.4}, v = {:.4}".format(0, float(e2.location), float(e2.velocity)))
    # print("StarT: T = {}, p = {:.4}, v = {:.4}".format(0, float(e3.location), float(e3.velocity)))
    # schedule.update_elevator_state(.4999999)
    # print("Start: T = {}, p = {:.4}, v = {:.4}".format(.5, float(e1.location), float(e1.velocity)))
    # print("Start: T = {}, p = {:.4}, v = {:.4}".format(.5, float(e2.location), float(e2.velocity)))
    # print("StarT: T = {}, p = {:.4}, v = {:.4}".format(.5, float(e3.location), float(e3.velocity)))
    # print("Start: T = {}, p = {:.4}, v = {:.4}".format(1, float(e1.location), float(e1.velocity)))
    # print("Start: T = {}, p = {:.4}, v = {:.4}".format(1, float(e2.location), float(e2.velocity)))
    # print("StarT: T = {}, p = {:.4}, v = {:.4}".format(1, float(e3.location), float(e3.velocity)))
    # schedule.update_elevator_state(1.4999999)
    # print("Start: T = {}, p = {:.4}, v = {:.4}".format(1.5, float(e1.location), float(e1.velocity)))
    # print("Start: T = {}, p = {:.4}, v = {:.4}".format(1.5, float(e2.location), float(e2.velocity)))
    # print("StarT: T = {}, p = {:.4}, v = {:.4}".format(1.5, float(e3.location), float(e3.velocity)))


    # for t in range(5, 11):
    #     t = t/10 + .000000001
    #     schedule.update_elevator_state(t)
    #     print("Before e1: T = {:.4}, p = {:.4}, v = {:.4}".format(t, float(e1.location), float(e1.velocity)))
    #     print("Before e2: T = {:.4}, p = {:.4}, v = {:.4}".format(t, float(e2.location), float(e2.velocity)))
    #     print("Before e3: T = {:.4}, p = {:.4}, v = {:.4}".format(t, float(e3.location), float(e3.velocity)))
    #
    # events = schedule.apply_schedule(1)
    # print("After  e1: T = 1, p = {}, v = {}".format(e1.location, e1.velocity))
    # print("After  e2: T = 1, p = {}, v = {}".format(e2.location, e2.velocity))
    # print("After  e3: T = 1, p = {}, v = {}".format(e3.location, e3.velocity))
    #
    # for t in range(5, 24):
    #     t = t/4
    #     schedule.update_elevator_state(t)
    #     print("After  e1: T = {}, p = {}, v = {}".format(t, e1.location, e1.velocity))
    #     print("After  e2: T = {}, p = {}, v = {}".format(t, e2.location, e2.velocity))
    #     print("After  e3: T = {}, p = {}, v = {}".format(t, e3.location, e3.velocity))
    #
    # while len(events) > 0:
    #     elevator_event = heappop(events)
    #     if elevator_event.elevator is e1:
    #         print("E1: {} T = {:.2f} Floor: {}".format(type(elevator_event), elevator_event.time, elevator_event.floor))
    #     elif elevator_event.elevator is e2:
    #         print("E2: {} T = {:.2f} Floor: {}".format(type(elevator_event), elevator_event.time, elevator_event.floor))
    #     elif elevator_event.elevator is e3:
    #         print("E3: {} T = {:.2f} Floor: {}".format(type(elevator_event), elevator_event.time, elevator_event.floor))
    #     else:
    #         print("Unknown elevator!")
