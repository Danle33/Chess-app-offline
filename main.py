import pygame
import sys
import copy
import os

pygame.init()

# CONFIGURATION

# aspect ratio 9 : 19.5
WIDTH = 450
HEIGHT = 975

# screen moves when in settings
SCREEN_OFFSET_X = 0
SCREEN_OFFSET_Y = 0

TABLE_X = SCREEN_OFFSET_X
TABLE_Y = HEIGHT / 2 - WIDTH / 2 + SCREEN_OFFSET_Y

#colors
WHITE = (255, 255, 255)
BLACKY = (30, 30, 30)
DARK_GREEN_TRANSPARENT = (0, 50, 0, 50)
DARK_GREEN_TRANSPARENT1 = (0, 50, 0, 25)
YELLOW_TRANSPARENT = (255, 255, 0, 20)
YELLOW_TRANSPARENT1 = (255, 255, 0, 10)
RED_TRANSPARENT = (255, 0, 0, 50)
GRAY = (128, 128, 128)

promoting = False
pieces_promotion = pygame.sprite.Group()
promotion_square = None

#globals
minutes = 0.25
availableMinutes = [0.25, 0.5, 1, 2, 3, 5, 10, 20, 30, 60, 120, 180]

increment = 0
availableIncrements = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 30, 60]

SQUARE_SIZE = WIDTH / 8
game_started = False
# clocks are only starting after a pair of moves
clocks_started = False

resigned = False
draw = False

# darken the screen while promoting
dark_overlay = pygame.Surface((WIDTH, WIDTH))  # Create a surface
dark_overlay.set_alpha(200)  # Set alpha (0 is transparent, 255 is opaque)
dark_overlay.fill((0, 0, 0))  # Fill with black

# mark moving squares yellowish
moving_square_prev = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
moving_square_prev.fill(YELLOW_TRANSPARENT1)
rect_moving_square_prev = moving_square_prev.get_rect()
rect_moving_square_prev.center = (-1, -1)

moving_square_curr = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
moving_square_curr.fill(YELLOW_TRANSPARENT)
rect_moving_square_curr = moving_square_prev.get_rect()

check_square = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
check_square.fill(RED_TRANSPARENT)
rect_check_square = check_square.get_rect()
rect_check_square.center = (-1, -1)

# either player (user) or opponent
player_to_move = "p"
player_color = "w"
# initializing table matrix, dot represents non occupied square
TABLE_MATRIX = []
for i in range(8):
    TABLE_MATRIX.append(['.'] * 8)

# fen code, list of strings where every string describes one position
fen = []

# mapping position to how many times it occured, used for threefold repetition detection
fen_count = dict()

enpassant_square = "-"
halfmoves = 0
fullmoves = 0

game_end_reason = None

# availability of each of 4 types of castling, used in fen
K = k = Q = q = True

# dictionary that maps (row, column) to piece instance
matrix_to_piece = {}
for row in range(0, 8):
    for column in range(0, 8):
        matrix_to_piece[(row, column)] = None

# dot while displaying available squares for a chosen piece
image_dot = pygame.image.load("Assets/shared/dot.png")
image_dot = pygame.transform.scale(image_dot, (SQUARE_SIZE * 0.7, SQUARE_SIZE * 0.7))
rect_dot = image_dot.get_rect()

# FUNCTIONS

# renders string s with (default center) position at (x, y) and given font size
def render_text(s, x, y, font_size, top_left=False, color=WHITE):
    font = pygame.font.Font("Assets/shared/fonts\\jetBrainsMono/ttf/JetBrainsMono-Regular.ttf", font_size)
    text_surface = font.render(s, True, color)
    rect_text = text_surface.get_rect()
    if top_left:
        rect_text.topleft = (x, y)
    else:
        rect_text.center = (x, y)
    screen.blit(text_surface, rect_text)

def render_gameplay():
    screen.blit(image_settings, rect_settings)

    if rect_moving_square_prev.center != (-1 + SCREEN_OFFSET_X, -1 + SCREEN_OFFSET_Y):
        screen.blit(moving_square_prev, rect_moving_square_prev)
        screen.blit(moving_square_curr, rect_moving_square_curr)
    
    if rect_check_square.center != (-1 + SCREEN_OFFSET_X, -1 + SCREEN_OFFSET_Y):
        screen.blit(check_square, rect_check_square)

    pieces_player.draw(screen)
    pieces_opponent.draw(screen)

    # rendering off table stuff
    screen.blit(image_unknown_user, rect_image_player)
    screen.blit(image_unknown_user, rect_image_opponent)

    render_text("Username", rect_image_player.right + f(15), rect_image_player.top + f(1), int(f(14)), True)
    render_text("(3500)", SCREEN_OFFSET_X + f(138), rect_image_player.top + f(1), int(f(14)), True, GRAY)
    render_text("Computer", rect_image_opponent.right + f(15), rect_image_opponent.top + f(1), int(f(14)), True)
    render_text("(987)", SCREEN_OFFSET_X  + f(138), rect_image_opponent.top + f(1), int(f(14)), True, GRAY)

    screen.blit(image_flag_player, rect_flag_player)
    screen.blit(image_flag_opponent, rect_flag_opponent)

    clock_player.draw()
    clock_opponent.draw()

    if promoting:
        # darken the screen
        screen.blit(dark_overlay, (TABLE_X + SCREEN_OFFSET_X, TABLE_Y + SCREEN_OFFSET_Y))
        pieces_promotion.draw(screen)

def simulate_move(square1, square2):
    (prev_row, prev_column) = square1
    (curr_row, curr_column) = square2

    # Save the piece's name before marking the square as available
    piece_name = TABLE_MATRIX[prev_row][prev_column]

    # Mark the previous square as available
    TABLE_MATRIX[prev_row][prev_column] = '.'

    # Handle castling by checking if the king moved two squares
    if piece_name in ["K", "k"]:
        # Left castling
        if curr_column + 2 == prev_column:
            ((rook_prev_row, rook_prev_column), (rook_curr_row, rook_curr_column)) = ((curr_row, 0), (curr_row, curr_column + 1))

            rook = matrix_to_piece[(rook_prev_row, rook_prev_column)]
            TABLE_MATRIX[rook_curr_row][rook_curr_column] = rook.name
            # Updating rook's previous square
            TABLE_MATRIX[rook_prev_row][rook_prev_column] = '.'

        # Right castling
        if prev_column + 2 == curr_column:
            ((rook_prev_row, rook_prev_column), (rook_curr_row, rook_curr_column)) = ((curr_row, 7), (curr_row, curr_column - 1))

            rook = matrix_to_piece[(rook_prev_row, rook_prev_column)]
            TABLE_MATRIX[rook_curr_row][rook_curr_column] = rook.name
            # Updating rook's previous square
            TABLE_MATRIX[rook_prev_row][rook_prev_column] = '.'

    # Handle en passant capture by checking if a pawn moved diagonally to an empty square
    if piece_name in ["P", "p"] and prev_column != curr_column and TABLE_MATRIX[curr_row][curr_column] == '.':
        if TABLE_MATRIX[curr_row + 1][curr_column] in ["P", "p"]:
            TABLE_MATRIX[curr_row + 1][curr_column] = '.'
        if TABLE_MATRIX[curr_row - 1][curr_column] in ["P", "p"]:
            TABLE_MATRIX[curr_row - 1][curr_column] = '.'

    # Update the target square with the piece's name
    TABLE_MATRIX[curr_row][curr_column] = piece_name

