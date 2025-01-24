import pygame
import sys

pygame.init()

# CONFIGURATION

# aspect ratio 9 : 19.5
WIDTH = 450
HEIGHT = 975

TABLE_X = 0
TABLE_Y = HEIGHT / 2 - WIDTH / 2

#colors
WHITE = (255, 255, 255)
BLACKY = (30, 30, 30)
DARK_GREEN_TRANSPARENT = (0, 50, 0, 50)
DARK_GREEN_TRANSPARENT1 = (0, 50, 0, 25)

# darken the screen while promoting
dark_overlay = pygame.Surface((WIDTH, WIDTH))  # Create a surface
dark_overlay.set_alpha(200)  # Set alpha (0 is transparent, 255 is opaque)
dark_overlay.fill((0, 0, 0))  # Fill with black

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

# either player (user) or opponent
player_to_move = "p"

# initializing table matrix, dot represents non occupied square
TABLE_MATRIX = []
for i in range(8):
    TABLE_MATRIX.append(['.'] * 8)

# fen code, list of strings where every string describes one position
fen = []

enpassant_square = "-"
halfmoves = 0
fullmoves = 0

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

# renders string s with center position at (x, y) and given font size
def render_text(s, x, y, font_size):
    font = pygame.font.Font("Assets/shared/fonts\\jetBrainsMono/ttf/JetBrainsMono-Regular.ttf", font_size)
    text_surface = font.render(s, True, WHITE)
    rect_text = text_surface.get_rect()
    rect_text.center = (x,y)
    screen.blit(text_surface, rect_text)

# updates available squares after every move for each piece
def update_available_squares():
    # updating available squares first pass (no filtering pins and checks)
    global pieces_player, pieces_opponent
    for piece in pieces_player:
        piece.update_available_squares()
        if piece.name in ["K", "k"]:
            king_player = (piece.row, piece.column)
    for piece in pieces_opponent:
        piece.update_available_squares()

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
    curr_fen += f" {halfmoves} {fullmoves}"

    # remove first slash
    curr_fen = curr_fen[1:]
    fen.append(curr_fen)

def convert_fen(fen_string):
    # first destroy everything
    global TABLE_MATRIX, matrix_to_piece, pieces_player, pieces_opponent, halfmoves, fullmoves, player_to_move, player_color, K, Q, k, q
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

