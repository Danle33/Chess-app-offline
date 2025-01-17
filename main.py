import pygame
import sys

pygame.init()

# CONFIGURATION

# aspect ratio 9 : 19.5
WIDTH = 450
HEIGHT = 975

TABLE_X = 0
TABLE_Y = HEIGHT / 2 - WIDTH / 2

# initializing table matrix, dot represents non occupied square
TABLE_MATRIX = []
for i in range(8):
    TABLE_MATRIX.append(['.'] * 8)

#colors
WHITE = (255, 255, 255)
BLACKY = (30, 30, 30)
DARK_GREEN_TRANSPARENT = (0, 50, 0, 50)
DARK_GREEN_TRANSPARENT1 = (0, 50, 0, 25)

#globals
minutes = 0.25
availableMinutes = [0.25, 0.5, 1, 2, 3, 5, 10, 20, 30, 60, 120, 180]

increment = 0
availableIncrements = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 30, 60]

SQUARE_SIZE = WIDTH / 8
game_started = False

# either player (user) or opponent
player_to_move = "p"

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
    for piece in pieces_player:
        piece.update_available_squares()
    for piece in pieces_opponent:
        piece.update_available_squares()

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

        # Separate rect for the larger square
        self.rect_square = pygame.Rect(0, 0, SQUARE_SIZE, SQUARE_SIZE)
        self.rect_square.center = self.rect.center  # Align centers

        self.dragging = False
        self.holding = False
        self.selected = False
        self.unselecting_downclick = False

        self.names = names.copy()

        # needed for castling
        self.moved = False

        # when initializing a piece, call only self method
        self.update_available_squares()
    
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
        self.available_squares = []

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
                    if self.column - 1 >= 0:
                        capture_left = TABLE_MATRIX[self.row - 1][self.column - 1]
                        if capture_left not in names_player and capture_left not in names_player and capture_left != '.':
                            self.available_squares.append((self.row - 1, self.column - 1))
                    if self.column + 1 < 8:
                        capture_right = TABLE_MATRIX[self.row - 1][self.column + 1]
                        if capture_right not in names_player and capture_right not in names_player and capture_right != '.':
                            self.available_squares.append((self.row - 1, self.column + 1))
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
                    if self.column - 1 >= 0:
                        capture_left = TABLE_MATRIX[self.row + 1][self.column - 1]
                        if capture_left not in self.names and capture_left not in self.names and capture_left != '.':
                            self.available_squares.append((self.row + 1, self.column - 1))
                    if self.column + 1 < 8:
                        capture_right = TABLE_MATRIX[self.row + 1][self.column + 1]
                        if capture_right not in self.names and capture_right not in self.names and capture_right != '.':
                            self.available_squares.append((self.row + 1, self.column + 1))

        if self.name == 'N' or self.name == 'n':
            # x, y offsets where knight can possibly jump to
            jumping_offsets = [(1, -2), (2, -1), (2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1), (-1, -2)]

            for (offset_x, offset_y) in jumping_offsets:
                try_row = self.row + offset_y
                try_column = self.column + offset_x
                # checking bounds and availability for every jumping square
                if 0 <= try_row <= 7 and 0 <= try_column <= 7 and TABLE_MATRIX[try_row][try_column] not in self.names:
                    self.available_squares.append((try_row, try_column))
        
        if self.name == "B" or self.name == 'b':
            # up left
            curr_row = self.row - 1
            curr_column = self.column - 1

            # loop stops when bishop encounters a piece, unlike knight which jumps above pieces
            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                # if current square is not player's and its not a dot -> its capturing square, break after
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.append((curr_row, curr_column))
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
                    break
                self.available_squares.append((curr_row, curr_column))
                curr_row -= 1
            
            # down
            curr_row = self.row + 1
            curr_column = self.column

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.append((curr_row, curr_column))
                    break
                self.available_squares.append((curr_row, curr_column))
                curr_row += 1
            
            # left
            curr_row = self.row
            curr_column = self.column - 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.append((curr_row, curr_column))
                    break
                self.available_squares.append((curr_row, curr_column))
                curr_column -= 1
            
            # right
            curr_row = self.row
            curr_column = self.column + 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.append((curr_row, curr_column))
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
                    break
                self.available_squares.append((curr_row, curr_column))
                curr_row -= 1
            
            # down
            curr_row = self.row + 1
            curr_column = self.column

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.append((curr_row, curr_column))
                    break
                self.available_squares.append((curr_row, curr_column))
                curr_row += 1
            
            # left
            curr_row = self.row
            curr_column = self.column - 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.append((curr_row, curr_column))
                    break
                self.available_squares.append((curr_row, curr_column))
                curr_column -= 1
            
            # right
            curr_row = self.row
            curr_column = self.column + 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.append((curr_row, curr_column))
                    break
                self.available_squares.append((curr_row, curr_column))
                curr_column += 1
        
        if self.name == "K" or self.name == 'k':
            # handle castling
            if not self.moved:
                # king is on the starting position
                pass

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
            else:
                self.selected = False
        
        if event.type == pygame.MOUSEBUTTONUP and mouse_on_piece:
            if self.dragging:
                self.dragging = False
                self.selected = False
                # Align the piece to the closest square if move is legal
                if self.available_move():
                    # mark previous square as available
                    TABLE_MATRIX[self.row][self.column] = '.'

                    self.row, self.column = self.calc_position_matrix(self.rect_square.center)

                    # handle castling by checking if king somehow "moved" two squares
                    if self.name in ["K", "k"]:
                        pass

                    self.rect.center = self.calc_position_screen(self.row, self.column)
                    self.rect_square.center = self.rect.center

                    # check if it was capture
                    if TABLE_MATRIX[self.row][self.column] != '.': # if its available move and not empty square -> its capture
                        captured_piece = matrix_to_piece[((self.row, self.column))]
                        captured_piece.kill()
                        matrix_to_piece[(row, column)] = None

                    # updating the position matrix
                    TABLE_MATRIX[self.row][self.column] = self.name

                    # updating position dictionary
                    matrix_to_piece[(self.row, self.column)] = self

                    # if it was king or a rook, disable castling rights by alerting that either moved
                    if self.name == "K" or self.name == "k" or self.name == "R" or self.name == "r":
                        self.moved = True

                    # update squares for every piece
                    update_available_squares()

                    # next player
                    global player_to_move
                    if player_to_move == "p":
                        player_to_move = "o"
                    else:
                        player_to_move = "p"

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
pieces_player = pygame.sprite.Group()
pieces_opponent = pygame.sprite.Group()