# user for some testing, calculates number of possible positions at a certain depth
def num_of_possible_positions(depth):
    if depth == 0:
        return 0
    ans = 0
    global fen, player_to_move
    if player_to_move == "p":

        for piece in pieces_player:
            available_squares_orig = copy.deepcopy(piece.available_squares)
            for square in available_squares_orig:
                convert_fen(fen[-1])
                piece.make_move(square)
                post_move_processing()
                player_to_move = "o"
                ans += num_of_possible_positions(depth - 1) + 1
                player_to_move = "p"
                fen.pop()
                convert_fen(fen[-1])

    else:
        for piece in pieces_opponent:
            available_squares_orig = copy.deepcopy(piece.available_squares)
            for square in available_squares_orig:
                last_fen = fen[-1]
                piece.make_move(square)
                post_move_processing()
                player_to_move = "p"
                ans += num_of_possible_positions(depth - 1) + 1
                player_to_move = "o"
                fen.pop()
                convert_fen(last_fen)
    return ans


# updates available squares after every move for each piece
def update_available_squares():
    global TABLE_MATRIX
    if player_to_move == "p":
        for piece in pieces_opponent:
            piece.update_available_squares()
        for piece in pieces_player:
            piece.update_available_squares()
        
        TABLE_MATRIX_ORIGINAL = copy.deepcopy(TABLE_MATRIX)
        for piece in pieces_player:
            available_squares_new = set()
            for square in piece.available_squares:
                square_orig = (piece.row, piece.column)
                simulate_move(square_orig, square)
                #print_table_state()
                (piece.row, piece.column) = square
                for piece2 in pieces_opponent:
                    piece2.update_available_squares()
                if not in_check():
                    available_squares_new.add(square)
                TABLE_MATRIX = copy.deepcopy(TABLE_MATRIX_ORIGINAL)
                (piece.row, piece.column) = square_orig
            piece.available_squares = copy.deepcopy(available_squares_new)
            piece.attacking_squares = copy.deepcopy(piece.available_squares)
        
        for piece in pieces_opponent:
            piece.update_available_squares()
    else:
        for piece in pieces_player:
            piece.update_available_squares()
        for piece in pieces_opponent:
            piece.update_available_squares()
        
        TABLE_MATRIX_ORIGINAL = copy.deepcopy(TABLE_MATRIX)
        for piece in pieces_opponent:
            available_squares_new = set()
            for square in piece.available_squares:
                square_orig = (piece.row, piece.column)
                simulate_move(square_orig, square)
                (piece.row, piece.column) = square
                for piece2 in pieces_player:
                    piece2.update_available_squares()
                if not in_check():
                    available_squares_new.add(square)
                TABLE_MATRIX = copy.deepcopy(TABLE_MATRIX_ORIGINAL)
                (piece.row, piece.column) = square_orig
            piece.available_squares = copy.deepcopy(available_squares_new)
            piece.attacking_squares = copy.deepcopy(piece.available_squares)
        
        for piece in pieces_player:
            piece.update_available_squares()

def print_table_state():
    for row in TABLE_MATRIX:
        print(*row)
    print("\n")

def post_move_processing():
    if promoting:
        return
    # next player
    global player_to_move
    if player_to_move == "p":
        player_to_move = "o"
    else:
        player_to_move = "p"
    
    # update fen history
    if not promoting:
        scan_fen()
        global enpassant_square
        enpassant_square = "-"
    
    update_available_squares()
    if clocks_started:
        global clock_player, clock_opponent
        if player_to_move == "p":
            clock_opponent.seconds_left += increment
        else:
            clock_player.seconds_left += increment
        clock_player.locked = not clock_player.locked
        clock_opponent.locked = not clock_opponent.locked
    set_game_end_reason()
    mark_check()

def mark_check():
    global rect_check_square
    if player_to_move == "p":
        for piece in pieces_player:
            if piece.name in ["K", "k"]:
                king = piece
                break
        
        for piece in pieces_opponent:
            if (king.row, king.column) in piece.available_squares:
                rect_check_square.center = king.calc_position_screen(king.row, king.column)
                return
    else:
        for piece in pieces_opponent:
            if piece.name in ["K", "k"]:
                king = piece
                break
        
        for piece in pieces_player:
            if (king.row, king.column) in piece.available_squares:
                rect_check_square.center = king.calc_position_screen(king.row, king.column)
                return
    
    rect_check_square.center = (-1, -1)

def in_check():
    if player_to_move == "p":
        for piece in pieces_player:
            if piece.name in ["K", "k"]:
                king = piece
                break
        
        for piece in pieces_opponent:
            # while simulating, maybe piece giving a check is overwritten in a TABLE_MATRIX
            if TABLE_MATRIX[piece.row][piece.column] not in names_opponent:
                continue
            if (king.row, king.column) in piece.available_squares:
                return True
        return False
    
    else:
        for piece in pieces_opponent:
            if piece.name in ["K", "k"]:
                king = piece
                break
        
        for piece in pieces_player:
            if TABLE_MATRIX[piece.row][piece.column] not in names_player:
                continue
            if (king.row, king.column) in piece.available_squares:
                return True
        return False

def checkmate():
    if player_to_move == "p":
        for piece in pieces_player:
            if len(piece.available_squares) > 0:
                return False
        if in_check():
            return True
    else:
        for piece in pieces_opponent:
            if len(piece.available_squares) > 0:
                return False
        if in_check():
            return True

def stalemate():
    if player_to_move == "p":
        for piece in pieces_player:
            if len(piece.available_squares) > 0:
                return False
        if not in_check():
            return True
    else:
        for piece in pieces_opponent:
            if len(piece.available_squares) > 0:
                return False
        if not in_check():
            return True

def insufficient_material():
    pieces_player_left = len(pieces_player)
    pieces_opponent_left = len(pieces_opponent)

    # king vs king
    if pieces_player_left == pieces_opponent_left == 1:
        return True

    if pieces_player_left + pieces_opponent_left == 3:
        # king vs king and bishop or king vs king and knight
        for piece in pieces_player:
            if piece.name in ["B", "b", "N", "n"]:
                return True
        for piece in pieces_opponent:
            if piece.name in ["B", "b", "N", "n"]:
                return True
    if pieces_player_left == pieces_opponent_left == 2:
        # get the non king pieces
        for piece in pieces_player:
            if piece.name not in ["K", "k"]:
                piece_player = piece
                break
        for piece in pieces_opponent:
            if piece.name not in ["K", "k"]:
                piece_opponent = piece
                break

        # check for two bishops
        # white squares have sum of coordinates being even, blacks odd
        if piece_player.name in ["B", "b"] and piece_opponent.name in ["B", "b"] and (piece_player.row + piece_player.column) % 2 == (piece_opponent.row + piece_opponent.column) % 2:
            return True
        
    return False

def fifty_move_rule():
    return halfmoves == 100

def threefold_repetition():
    curr_fen = " ".join(fen[-1].split()[:4])
    return fen_count[curr_fen] == 3

def set_game_end_reason():
    global game_end_reason
    if checkmate(): game_end_reason = "checkmate"
    elif stalemate(): game_end_reason = "stalemate"
    elif insufficient_material(): game_end_reason = "insufficient material"
    elif fifty_move_rule(): game_end_reason = "50-move rule"
    elif threefold_repetition(): game_end_reason = "threefold repetition"