# calculates new dimensions based on initial ones which are 450*975
# handles rescalling while keeping aspect ratio
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

        self.available_squares = []
        self.capturing_squares = []
    
    # caluclates screen position of a piece based on matrix position
    def calc_position_screen(self, row, column):
        x = TABLE_X + column * SQUARE_SIZE + SQUARE_SIZE / 2
        y = TABLE_Y + row * SQUARE_SIZE + SQUARE_SIZE / 2
        return (int(x), int(y))
    
    # calculates row and column for a given screen position
    # inverse function of the calc_position_screen()
    def calc_position_matrix(self, center):
        (x, y) = center
        row = (y - TABLE_Y) / SQUARE_SIZE
        column = (x -TABLE_X) / SQUARE_SIZE
        return (int(row), int(column))
    
    # initializes pairs of (row, column) coordinates of available squares after every move for a current piece
    def update_available_squares(self):
        self.available_squares = [] # also containts capturing squares
        self.capturing_squares = []

        if self.name == 'P' or self.name == 'p':
            # pawns only go forward
            if self.names == names_player:
                next_row = self.row - 1
                if next_row >= 0:
                    # square in front of the pawn
                    if TABLE_MATRIX[self.row - 1][self.column] == '.':
                        self.available_squares.append((self.row - 1, self.column))

                    # two squares from starting position
                    if self.row == 6 and TABLE_MATRIX[self.row - 2][self.column] == '.':
                        self.available_squares.append((self.row - 2, self.column))

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
                                self.available_squares.append((row, column))
                                self.capturing_squares.append((row, column))


                    if self.column - 1 >= 0:
                        capture_left = TABLE_MATRIX[self.row - 1][self.column - 1]
                        if capture_left not in names_player and capture_left != '.':
                            self.available_squares.append((self.row - 1, self.column - 1))
                            self.capturing_squares.append((self.row - 1, self.column - 1))
                    if self.column + 1 < 8:
                        capture_right = TABLE_MATRIX[self.row - 1][self.column + 1]
                        if capture_right not in names_player and capture_right != '.':
                            self.available_squares.append((self.row - 1, self.column + 1))
                            self.capturing_squares.append((self.row - 1, self.column + 1))
            else:
                next_row = self.row + 1
                if next_row <= 7:
                    # square in front of the pawn
                    if TABLE_MATRIX[self.row + 1][self.column] == '.':
                        self.available_squares.append((self.row + 1, self.column))

                    # two squares from starting position
                    if self.row == 1 and TABLE_MATRIX[self.row + 2][self.column] == '.':
                        self.available_squares.append((self.row + 2, self.column))
                    
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
                                self.available_squares.append((row, column))
                                self.capturing_squares.append((row, column))
                            
                    if self.column - 1 >= 0:
                        capture_left = TABLE_MATRIX[self.row + 1][self.column - 1]
                        if capture_left not in names_opponent and capture_left != '.':
                            self.available_squares.append((self.row + 1, self.column - 1))
                            self.capturing_squares.append((self.row + 1, self.column - 1))

                    if self.column + 1 < 8:
                        capture_right = TABLE_MATRIX[self.row + 1][self.column + 1]
                        if capture_right not in names_opponent and capture_right != '.':
                            self.available_squares.append((self.row + 1, self.column + 1))
                            self.capturing_squares.append((self.row + 1, self.column + 1))

        if self.name == 'N' or self.name == 'n':
            # x, y offsets where knight can possibly jump to
            jumping_offsets = [(1, -2), (2, -1), (2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1), (-1, -2)]

            for (offset_x, offset_y) in jumping_offsets:
                try_row = self.row + offset_y
                try_column = self.column + offset_x
                # checking bounds and availability for every jumping square
                if 0 <= try_row <= 7 and 0 <= try_column <= 7 and TABLE_MATRIX[try_row][try_column] not in self.names:
                    self.available_squares.append((try_row, try_column))
                    if TABLE_MATRIX[try_row][try_column] != '.':
                        self.capturing_squares.append((try_row, try_column))
        
        if self.name == "B" or self.name == 'b':
            # up left
            curr_row = self.row - 1
            curr_column = self.column - 1

            # loop stops when bishop encounters a piece, unlike knight which jumps above pieces
            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                # if current square is not player's and its not a dot -> its capturing square, break after
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.append((curr_row, curr_column))
                    self.capturing_squares.append((curr_row, curr_column))
                    break
                self.available_squares.append((curr_row, curr_column))
                curr_row -= 1
                curr_column -= 1
            
            # up right
            curr_row = self.row - 1
            curr_column = self.column + 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.append((curr_row, curr_column))
                    self.capturing_squares.append((curr_row, curr_column))
                    break
                self.available_squares.append((curr_row, curr_column))
                curr_row -= 1
                curr_column += 1
            
            # down left
            curr_row = self.row + 1
            curr_column = self.column - 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.append((curr_row, curr_column))
                    self.capturing_squares.append((curr_row, curr_column))
                    break
                self.available_squares.append((curr_row, curr_column))
                curr_row += 1
                curr_column -= 1
            
            # down right
            curr_row = self.row + 1
            curr_column = self.column + 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.append((curr_row, curr_column))
                    self.capturing_squares.append((curr_row, curr_column))
                    break
                self.available_squares.append((curr_row, curr_column))
                curr_row += 1
                curr_column += 1

        if self.name == "R" or self.name == 'r':
            # up
            curr_row = self.row - 1
            curr_column = self.column

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.append((curr_row, curr_column))
                    self.capturing_squares.append((curr_row, curr_column))
                    break
                self.available_squares.append((curr_row, curr_column))
                curr_row -= 1
            
            # down
            curr_row = self.row + 1
            curr_column = self.column

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.append((curr_row, curr_column))
                    self.capturing_squares.append((curr_row, curr_column))
                    break
                self.available_squares.append((curr_row, curr_column))
                curr_row += 1
            
            # left
            curr_row = self.row
            curr_column = self.column - 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.append((curr_row, curr_column))
                    self.capturing_squares.append((curr_row, curr_column))
                    break
                self.available_squares.append((curr_row, curr_column))
                curr_column -= 1
            
            # right
            curr_row = self.row
            curr_column = self.column + 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.append((curr_row, curr_column))
                    self.capturing_squares.append((curr_row, curr_column))
                    break
                self.available_squares.append((curr_row, curr_column))
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
                    self.available_squares.append((curr_row, curr_column))
                    self.capturing_squares.append((curr_row, curr_column))
                    break
                self.available_squares.append((curr_row, curr_column))
                curr_row -= 1
                curr_column -= 1
            
            # up right
            curr_row = self.row - 1
            curr_column = self.column + 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.append((curr_row, curr_column))
                    self.capturing_squares.append((curr_row, curr_column))
                    break
                self.available_squares.append((curr_row, curr_column))
                curr_row -= 1
                curr_column += 1
            
            # down left
            curr_row = self.row + 1
            curr_column = self.column - 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.append((curr_row, curr_column))
                    self.capturing_squares.append((curr_row, curr_column))
                    break
                self.available_squares.append((curr_row, curr_column))
                curr_row += 1
                curr_column -= 1
            
            # down right
            curr_row = self.row + 1
            curr_column = self.column + 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.append((curr_row, curr_column))
                    self.capturing_squares.append((curr_row, curr_column))
                    break
                self.available_squares.append((curr_row, curr_column))
                curr_row += 1
                curr_column += 1
            
            # up
            curr_row = self.row - 1
            curr_column = self.column

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.append((curr_row, curr_column))
                    self.capturing_squares.append((curr_row, curr_column))
                    break
                self.available_squares.append((curr_row, curr_column))
                curr_row -= 1
            
            # down
            curr_row = self.row + 1
            curr_column = self.column

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.append((curr_row, curr_column))
                    self.capturing_squares.append((curr_row, curr_column))
                    break
                self.available_squares.append((curr_row, curr_column))
                curr_row += 1
            
            # left
            curr_row = self.row
            curr_column = self.column - 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.append((curr_row, curr_column))
                    self.capturing_squares.append((curr_row, curr_column))
                    break
                self.available_squares.append((curr_row, curr_column))
                curr_column -= 1
            
            # right
            curr_row = self.row
            curr_column = self.column + 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.append((curr_row, curr_column))
                    self.capturing_squares.append((curr_row, curr_column))
                    break
                self.available_squares.append((curr_row, curr_column))
                curr_column += 1
        
        if self.name == "K" or self.name == "k":
            # handle castling
            if not self.moved:
                # king is on the starting position

                # left castling

                # check if leftmost piece in the row is rook with the same color, and hasnt moved
                if TABLE_MATRIX[self.row][0] in ["R", "r"] and TABLE_MATRIX[self.row][0] in self.names and not matrix_to_piece[(self.row, 0)].moved:
                    # check if all squares between are free and not attacked by pieces
                    free = True
                    curr_column = 1
                    while curr_column < self.column:
                        if TABLE_MATRIX[self.row][curr_column] != '.':
                            free = False
                            break
                        curr_column += 1
                    if free:
                        self.available_squares.append((self.row, self.column - 2))
                
                # right castling

                # check if rightmost piece in the row is rook with the same color, and hasnt moved
                if TABLE_MATRIX[self.row][7] in ["R", "r"] and TABLE_MATRIX[self.row][7] in self.names and not matrix_to_piece[(self.row, 7)].moved:
                    # check if all squares between are free and not attacked by pieces
                    free = True
                    curr_column = self.column + 1
                    while curr_column <= 6:
                        if TABLE_MATRIX[self.row][curr_column] != '.':
                            free = False
                            break
                        curr_column += 1
                    if free:
                        self.available_squares.append((self.row, self.column + 2))

            # same as queen, but range is only 1 square

            # up left
            curr_row = self.row - 1
            curr_column = self.column - 1

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.append((curr_row, curr_column))
            
            # up right
            curr_row = self.row - 1
            curr_column = self.column + 1

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.append((curr_row, curr_column))
            
            # down left
            curr_row = self.row + 1
            curr_column = self.column - 1

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.append((curr_row, curr_column))
            
            # down right
            curr_row = self.row + 1
            curr_column = self.column + 1

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.append((curr_row, curr_column))
            
            # up
            curr_row = self.row - 1
            curr_column = self.column

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.append((curr_row, curr_column))
            
            # down
            curr_row = self.row + 1
            curr_column = self.column

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.append((curr_row, curr_column))
            
            # left
            curr_row = self.row
            curr_column = self.column - 1

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.append((curr_row, curr_column))
            
            # right
            curr_row = self.row
            curr_column = self.column + 1

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.append((curr_row, curr_column))

    def display_available_squares(self):
        # and also mark selected square
        marked_square = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        marked_square.fill(DARK_GREEN_TRANSPARENT)

        rect_marked_square = marked_square.get_rect()
        (x, y) = self.calc_position_screen(self.row, self.column)
        rect_marked_square.center = (x + 1, y + 1) # adding +1 cause board image doesnt contain perfect squares and alignment

        screen.blit(marked_square, rect_marked_square)

        for (row, column) in self.available_squares:
            (x, y) = self.calc_position_screen(row, column)
            rect_dot.center = (x, y)
            # if its not empty square, then player is capturing
            # marking it green
            if TABLE_MATRIX[row][column] != '.':
                marked_square.fill(DARK_GREEN_TRANSPARENT1)
                (x, y) = self.calc_position_screen(row, column)
                rect_marked_square.center = (x + 1, y + 1) # adding +1 cause board image doesnt contain perfect squares and alignment
                screen.blit(marked_square, rect_marked_square)
            # else display a dot
            else:
                screen.blit(image_dot, rect_dot)
    
    def available_move(self):
        # catches the current (x, y) coordinates of a piece while being dragged accross the board and checks if the chosen square is available
        (row_try, column_try) = self.calc_position_matrix(self.rect_square.center)
        return (row_try, column_try) in self.available_squares
    
    def make_move(self, square=None):

        global TABLE_MATRIX, matrix_to_piece
        # mark previous square as available
        TABLE_MATRIX[self.row][self.column] = '.'
        matrix_to_piece[(self.row, self.column)] = None

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
            if not self.moved:
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
            if square is None:
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

        # next player
        if square is None:
            global player_to_move
            if player_to_move == "p":
                player_to_move = "o"
            else:
                player_to_move = "p"
        
        # update fen history
        if not promoting and square is None:
            scan_fen()
            print(fen[-1])
            enpassant_square = "-"

    def handle_event(self, event):
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
            if not (TABLE_X <= mouse_x <= TABLE_X + 8 * SQUARE_SIZE and TABLE_Y <= mouse_y <= TABLE_Y + 8 * SQUARE_SIZE):
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
            # handle making a move by clicking at an availablq square
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
                    # update squares for every piece
                    update_available_squares()
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
                    # update squares for every piece
                    update_available_squares()
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
            curr_x = max(mouse_x, self.rect.size[0] / 2)
            curr_x = min(curr_x, WIDTH - self.rect.size[0] / 2)
            curr_y = max(mouse_y, TABLE_Y + self.rect.size[1] / 2)
            curr_y = min(curr_y, TABLE_Y + 8 * SQUARE_SIZE - self.rect.size[1] / 2)

            self.rect.center = (curr_x, curr_y)
            self.rect_square.center = self.rect.center

    def handle_event_promotion(self, event):
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
            print(fen[-1])
            update_available_squares()

