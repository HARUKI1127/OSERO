import pygame

pygame.init()

#関数---------------------------------------------------------------------------
#グリッド線の描画
def draw_grid():
    for i in range(square_num):
        #横線
        pygame.draw.line(screen, BLACK, (0, i * square_size), (screen_width, i * square_size), 3)
        #縦線
        pygame.draw.line(screen, BLACK, (i * square_size, 0), (i * square_size, screen_height), 3)

#盤面の描画
def draw_board():
    for row_index, row in enumerate(board):
        for col_index, col in enumerate(row):
            if col == 1:
                pygame.draw.circle(screen, BLACK, (col_index * square_size + 50, row_index * square_size + 50), 45)
            elif col == -1:
                pygame.draw.circle(screen, WHITE, (col_index * square_size + 50, row_index * square_size + 50), 45)

#石を置ける場所の取得
def get_valid_positions():
    valid_position_list = []
    for row in range(square_num):
        for col in range(square_num):
            #石を置いていないマスのみチェック
            if board[row][col] == 0:
                for vx, vy in vec_table:
                    x = vx + col
                    y = vy + row
                    #マスの範囲内、かつプレイヤーの石と異なる石がある場合、その方向は引き続きチェック
                    if 0 <= x < square_num and 0 <= y < square_num and board[y][x] == -player:
                        while True:
                            x += vx
                            y += vy
                            #プレイヤーの石と異なる色の石がある場合、その方向は引き続きチェック
                            if 0 <= x < square_num and 0 <= y < square_num and board[y][x] == -player:
                                continue
                            #プレイヤーの石と同色の石がある場合、石を置けるためインデックスを保存
                            elif 0 <= x < square_num and 0 <= y < square_num and board[y][x] == player:
                                valid_position_list.append((col, row))
                                break
                            else:
                                break
    return valid_position_list

#石をひっくり返す
def flip_pieces(col, row):
    for vx, vy in vec_table:
        flip_list = []
        x = vx + col
        y = vy + row
        while 0 <= x < square_num and 0 <= y < square_num and board[y][x] == -player:
            flip_list.append((x, y))
            x += vx
            y += vy
            if 0 <= x < square_num and 0 <= y < square_num and board[y][x] == player:
                for flip_x, flip_y in flip_list:
                    board[flip_y][flip_x] = player