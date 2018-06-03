from heapq import heappush, heappop

from typing import List

from elevate.RunStats import RunStats
from elevate.ButtonPush import ButtonPush
from elevate.Elevator import Elevator
from elevate.Events import ElevatorStart, ElevatorStop
from elevate.strategies.RandomElevatorStrategy import RandomElevatorStrategy
from elevate.strategies.BaseElevatorStrategy import ElevatorStrategy
from elevate.TravelBehaviors import OfficeBuildingTravelBehavior, TravelBehavior
from elevate.TravelGoal import TravelGoal


class ElevatorSimulator:
    def __init__(self, travel_behavior: TravelBehavior, strategy: ElevatorStrategy, num_elevators=3):
        self.strategy = strategy
        self.travel_behavior = travel_behavior
        self.num_elevators = num_elevators

        # Init Mutable state:
        # IF IT'S NOT ONE OF THESE THINGS, IT SHOULD NOT BE MUTABLE!
        self.elevators = [Elevator(passenger_goals=set()) for _ in range(self.num_elevators)]
        self.current_time = 0
        self.pending_elevator_events = []  # heap of pending events
        self.pending_button_presses = {}  # ButtonPress to TravelGoal
        self.current_schedule = None  # an ElevatorSchedule object generated from the strategy
        self.completed_goals = []
        self.elevator_history = {e: [] for e in self.elevators}

    def construct_travel_goals(self, num_people) -> List[TravelGoal]:
        if num_people is None:
            num_people = self.travel_behavior.num_floors * 40
        # Where going to create a heap out of the travel goals
        # The time based comparison is already specified there.
        all_trips = []
        for i in range(num_people):
            trips = self.travel_behavior.generate_path()
            for trip in trips:
                heappush(all_trips, trip)
        return all_trips

    def update_elevator_schedule(self, current_time):
        print("[T={}] Begin:  Rescheduling.".format(current_time))
        if self.current_schedule is not None:
            self.current_schedule.update_elevator_state(current_time)
        self.current_schedule = self.strategy.get_plan(self.elevators, self.pending_button_presses.keys(), current_time)
        self.pending_elevator_events = self.current_schedule.event_gen_and_apply()
        print("[T={}] Results of Rescheduling:".format(current_time))
        temp_events = []
        while len(self.pending_elevator_events) > 0:
            event = heappop(self.pending_elevator_events)
            print("    {}".format(event))
            heappush(temp_events, event)
        self.pending_elevator_events = temp_events
        print("[T={}] Finish: Rescheduling.".format(current_time))

    def run(self, num_people=None, logResults=False) -> RunStats:
        # Generate a set of schedules for today
        trip_schedule = self.construct_travel_goals(num_people)
        # for trip in trip_schedule:
        #     print(trip.time)
        print("Running {} total goals".format(len(trip_schedule)))

        self.update_elevator_schedule(0)

        while len(trip_schedule) > 0:
            print("T={}".format(self.current_time))
            next_travel_goal = heappop(trip_schedule)
            # Process everything that is going to happen with the elevators until then:
            self.simulate(next_travel_goal.time)
            # Now get the next travel goal and add it to button presses
            self.current_time = next_travel_goal.time
            caused_button_press = self.add_travel_goal(next_travel_goal)
            if caused_button_press:  # Then we need to recalculate the schedule
                self.update_elevator_schedule(self.current_time)

        if self.has_pending():
            self.simulate(None)  # Simulate all remaining elevator events
        if logResults:
            print("Generating summary after completing {} total goals".format(len(self.completed_goals)))
            with open("summary.csv", 'w') as summary_file:
                for g in self.completed_goals:
                    summary_file.write("{},{},{},{},{}\n".format(
                        g.start_floor, g.end_floor, g.time, g.board_time - g.time, g.finish_time - g.time
                    ))

        return RunStats(self.completed_goals, self.elevator_history)

    def has_pending(self):
        return len(self.pending_button_presses) + len(self.pending_elevator_events) > 0

    def simulate(self, end_time=None):
        print("Beginning elevator event processing...")
        count = 0
        while len(self.pending_elevator_events) > 0 and (
                end_time is None or self.pending_elevator_events[0].time < end_time):
            count += 1
            next_event = heappop(self.pending_elevator_events)
            print("[T={}] Begin:  {}".format(self.current_time, next_event))
            # Record the event for history
            self.elevator_history[next_event.elevator].append(
                (self.current_time, next_event.floor, len(next_event.elevator.passenger_goals)))
            if isinstance(next_event, ElevatorStart):
                self.process_elevator_start(next_event)
            elif isinstance(next_event, ElevatorStop):
                self.process_elevator_stop(next_event)
            else:
                print("Unrecognized elevator event type!")
            print("[T={}] Finish: {}".format(self.current_time, next_event))
        print("Processed {} elevator events".format(count))

    def process_elevator_stop(self, this_stop: ElevatorStop):
        # First, update state stuff from the stop
        elevator = this_stop.elevator
        elevator.location = this_stop.floor
        self.current_time = this_stop.time

        # Next, update elevator state
        completed_goals = elevator.stop_and_drop_off()
        for goal in completed_goals:
            goal.exit_elevator(self.current_time)
            self.completed_goals.append(goal)

    def process_elevator_start(self, this_start: ElevatorStart):
        self.current_time = this_start.time
        elevator = this_start.elevator
        elevator.location = this_start.floor
        if this_start.button_press_handled in self.pending_button_presses:
            # We're picking up from this floor
            passengers_to_add = self.pending_button_presses.pop(this_start.button_press_handled)
            for travel_goal in passengers_to_add:
                travel_goal.board_elevator(self.current_time)
            elevator.start_and_pick_up(set(passengers_to_add), this_start)
            self.update_elevator_schedule(self.current_time)  # And update the schedule with new info
        else:
            elevator.start_and_pick_up(set(), this_start)
        # else:
        #     print("Useless Start {}. Would have taken: {}".format(this_start, self.pending_button_presses.keys()))

    def add_travel_goal(self, next_travel_goal: TravelGoal) -> bool:
        # Translate the goal into a ButtonPress
        button_push = ButtonPush(next_travel_goal.start_floor, next_travel_goal.direction(), self.current_time)
        # And add it, either by updating a new list or appending it to an existing one.
        new_press = False
        if button_push not in self.pending_button_presses:
            self.pending_button_presses[button_push] = []
            new_press = True
        self.pending_button_presses[button_push].append(next_travel_goal)
        print("Added travel goal {} - caused New Press? {}. {} pending button presses".format(
            next_travel_goal, new_press, len(self.pending_button_presses)))
        return new_press


if __name__ == "__main__":
    ElevatorSimulator(
        OfficeBuildingTravelBehavior(40),
        RandomElevatorStrategy()
        # BoringElevatorStrategy()
    ).run(num_people=1000)
