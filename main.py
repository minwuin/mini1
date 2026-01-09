import pygame, sys, time, random, os
from constants import *
from classes import *
from utils import a_star, create_maze, save_ranking

def main():
    pygame.init()
    pygame.mixer.init()
    
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("MAZE RUNNER")
    clock = pygame.time.Clock()
    
    if os.path.exists(FONT_PATH):
        font = pygame.font.Font(FONT_PATH, 25)
        big_font = pygame.font.Font(FONT_PATH, 70)
    else:
        # 폰트 파일이 없으면 맑은 고딕 시도
        print("폰트 파일을 찾을 수 없어 시스템 폰트를 사용합니다.")
        font = pygame.font.SysFont("malgungothic", 25, bold=True)
        big_font = pygame.font.SysFont("malgungothic", 70, bold=True)

    # --- 이미지 로드 섹션 ---
    item_imgs = {}
    field_item_imgs = {} # 필드용 작은 이미지
    bullet_img = None
    player_img = None
    enemy_imgs = [] # 적 이미지 3개를 담을 리스트

    try:
        # 1. 아이템 효과음 로드 (mp3)
        if os.path.exists(ITEM_SFX_PATH):
            item_sfx = pygame.mixer.Sound(ITEM_SFX_PATH)
            item_sfx.set_volume(0.7) # 소리가 너무 크면 0.1~1.0 사이로 조절하세요
            
        # 2. 게임오버 효과음 로드
        if os.path.exists(GAMEOVER_SFX_PATH):
            gameover_sfx = pygame.mixer.Sound(GAMEOVER_SFX_PATH)
            gameover_sfx.set_volume(1.0)

        # 1. 배경 및 벽 로드 (constants.py의 변수명 사용)
        ground_img = pygame.transform.scale(pygame.image.load(GROUND_PATH), (WIDTH, GAME_WORLD_HEIGHT))
        stone_img = pygame.transform.scale(pygame.image.load(STONE_PATH), (GRID_SIZE, GRID_SIZE))
        start_img = pygame.transform.scale(pygame.image.load(START_PATH), (WIDTH, HEIGHT))
        frozen_img = pygame.transform.scale(pygame.image.load(FROZEN_ENEMY_PATH), (GRID_SIZE-4, GRID_SIZE-4))
        bullet_img = pygame.transform.scale(pygame.image.load(BULLET_PATH), (GRID_SIZE//2 + 5, GRID_SIZE//2 + 5))
        player_img = pygame.transform.scale(pygame.image.load(PLAYER_PATH), (GRID_SIZE-4, GRID_SIZE-4))
        e_paths = [ENEMY_1_PATH, ENEMY_2_PATH, ENEMY_3_PATH]
        for path in e_paths:
            if os.path.exists(path):
                e_raw = pygame.image.load(path)
                scaled_e = pygame.transform.scale(e_raw, (GRID_SIZE-4, GRID_SIZE-4))
                enemy_imgs.append(scaled_e)
            else:
                enemy_imgs.append(None) # 파일 없으면 None



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
    bullets = []
    start_time = 0
    next_spawn = 0
    p_ticks = 0
    show_help = False
    pause_start = 0
    start_time = 0
    countdown_start = 0
    if os.path.exists(LOBBY_BGM_PATH):
        pygame.mixer.music.load(LOBBY_BGM_PATH)
        pygame.mixer.music.play(-1) # -1은 '무한 반복'이라는 뜻입니다.

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
                    if start_btn.collidepoint(event.pos):
                        # 설명창이 열려있으면 시작 안 됨
                        if not show_help and user_name: 
                            state = "PLAYING_INIT"

                    help_btn = pygame.Rect(WIDTH//2-100, 730, 200, 60)
                    if help_btn.collidepoint(event.pos):
                        show_help = not show_help # 켜져있으면 끄고, 꺼져있으면 켬


            elif state == "PLAYING":
                if event.type == pygame.KEYDOWN:
                    # 아이템 사용 로직 (기존과 동일)
                    if event.key == pygame.K_1 and player.inventory['shoes'] > 0:
                        player.inventory['shoes'] -= 1; player.shoes_until = curr_time + 10
                    elif event.key == pygame.K_2 and player.inventory['gun'] > 0:
                        player.inventory['gun'] -= 1
                        bullets.append(Bullet(player.pos, player.last_dir))

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

                    if event.key == pygame.K_ESCAPE:
                        state = "PAUSED"
                        pause_start = curr_time # 멈춘 시각 기록
                        pygame.mixer.music.pause()


            elif state == "PAUSED":
                if event.type == pygame.KEYDOWN:
                    # ESC 다시 누르면 게임 재개
                    if event.key == pygame.K_ESCAPE:
                        # 멈춰있던 시간만큼 게임 시간들을 뒤로 밀어주기 (보정)
                        offset = curr_time - pause_start
                        start_time += offset
                        next_spawn += offset
                        player.shoes_until += offset
                        for e in enemies: e.frozen_until += offset
                        state = "PLAYING"
                        pygame.mixer.music.unpause()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    # 버튼 영역 정의 (그리기 좌표와 동일하게 설정)
                    resume_btn = pygame.Rect(WIDTH//2 - 100, 450, 200, 60)
                    home_btn = pygame.Rect(WIDTH//2 - 100, 530, 200, 60)

                    # 1. 계속하기 (Resume)
                    if resume_btn.collidepoint(event.pos):
                        offset = curr_time - pause_start
                        start_time += offset
                        next_spawn += offset
                        player.shoes_until += offset
                        for e in enemies: e.frozen_until += offset
                        state = "PLAYING"
                        pygame.mixer.music.unpause()

                    # 2. 홈으로 (Home)
                    if home_btn.collidepoint(event.pos):
                        state = "START"
                        user_name = ""
                        if os.path.exists(LOBBY_BGM_PATH):
                            pygame.mixer.music.load(LOBBY_BGM_PATH)
                            pygame.mixer.music.set_volume(1.0) # 볼륨 다시 원상복구 (100%)
                            pygame.mixer.music.play(-1)

            elif state == "GAMEOVER":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    retry_btn = pygame.Rect(WIDTH//2 - 150, 550, 140, 50)
                    quit_btn = pygame.Rect(WIDTH//2 + 10, 550, 140, 50)
                    if retry_btn.collidepoint(event.pos): 
                        state = "START"; user_name = ""

                        if os.path.exists(LOBBY_BGM_PATH):
                            pygame.mixer.music.load(LOBBY_BGM_PATH)
                            pygame.mixer.music.play(-1)
                    
                    if quit_btn.collidepoint(event.pos):
                        pygame.quit()  # 파이게임 창 닫기
                        sys.exit()     # 파이썬 프로그램 종료

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
            
            help_btn = pygame.Rect(WIDTH//2-100, 730, 200, 60)
            pygame.draw.rect(screen, (50, 50, 50), help_btn) # 회색 버튼
            help_txt = font.render("HOW TO PLAY", True, WHITE)
            screen.blit(help_txt, (help_btn.centerx - help_txt.get_width()//2, help_btn.centery - help_txt.get_height()//2))
            
            if show_help:
                # 반투명 검은 배경
                s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                s.fill((0, 0, 0, 230)) 
                screen.blit(s, (0,0))
                
                # 설명 문구들
                msgs = [
                    "--- GAME RULES ---",
                    "",
                    "[WASD] Move",
                    "[1] Shoes (Speed Up)",
                    "[2] Gun (Kill Enemy)",
                    "[3] Spring (Jump Wall)",
                    "[4] Hourglass (Freeze)",
                    "[5] Brick (Build Wall)",
                    "",
                    "Survive as long as you can!",
                    "(Click to Close)"
                ]
                
                # 줄바꿈하며 출력
                for i, line in enumerate(msgs):
                    txt = font.render(line, True, WHITE)
                    screen.blit(txt, (WIDTH//2 - txt.get_width()//2, 150 + i * 40))


        elif state == "PLAYING_INIT":
            maze = create_maze()
            player = Player((ROWS-1, 0), BLUE)
            player.trail = []
            trail_decay = 0
            enemies = [Enemy((0, COLS-1), RED, 12)]
            items = []
            bullets = []
            prev_player_pos = player.pos
            countdown_start = curr_time 
            pygame.mixer.music.stop()
            state = "COUNTDOWN"
        
        # [수정됨] COUNTDOWN과 PLAYING 상태를 하나의 블록으로 통합
        elif state == "PLAYING" or state == "COUNTDOWN":
            
            # 1. 카운트다운 로직 (타이머 계산만 수행)
            if state == "COUNTDOWN":
                elapsed = curr_time - countdown_start
                if elapsed >= 4:
                    start_time = curr_time
                    next_spawn = curr_time + random.randint(5, 10)
                    player.shoes_until = 0
                    state = "PLAYING"

                    if os.path.exists(GAME_BGM_PATH):
                        pygame.mixer.music.load(GAME_BGM_PATH) # 게임 BGM 로드
                        pygame.mixer.music.set_volume(0.4)
                        pygame.mixer.music.play(-1) # 무한 반복 재생
            
            # 2. 게임 플레이 로직 (이동, 스폰, 충돌 등) -> ★ PLAYING 상태일 때만 실행 ★
            if state == "PLAYING":
                survival_time = int(curr_time - start_time)
                current_delay = max(4, 12 - (survival_time // 10)) 
            
                if len(enemies) < (survival_time // 10) + 1:
                    try:
                        spawn_pos = get_safe_pos(maze)
                    except:
                        spawn_pos = (0, COLS - 1)
                    if abs(spawn_pos[0] - player.pos[0]) + abs(spawn_pos[1] - player.pos[1]) > 10:
                        enemies.append(Enemy(spawn_pos, RED, current_delay))
            
                for e in enemies:
                    e.speed_delay = current_delay

                if curr_time >= next_spawn and len(items) < 10:
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
                    next_spawn = curr_time + random.randint(2, 3)

                keys = pygame.key.get_pressed()
                move_speed = 3 if curr_time < player.shoes_until else player.speed_delay
                p_ticks += 1
                temp_prev_pos = list(player.pos)
                player_moved = False

                if p_ticks >= move_speed:
                    dr, dc = 0, 0
                    if keys[pygame.K_w]: dr, dc = -1, 0
                    elif keys[pygame.K_s]: dr, dc = 1, 0
                    elif keys[pygame.K_a]: dr, dc = 0, -1
                    elif keys[pygame.K_d]: dr, dc = 0, 1

                    if dr != 0 or dc != 0:
                        # 다음 이동할 좌표 계산
                        nr, nc = player.pos[0] + dr, player.pos[1] + dc
                        
                        # 실제로 이동할 확정 좌표를 담을 변수
                        final_pos = None
                        final_dir = (0, 0)

                        # 1. 원래 가려던 방향이 뚫려있는지 체크 (일반 이동)
                        if 0 <= nr < ROWS and 0 <= nc < COLS and maze[nr][nc] == 0:
                            final_pos = [nr, nc]
                            final_dir = (dr, dc)
                        
                        # 2. 막혔다면 미끄러짐(Sliding) 체크
                        else:
                            slide_dr, slide_dc = 0, 0
                            if dr != 0: # 상하로 가려다 막힘 -> 좌우 체크
                                if keys[pygame.K_a]: slide_dr, slide_dc = 0, -1
                                elif keys[pygame.K_d]: slide_dr, slide_dc = 0, 1
                            elif dc != 0: # 좌우로 가려다 막힘 -> 상하 체크
                                if keys[pygame.K_w]: slide_dr, slide_dc = -1, 0
                                elif keys[pygame.K_s]: slide_dr, slide_dc = 1, 0
                            
                            # 미끄러질 방향이 유효한지 체크
                            if slide_dr != 0 or slide_dc != 0:
                                nr, nc = player.pos[0] + slide_dr, player.pos[1] + slide_dc
                                if 0 <= nr < ROWS and 0 <= nc < COLS and maze[nr][nc] == 0:
                                    final_pos = [nr, nc]
                                    final_dir = (slide_dr, slide_dc)

                        # [핵심] 이동이 확정되었다면 잔상을 남기고 이동
                        if final_pos is not None:
                            player_moved = True

                            # 신발 사용 중일 때만 잔상 기록
                            if curr_time < player.shoes_until:
                                player.trail.append(tuple(player.pos)) # 현재 위치를 과거 기록에 저장
                                # 꼬리 길이 제한 (너무 길면 지저분하므로 5개 정도 유지)
                                if len(player.trail) > 6:
                                    player.trail.pop(0)

                            player.pos = final_pos
                            player.last_dir = final_dir

                        p_ticks = 0 # 틱 초기화

                    if not player_moved and player.trail:
                        trail_decay += 1
                    # 5프레임마다 잔상을 하나씩 지움 (속도 조절 가능)
                        if trail_decay >= 1:
                            player.trail.pop(0) # 가장 오래된 잔상 제거
                            trail_decay = 0
                    else:
                        trail_decay = 0 # 움직이면 소멸 타이머 초기화

                    if player.pos != temp_prev_pos:
                        prev_player_pos = temp_prev_pos
                    
                    if curr_time >= player.shoes_until and player.trail:
                        player.trail = []
                    
                   

                if player.pos != temp_prev_pos:
                    prev_player_pos = temp_prev_pos

                # 아이템 획득
                for it in items[:]:
                    if tuple(it.pos) == tuple(player.pos):
                        player.inventory[it.itype] += 1
                        items.remove(it)

                        if item_sfx: 
                            item_sfx.play()

                # 총알 업데이트
                for b in bullets[:]:
                    b.update()
                    if not (0 <= b.r < ROWS and 0 <= b.c < COLS) or maze[int(b.r)][int(b.c)] == 1:
                        bullets.remove(b)
                        continue
                    hit_enemy = False
                    for e in enemies[:]:
                        if abs(b.r - e.pos[0]) < 0.8 and abs(b.c - e.pos[1]) < 0.8:
                            enemies.remove(e)
                            hit_enemy = True
                            break 
                    if hit_enemy:
                        bullets.remove(b)

                # 적 AI 로직
                sorted_e = sorted(enemies, key=lambda e: abs(e.pos[0] - player.pos[0]) + abs(e.pos[1] - player.pos[1]))
                min_dist = abs(sorted_e[0].pos[0] - player.pos[0]) + abs(sorted_e[0].pos[1] - player.pos[1]) if sorted_e else 999
                is_full_pursuit = (min_dist <= 5)

                for rank, e in enumerate(sorted_e): e.rank_idx = rank
                for e in enemies:
                    if curr_time < e.frozen_until: continue
                    e.ticks += 1
                    if e.ticks >= e.speed_delay:
                        others = [oe.pos for oe in enemies if oe != e]
                        role_idx = getattr(e, 'rank_idx', 0) % 3
                        target = player.pos
                        if is_full_pursuit or role_idx == 0:
                            e.color = RED
                            target = player.pos
                        elif role_idx == 1:
                            e.color = (255, 255, 0)
                            try: target = get_intercept_pos(maze, player.pos, prev_player_pos, offset=3)
                            except: target = player.pos
                        else:
                            e.color = (128, 0, 128)
                            try: target = get_intercept_pos(maze, player.pos, prev_player_pos, offset=5)
                            except: target = player.pos

                        try: path = a_star(maze, tuple(e.pos), tuple(target), others)
                        except TypeError: path = a_star(maze, tuple(e.pos), tuple(target))
                        
                        if path and len(path) > 1: e.pos = list(path[1])
                        else:
                            try: p_alt = a_star(maze, tuple(e.pos), tuple(player.pos), others)
                            except: p_alt = a_star(maze, tuple(e.pos), tuple(player.pos))
                            if p_alt and len(p_alt) > 1: e.pos = list(p_alt[1])
                        e.ticks = 0
                    
                    if e.pos == player.pos:
                        rank_data = save_ranking(user_name, survival_time)
                        state = "GAMEOVER"

                        pygame.mixer.music.stop() # 시끄러운 배경음악 끄기
                        if gameover_sfx: 
                            gameover_sfx.play() # 띠로리~ 효과음 재생

            # --- 그리기 영역 (COUNTDOWN, PLAYING 공통) ---
            screen.fill(BLACK)
            if has_imgs: screen.blit(ground_img, (0,0))
            
            for r in range(ROWS):
                for c in range(COLS):
                    if maze[r][c] == 1:
                        if has_imgs: screen.blit(stone_img, (c*GRID_SIZE, r*GRID_SIZE))
                        else: pygame.draw.rect(screen, (50,50,50), (c*GRID_SIZE, r*GRID_SIZE, GRID_SIZE, GRID_SIZE))

            for it in items:
                if it.itype in field_item_imgs:
                    screen.blit(field_item_imgs[it.itype], (it.pos[1]*GRID_SIZE+2, it.pos[0]*GRID_SIZE+2))
                else: it.draw(screen)

            for b in bullets:
                # 아까 로드한 bullet_img를 인자로 넘겨줍니다.
                b.draw(screen, bullet_img)

            for b in bullets: b.draw(screen)

            if state == "PLAYING" and curr_time < player.shoes_until and player.trail:
                # 1. 반투명한 파란색 네모를 그릴 임시 도화지(Surface) 생성
                # 크기는 GRID_SIZE x GRID_SIZE
                for i, (tr, tc) in enumerate(player.trail):
                    
                    # 1. 꽉 찬 사각형 도화지 생성 (여백 없음!)
                    ghost_surf = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
                    
                    # 2. 그라데이션 효과 (플레이어에 가까울수록 진하게)
                    # i+1을 해서 0이 안 되게 하고, 전체 개수로 나눠 비율을 구함
                    # 최대 투명도 150 (0~255)
                    alpha = int(150 * (i + 1) / len(player.trail))
                    ghost_color = (BLUE[0], BLUE[1], BLUE[2], alpha)
                    
                    # 3. 꽉 찬 네모 그리기 (좌표 0, 0에서 시작, 크기는 GRID_SIZE 전체)
                    # 여백을 주던 (2, 2, GRID_SIZE-4...) 코드를 제거했습니다.
                    pygame.draw.rect(ghost_surf, ghost_color, (0, 0, GRID_SIZE, GRID_SIZE))

                    # 4. 화면에 그리기
                    screen.blit(ghost_surf, (tc * GRID_SIZE, tr * GRID_SIZE))

            # [수정] 플레이어 그리기 (플레이어 이미지 전달)
            # player_img 변수가 로드되어 있어야 합니다.
            player.draw(screen, player_img)

            # [수정] 적 그리기 (얼음 이미지 + 종류별 이미지 전달)
            # 1. 얼음 이미지 준비
            f_img_to_use = frozen_img if has_imgs and 'frozen_img' in locals() and frozen_img is not None else None
            
            for e in enemies:
                # 2. 적의 역할(0, 1, 2) 계산
                # e.rank_idx가 없으면 기본값 0
                role_idx = getattr(e, 'rank_idx', 0) % 3
                
                # 3. 해당 역할에 맞는 이미지 선택 (enemy_imgs 리스트에서 꺼냄)
                current_enemy_img = None
                # enemy_imgs 리스트가 있고, 인덱스가 유효한지 확인
                if 'enemy_imgs' in locals() and enemy_imgs and len(enemy_imgs) > role_idx:
                    current_enemy_img = enemy_imgs[role_idx]

                # 4. 그리기 메서드 호출 
                # 인자 순서: (화면, 얼음이미지, 평소이미지, 현재시간)
                e.draw(screen, f_img_to_use, current_enemy_img, curr_time)



            
            if state == "PLAYING" and 'survival_time' in locals() and survival_time >= 120:
                fog = pygame.Surface((WIDTH, GAME_WORLD_HEIGHT), pygame.SRCALPHA)
                fog.fill(FOG_COLOR)
                pygame.draw.circle(fog, (0,0,0,0), (player.pos[1]*GRID_SIZE+10, player.pos[0]*GRID_SIZE+10), 120)
                screen.blit(fog, (0,0))

            # 인벤토리 패널
            pygame.draw.rect(screen, (30, 30, 30), (0, INV_Y, WIDTH, INV_HEIGHT))
            pygame.draw.line(screen, WHITE, (0, INV_Y), (WIDTH, INV_Y), 2)

            for i, itype in enumerate(ITEM_LIST):
                slot_rect = pygame.Rect(WIDTH//2 - 175 + i*70, INV_Y + (INV_HEIGHT - INV_SLOT_SIZE)//2, INV_SLOT_SIZE, INV_SLOT_SIZE)
                pygame.draw.rect(screen, (50, 50, 50), slot_rect)
                pygame.draw.rect(screen, WHITE, slot_rect, 1)
                
                if itype in item_imgs: screen.blit(item_imgs[itype], (slot_rect.x+5, slot_rect.y+5))
                else: pygame.draw.circle(screen, ITEM_COLORS[itype], slot_rect.center, 15)
                
                screen.blit(font.render(f"{i+1}", True, WHITE), (slot_rect.x+5, slot_rect.y+2))
                count_txt = font.render(f"x{player.inventory[itype]}", True, WHITE)
                screen.blit(count_txt, (slot_rect.right - count_txt.get_width() - 5, slot_rect.bottom - count_txt.get_height()))

            # UI 텍스트 (시간, 적 숫자) - 카운트다운 중에는 0초/1마리로 표시
            disp_time = survival_time if state == "PLAYING" else 0
            disp_enemies = len(enemies)
            
            time_txt = font.render(f"TIME: {disp_time}s", True, WHITE)
            screen.blit(time_txt, (WIDTH - time_txt.get_width() - 20, INV_Y + 20))

            enemy_txt = font.render(f"Enemies: {disp_enemies}", True, WHITE)
            screen.blit(enemy_txt, (WIDTH - enemy_txt.get_width() - 20, INV_Y + 50))
            
            # [카운트다운 숫자 표시]
            if state == "COUNTDOWN":
                overlay = pygame.Surface((WIDTH, GAME_WORLD_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 100))
                screen.blit(overlay, (0, 0))

                elapsed = curr_time - countdown_start
                count_txt = ""
                if elapsed < 1: count_txt = "3"
                elif elapsed < 2: count_txt = "2"
                elif elapsed < 3: count_txt = "1"
                else: count_txt = "START!!"

                txt_color = RED if count_txt == "START!!" else GOLD
                
                # 폰트 안전장치
                try: c_font = pygame.font.Font(FONT_PATH, 150) 
                except: c_font = pygame.font.SysFont("malgungothic", 150, bold=True)
                
                render_txt = c_font.render(count_txt, True, txt_color)
                outline_txt = c_font.render(count_txt, True, BLACK)
                screen.blit(outline_txt, (WIDTH//2 - render_txt.get_width()//2 + 4, GAME_WORLD_HEIGHT//2 - render_txt.get_height()//2 + 4))
                screen.blit(render_txt, (WIDTH//2 - render_txt.get_width()//2, GAME_WORLD_HEIGHT//2 - render_txt.get_height()//2))

        # [여기에 바로 이어지는 코드는 elif state == "GAMEOVER": 여야 합니다]

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

            retry_btn = pygame.Rect(WIDTH//2-150, 550, 140, 50)
            pygame.draw.rect(screen, RED, retry_btn)
            c_txt = font.render("RETRY", True, WHITE)
            screen.blit(c_txt, (retry_btn.centerx-c_txt.get_width()//2, retry_btn.centery-c_txt.get_height()//2))

            quit_btn = pygame.Rect(WIDTH//2 + 10, 550, 140, 50)
            pygame.draw.rect(screen, RED, quit_btn)
            q_txt = font.render("QUIT", True, WHITE)
            screen.blit(q_txt, (quit_btn.centerx - q_txt.get_width()//2, quit_btn.centery - q_txt.get_height()//2))
        
        # 화면 그리기 섹션의 적당한 곳 (elif state == "GAMEOVER": 위나 아래)
        
        elif state == "PAUSED":
            # 1. 반투명 배경
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            s.fill((0, 0, 0, 150)) # 약간 어둡게
            screen.blit(s, (0,0))

            # 2. PAUSE 제목
            pause_txt = big_font.render("PAUSED", True, WHITE)
            screen.blit(pause_txt, (WIDTH//2 - pause_txt.get_width()//2, 200))

            # 3. 현재 스코어 표시
            # 멈춘 시점 기준 스코어 계산
            current_score = int(pause_start - start_time) 
            score_txt = font.render(f"Current Score: {current_score}s", True, GOLD)
            screen.blit(score_txt, (WIDTH//2 - score_txt.get_width()//2, 300))

            # 4. 계속하기 버튼 (Resume)
            resume_btn = pygame.Rect(WIDTH//2 - 100, 450, 200, 60)
            pygame.draw.rect(screen, BLUE, resume_btn)
            
            # 4-1. 꽉 찬 삼각형 (>) 그리기
            # 버튼 왼쪽 부분에 삼각형 배치
            tri_center_x = resume_btn.left + 40
            tri_center_y = resume_btn.centery
            # 삼각형 좌표: (왼쪽위, 왼쪽아래, 오른쪽중간)
            points = [
                (tri_center_x - 10, tri_center_y - 12),
                (tri_center_x - 10, tri_center_y + 12),
                (tri_center_x + 10, tri_center_y)
            ]
            pygame.draw.polygon(screen, WHITE, points)

            # 4-2. 텍스트
            cont_txt = font.render("CONTINUE", True, WHITE)
            screen.blit(cont_txt, (resume_btn.centerx -20, resume_btn.centery - cont_txt.get_height()//2))


            # 5. 홈으로 가기 버튼 (Home)
            home_btn = pygame.Rect(WIDTH//2 - 100, 530, 200, 60)
            pygame.draw.rect(screen, RED, home_btn)

            # 5-1. 집 모양 그리기 (세모 지붕 + 네모 몸통)
            house_center_x = home_btn.left + 40
            house_center_y = home_btn.centery
            
            # 지붕 (세모)
            roof_points = [
                (house_center_x, house_center_y - 15),       # 위
                (house_center_x - 12, house_center_y - 3),   # 왼쪽 아래
                (house_center_x + 12, house_center_y - 3)    # 오른쪽 아래
            ]
            pygame.draw.polygon(screen, WHITE, roof_points)
            
            # 몸통 (네모)
            pygame.draw.rect(screen, WHITE, (house_center_x - 9, house_center_y - 3, 18, 15))

            # 5-2. 텍스트
            h_txt = font.render("GO HOME", True, WHITE)
            screen.blit(h_txt, (home_btn.centerx - 20 , home_btn.centery - h_txt.get_height()//2))
    
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()