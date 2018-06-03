from elevate.PhysicsCalculator import ElevatorPhysicsCalculator


class Run(object):
    def __init__(self, direction: str, first_stop: int):
        self.direction = direction
        self.stops = [first_stop]
        self.times = [0]

    def __sizeof__(self) -> int:
        return len(self.stops)

    def __getitem__(self, item):
        return self.stops[item]

    def add_stop(self, stop):
        assert self.direction == ElevatorPhysicsCalculator.direction(self.stops[-1], stop)
        self.stops.append(stop)
        self.times.append(0)

    def insert_stop(self, stop, i):
        assert 0 <= i <= len(self.stops)
        if i > 0:
            assert self.direction == ElevatorPhysicsCalculator.direction(self.stops[i-1], stop)
        if i < len(self.stops):
            assert self.direction == ElevatorPhysicsCalculator.direction(stop, self.stops[i])
        self.stops.insert(stop, i)
        self.times.append(0)

    def last(self):
        assert len(self.stops) > 0
        return self[-1]

    def first(self):
        assert len(self.stops) > 0
        return self[0]

    def normalize_times(self):

        pass

