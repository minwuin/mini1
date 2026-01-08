import random, heapq, os
from constants import ROWS, COLS, ITEM_LIST

class Node:
    def __init__(self, pos, parent=None):
        self.pos = pos
        self.parent = parent
        self.g = self.h = self.f = 0
    def __lt__(self, other): return self.f < other.f

# [수정됨] others 인자를 받아서 동료 적들을 피해서 길을 찾음
def a_star(maze, start, target, others=None):
    open_list = []
    closed_set = set()
    
    # others가 없으면 빈 리스트로 처리
    if others is None: others = []
    
    heapq.heappush(open_list, Node(start))
    
    # 너무 오래 걸리지 않게 루프 제한 (선택사항)
    loop_cnt = 0
    
    while open_list:
        loop_cnt += 1
        if loop_cnt > 1000: break # 성능 방어

        curr = heapq.heappop(open_list)
        
        if curr.pos == target:
            path = []
            while curr:
                path.append(curr.pos)
                curr = curr.parent
            return path[::-1]
            
        closed_set.add(curr.pos)
        
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            nr, nc = curr.pos[0]+dr, curr.pos[1]+dc
            
            # 1. 맵 범위 체크
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                # 2. 벽이 아니고, 이미 방문하지 않았는지 체크
                if maze[nr][nc] == 0 and (nr, nc) not in closed_set:
                    # 3. [추가] 다른 적이 있는 위치는 장애물로 인식 (단, 목표지점은 예외)
                    if (nr, nc) in others and (nr, nc) != target:
                        continue
                        
                    child = Node((nr, nc), curr)
                    child.g = curr.g + 1
                    child.h = abs(nr-target[0]) + abs(nc-target[1])
                    child.f = child.g + child.h
                    heapq.heappush(open_list, child)
    return None

def create_maze():
    maze = [[1 for _ in range(COLS)] for _ in range(ROWS)]
    def walk(r, c):
        maze[r][c] = 0
        dirs = [(0,1),(0,-1),(1,0),(-1,0)]; random.shuffle(dirs)
        for dr, dc in dirs:
            nr, nc = r+dr*2, c+dc*2
            if 0<=nr<ROWS and 0<=nc<COLS and maze[nr][nc]==1:
                maze[r+dr][c+dc]=0; walk(nr, nc)
    walk(0,0)
    for _ in range(200): maze[random.randint(1, ROWS-2)][random.randint(1, COLS-2)] = 0
    for _ in range(18):
        rr, rc = random.randint(1, ROWS-4), random.randint(1, COLS-4)
        for i in range(3):
            for j in range(3): maze[rr+i][rc+j] = 0
    maze[ROWS-1][0] = 0
    maze[0][COLS-1] = 0
    return maze

def save_ranking(name, score):
    ranks = []
    if os.path.exists("ranking.txt"):
        with open("ranking.txt", "r") as f:
            for line in f:
                p = line.strip().split(',')
                if len(p) == 2: ranks.append(p)
    ranks.append([name, str(score)])
    ranks.sort(key=lambda x: int(x[1]), reverse=True)
    with open("ranking.txt", "w") as f:
        for r in ranks[:5]: f.write(f"{r[0]},{r[1]}\n")
    return ranks[:5]

def get_safe_pos(maze):
    safe_cells = []
    for r in range(ROWS):
        for c in range(COLS):
            if maze[r][c] == 0:
                safe_cells.append((r, c))
    if safe_cells:
        return list(random.choice(safe_cells))
    else:
        return [1, 1]

# [추가] 적의 예측 경로를 계산하는 함수 (매복/지원용)
def get_intercept_pos(maze, player_pos, prev_player_pos, offset=3):
    # 플레이어의 이동 방향 계산
    dr = player_pos[0] - prev_player_pos[0]
    dc = player_pos[1] - prev_player_pos[1]
    
    # 플레이어가 멈춰있으면 그냥 현재 위치 반환
    if dr == 0 and dc == 0:
        return player_pos
    
    # 플레이어의 진행 방향으로 offset만큼 떨어진 위치 계산
    target_r = player_pos[0] + (dr * offset)
    target_c = player_pos[1] + (dc * offset)
    
    # 맵 범위 내로 보정
    target_r = max(0, min(target_r, ROWS - 1))
    target_c = max(0, min(target_c, COLS - 1))
    
    # 해당 위치가 벽이라면, 플레이어 위치로 fallback (또는 주변 빈 곳 탐색 가능)
    if maze[int(target_r)][int(target_c)] == 1:
        return player_pos
        
    return (int(target_r), int(target_c))