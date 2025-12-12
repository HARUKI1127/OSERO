import pygame

# オセロ（リバーシ）改良版
# 主な改善点:
# - 描画を square_size に合わせて動的に計算（ハードコーディングされた "50/45" を廃止）
# - 合法手表示を半透明のプレビューでわかりやすく表示
# - 最後に置いた石をハイライト
# - パス判定の二重実行を防ぐフラグ（同じターンで繰り返しパスしない）
# - 黒/白の石数と現在のターンを画面に表示
# - r キーでリセット、Esc で終了

pygame.init()

# 定数 / 設定 ---------------------------------------------------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
SQUARE_NUM = 8
FPS = 60

# 色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 128, 0)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)

# 方向ベクトル
VEC_TABLE = [
    (-1, -1), (0, -1), (1, -1),
    (-1, 0),          (1, 0),
    (-1, 1),  (0, 1),  (1, 1)
]

# 初期化 ------------------------------------------------------------------
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("オセロ（改良版）")
clock = pygame.time.Clock()

square_size = SCREEN_WIDTH // SQUARE_NUM
stone_radius = int(square_size * 0.42)

font_small = pygame.font.SysFont(None, 28)
font_big = pygame.font.SysFont(None, 72)

# 盤面（黒:1、白:-1、空:0）
def create_initial_board():
    b = [[0] * SQUARE_NUM for _ in range(SQUARE_NUM)]
    mid = SQUARE_NUM // 2
    b[mid - 1][mid - 1] = -1
    b[mid - 1][mid] = 1
    b[mid][mid - 1] = 1
    b[mid][mid] = -1
    return b

board = create_initial_board()
player = 1  # 黒からスタート

game_over = False
pass_num = 0
passed_this_turn = False  # 同じプレイヤーが何フレームもパスされるのを防ぐフラグ
last_move = None  # (x,y) 最後に置かれたマス

# ユーティリティ関数 ------------------------------------------------------

def board_center(col, row):
    return (col * square_size + square_size // 2, row * square_size + square_size // 2)


def count_pieces(b):
    black = sum(row.count(1) for row in b)
    white = sum(row.count(-1) for row in b)
    return black, white

# 描画 --------------------------------------------------------------------

def draw_grid():
    for i in range(SQUARE_NUM + 1):
        pygame.draw.line(screen, BLACK, (0, i * square_size), (SCREEN_WIDTH, i * square_size), 2)
        pygame.draw.line(screen, BLACK, (i * square_size, 0), (i * square_size, SCREEN_HEIGHT), 2)


def draw_board(b):
    for y, row in enumerate(b):
        for x, col in enumerate(row):
            if col == 1:
                pygame.draw.circle(screen, BLACK, board_center(x, y), stone_radius)
            elif col == -1:
                pygame.draw.circle(screen, WHITE, board_center(x, y), stone_radius)

    # 最後の手をハイライト
    if last_move is not None:
        lx, ly = last_move
        cx, cy = board_center(lx, ly)
        pygame.draw.circle(screen, YELLOW, (cx, cy), stone_radius + 6, 3)


def draw_ui(b, current_player):
    black, white = count_pieces(b)
    # スコア表示
    score_text = f"Black: {black}   White: {white}"
    screen.blit(font_small.render(score_text, True, BLACK), (10, 10))

    # 現在のターン表示
    turn_text = "Black's turn" if current_player == 1 else "White's turn"
    screen.blit(font_small.render(turn_text, True, BLACK), (10, 36))

    # ゲームオーバー表示
    if game_over:
        if black > white:
            text = "Black Win!"
        elif black < white:
            text = "White Win!"
        else:
            text = "Draw"
        surf = font_big.render(text, True, BLACK)
        rect = surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        screen.blit(surf, rect)
        reset_surf = font_small.render("Press R to reset", True, BLACK)
        screen.blit(reset_surf, (SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 + 30))

# 合法手の探索 --------------------------------------------------------------

def get_valid_positions_for(b, current_player):
    valid = set()
    for row in range(SQUARE_NUM):
        for col in range(SQUARE_NUM):
            if b[row][col] != 0:
                continue
            for vx, vy in VEC_TABLE:
                x = col + vx
                y = row + vy
                if not (0 <= x < SQUARE_NUM and 0 <= y < SQUARE_NUM):
                    continue
                if b[y][x] != -current_player:
                    continue
                # 隣が相手の石なので先へ進める
                while True:
                    x += vx
                    y += vy
                    if not (0 <= x < SQUARE_NUM and 0 <= y < SQUARE_NUM):
                        break
                    if b[y][x] == 0:
                        break
                    if b[y][x] == current_player:
                        valid.add((col, row))
                        break
                    # else continue（相手の石が続く）
    return list(valid)

# 石をひっくり返す ---------------------------------------------------------

def flip_pieces(b, col, row, current_player):
    flipped_any = False
    for vx, vy in VEC_TABLE:
        flip_list = []
        x = col + vx
        y = row + vy
        while 0 <= x < SQUARE_NUM and 0 <= y < SQUARE_NUM and b[y][x] == -current_player:
            flip_list.append((x, y))
            x += vx
            y += vy
        if 0 <= x < SQUARE_NUM and 0 <= y < SQUARE_NUM and b[y][x] == current_player and flip_list:
            for fx, fy in flip_list:
                b[fy][fx] = current_player
            flipped_any = True
    return flipped_any

# リセット ----------------------------------------------------------------

def reset_game():
    global board, player, game_over, pass_num, passed_this_turn, last_move
    board = create_initial_board()
    player = 1
    game_over = False
    pass_num = 0
    passed_this_turn = False
    last_move = None

# メインループ --------------------------------------------------------------

run = True
while run:
    screen.fill(GREEN)

    draw_grid()
    draw_board(board)

    valid_positions = get_valid_positions_for(board, player)

    # 合法手のプレビュー（半透明）
    if valid_positions:
        passed_this_turn = False
        for x, y in valid_positions:
            cx, cy = board_center(x, y)
            preview = pygame.Surface((square_size, square_size), pygame.SRCALPHA)
            pygame.draw.circle(preview, (255, 255, 0, 120), (square_size // 2, square_size // 2), stone_radius, 0)
            screen.blit(preview, (x * square_size, y * square_size))
    else:
        # 合法手が無ければ自動でパス（ただし同じプレイヤーの連続パスはしない）
        if not passed_this_turn and not game_over:
            player *= -1
            pass_num += 1
            passed_this_turn = True

    # ゲームオーバー判定
    if pass_num > 1:
        game_over = True
        pass_num = 2

    draw_ui(board, player)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                run = False
            elif event.key == pygame.K_r:
                reset_game()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            x = mx // square_size
            y = my // square_size
            # 範囲外クリックに備える
            if not (0 <= x < SQUARE_NUM and 0 <= y < SQUARE_NUM):
                continue

            if game_over:
                # ゲームオーバー中はクリックでリセット
                reset_game()
                continue

            valid_positions = get_valid_positions_for(board, player)
            if (x, y) in valid_positions and board[y][x] == 0:
                flipped = flip_pieces(board, x, y, player)
                if flipped:
                    board[y][x] = player
                    last_move = (x, y)
                    player *= -1
                    pass_num = 0
                    passed_this_turn = False

    pygame.display.update()
    clock.tick(FPS)

pygame.quit()
