class ButtonPush:
    def __init__(self, floor, direction, time=None):
        self.floor = floor
        self.direction = direction
        self.time = time

    def __key(self):
        return self.floor, self.direction

    def __eq__(self, other):
        return self.__key() == other.__key()

    def __hash__(self):
        return hash(self.__key())

    def __repr__(self):
        return str(self.__key())


if __name__ == "__main__":
    a = ButtonPush(0, 'UP')
    b = ButtonPush(0, "U" + "P")
    print(a == b)
    print(a in {b})
    print(a in {b: []}.keys())
