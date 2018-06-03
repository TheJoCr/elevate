class ElevatorEvent:
    def __init__(self, elevator, time, floor):
        self.elevator = elevator
        self.time = time
        self.floor = floor

    def __lt__(self, other):
        return self.time < other.time


class ElevatorStop(ElevatorEvent):
    """
    An elevate Stops at a certain floor and time

    It stops for 5 seconds.
    """
    duration = 5

    def __init__(self, elevator, time, floor):
        super().__init__(elevator, time, floor)

    def __repr__(self):
        return "END   @T={:.6}, floor={}, elevator={}".format(self.time, self.floor, self.elevator)


class ElevatorStart(ElevatorEvent):
    """
    An elevate Starts at a certain floor and moves a certain direction.

    As such, it is associated with a particular Button_Press action, which
    becomes deactivated as soon as the ElevatorStart event is finished
    """
    def __init__(self, elevator, time, floor, stop_event: ElevatorStop=None, button_press_handled=None):
        super().__init__(elevator, time, floor)
        self.stop_event = stop_event
        self.button_press_handled = button_press_handled
        self.elevator_state = time, floor, 0

    def override_elevator_state(self, time, elevator):
        self.elevator_state = time, elevator.location, elevator.velocity

    def __repr__(self):
        return "START @T={:.6}, floor={}, button_press={}. Elevator = {}".format(
            float(self.time), self.floor, self.button_press_handled if self.button_press_handled is not None else "None",
            self.elevator
        )
