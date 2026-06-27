class Tank(object):
    __slots__ = ['x', 'y', 'direc']

    def __init__(self, x, y, direc):
        self.x = int (x)
        self.y = int (y)
        self.direc = direc

    