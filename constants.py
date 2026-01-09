import pygame
import os

# 폰트 설정
FONT_PATH = r"C:\minwoin\miniproject\mini1\DungGeunMo.ttf"

# 디렉토리 설정
BASE_PATH = r"C:\minwoin\miniproject\mini1"
STONE_PATH = r"C:\minwoin\miniproject\mini1\background\stone.png"
GROUND_PATH = r"C:\minwoin\miniproject\mini1\background\ground.png"
SHOE_PATH = r"C:\minwoin\miniproject\mini1\item\shoes.png"
WALL_PATH = r"C:\minwoin\miniproject\mini1\item\wall.png"
SPRING_PATH = r"C:\minwoin\miniproject\mini1\item\spring.png"
STOP_PATH = r"C:\minwoin\miniproject\mini1\item/stop.png"
GUN_PATH = r"C:\minwoin\miniproject\mini1\item\gun.png"
START_PATH = r"C:\minwoin\miniproject\mini1\background\start.png"
BULLET_PATH = r""

# --- 화면 및 공간 분리 설정 ---
WIDTH = 800
HEIGHT = 900  # 전체 창 높이
GRID_SIZE = 20

INV_HEIGHT = 100 # 하단 인벤토리 영역 높이 (고정)
GAME_WORLD_HEIGHT = HEIGHT - INV_HEIGHT # 플레이 영역 (800)

# 행(ROWS)과 열(COLS) 계산
# 800 / 20 = 40행, 800 / 20 = 40열
ROWS = GAME_WORLD_HEIGHT // GRID_SIZE 
COLS = WIDTH // GRID_SIZE

# 인벤토리가 시작되는 Y 좌표 (800 지점)
INV_Y = GAME_WORLD_HEIGHT 

# --- 인벤토리 내부 설정 ---
INV_SLOT_SIZE = 60
FPS = 60

# --- 색상 설정 ---
WHITE, BLACK = (255, 255, 255), (20, 20, 20)
RED, BLUE = (255, 50, 50), (50, 150, 255)
GOLD, GREEN = (255, 215, 0), (50, 255, 50)
FOG_COLOR = (0, 0, 0, 220)

# --- 아이템 정보 ---
ITEM_LIST = ['shoes', 'gun', 'spring', 'hourglass', 'brick']
ITEM_COLORS = {
    'shoes': GREEN, 
    'gun': GOLD, 
    'spring': (255, 100, 255),
    'hourglass': (100, 100, 255), 
    'brick': (150, 75, 0)
}