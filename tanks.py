class Entity(object):
    __slots__ = ['x', 'y', 'hp', 'tipo', 'direc', 'shape_name', 'direccion_patrulla', 'pasos_rafaga']

    def __init__(self, x, y, hp, tipo, direc=0, shape_name='TANK'):
        self.x = int(x)
        self.y = int(y)
        self.hp = hp
        self.tipo = tipo
        self.direc = direc
        self.shape_name = shape_name
        self.direccion_patrulla = 1
        self.pasos_rafaga = 0 # <--- Contador de pasos para mantener el rumbo
    def recibir_danio(self, danio):
        self.hp -= danio


class Tank(Entity):
    def __init__(self, x, y, direc, hp=1, tipo='ENEMY'):
        Entity.__init__(self, x, y, hp, tipo, direc, 'TANK')