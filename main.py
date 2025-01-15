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

#globals
minutes = 0.25
availableMinutes = [0.25, 0.5, 1, 2, 3, 5, 10, 20, 30, 60, 120, 180]

increment = 0
availableIncrements = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 30, 60]

SQUARE_SIZE = WIDTH / 8
game_started = False

names_white = ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
names_black = [piece.lower() for piece in names_white]

# FUNCTIONS

# renders string s with center position at (x, y) and given font size
def render_text(s, x, y, font_size):
    font = pygame.font.Font("Assets/shared/fonts\jetBrainsMono/ttf/JetBrainsMono-Regular.ttf", font_size)
    text_surface = font.render(s, True, WHITE)
    rect_text = text_surface.get_rect()
    rect_text.center = (x,y)
    screen.blit(text_surface, rect_text)

# caluclates screen position of a piece based on matrix position
def calc_position(row, column):
    x = TABLE_X + column * SQUARE_SIZE + SQUARE_SIZE / 2
    y = TABLE_Y + row * SQUARE_SIZE + SQUARE_SIZE / 2
    return (int(x), int(y))

# calculates new dimensions based on initial ones which are 450*975
# handles rescalling while keeping aspect ratio
def f(x):
    return x * WIDTH / 450


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
    def __init__(self, name, image, x, y, row, column):
        super().__init__()
        self.x = x
        self.y = y
        self.name = name
        self.image = pygame.transform.scale(image, (SQUARE_SIZE * 0.7, SQUARE_SIZE * 0.7))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        self.row = row
        self.column = column

        self.init_available_squares()

        self.dragging = False
        self.clicked = False  # To track simple clicks
    
    # initializes pairs of (row, column) coordinates of available squares
    def init_available_squares(self):
        pass
    
    def display_available_squares(self):
        # and also mark selected square
        pass

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if the mouse clicked on the sprite
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.clicked = True  # Initially assume it's a click

        elif event.type == pygame.MOUSEBUTTONUP:
            # Handle release
            if self.dragging:
                self.dragging = False
                # If the mouse hasnt moved, treat it as a click
                if self.clicked:
                    self.display_available_squares()
        
        elif event.type == pygame.MOUSEMOTION:
            # Handle dragging
            if self.dragging:
                # handle board bounds
                curr_x = max(event.pos[0], 0 + self.rect.size[0] / 2)
                curr_x = min(curr_x, WIDTH - self.rect.size[0] / 2)
                curr_y = max(event.pos[1], TABLE_Y + self.rect.size[1] / 2)
                curr_y = min(curr_y, TABLE_Y + 8 * SQUARE_SIZE - self.rect.size[1] / 2)
                self.rect.center = (curr_x, curr_y)  # Update position
                self.clicked = False  # Moving means its not a simple click


# background image
image_bg = pygame.image.load("Assets/dark/backgrounds/background dark 1.png")
image_bg = pygame.transform.scale(image_bg, (WIDTH, HEIGHT))

# table
image_table = pygame.image.load("Assets/dark/boards/tiles.png")
image_table = pygame.transform.scale(image_table, (WIDTH, WIDTH))
rect_table = image_table.get_rect()
rect_table.topleft = (TABLE_X, TABLE_Y)

# SETUP
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Offline Chess")

clock = pygame.time.Clock()

# home screen
slider1 = Slider(f(200))
slider2 = Slider(f(400))

route_whites = "Assets/dark/pieces white/"
route_blacks = "Assets/dark/pieces black/"

image_K = pygame.image.load(route_whites + "K.png")
image_K = pygame.transform.scale(image_K, (f(100), f(100)))
rect_K = image_K.get_rect()
rect_K.center = (WIDTH / 2 - f(100), HEIGHT - f(100))

image_k = pygame.image.load(route_blacks + "k.png")
image_k = pygame.transform.scale(image_k, (f(100), f(100)))
rect_k = image_k.get_rect()
rect_k.center = (WIDTH / 2 + f(100), HEIGHT - f(100))

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

if player_color == "b":
    # invert king and queen and also routes
    names_white = ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P', 'R', 'N', 'B', 'K', 'Q', 'B', 'N', 'R']
    names_black = [piece.lower() for piece in names_white]
    (route_whites, route_blacks) = (route_blacks, route_whites)

# whites
pieces_white = pygame.sprite.Group()
row = 6
column = 0
for name in names_white:
    if column == 8:
        column = 0
    if name != 'P':
        row = 7
    (x, y) = calc_position(row, column)
    pieces_white.add(Piece(name, pygame.image.load(route_whites + f"{name}.png"), x, y, row, column))
    TABLE_MATRIX[row][column] = name
    column += 1

# blacks
pieces_black = pygame.sprite.Group()
row = 1
column = 0
for name in names_white:
    if column == 8:
        column = 0
    if name != 'P':
        row = 0
    (x, y) = calc_position(row, column)
    pieces_black.add(Piece(name, pygame.image.load(route_blacks + f"{name}.png"), x, y, row, column))
    TABLE_MATRIX[row][column] = name
    column += 1

# game
# "white" pieces are always the ones on the bottom of the screen, even though their color is black
while 1:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        for piece_white in pieces_white:
            piece_white.handle_event(event)

    screen.blit(image_bg, (0, 0))
    screen.blit(image_table, rect_table)

    pieces_white.draw(screen)
    pieces_black.draw(screen)

    pygame.display.flip()
    clock.tick(60)

