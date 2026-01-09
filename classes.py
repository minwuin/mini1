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

    def draw(self, screen, img=None):
        from constants import GRID_SIZE
        
        # 이미지가 있으면 이미지 그리기
        if img:
            screen.blit(img, (self.pos[1]*GRID_SIZE + 1, self.pos[0]*GRID_SIZE + 1))
        # 없으면 원래대로 파란 네모 (부모 draw 호출)
        else:
            super().draw(screen)

class Enemy(Entity):
    def __init__(self, pos, color, speed_delay):
        super().__init__(pos, color)
        self.speed_delay = speed_delay
        self.ticks = 0
        self.frozen_until = 0
        self.role = "CHASER"
    # frozen_img(이미지)와 curr_time(현재 시간)을 인자로 받아야 판단할 수 있습니다.
    def draw(self, screen, frozen_img=None,normal_img=None, curr_time=0):
        from constants import GRID_SIZE
        
        # 1. 현재 얼어있는 상태인지 확인 (현재 시간이 해동 시간보다 이전이면 얼은 상태)
        is_frozen = curr_time < self.frozen_until
        
        # 2. 얼어있고, 그릴 이미지가 있다면 -> 얼음 이미지 그리기
        if is_frozen and frozen_img:
             screen.blit(frozen_img, (self.pos[1]*GRID_SIZE + 2, self.pos[0]*GRID_SIZE + 2))
             
        elif normal_img:
             screen.blit(normal_img, (self.pos[1]*GRID_SIZE + 2, self.pos[0]*GRID_SIZE + 2))
        
        # 3. 얼지 않았거나 이미지가 없다면 -> 원래대로 색깔 네모 그리기
        else:
            # 부모(Entity)의 draw 메서드를 호출해서 원래대로 그립니다.
            super().draw(screen)

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

class Bullet:
    def __init__(self, pos, direction):
        # pos는 (행, 열) 튜플
        self.r = float(pos[0]) 
        self.c = float(pos[1])
        self.dr = direction[0]
        self.dc = direction[1]
        self.speed = 0.8  # 총알 속도 (한 프레임당 0.8칸 이동)
        self.active = True

    def update(self):
        self.r += self.dr * self.speed
        self.c += self.dc * self.speed

    def draw(self, screen, img=None):
        from constants import GRID_SIZE, GOLD
        
        # 총알의 중심 좌표 계산 (픽셀 단위)
        center_x = int(self.c * GRID_SIZE + GRID_SIZE // 2)
        center_y = int(self.r * GRID_SIZE + GRID_SIZE // 2)

        # 1. 이미지가 있으면 이미지 그리기
        if img:
            # 이미지의 중심을 계산된 좌표에 맞춤
            rect = img.get_rect(center=(center_x, center_y))
            screen.blit(img, rect)
            
        # 2. 이미지가 없으면 기존처럼 노란 원 그리기
        else:
            pygame.draw.circle(screen, GOLD, (center_x, center_y), 5)