# background image
image_bg = pygame.image.load("Assets/dark/backgrounds/background dark 1.png")
image_bg = pygame.transform.scale(image_bg, (WIDTH, HEIGHT))

# table
image_table = pygame.image.load("Assets/dark/boards/tiles.png")
image_table = pygame.transform.scale(image_table, (WIDTH, WIDTH))
rect_table = image_table.get_rect()
rect_table.topleft = (TABLE_X, TABLE_Y)

# home screen
slider1 = Slider(f(200))
slider2 = Slider(f(400))

# assuming player is white
route_player = "Assets/dark/pieces white/"
route_opponent = "Assets/dark/pieces black/"

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

    screen.blit(image_bg, (0, 0))

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
# real pieces in real time
pieces_player = pygame.sprite.Group()
pieces_opponent = pygame.sprite.Group()
# pieces while simulating and etc...
pieces_player_sim = pygame.sprite.Group()
pieces_opponent_sim = pygame.sprite.Group()

# assuming player is white
names_player = ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
names_opponent = [piece.lower() for piece in names_player]

# if player is indeed black, switch player route to blacks and change piece names to lowercase, also replace king and queen
if player_color == "b":
    player_to_move = "o"
    names_player = ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p', 'r', 'n', 'b', 'k', 'q', 'b', 'n', 'r']
    names_opponent = [piece.upper() for piece in names_player]
    (route_player, route_opponent) = (route_opponent, route_player)

fen_start = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
fen_start = "rnbqk1nr/pppp1ppp/4p3/8/1b6/2NP4/PPP1PPPP/R1BQKBNR w KQkq - 1 3" # bishop pinning the knight
#fen_start = "r1bqkbnr/ppppp1pp/2n5/4Pp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3" # en passant possible
#fen_start = "r1bqkbnr/ppppp1pp/2n5/4Pp2/8/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 4" # en passant not possible
fen.append(fen_start)
convert_fen(fen_start)

update_available_squares()
print(fen[-1])

# game loop
while 1:
    screen.blit(image_bg, (0, 0))
    screen.blit(image_table, rect_table)

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
        if player_to_move == "p":
            for piece in pieces_player:
                piece.handle_event(event)
        else:
            for piece in pieces_opponent:
                piece.handle_event(event)

    pieces_player.draw(screen)
    pieces_opponent.draw(screen)

    if promoting:
        # darken the screen
        screen.blit(dark_overlay, (TABLE_X, TABLE_Y))
        pieces_promotion.draw(screen)

        for piece in pieces_promotion:
            piece.handle_event_promotion(event)

    pygame.display.flip()
    clock.tick(60)