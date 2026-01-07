import pygame
import time
from constants import GRID_SIZE, ITEM_COLORS

# --- 엔티티 상속 구조 ---
class Entity:
    def __init__(self, pos, color):
        self.pos = list(pos)
        self.color = color

    def draw(self, screen):
        # 플레이어와 적이 미로 벽보다 위에 그려지도록 
        # GRID_SIZE를 곱해 좌표를 변환하고, 약간의 여백(2)을 줍니다.
        from constants import GRID_SIZE
        pygame.draw.rect(screen, self.color, 
                         (self.pos[1]*GRID_SIZE + 2, self.pos[0]*GRID_SIZE + 2, 
                          GRID_SIZE - 4, GRID_SIZE - 4))

class Player(Entity):
    def __init__(self, pos, color):
        super().__init__(pos, color)
        self.speed_delay = 6
        self.inventory = {itype: 0 for itype in ['shoes', 'gun', 'spring', 'hourglass', 'brick']}
        self.last_dir = (-1, 0)
        self.shoes_until = 0

class Enemy(Entity):
    def __init__(self, pos, color, speed_delay):
        super().__init__(pos, color)
        self.speed_delay = speed_delay
        self.ticks = 0
        self.frozen_until = 0

# --- 아이템 상속 구조 ---
class Item:
    def __init__(self, pos, itype):
        self.pos = pos
        self.itype = itype
        self.color = ITEM_COLORS[itype]

    def draw(self, screen):
        center = (self.pos[1]*GRID_SIZE + GRID_SIZE//2, self.pos[0]*GRID_SIZE + GRID_SIZE//2)
        pygame.draw.circle(screen, self.color, center, 8)

class Shoes(Item):
    def __init__(self, pos): super().__init__(pos, 'shoes')
class Gun(Item):
    def __init__(self, pos): super().__init__(pos, 'gun')
class Spring(Item):
    def __init__(self, pos): super().__init__(pos, 'spring')
class Hourglass(Item):
    def __init__(self, pos): super().__init__(pos, 'hourglass')
class Brick(Item):
    def __init__(self, pos): super().__init__(pos, 'brick')

class Node:
    def __init__(self, pos, parent=None):
        self.pos = pos
        self.parent = parent
        self.g = self.h = self.f = 0
    def __lt__(self, other): return self.f < other.f