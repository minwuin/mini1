import random, heapq, os
from constants import ROWS, COLS, ITEM_LIST

def a_star(maze, start, target):
    from classes import Node
    open_list = []
    closed_set = set()
    heapq.heappush(open_list, Node(start))
    while open_list:
        curr = heapq.heappop(open_list)
        if curr.pos == target:
            path = []
            while curr: path.append(curr.pos); curr = curr.parent
            return path[::-1]
        closed_set.add(curr.pos)
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            np = (curr.pos[0]+dr, curr.pos[1]+dc)
            if 0<=np[0]<ROWS and 0<=np[1]<COLS and maze[np[0]][np[1]] == 0 and np not in closed_set:
                child = Node(np, curr)
                child.g, child.h = curr.g + 1, abs(np[0]-target[0]) + abs(np[1]-target[1])
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
    for _ in range(120): maze[random.randint(1, ROWS-2)][random.randint(1, COLS-2)] = 0
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