def scan_fen():
    # table is seen from whites perspective
    curr_fen = ""
    blank_squares_counter = 0
    (start, end, step) = (0, 8, 1)
    if player_color == "b":
        (start, end, step) = (7, -1, -1)
    
    for row in range(start, end, step):
            curr_fen += "/"
            blank_squares_counter = 0
            for column in range(start, end, step):
                if TABLE_MATRIX[row][column] != '.':
                    if blank_squares_counter > 0:
                        curr_fen += str(blank_squares_counter)
                    curr_fen += TABLE_MATRIX[row][column]
                    blank_squares_counter = 0
                else:
                    blank_squares_counter += 1
            if blank_squares_counter > 0:
                curr_fen += str(blank_squares_counter)

    # remove first slash
    curr_fen = curr_fen[1:]

    global fullmoves
    if player_to_move == "p":
        if player_color == "w":
            curr_fen += " w"
            fullmoves += 1
        else:
            curr_fen += " b"
    else:
        if player_color == "w":
            curr_fen += " b"
        else:
            curr_fen += " w"
            fullmoves += 1
    
    curr_fen += " "

    if not K and not k and not Q and not q:
        curr_fen += "-"
    else:
        if K: curr_fen += "K"
        if Q: curr_fen += "Q"
        if k: curr_fen += "k"
        if q: curr_fen += "q"
    
    curr_fen += " "
    curr_fen += enpassant_square

    global fen_count
    # store fen without halfomves and fullmoves
    if curr_fen not in fen_count:
        fen_count[curr_fen] = 0
    fen_count[curr_fen] += 1

    curr_fen += f" {halfmoves} {fullmoves}"

    fen.append(curr_fen)

def convert_fen(fen_string):
    promoting = False
    # first destroy everything
    global TABLE_MATRIX, matrix_to_piece, pieces_player, pieces_opponent, halfmoves, fullmoves, player_to_move, player_color, K, Q, k, q
    TABLE_MATRIX = []
    for i in range(8):
        TABLE_MATRIX.append(['.'] * 8)
    for row in range(0, 8):
        for column in range(0, 8):
            if matrix_to_piece[(row, column)] is not None:
                matrix_to_piece[(row, column)].kill()
            matrix_to_piece[(row, column)] = None
    pieces_player = pygame.sprite.Group()
    pieces_opponent = pygame.sprite.Group()

    data = fen_string.split("/")

    if player_color == "w":
        for row in range(7):
            column = 0
            for c in data[row]:
                if c.isnumeric():
                    column += int(c)
                    continue
                elif c.isupper():
                    # white piece
                    piece = Piece(c, pygame.image.load(route_player + f"{c}.png"), row, column, names_player)
                    pieces_player.add(piece)
                    TABLE_MATRIX[row][column] = c
                    matrix_to_piece[(row, column)] = piece
                    column += 1
                elif c.islower():
                    # black piece
                    piece = Piece(c, pygame.image.load(route_opponent + f"{c}.png"), row, column, names_opponent)
                    pieces_opponent.add(piece)
                    TABLE_MATRIX[row][column] = c
                    matrix_to_piece[(row, column)] = piece
                    column += 1

        last_row_and_rest = data[-1].split(" ", 1) # split only once
        (last_row, rest) = (last_row_and_rest[0], last_row_and_rest[1])
        row = 7
        column = 0
        for c in last_row:
            if c.isnumeric():
                column += int(c)
                continue
            elif c.isupper():
                # white piece
                piece = Piece(c, pygame.image.load(route_player + f"{c}.png"), row, column, names_player)
                pieces_player.add(piece)
                TABLE_MATRIX[row][column] = c
                matrix_to_piece[(row, column)] = piece
                column += 1
            elif c.islower():
                # black piece
                piece = Piece(c, pygame.image.load(route_opponent + f"{c}.png"), row, column, names_opponent)
                pieces_opponent.add(piece)
                TABLE_MATRIX[row][column] = c
                matrix_to_piece[(row, column)] = piece
                column += 1
    else:
        for row in range(7):
            column = 7
            for c in data[row]:
                if c.isnumeric():
                    column -= int(c)
                    continue
                elif c.isupper():
                    # white piece
                    piece = Piece(c, pygame.image.load(route_opponent + f"{c}.png"), 7 - row, column, names_opponent)
                    pieces_opponent.add(piece)
                    TABLE_MATRIX[7 - row][column] = c
                    matrix_to_piece[(7 - row, column)] = piece
                    column -= 1
                elif c.islower():
                    # black piece
                    piece = Piece(c, pygame.image.load(route_player + f"{c}.png"), 7 - row, column, names_player)
                    pieces_player.add(piece)
                    TABLE_MATRIX[7 - row][column] = c
                    matrix_to_piece[(7 - row, column)] = piece
                    column -= 1

        last_row_and_rest = data[-1].split(" ", 1) # split only once
        (last_row, rest) = (last_row_and_rest[0], last_row_and_rest[1])
        row = 7
        column = 7
        for c in last_row:
            if c.isnumeric():
                column -= int(c)
                continue
            elif c.isupper():
                # white piece
                piece = Piece(c, pygame.image.load(route_opponent + f"{c}.png"), 7 - row, column, names_opponent)
                pieces_opponent.add(piece)
                TABLE_MATRIX[7 - row][column] = c
                matrix_to_piece[(7 - row, column)] = piece
                column -= 1
            elif c.islower():
                # black piece
                piece = Piece(c, pygame.image.load(route_player + f"{c}.png"), 7 - row, column, names_player)
                pieces_player.add(piece)
                TABLE_MATRIX[7 - row][column] = c
                matrix_to_piece[(7 - row, column)] = piece
                column -= 1
    
    data = rest.split(" ")
    (mover, castling_rights, ep_square, halfmoves, fullmoves) = (data[0], data[1], data[2], int(data[3]), int(data[4]))

    if player_color == "w":
        if mover == "w":
            player_to_move = "p"
        else:
            player_to_move = "o"
    else:
        if mover == "w":
            player_to_move = "o"
        else:
            player_to_move = "p"
    
    if castling_rights == "-":
        K = Q = k = q = False
    else:
        for right in castling_rights:
            if right == "K": K = True
            if right == "k": k = True
            if right == "Q": Q = True
            if right == "q": q = True

    update_available_squares()


# calculates new dimensions based on initial ones which are 450*975
# enables rescalling while keeping aspect ratio
def f(x):
    return x * WIDTH / 450

# SETUP
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Offline Chess")

clock = pygame.time.Clock()

# CLASSES
class Slider(pygame.sprite.Sprite):

    def __init__(self, y):
        super().__init__()
        self.y = y
        self.image_panel = pygame.image.load("Assets/shared/home/Rectangle 28.png").convert_alpha()
        self.width_panel = WIDTH*3 / 4
        self.height = f(15)
        self.image_panel = pygame.transform.scale(self.image_panel, (self.width_panel, self.height))
        self.rect_panel = self.image_panel.get_rect()
        self.rect_panel.center = (int(WIDTH / 2), y)

        self.image_cursor = pygame.image.load("Assets/shared/home/Rectangle 32.png").convert_alpha()
        self.width_cursor = f(30)
        self.image_cursor = pygame.transform.scale(self.image_cursor, (self.width_cursor, self.height))
        self.rect_cursor = self.image_cursor.get_rect()
        self.rect_cursor.x = self.rect_panel.x
        self.rect_cursor.y = self.rect_panel.y

        self.dragging_cursor = False
        self.left_bound = self.rect_panel.x
        self.right_bound = self.rect_panel.topright[0] - self.rect_cursor.size[0]
    
    def draw(self):
        screen.blit(self.image_panel, self.rect_panel)
        screen.blit(self.image_cursor, self.rect_cursor)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect_cursor.collidepoint(event.pos):
                self.dragging_cursor = True
                self.mouse_offset_x = self.rect_cursor.x - event.pos[0]
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.dragging_cursor:
                self.dragging_cursor = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_cursor:
                # Update only the x-coordinate
                self.rect_cursor.x = event.pos[0] + self.mouse_offset_x

                # handle left bound
                self.rect_cursor.x = min(self.rect_cursor.x, self.right_bound)
                
                # handle right bound
                self.rect_cursor.x = max(self.rect_cursor.x, self.left_bound)
    
    def calc_based_on_cursor(self, num):
        # if num is 1, calculate minutes, else increment
        global minutes
        global increment
        total = len(availableMinutes) - 1 if num == 1 else len(availableIncrements) - 1
        unitLength = (self.right_bound - self.left_bound) // total
        i = (self.rect_cursor.x - self.left_bound) // unitLength
        if num == 1:
            minutes = availableMinutes[i]
        else:
            increment = availableIncrements[i]

