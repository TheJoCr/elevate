from heapq import heappop

from elevate.ButtonPush import ButtonPush
from elevate.Elevator import Elevator
from elevate.Events import ElevatorStart, ElevatorStop
from elevate.PhysicsCalculator import ElevatorPhysicsCalculator
from elevate.Schedule import ElevatorSchedule
from elevate.TravelGoal import TravelGoal
from elevate.strategies.BoringElevatorStrategy import BoringElevatorStrategy

'''
A PriorBeliefElevatorStrategy is used to follow the Boring elevator strategy 
with some side constraints - a list of suggested stops passed in at creation time. 
'''
if __name__ == "__main__":
    # We have 3 elevators: 1 going up, 1 soon to be going down, and one stopped.
    e1 = Elevator(is_stopped=True, location=10)
    e1.last_start_event = ElevatorStart(e1, -8, 12, ElevatorStop(e1, ElevatorPhysicsCalculator.time_to(12, 10)-8, 10))
    e1.passenger_goals = [
        TravelGoal(time=-8, start_floor=12, end_floor=5),
        TravelGoal(time=-2, start_floor=10, end_floor=5)
    ]

    e2 = Elevator(is_stopped=False, location=1,)
    e2.last_start_event = ElevatorStart(e2, 0, 1, ElevatorStop(e2, ElevatorPhysicsCalculator.time_to(1, 6), 6))
    e2.passenger_goals = [
        TravelGoal(time=0, start_floor=1, end_floor=10),
        TravelGoal(time=0, start_floor=1, end_floor=6)
    ]

    e3 = Elevator(is_stopped=True, location=1)
    e3.passenger_goals = []

    time = 1.5
    original_schedule = ElevatorSchedule({e1: [5], e2: [6, 10], e3: []}, {})
    events = original_schedule.event_gen_and_apply(0)
    original_schedule.update_elevator_state(time)

    print("E1: T = {:.2}, p = {:6.4}, v = {:6.4}".format(time, float(e1.location), float(e1.velocity)))
    print("E2: T = {:.2}, p = {:6.4}, v = {:6.4}".format(time, float(e2.location), float(e2.velocity)))
    print("E3: T = {:.2}, p = {:6.4}, v = {:6.4}".format(time, float(e3.location), float(e3.velocity)))

    while len(events) > 0:
        elevator_event = heappop(events)
        if elevator_event.elevator is e1:
            print("(original) E1: {} T = {:.2f} Floor: {}".format(type(elevator_event), elevator_event.time, elevator_event.floor))
        elif elevator_event.elevator is e2:
            print("(original) E2: {} T = {:.2f} Floor: {}".format(type(elevator_event), elevator_event.time, elevator_event.floor))
        elif elevator_event.elevator is e3:
            print("(original) E3: {} T = {:.2f} Floor: {}".format(type(elevator_event), elevator_event.time, elevator_event.floor))
        else:
            print("Unknown elevator!")

    strat = BoringElevatorStrategy()

    outstanding_presses = [
        ButtonPush(8, "UP", 1),
        ButtonPush(1, "UP", 2),
        ButtonPush(4, "DOWN", 3),
        ButtonPush(6, "DOWN", 4),
        ButtonPush(2, "UP", 5),
        ButtonPush(2, "DOWN", 6)
    ]

    new_schedule = strat.get_plan([e1, e2, e3], outstanding_presses)
    new_events = new_schedule.event_gen_and_apply(100)

    print("New values, just to verify they're correct:")
    print("E1: T = {:.2}, p = {:6.4}, v = {:6.4}".format(time, float(e1.location), float(e1.velocity)))
    print("E2: T = {:.2}, p = {:6.4}, v = {:6.4}".format(time, float(e2.location), float(e2.velocity)))
    print("E3: T = {:.2}, p = {:6.4}, v = {:6.4}".format(time, float(e3.location), float(e3.velocity)))

    print("New events:")
    while len(new_events) > 0:
        elevator_event = heappop(new_events)
        if elevator_event.elevator is e1:
            print("(new) E1: {} T = {:.2f} Floor: {}".format(type(elevator_event), elevator_event.time, elevator_event.floor))
        elif elevator_event.elevator is e2:
            print("(new) E2: {} T = {:.2f} Floor: {}".format(type(elevator_event), elevator_event.time, elevator_event.floor))
        elif elevator_event.elevator is e3:
            print("(new) E3: {} T = {:.2f} Floor: {}".format(type(elevator_event), elevator_event.time, elevator_event.floor))
        else:
            print("Unknown elevator!")

