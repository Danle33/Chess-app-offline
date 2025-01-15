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

#globals
minutes = 0.25
availableMinutes = [0.25, 0.5, 1, 2, 3, 5, 10, 20, 30, 60, 120, 180]

increment = 0
availableIncrements = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 30, 60]

SQUARE_SIZE = WIDTH / 8
game_started = False

image_dot = pygame.image.load("Assets/shared/dot.png")
image_dot = pygame.transform.scale(image_dot, (SQUARE_SIZE * 0.7, SQUARE_SIZE * 0.7))
rect_dot = image_dot.get_rect()

# FUNCTIONS

# renders string s with center position at (x, y) and given font size
def render_text(s, x, y, font_size):
    font = pygame.font.Font("Assets/shared/fonts\jetBrainsMono/ttf/JetBrainsMono-Regular.ttf", font_size)
    text_surface = font.render(s, True, WHITE)
    rect_text = text_surface.get_rect()
    rect_text.center = (x,y)
    screen.blit(text_surface, rect_text)

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
    def __init__(self, name, image, row, column):
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

        self.update_available_squares()

        self.dragging = False
        self.holding = False  # To track simple clicks
        self.selected = False
    
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
    
    # initializes pairs of (row, column) coordinates of available squares
    def update_available_squares(self):
        self.available_squares = []

        if self.name == 'P':
            # square in front of the pawn
            if TABLE_MATRIX[self.row - 1][self.column] == '.':
                self.available_squares.append((self.row - 1, self.column))

            # two squares from starting position
            if self.row == 6 and TABLE_MATRIX[self.row - 2][self.column] == '.':
                self.available_squares.append((self.row - 2, self.column))
           
    
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
            screen.blit(image_dot, rect_dot)
    
    def legal_move(self):
        return False


    def handle_event(self, event):
        (mouse_x, mouse_y) = pygame.mouse.get_pos()
        mouse_on_piece = self.rect_square.collidepoint((mouse_x, mouse_y))

        if event.type == pygame.MOUSEBUTTONDOWN:
            if mouse_on_piece:
                self.selected = not self.selected
                self.holding = True
            else:
                self.selected = False
        
        if event.type == pygame.MOUSEBUTTONUP and mouse_on_piece:
            if self.dragging:
                self.dragging = False
                self.selected = False
                # Align the piece to the closest square if move is legal
                if self.legal_move():
                    self.row, self.column = self.calc_position_matrix(self.rect_square.center)
                    self.rect.center = self.calc_position_screen(self.row, self.column)
                    self.rect_square.center = self.rect.center

                    # Update available squares after the move
                    self.update_available_squares()

                else: # else reset the piece to current position
                    self.rect.center = self.calc_position_screen(self.row, self.column)
                    self.rect_square.center = self.rect.center
            self.holding = False

        if event.type == pygame.MOUSEMOTION and mouse_on_piece and self.selected and self.holding:
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
    names_player = ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p', 'r', 'n', 'b', 'k', 'q', 'b', 'n', 'r']
    names_opponent = [piece.upper() for piece in names_player]
    (route_player, route_opponent) = (route_opponent, route_player)

row = 6
column = 0
for name in names_player:
    if column == 8:
        column = 0
    if name != names_player[0]: # done with pawns
        row = 7
    pieces_player.add(Piece(name, pygame.image.load(route_player + f"{name}.png"), row, column))
    TABLE_MATRIX[row][column] = name
    column += 1

row = 1
column = 0
for name in names_opponent:
    if column == 8:
        column = 0
    if name != names_opponent[0]: # done with pawns
        row = 0
    pieces_opponent.add(Piece(name, pygame.image.load(route_opponent + f"{name}.png"), row, column))
    TABLE_MATRIX[row][column] = name
    column += 1

# game loop
while 1:
    screen.blit(image_bg, (0, 0))
    screen.blit(image_table, rect_table)

    for piece in pieces_player:
        if piece.selected:
            piece.display_available_squares()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        for piece in pieces_player:
            piece.handle_event(event)

    pieces_player.draw(screen)
    pieces_opponent.draw(screen)

    pygame.display.flip()
    clock.tick(60)