class Piece(pygame.sprite.Sprite):
    def __init__(self, name, image, row, column, names):
        super().__init__()
        self.name = name

        self.image = pygame.transform.scale(image, (int(SQUARE_SIZE * 0.7), int(SQUARE_SIZE * 0.7)))  # Scale image
        self.row = row
        self.column = column

        # Rect for the image (used for rendering)
        self.rect = self.image.get_rect()
        self.rect.center = self.calc_position_screen(self.row, self.column)

        # Separated larger rect for the square
        self.rect_square = pygame.Rect(0, 0, SQUARE_SIZE, SQUARE_SIZE)
        self.rect_square.center = self.rect.center  # Align centers

        self.dragging = False
        self.holding = False
        self.selected = False
        self.unselecting_downclick = False

        self.names = names.copy()

        # needed for castling
        self.moved = False

        self.available_squares = set()
        self.attacking_squares = set()
    
    def update_rect_position(self):
        self.rect.x += SETTINGS_ANIMATION_SPEED
        #self.rect.y += SETTINGS_ANIMATION_SPEED / 2
        self.rect_square.x += SETTINGS_ANIMATION_SPEED
        #self.rect_square.y += SETTINGS_ANIMATION_SPEED / 2

    # caluclates screen position of a piece based on matrix position
    def calc_position_screen(self, row, column):
        x = TABLE_X + column * SQUARE_SIZE + SQUARE_SIZE / 2 + SCREEN_OFFSET_X
        y = TABLE_Y + row * SQUARE_SIZE + SQUARE_SIZE / 2 + SCREEN_OFFSET_Y
        return (int(x), int(y))
    
    # calculates row and column for a given screen position
    # inverse function of the calc_position_screen()
    def calc_position_matrix(self, center):
        (x, y) = center
        row = (y + SCREEN_OFFSET_Y - TABLE_Y) / SQUARE_SIZE
        column = (x + SCREEN_OFFSET_X -TABLE_X) / SQUARE_SIZE
        return (int(row), int(column))
    
    # initializes pairs of (row, column) coordinates of available squares after every move for a current piece
    def update_available_squares(self):
        self.available_squares = set() 
        self.attacking_squares = set() # only difference is when piece is pawn, since pawn attacks diagonally but can move forward

        if self.name == 'P' or self.name == 'p':
            # pawns only go forward
            if self.names == names_player:
                next_row = self.row - 1
                if next_row >= 0:
                    # square in front of the pawn
                    if TABLE_MATRIX[self.row - 1][self.column] == '.':
                        self.available_squares.add((self.row - 1, self.column))

                    # two squares from starting position
                    if self.row == 6 and TABLE_MATRIX[self.row - 2][self.column] == '.':
                        self.available_squares.add((self.row - 2, self.column))

                    # capturing opponents piece, one square diagonally, with bound check

                    # enpassant square
                    if len(fen) > 0:
                        ep_square = fen[-1].split(" ")[-3]
                        if ep_square != "-":
                            if player_color == "w" :
                                row = 7 - (int(ep_square[1]) - 1)
                                column = ord(ep_square[0]) - ord("a")
                            else:
                                row = (int(ep_square[1]) - 1)
                                column = 7 - (ord(ep_square[0]) - ord("a"))
                            if self.row == row + 1 and (self.column == column - 1 or self.column == column + 1):
                                self.available_squares.add((row, column))
                                self.attacking_squares.add((row, column))


                    if self.column - 1 >= 0:
                        capture_left = TABLE_MATRIX[self.row - 1][self.column - 1]
                        if capture_left not in self.names:
                            self.attacking_squares.add((self.row - 1, self.column - 1))
                            if capture_left != '.':
                                self.available_squares.add((self.row - 1, self.column - 1))
                    if self.column + 1 <= 7:
                        capture_right = TABLE_MATRIX[self.row - 1][self.column + 1]
                        if capture_right not in self.names:
                            self.attacking_squares.add((self.row - 1, self.column + 1))
                            if capture_right != '.':
                                self.available_squares.add((self.row - 1, self.column + 1))
            else:
                next_row = self.row + 1
                if next_row <= 7:
                    # square in front of the pawn
                    if TABLE_MATRIX[self.row + 1][self.column] == '.':
                        self.available_squares.add((self.row + 1, self.column))

                    # two squares from starting position
                    if self.row == 1 and TABLE_MATRIX[self.row + 2][self.column] == '.':
                        self.available_squares.add((self.row + 2, self.column))
                    
                    # capturing opponents piece, one square diagonally, with bound check

                    # enpassant square
                    if len(fen) > 0:
                        ep_square = fen[-1].split(" ")[-3]
                        if ep_square != "-":
                            if player_color == "w":
                                row = 7 - (int(ep_square[1]) - 1)
                                column = ord(ep_square[0]) - ord("a")
                            else:
                                row = (int(ep_square[1]) - 1)
                                column = 7 - (ord(ep_square[0]) - ord("a"))
                            if self.row == row - 1 and (self.column == column - 1 or self.column == column + 1):
                                self.available_squares.add((row, column))
                                self.attacking_squares.add((row, column))
                            
                    if self.column - 1 >= 0:
                        capture_left = TABLE_MATRIX[self.row + 1][self.column - 1]
                        if capture_left not in self.names:
                            self.attacking_squares.add((self.row + 1, self.column - 1))
                            if capture_left != '.':
                                self.available_squares.add((self.row + 1, self.column - 1))
                    if self.column + 1 <= 7:
                        capture_right = TABLE_MATRIX[self.row + 1][self.column + 1]
                        if capture_right not in self.names:
                            self.attacking_squares.add((self.row + 1, self.column + 1))
                            if capture_right != '.':
                                self.available_squares.add((self.row + 1, self.column + 1))

        if self.name == 'N' or self.name == 'n':
            # x, y offsets where knight can possibly jump to
            jumping_offsets = [(1, -2), (2, -1), (2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1), (-1, -2)]

            for (offset_x, offset_y) in jumping_offsets:
                try_row = self.row + offset_y
                try_column = self.column + offset_x
                # checking bounds and availability for every jumping square
                if 0 <= try_row <= 7 and 0 <= try_column <= 7 and TABLE_MATRIX[try_row][try_column] not in self.names:
                    self.available_squares.add((try_row, try_column))
        
        if self.name == "B" or self.name == 'b':
            # up left
            curr_row = self.row - 1
            curr_column = self.column - 1

            # loop stops when bishop encounters a piece, unlike knight which jumps above pieces
            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                # if current square is not player's and its not a dot -> its capturing square, break after
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row -= 1
                curr_column -= 1
            
            # up right
            curr_row = self.row - 1
            curr_column = self.column + 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row -= 1
                curr_column += 1
            
            # down left
            curr_row = self.row + 1
            curr_column = self.column - 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row += 1
                curr_column -= 1
            
            # down right
            curr_row = self.row + 1
            curr_column = self.column + 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row += 1
                curr_column += 1

        if self.name == "R" or self.name == 'r':
            # up
            curr_row = self.row - 1
            curr_column = self.column

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row -= 1
            
            # down
            curr_row = self.row + 1
            curr_column = self.column

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row += 1
            
            # left
            curr_row = self.row
            curr_column = self.column - 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_column -= 1
            
            # right
            curr_row = self.row
            curr_column = self.column + 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_column += 1
        
        if self.name == "Q" or self.name == 'q':
            # bishop movement + rook movement
            # up left
            curr_row = self.row - 1
            curr_column = self.column - 1

            # loop stops when queen encounters a piece, unlike knight which jumps above pieces
            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                # if current square is not player's and its not a dot -> its capturing square, break after
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row -= 1
                curr_column -= 1
            
            # up right
            curr_row = self.row - 1
            curr_column = self.column + 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row -= 1
                curr_column += 1
            
            # down left
            curr_row = self.row + 1
            curr_column = self.column - 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row += 1
                curr_column -= 1
            
            # down right
            curr_row = self.row + 1
            curr_column = self.column + 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row += 1
                curr_column += 1
            
            # up
            curr_row = self.row - 1
            curr_column = self.column

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row -= 1
            
            # down
            curr_row = self.row + 1
            curr_column = self.column

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row += 1
            
            # left
            curr_row = self.row
            curr_column = self.column - 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_column -= 1
            
            # right
            curr_row = self.row
            curr_column = self.column + 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_column += 1
        
        if self.name == "K" or self.name == "k":
            # get all the attacking squares from other player
            attacked_squares = set()
            if self.names == names_player:
                for piece in pieces_opponent:
                    for square in piece.attacking_squares:
                        attacked_squares.add(square)
            else:
                for piece in pieces_player:
                    for square in piece.attacking_squares:
                        attacked_squares.add(square)

            # handle castling
            if not self.moved and not in_check():
                # king is on the starting position

                # left castling

                # check if leftmost piece in the row is rook with the same color, and hasnt moved
                if TABLE_MATRIX[self.row][0] in ["R", "r"] and TABLE_MATRIX[self.row][0] in self.names and not matrix_to_piece[(self.row, 0)].moved:
                    # check if all squares between are free and not attacked by pieces
                    free = True
                    curr_column = 1
                    while curr_column < self.column:
                        if TABLE_MATRIX[self.row][curr_column] != '.' or (self.row, curr_column) in attacked_squares:
                            free = False
                            break
                        curr_column += 1
                    if free:
                        self.available_squares.add((self.row, self.column - 2))
                
                # right castling

                # check if rightmost piece in the row is rook with the same color, and hasnt moved
                if TABLE_MATRIX[self.row][7] in ["R", "r"] and TABLE_MATRIX[self.row][7] in self.names and not matrix_to_piece[(self.row, 7)].moved:
                    # check if all squares between are free and not attacked by pieces
                    free = True
                    curr_column = self.column + 1
                    while curr_column <= 6:
                        if TABLE_MATRIX[self.row][curr_column] != '.' or (self.row, curr_column) in attacked_squares:
                            free = False
                            break
                        curr_column += 1
                    if free:
                        self.available_squares.add((self.row, self.column + 2))

            # same as queen, but range is only 1 square

            # up left
            curr_row = self.row - 1
            curr_column = self.column - 1

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.add((curr_row, curr_column))
            
            # up right
            curr_row = self.row - 1
            curr_column = self.column + 1

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.add((curr_row, curr_column))
            
            # down left
            curr_row = self.row + 1
            curr_column = self.column - 1

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.add((curr_row, curr_column))
            
            # down right
            curr_row = self.row + 1
            curr_column = self.column + 1

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.add((curr_row, curr_column))
            
            # up
            curr_row = self.row - 1
            curr_column = self.column

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.add((curr_row, curr_column))
            
            # down
            curr_row = self.row + 1
            curr_column = self.column

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.add((curr_row, curr_column))
            
            # left
            curr_row = self.row
            curr_column = self.column - 1

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.add((curr_row, curr_column))
            
            # right
            curr_row = self.row
            curr_column = self.column + 1

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.add((curr_row, curr_column))

        if self.name not in ["P", "p"]:
            self.attacking_squares = copy.deepcopy(self.available_squares)

    def display_available_squares(self):
        # and also mark selected square
        marked_square = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        marked_square.fill(DARK_GREEN_TRANSPARENT)

        rect_marked_square = marked_square.get_rect()
        (x, y) = self.calc_position_screen(self.row, self.column)
        rect_marked_square.center = (x, y)

        screen.blit(marked_square, rect_marked_square)

        for (row, column) in self.available_squares:
            (x, y) = self.calc_position_screen(row, column)
            rect_dot.center = (x, y)
            # if its not empty square, then player is capturing
            # marking it green
            if TABLE_MATRIX[row][column] != '.':
                marked_square.fill(DARK_GREEN_TRANSPARENT1)
                (x, y) = self.calc_position_screen(row, column)
                rect_marked_square.center = (x, y)
                screen.blit(marked_square, rect_marked_square)
            # else display a dot
            else:
                screen.blit(image_dot, rect_dot)
    
    def available_move(self):
        # catches the current (x, y) coordinates of a piece while being dragged accross the board and checks if the chosen square is available
        (row_try, column_try) = self.calc_position_matrix(self.rect_square.center)
        return (row_try, column_try) in self.available_squares
    
    def make_move(self, square=None):

        global TABLE_MATRIX, matrix_to_piece, rect_moving_square_prev, rect_moving_square_curr
        # mark previous square as available
        TABLE_MATRIX[self.row][self.column] = '.'
        matrix_to_piece[(self.row, self.column)] = None

        (x, y) = self.calc_position_screen(self.row, self.column)
        rect_moving_square_prev.center = (x, y)

        # if it was king or a rook, disable castling rights by alerting that either moved
        if self.name in ["K", "k", "R", "r"]:

            if not self.moved:
                global K, Q, k, q
                if self.name == "K":
                    # disable both sides white
                    K = Q = False
                elif self.name == "k":
                    # disable both sides black
                    k = q = False
            
                elif self.name == "R":
                    # check king side by comparing distance to the king
                    if (0 <= self.column + 3 <= 7 and TABLE_MATRIX[self.row][self.column + 3] == "K") or (0 <= self.column - 3 <= 7 and TABLE_MATRIX[self.row][self.column - 3] == "K"):
                        K = False
                    else:
                        Q = False

                elif self.name == "r":
                    # check king side by comparing distance to the king
                    if (0 <= self.column + 3 <= 7 and TABLE_MATRIX[self.row][self.column + 3] == "k") or (0 <= self.column - 3 <= 7 and TABLE_MATRIX[self.row][self.column - 3] == "k"):
                        k = False
                    else:
                        q = False
            self.moved = True

        # save previous position to handle castling and en passant
        prev_row = self.row
        prev_column = self.column

        # if the moving square is not explicitely passed as an argument, catch the mouse position
        (self.row, self.column) = self.calc_position_matrix(self.rect_square.center) if square is None else square
        (x, y) = self.calc_position_screen(self.row, self.column)
        rect_moving_square_curr.center = (x, y)

        # handle castling by checking if king somehow "moved" two squares
        if self.name in ["K", "k"]:
            # left castling
            if self.column + 2 == prev_column:
                ((rook_prev_row, rook_prev_column), (rook_curr_row, rook_curr_column)) = ((self.row, 0), (self.row, self.column + 1))

                rook = matrix_to_piece[(rook_prev_row, rook_prev_column)]
                # updating rooks current square
                rook.rect.center = rook.calc_position_screen(rook_curr_row, rook_curr_column)
                rook.rect_square.center = rook.rect.center
                (rook.row, rook.column) = rook.calc_position_matrix(rook.rect_square.center)
                TABLE_MATRIX[rook_curr_row][rook_curr_column] = rook.name
                matrix_to_piece[(rook_curr_row, rook_curr_column)] = rook
                # updating rooks previous square
                TABLE_MATRIX[rook_prev_row][rook_prev_column] = '.'
                matrix_to_piece[(rook_prev_row, rook_curr_column)] = None
                rook.update_available_squares()

            # right castling
            if prev_column + 2 == self.column:
                ((rook_prev_row, rook_prev_column), (rook_curr_row, rook_curr_column)) = ((self.row, 7), (self.row, self.column - 1))

                rook = matrix_to_piece[(rook_prev_row, rook_prev_column)]
                # updating rooks current square
                rook.rect.center = rook.calc_position_screen(rook_curr_row, rook_curr_column)
                rook.rect_square.center = rook.rect.center
                (rook.row, rook.column) = rook.calc_position_matrix(rook.rect_square.center)
                TABLE_MATRIX[rook_curr_row][rook_curr_column] = rook.name
                matrix_to_piece[(rook_curr_row, rook_curr_column)] = rook
                # updating rooks previous square
                TABLE_MATRIX[rook_prev_row][rook_prev_column] = '.'
                matrix_to_piece[(rook_prev_row, rook_curr_column)] = None
                rook.update_available_squares()

        # mark en passant square
        global enpassant_square, halfmoves
        if self.name in ["P", "p"]:
            halfmoves = 0
            if abs(prev_row - self.row) == 2:
                if player_color == "w":
                    # enpassant square (for example e3) is constructed by converting a row to a file and getting the average of the two movement squares
                    # adding 7 to rows cause table begin is up not down
                    enpassant_square = chr(ord('a') + self.column) + str((7 - prev_row + 7 - self.row) // 2 + 1)
                else:
                    enpassant_square = chr(ord('a') + 7 - self.column) + str((prev_row + self.row) // 2 + 1)
        
        # capturing enpassant by checking if pawn moved diagonally to an empty square
        if self.name in ["P", "p"] and prev_column != self.column and TABLE_MATRIX[self.row][self.column] == '.':
            if TABLE_MATRIX[self.row + 1][self.column] in ["P", "p"]:
                halfmoves = 0
                captured_piece = matrix_to_piece[((self.row + 1, self.column))]
                captured_piece.kill()
                TABLE_MATRIX[self.row + 1][self.column] = '.'
                matrix_to_piece[(self.row, self.column)] = None
            if TABLE_MATRIX[self.row - 1][self.column] in ["P", "p"]:
                halfmoves = 0
                captured_piece = matrix_to_piece[((self.row - 1, self.column))]
                captured_piece.kill()
                TABLE_MATRIX[self.row - 1][self.column] = '.'
                matrix_to_piece[(self.row, self.column)] = None

        self.rect.center = self.calc_position_screen(self.row, self.column)
        self.rect_square.center = self.rect.center

        # check if it was capture
        if TABLE_MATRIX[self.row][self.column] != '.': # if its available move and not empty square -> its capture
            halfmoves = 0
            captured_piece = matrix_to_piece[((self.row, self.column))]
            # disable capturing when rook gets taken
            if TABLE_MATRIX[self.row][self.column] in ["R", "r"] and not captured_piece.moved:
                if captured_piece.name == "R":
                    # check king side by comparing distance to the king
                    if (0 <= captured_piece.column + 3 <= 7 and TABLE_MATRIX[captured_piece.row][captured_piece.column + 3] == "K") or (0 <= captured_piece.column - 3 <= 7 and TABLE_MATRIX[captured_piece.row][captured_piece.column - 3] == "K"):
                        K = False
                    else:
                        Q = False

                elif captured_piece.name == "r":
                    # check king side by comparing distance to the king
                    if (0 <= captured_piece.column + 3 <= 7 and TABLE_MATRIX[captured_piece.row][captured_piece.column + 3] == "k") or (0 <= captured_piece.column - 3 <= 7 and TABLE_MATRIX[captured_piece.row][captured_piece.column - 3] == "k"):
                        k = False
                    else:
                        q = False
            captured_piece.kill()
            matrix_to_piece[(self.row, self.column)] = None
        
        # if its not a pawn move nor a capture, increment halfmoves
        if not self.name in ["P", "p"] and not TABLE_MATRIX[self.row][self.column] != '.':
            halfmoves += 1

        # updating the position matrix
        TABLE_MATRIX[self.row][self.column] = self.name

        # updating position dictionary
        matrix_to_piece[(self.row, self.column)] = self

        # handling promotion
        if self.name in ["P", "p"]:
            global promoting, promotion_square
            row = self.row
            if self.row == 0:
                promotion_square = (self.row, self.column)
                promoting = True
                names_list = ["Q", "R", "N", "B"]
                if player_color == "b":
                    names_list = [name.lower() for name in names_list]
                for name in names_list:
                    pieces_promotion.add(Piece(name, pygame.image.load(route_player + f"{name}.png"), row, self.column, self.names))
                    row += 1
            if self.row == 7:
                promotion_square = (self.row, self.column)
                promoting = True
                names_list = ["Q", "R", "N", "B"]
                if player_color == "w":
                    names_list = [name.lower() for name in names_list]
                for name in names_list:
                    pieces_promotion.add(Piece(name, pygame.image.load(route_opponent + f"{name}.png"), row, self.column, self.names))
                    row -= 1

    def handle_event(self, event):
        if IN_SETTINGS:
            return
        (mouse_x, mouse_y) = pygame.mouse.get_pos()
        mouse_on_piece = self.rect_square.collidepoint((mouse_x, mouse_y))
        left_click = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
        right_click = event.type == pygame.MOUSEBUTTONDOWN and event.button == 3

        if right_click:
            # reset piece position
            self.rect.center = self.calc_position_screen(self.row, self.column)
            self.rect_square.center = self.rect.center
            self.selected = False
            self.dragging = False
            self.holding = False
            return

        if left_click:
            # if out of screen bounds
            if not (TABLE_X  <= mouse_x <= TABLE_X + 8 * SQUARE_SIZE and TABLE_Y <= mouse_y <= TABLE_Y + 8 * SQUARE_SIZE):
                # reset piece position
                self.rect.center = self.calc_position_screen(self.row, self.column)
                self.rect_square.center = self.rect.center
                self.selected = False
                self.dragging = False
                self.holding = False
                return

            if mouse_on_piece:
                if self.selected:
                    self.unselecting_downclick = True
                else:
                    self.selected = True
                self.holding = True
            # handle making a move by clicking at available square
            elif self.selected:
                curr_x = max(mouse_x, self.rect.size[0] / 2)
                curr_x = min(curr_x, WIDTH - self.rect.size[0] / 2)
                curr_y = max(mouse_y, TABLE_Y + self.rect.size[1] / 2)
                curr_y = min(curr_y, TABLE_Y + 8 * SQUARE_SIZE - self.rect.size[1] / 2)

                self.rect.center = (curr_x, curr_y)
                self.rect_square.center = self.rect.center

                if self.available_move():
                    self.selected = False
                    self.dragging = False
                    self.holding = False
                    self.unselecting_downclick = False
                    self.make_move()                        
                    post_move_processing()
                    return
                else:
                    self.rect.center = self.calc_position_screen(self.row, self.column)
                    self.rect_square.center = self.rect.center
                    self.selected = False
                    self.dragging = False
                    self.holding = False
        
        if event.type == pygame.MOUSEBUTTONUP and mouse_on_piece:
            if self.dragging:
                self.dragging = False
                self.selected = False
                # Align the piece to the closest square if move is legal
                if self.available_move():
                    self.make_move()
                    post_move_processing()
                else: # else reset the piece to the current position
                    self.rect.center = self.calc_position_screen(self.row, self.column)
                    self.rect_square.center = self.rect.center

            if self.unselecting_downclick and not self.dragging:
                self.selected = False
                self.unselecting_downclick = False
            self.holding = False

        if event.type == pygame.MOUSEMOTION and mouse_on_piece and self.holding:
            self.dragging = True

        if self.dragging and self.selected:
            # Update the position of the piece while dragging
            curr_x = max(mouse_x, SCREEN_OFFSET_X + self.rect.size[0] / 2)
            curr_x = min(curr_x, WIDTH - self.rect.size[0] / 2)
            curr_y = max(mouse_y, TABLE_Y + self.rect.size[1] / 2)
            curr_y = min(curr_y, TABLE_Y + 8 * SQUARE_SIZE - self.rect.size[1] / 2)

            self.rect.center = (curr_x, curr_y)
            self.rect_square.center = self.rect.center

    def handle_event_promotion(self, event):
        if IN_SETTINGS:
            return
        (mouse_x, mouse_y) = pygame.mouse.get_pos()
        mouse_on_piece = self.rect_square.collidepoint((mouse_x, mouse_y))
        left_click = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1

        if left_click and mouse_on_piece:
            global promoting, promotion_square, pieces_promotion

            (row, column) = promotion_square
            self.row = row
            self.column = column
            TABLE_MATRIX[row][column] = self.name

            pawn = matrix_to_piece[((row, column))]
            pawn.kill()

            new_piece = Piece(self.name, self.image, self.row, self.column, self.names)
            matrix_to_piece[((row, column))] = new_piece
            if self.row == 0:
                pieces_player.add(new_piece)
            elif self.row == 7:
                pieces_opponent.add(new_piece)

            for piece in pieces_promotion:
                piece.kill()
            
            pieces_promotion = pygame.sprite.Group()
            promoting = False
            scan_fen()
            
            post_move_processing()

class Clock(pygame.sprite.Sprite):
    def __init__(self, x, y, player):
        super().__init__()
        self.start_seconds = minutes * 60
        self.seconds_left = self.start_seconds
        self.rect = pygame.Rect(x, y, WIDTH - x - f(10), SQUARE_SIZE * 0.7)
        self.low_time_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        self.low_time_surface.fill(RED_TRANSPARENT)
        self.locked = True
        self.player = player
    def draw(self):
        render_color = WHITE
        if self.locked:
            render_color = GRAY
        minutes = int(self.seconds_left // 60)
        seconds = self.seconds_left % 60
        if self.seconds_left > 10:
            pygame.draw.rect(screen, render_color, self.rect, width=max(1, f(1)))
            seconds = int(seconds)
            render_text(f"{minutes:02}:{seconds:02}", self.rect.center[0], self.rect.center[1], int(f(25)), color=render_color)
        else:
            screen.blit(self.low_time_surface, self.rect.topleft)
            render_text(f"{minutes:02}:{seconds:04.1f}", self.rect.center[0], self.rect.center[1], int(f(25)), color=render_color)

    def update(self, dt):
        if not self.locked:
            self.seconds_left -= dt
    
    def update_rect_position(self):
        if self.player:
            self.rect.y += SETTINGS_ANIMATION_SPEED / 4
        else:
            self.rect.y -= SETTINGS_ANIMATION_SPEED / 4

SETTINGS_ANIMATION_SPEED = -f(20) # pixels per frame
SETTINGS_ANIMATION_RUNNING = False
IN_SETTINGS = False

# background image
image_bg = pygame.image.load("Assets/dark/backgrounds/boje1.png")
image_bg = pygame.transform.scale(image_bg, (WIDTH, HEIGHT))

# table
image_table = pygame.image.load("Assets/dark/boards/tiles.png")
image_table = pygame.transform.scale(image_table, (WIDTH, WIDTH))
rect_table = image_table.get_rect()
rect_table.topleft = (TABLE_X, TABLE_Y)

# home screen
slider1 = Slider(f(200))
# set 3+2 mode manually
slider1.rect_cursor.x += f(120)
slider2 = Slider(f(400))
slider2.rect_cursor.x += f(60)

# assuming player is white
route_player = "Assets/dark/pieces white/"
route_opponent = "Assets/dark/pieces black/"

# kings images home screen
image_K = pygame.image.load(route_player + "K.png")
image_K = pygame.transform.scale(image_K, (f(100), f(100)))
rect_K = image_K.get_rect()
rect_K.center = (WIDTH / 2 - f(100), HEIGHT - f(100))

image_k = pygame.image.load(route_opponent + "k.png")
image_k = pygame.transform.scale(image_k, (f(100), f(100)))
rect_k = image_k.get_rect()
rect_k.center = (WIDTH / 2 + f(100), HEIGHT - f(100))

# home screen loop
while 1:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        slider1.handle_event(event)
        slider2.handle_event(event)
        
        # handle clicking on kings
        if event.type == pygame.MOUSEBUTTONDOWN:
            if rect_K.collidepoint(event.pos):
                game_started = True
                player_color = "w"
            if rect_k.collidepoint(event.pos):
                game_started = True
                player_color = "b"
    
    if game_started:
        break
    
    screen.fill(BLACKY)
    screen.blit(image_bg, (0-f(0), 0-f(0)))

    screen.blit(image_K, rect_K)
    screen.blit(image_k, rect_k)

    slider1.draw()
    slider1.calc_based_on_cursor(1)
    render_text(f"Minutes per player: {minutes}", WIDTH / 2, slider1.y - f(40), int(f(20)))

    slider2.draw()
    slider2.calc_based_on_cursor(2)
    render_text(f"Increment in seconds: {increment}", WIDTH / 2, slider2.y - f(40), int(f(20)))

    render_text("Choose side", WIDTH / 2, rect_k.center[1] - f(150), int(f(25)))

    pygame.display.flip()
    clock.tick(60)

# SETTING PIECES UP
pieces_player = pygame.sprite.Group()
pieces_opponent = pygame.sprite.Group()

captured_pieces_player = pygame.sprite.Group()
captured_pieces_opponent = pygame.sprite.Group()

image_unknown_user = pygame.image.load("Assets/dark/users/unknown user.png")
image_unknown_user = pygame.transform.smoothscale(image_unknown_user, (SQUARE_SIZE * 0.7, SQUARE_SIZE * 0.7 * 93 / 97))
rect_image_player = image_unknown_user.get_rect()
rect_image_player.topleft = (SCREEN_OFFSET_X + f(10), TABLE_Y + 8 * SQUARE_SIZE + f(15))
rect_image_opponent = image_unknown_user.get_rect()
rect_image_opponent.bottomleft = (SCREEN_OFFSET_X  + f(10), TABLE_Y - f(15))

image_flag_player = pygame.image.load("Assets/shared/flags/64/unknown.png")
image_flag_player = pygame.transform.scale(image_flag_player, (f(20), f(20)))
rect_flag_player = image_flag_player.get_rect()
rect_flag_player.topleft = (SCREEN_OFFSET_X + f(200), rect_image_player.top)

image_flag_opponent = pygame.image.load("Assets/shared/flags/64/unknown.png")
image_flag_opponent = pygame.transform.scale(image_flag_opponent, (f(20), f(20)))
rect_flag_opponent = image_flag_opponent.get_rect()
rect_flag_opponent.topleft = (SCREEN_OFFSET_X + f(192), rect_image_opponent.top)

image_settings = pygame.image.load("Assets/dark/options.png")
image_settings = pygame.transform.scale(image_settings, (SQUARE_SIZE * 0.6, SQUARE_SIZE * 0.6 * 55 / 75))
rect_settings = image_settings.get_rect()
rect_settings.topleft = (SCREEN_OFFSET_X + f(30), SCREEN_OFFSET_Y + f(30))

clock_player = Clock(SCREEN_OFFSET_X + WIDTH - 2 * SQUARE_SIZE - f(20), rect_image_player.top, True)
clock_opponent = Clock(SCREEN_OFFSET_X + WIDTH - 2 * SQUARE_SIZE - f(20), rect_image_opponent.top, False)

# assuming player is white
names_player = ['P', 'N', 'B', 'R', 'Q', 'K']
names_opponent = [piece.lower() for piece in names_player]

# if player is indeed black, switch player route to blacks and change piece names to lowercase, also replace king and queen
if player_color == "b":
    player_to_move = "o"
    (names_player, names_opponent) = (names_opponent, names_player)
    (route_player, route_opponent) = (route_opponent, route_player)

piece_values = [1, 3, 3, 5, 8, 0]
piece_to_value = dict()
for name, value in zip(names_player, piece_values):
    piece_to_value[name] = value
for name, value in zip(names_opponent, piece_values):
    piece_to_value[name] = value

fen_start = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

# try positions
'''
fen_start = "rnbqk1nr/pppp1ppp/4p3/8/1b6/2NP4/PPP1PPPP/R1BQKBNR w KQkq - 1 3" # bishop pinning the knight
fen_start = "r1bqkbnr/ppppp1pp/2n5/4Pp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3" # en passant possible
fen_start = "r1bqkbnr/ppppp1pp/2n5/4Pp2/8/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 4" # en passant not possible
fen_start = "rnbq1rk1/pppp1ppp/5n2/2b1p3/2B1PP2/5N2/PPPP2PP/RNBQK2R w KQ - 5 5" # castling throught the bishop check
fen_start = "6k1/8/4B3/8/6R1/8/8/6K1 b - - 0 1" # double check
fen_start = "3k4/8/8/1q6/3B4/8/5n2/3R2K1 w - - 0 1" # double check 2
fen_start = "8/4k3/8/2q5/8/8/5n2/4R1K1 b - - 1 3" # counter check
fen_start = "8/1QP3k1/8/8/2q5/8/8/6K1 w - - 0 1" # promotion with check
fen_start = "8/8/4k3/8/8/5K2/8/8 w - - 0 1" # only 2 kings
fen_start = "8/8/4k3/8/4K3/8/8/8 b - - 1 1" # kings in opposition
fen_start = "8/2p5/3p4/KP5r/5p1k/4P3/6P1/8 b - - 0 1" # en passant with pin
fen_start = "8/8/4k3/8/3P4/4K3/8/8 w - - 0 1" # king vs king draw
fen_start = "8/8/3k4/8/2B5/4Kb2/8/8 w - - 0 1" # king vs king and bishop draw
fen_start = "8/4k3/8/8/2N5/4Kb2/8/8 w - - 0 1" # king vs king and knight draw
fen_start = "8/4k3/2b5/8/2B5/4K3/3r4/8 w - - 0 1" # king and bishop vs king and bishop (same colors) draw
fen_start = "8/2b1k3/8/8/2B5/4K3/3r4/8 w - - 0 1" # king and bishop vs king and bishop (opposite colors) not draw
'''

fen.append(fen_start)
convert_fen(fen_start)

# DONT RUN THIS UR PC WILL DIE
#print(num_of_possible_positions(3))

# game loop
while 1:
    # rendering "behind" the gameplay
    screen.fill(BLACKY)
    screen.blit(image_bg, (SCREEN_OFFSET_X, SCREEN_OFFSET_Y))
    screen.blit(image_table, rect_table)

    if SETTINGS_ANIMATION_RUNNING:
        SCREEN_OFFSET_X += SETTINGS_ANIMATION_SPEED
        rect_table.x += SETTINGS_ANIMATION_SPEED
        rect_settings.x += SETTINGS_ANIMATION_SPEED
        rect_image_player.x += SETTINGS_ANIMATION_SPEED
        rect_image_opponent.x += SETTINGS_ANIMATION_SPEED
        rect_flag_player.x += SETTINGS_ANIMATION_SPEED
        rect_flag_opponent.x += SETTINGS_ANIMATION_SPEED
        rect_moving_square_prev.x += SETTINGS_ANIMATION_SPEED
        rect_moving_square_curr.x += SETTINGS_ANIMATION_SPEED
        rect_check_square.x += SETTINGS_ANIMATION_SPEED

        for piece in pieces_player:
            piece.update_rect_position()
        for piece in pieces_opponent:
            piece.update_rect_position()
        
        for piece in pieces_promotion:
            piece.update_rect_position()
        
        clock_player.update_rect_position()
        clock_opponent.update_rect_position()

    if SCREEN_OFFSET_X >= WIDTH * 0.6:
        SETTINGS_ANIMATION_RUNNING = False
        IN_SETTINGS = True
    if SCREEN_OFFSET_X <= 0:
        SETTINGS_ANIMATION_RUNNING = False
        IN_SETTINGS = False

    if player_to_move == "p":
        for piece in pieces_player:
            if piece.selected:
                piece.display_available_squares()
    else:
        for piece in pieces_opponent:
            if piece.selected:
                piece.display_available_squares()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            rect_settings_bigger = rect_settings.copy()
            rect_settings_bigger.width *= 1.5
            rect_settings_bigger.height *= 1.5
            rect_settings_bigger.center = rect_settings.center 
            if rect_settings_bigger.collidepoint(event.pos):
                SETTINGS_ANIMATION_RUNNING = True
                SETTINGS_ANIMATION_SPEED *= -1
        if player_to_move == "p":
            for piece in pieces_player:
                piece.handle_event(event)
        else:
            for piece in pieces_opponent:
                piece.handle_event(event)
            
        if promoting:
            for piece in pieces_promotion:
                piece.handle_event_promotion(event)
    
    dt = clock.tick(60) / 1000
    # after 2 moves, lenght will be 3 since starting position is also in fen
    if len(fen) == 3:
        if player_to_move == "p":
            clock_player.locked = False
        else:
            clock_opponent.locked = False
        clocks_started = True
    
    render_gameplay()
    clock_player.update(dt)
    clock_opponent.update(dt)

    # these situations have to be checked every frame, whereas set_game_reason() gets called only after a move
    if clock_player.seconds_left < 0 or clock_opponent.seconds_left < 0: game_end_reason = "timeout"
    elif resigned: game_end_reason = "resignation"
    elif draw: game_end_reason = "mutual agreement"

    if game_end_reason is not None:
        print(game_end_reason)
        break

    pygame.display.flip()