# assuming player is white
names_player = ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
names_opponent = [piece.lower() for piece in names_player]

# if player is indeed black, switch player route to blacks and change piece names to lowercase, also replace king and queen
if player_color == "b":
    player_to_move = "o"
    names_player = ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p', 'r', 'n', 'b', 'k', 'q', 'b', 'n', 'r']
    names_opponent = [piece.upper() for piece in names_player]
    (route_player, route_opponent) = (route_opponent, route_player)

# initializing piece by piece, and a position matrix
row = 6
column = 0
for name in names_player:
    if column == 8:
        column = 0
    if name != names_player[0]: # done with pawns
        row = 7
    piece = Piece(name, pygame.image.load(route_player + f"{name}.png"), row, column, names_player)
    pieces_player.add(piece)
    TABLE_MATRIX[row][column] = name
    matrix_to_piece[(row, column)] = piece
    column += 1

row = 1
column = 0
for name in names_opponent:
    if column == 8:
        column = 0
    if name != names_opponent[0]: # done with pawns
        row = 0
    piece = Piece(name, pygame.image.load(route_opponent + f"{name}.png"), row, column, names_opponent)
    pieces_opponent.add(piece)
    TABLE_MATRIX[row][column] = name
    matrix_to_piece[(row, column)] = piece
    column += 1

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

    pygame.display.flip()
    clock.tick(60)

