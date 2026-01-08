import pygame, sys, time, random, os
from constants import *
from classes import *
from utils import a_star, create_maze, save_ranking

def main():
    pygame.init()
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("MAZE RUNNER")
    clock = pygame.time.Clock()
    
    font = pygame.font.SysFont("malgungothic", 25, bold=True)
    big_font = pygame.font.SysFont("malgungothic", 70, bold=True)

    # --- 이미지 로드 섹션 ---
    item_imgs = {}
    field_item_imgs = {} # 필드용 작은 이미지
    try:
        # 1. 배경 및 벽 로드 (constants.py의 변수명 사용)
        ground_img = pygame.transform.scale(pygame.image.load(GROUND_PATH), (WIDTH, GAME_WORLD_HEIGHT))
        stone_img = pygame.transform.scale(pygame.image.load(STONE_PATH), (GRID_SIZE, GRID_SIZE))
        start_img = pygame.transform.scale(pygame.image.load(START_PATH), (WIDTH, HEIGHT))

        # 2. 아이템별 경로 매핑 (constants.py 설정 기반)
        path_map = {
            'shoes': SHOE_PATH,
            'gun': GUN_PATH,
            'spring': SPRING_PATH,
            'hourglass': STOP_PATH,
            'brick': WALL_PATH
        }
        
        for itype, path in path_map.items():
            if os.path.exists(path):
                img = pygame.image.load(path)
                # 인벤토리용 (큰 사이즈)
                item_imgs[itype] = pygame.transform.scale(img, (INV_SLOT_SIZE-10, INV_SLOT_SIZE-10))
                # 필드 드랍용 (작은 사이즈)
                field_item_imgs[itype] = pygame.transform.scale(img, (GRID_SIZE-4, GRID_SIZE-4))
        has_imgs = True
    except Exception as e:
        print(f"이미지 로드 오류: {e}")
        has_imgs = False

    state = "START"
    user_name = ""
    rank_data = []
    sys.setrecursionlimit(5000)

    player = None
    enemies = []
    items = []
    maze = []
    start_time = 0
    next_spawn = 0
    p_ticks = 0

    while True:
        curr_time = time.time()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if state == "START":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE: user_name = user_name[:-1]
                    elif event.key == pygame.K_RETURN and user_name: state = "PLAYING_INIT"
                    elif len(user_name) < 10: user_name += event.unicode
                if event.type == pygame.MOUSEBUTTONDOWN:
                    start_btn = pygame.Rect(WIDTH//2-100, 650, 200, 60)
                    if start_btn.collidepoint(event.pos) and user_name: state = "PLAYING_INIT"

            elif state == "PLAYING":
                if event.type == pygame.KEYDOWN:
                    # 아이템 사용 로직 (기존과 동일)
                    if event.key == pygame.K_1 and player.inventory['shoes'] > 0:
                        player.inventory['shoes'] -= 1; player.shoes_until = curr_time + 10
                    elif event.key == pygame.K_2 and player.inventory['gun'] > 0:
                        player.inventory['gun'] -= 1
                        for e in enemies[:]:
                            if (player.last_dir[0] != 0 and e.pos[1] == player.pos[1] and (e.pos[0]-player.pos[0])*player.last_dir[0] > 0) or \
                               (player.last_dir[1] != 0 and e.pos[0] == player.pos[0] and (e.pos[1]-player.pos[1])*player.last_dir[1] > 0):
                                enemies.remove(e); break
                    elif event.key == pygame.K_3 and player.inventory['spring'] > 0:
                        player.inventory['spring'] -= 1
                        np = [player.pos[0] + player.last_dir[0]*2, player.pos[1] + player.last_dir[1]*2]
                        if 0<=np[0]<ROWS and 0<=np[1]<COLS: player.pos = np
                    elif event.key == pygame.K_4 and player.inventory['hourglass'] > 0:
                        player.inventory['hourglass'] -= 1
                        for e in enemies: e.frozen_until = curr_time + 3
                    elif event.key == pygame.K_5 and player.inventory['brick'] > 0:
                        player.inventory['brick'] -= 1
                        bp = [player.pos[0] + player.last_dir[0], player.pos[1] + player.last_dir[1]]
                        if 0<=bp[0]<ROWS and 0<=bp[1]<COLS: maze[bp[0]][bp[1]] = 1

            elif state == "GAMEOVER":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    close_btn = pygame.Rect(WIDTH//2-70, 550, 140, 50)
                    if close_btn.collidepoint(event.pos): state = "START"; user_name = ""

        if state == "START":

            screen.blit(start_img, (0, 0))

                
            title = big_font.render("MAZE RUNNER", True, GOLD)
            screen.blit(title, (WIDTH//2 - title.get_width()//2, 160))
            pygame.draw.rect(screen, WHITE, (WIDTH//2-150, 580, 300, 50), 2)
            name_label = font.render(f"NAME : {user_name}", True, WHITE)
            screen.blit(name_label, (WIDTH//2-130, 585))
            start_btn = pygame.Rect(WIDTH//2-100, 650, 200, 60)
            pygame.draw.rect(screen, BLUE, start_btn)
            btn_txt = font.render("START", True, WHITE)
            screen.blit(btn_txt, (start_btn.centerx-btn_txt.get_width()//2, start_btn.centery-btn_txt.get_height()//2))

        elif state == "PLAYING_INIT":
            maze = create_maze()
            player = Player((ROWS-1, 0), BLUE)
            enemies = [Enemy((0, COLS-1), RED, 12)]
            items = []
            start_time = curr_time
            next_spawn = curr_time + random.randint(20, 40)
            state = "PLAYING"

        elif state == "PLAYING":
            survival_time = int(curr_time - start_time)
            # 난이도 및 스폰 로직 (기존과 동일)
            current_delay = max(4, 12 - (survival_time // 10))
            if len(enemies) < (survival_time // 30) + 1:
                enemies.append(Enemy((0, COLS-1), RED, current_delay))
            for e in enemies: e.speed_delay = current_delay

            if curr_time >= next_spawn and len(items) < 2:
                itype = random.choice(ITEM_LIST)
                while True:
                    p = (random.randint(0, ROWS-1), random.randint(0, COLS-1))
                    if maze[p[0]][p[1]] == 0:
                        if itype == 'shoes': items.append(Shoes(p))
                        elif itype == 'gun': items.append(Gun(p))
                        elif itype == 'spring': items.append(Spring(p))
                        elif itype == 'hourglass': items.append(Hourglass(p))
                        elif itype == 'brick': items.append(Brick(p))
                        break
                next_spawn = curr_time + random.randint(20, 40)

            keys = pygame.key.get_pressed()
            move_speed = 3 if curr_time < player.shoes_until else player.speed_delay
            p_ticks += 1

            if p_ticks >= move_speed:
                dr, dc = 0, 0
                
                # 1. 우선순위 입력 감지 (상하좌우 순서는 취향이나, 보통 W/S/A/D)
                if keys[pygame.K_w]: dr, dc = -1, 0
                elif keys[pygame.K_s]: dr, dc = 1, 0
                elif keys[pygame.K_a]: dr, dc = 0, -1
                elif keys[pygame.K_d]: dr, dc = 0, 1

                # 2. 이동 로직 및 벽타기(Sliding) 처리
                if dr != 0 or dc != 0:
                    nr, nc = player.pos[0] + dr, player.pos[1] + dc
                    
                    # 2-1. 원래 가려던 방향이 뚫려있는지 체크
                    if 0 <= nr < ROWS and 0 <= nc < COLS and maze[nr][nc] == 0:
                        player.pos = [nr, nc]
                        player.last_dir = (dr, dc)
                    else:
                        # 2-2. [핵심] 막혔다면, 현재 눌린 '다른 축'의 키를 체크하여 미끄러짐 구현
                        # dr(상하) 시도였다면 -> 좌우(A/D) 체크
                        # dc(좌우) 시도였다면 -> 상하(W/S) 체크
                        
                        slide_dr, slide_dc = 0, 0 # 미끄러질 방향
                        
                        if dr != 0: # 상하로 가려다 막힘 -> 좌우 체크
                            if keys[pygame.K_a]: slide_dr, slide_dc = 0, -1
                            elif keys[pygame.K_d]: slide_dr, slide_dc = 0, 1
                        elif dc != 0: # 좌우로 가려다 막힘 -> 상하 체크
                            if keys[pygame.K_w]: slide_dr, slide_dc = -1, 0
                            elif keys[pygame.K_s]: slide_dr, slide_dc = 1, 0
                        
                        # 미끄러질 방향이 정해졌다면 이동 시도
                        if slide_dr != 0 or slide_dc != 0:
                            nr, nc = player.pos[0] + slide_dr, player.pos[1] + slide_dc
                            if 0 <= nr < ROWS and 0 <= nc < COLS and maze[nr][nc] == 0:
                                player.pos = [nr, nc]
                                player.last_dir = (slide_dr, slide_dc)
                
                p_ticks = 0 # 이동 했든 못했든 틱 초기화 (입력 반응 속도 유지)

            # 아이템 획득
            for it in items[:]:
                if tuple(it.pos) == tuple(player.pos):
                    player.inventory[it.itype] += 1
                    items.remove(it)

            # 적 AI 및 충돌 (기존과 동일)
            for e in enemies:
                if curr_time < e.frozen_until: continue
                e.ticks += 1
                if e.ticks >= e.speed_delay:
                    path = a_star(maze, tuple(e.pos), tuple(player.pos))
                    if path and len(path) > 1: e.pos = list(path[1])
                    e.ticks = 0
                if e.pos == player.pos:
                    rank_data = save_ranking(user_name, survival_time)
                    state = "GAMEOVER"

            # --- 그리기 영역 ---
            # 1. 월드 렌더링
            screen.fill(BLACK)
            if has_imgs: screen.blit(ground_img, (0,0))
            
            for r in range(ROWS):
                for c in range(COLS):
                    if maze[r][c] == 1:
                        if has_imgs: screen.blit(stone_img, (c*GRID_SIZE, r*GRID_SIZE))
                        else: pygame.draw.rect(screen, (50,50,50), (c*GRID_SIZE, r*GRID_SIZE, GRID_SIZE, GRID_SIZE))

            # 아이템 그리기 (이미지 적용)
            for it in items:
                if it.itype in field_item_imgs:
                    screen.blit(field_item_imgs[it.itype], (it.pos[1]*GRID_SIZE+2, it.pos[0]*GRID_SIZE+2))
                else:
                    it.draw(screen)

            player.draw(screen)
            for e in enemies: e.draw(screen)

            if survival_time >= 120:
                fog = pygame.Surface((WIDTH, GAME_WORLD_HEIGHT), pygame.SRCALPHA)
                fog.fill(FOG_COLOR)
                pygame.draw.circle(fog, (0,0,0,0), (player.pos[1]*GRID_SIZE+10, player.pos[0]*GRID_SIZE+10), 120)
                screen.blit(fog, (0,0))

            # 2. 인벤토리 패널 렌더링
            pygame.draw.rect(screen, (30, 30, 30), (0, INV_Y, WIDTH, INV_HEIGHT))
            pygame.draw.line(screen, WHITE, (0, INV_Y), (WIDTH, INV_Y), 2)

            for i, itype in enumerate(ITEM_LIST):
                slot_rect = pygame.Rect(WIDTH//2 - 175 + i*70, INV_Y + (INV_HEIGHT - INV_SLOT_SIZE)//2, INV_SLOT_SIZE, INV_SLOT_SIZE)
                pygame.draw.rect(screen, (50, 50, 50), slot_rect)
                pygame.draw.rect(screen, WHITE, slot_rect, 1)
                
                # 인벤토리 이미지 적용
                if itype in item_imgs:
                    screen.blit(item_imgs[itype], (slot_rect.x+5, slot_rect.y+5))
                else:
                    pygame.draw.circle(screen, ITEM_COLORS[itype], slot_rect.center, 15)
                
                screen.blit(font.render(f"{i+1}", True, WHITE), (slot_rect.x+5, slot_rect.y+2))
                count_txt = font.render(f"x{player.inventory[itype]}", True, WHITE)
                screen.blit(count_txt, (slot_rect.right - count_txt.get_width() - 5, slot_rect.bottom - count_txt.get_height()))

            info_txt = font.render(f"TIME: {survival_time}s  Enemies: {len(enemies)}", True, WHITE)
            screen.blit(info_txt, (20, 20))

        elif state == "GAMEOVER":
            screen.fill(BLACK)
            # 랭킹 UI (기존과 동일)
            over_txt = big_font.render("GAME OVER", True, RED)
            screen.blit(over_txt, (WIDTH//2-over_txt.get_width()//2, 100))
            y_off = 250
            rank_h = font.render("--- TOP 5 RANKING ---", True, GOLD)
            screen.blit(rank_h, (WIDTH//2-rank_h.get_width()//2, y_off))
            for i, r in enumerate(rank_data):
                txt = font.render(f"{i+1}. {r[0]} : {r[1]}s", True, WHITE)
                screen.blit(txt, (WIDTH//2-txt.get_width()//2, y_off + 40 + i*35))
            close_btn = pygame.Rect(WIDTH//2-70, 550, 140, 50)
            pygame.draw.rect(screen, RED, close_btn)
            c_txt = font.render("CLOSE", True, WHITE)
            screen.blit(c_txt, (close_btn.centerx-c_txt.get_width()//2, close_btn.centery-c_txt.get_height()//2))

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()