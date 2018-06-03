class TravelGoal:
    """
    A travel goal represents some path that someone
    wants to take at some point. It also stores information
    that is used to evaluate how long it actually took
    them to get there.

    Time is measured in the number of seconds since the start of the day (float)
    """
    def __init__(self, time, start_floor, end_floor):
        self.time = time
        self.start_floor = start_floor
        self.end_floor = end_floor
        self.board_time = 0
        self.finish_time = 0

    def __lt__(self, other):
        return self.time.__lt__(other.time)

    def direction(self):
        return "UP" if self.start_floor < self.end_floor else "DOWN"

    def exit_elevator(self, current_time):
        self.finish_time = current_time

    def board_elevator(self, current_time):
        self.board_time = current_time

    def __repr__(self):
        return "[TravelGoal@T={:.6} ({}->{})".format(self.time, self.start_floor, self.end_floor)
