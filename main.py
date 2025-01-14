import pygame
import sys

pygame.init()

# CONFIGURATION

# aspect ratio 9 : 19.5
WIDTH = 450
HEIGHT = 975

#colors
WHITE = (255, 255, 255)
BLACKY = (30, 30, 30)

#globals
minutes = 0.25
availableMinutes = [0.25, 0.5, 1, 2, 3, 5, 10, 20, 30, 60, 120, 180]

increment = 0
availableIncrements = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 30, 60]

SQUARE_SIZE = int(WIDTH / 8)
game_started = False

# FUNCTIONS
def render_text(s, x, y, font_size):
    # renders string s with center position at (x, y) and font size font_size
    font = pygame.font.Font("Chess-Assets-main/shared/fonts\jetBrainsMono/ttf/JetBrainsMono-Regular.ttf", font_size)
    text_surface = font.render(s, True, WHITE)
    rect_text = text_surface.get_rect()
    rect_text.center = (x,y)
    screen.blit(text_surface, rect_text)

# calculates new dimensions based on initial ones which are 450*975
# handles rescalling while keeping aspect ratio
def f(x):
    return int(x * WIDTH / 450)


# CLASSES
class Slider(pygame.sprite.Sprite):

    def __init__(self, y):
        super().__init__()
        self.y = y
        self.image_panel = pygame.image.load("Chess-Assets-main/shared/home/Rectangle 28.png").convert_alpha()
        self.width_panel = int(WIDTH*3 / 4)
        self.height = f(15)
        self.image_panel = pygame.transform.scale(self.image_panel, (self.width_panel, self.height))
        self.rect_panel = self.image_panel.get_rect()
        self.rect_panel.center = (int(WIDTH / 2), y)

        self.image_cursor = pygame.image.load("Chess-Assets-main/shared/home/Rectangle 32.png").convert_alpha()
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
    def __init__(self, name, image, x, y):
        super().__init__()
        self.x = x
        self.y = y
        self.name = name
        self.image = pygame.transform.scale(image, (SQUARE_SIZE, SQUARE_SIZE))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.dragging = False
        self.clicked = False  # To track simple clicks
    
    def display_available_squares():
        pass

    def handle_event(self, event, locked=False):
        global game_started
        # locked are the ones on the home screen
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
                    if not game_started:
                        global player_color
                        player_color = "w" if self.name == "K" else "b"
                        game_started = True
                    else:
                        self.display_available_squares()
        
        elif event.type == pygame.MOUSEMOTION:
            # Handle dragging
            if self.dragging:
                if not locked:
                    self.rect.center = event.pos  # Update position
                self.clicked = False  # Moving means its not a simple click


# PIECES
image_bg = pygame.image.load("Chess-Assets-main/dark/backgrounds/background dark 1.png")
image_bg = pygame.transform.scale(image_bg, (WIDTH, HEIGHT))

# blacks
blacks_route = "Chess-Assets-main/dark/pieces black/"
image_p = pygame.image.load(blacks_route + "pawn.png")
image_r = pygame.image.load(blacks_route + "top.png")
image_n = pygame.image.load(blacks_route + "knight.png")
image_b = pygame.image.load(blacks_route + "bishop.png")
image_k = pygame.image.load(blacks_route + "kralj.png")
image_q = pygame.image.load(blacks_route + "queen.png")

# whites
whites_route = "Chess-Assets-main/dark/pieces white/"
image_P = pygame.image.load(whites_route + "pawn-1.png")
image_R = pygame.image.load(whites_route + "top-1.png")
image_N = pygame.image.load(whites_route + "knight-1.png")
image_B = pygame.image.load(whites_route + "bishop-1.png")
image_K = pygame.image.load(whites_route + "kralj-1.png")
image_Q = pygame.image.load(whites_route + "queen-1.png")


# SETUP
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Offline Chess")

clock = pygame.time.Clock()

# INSTANCES
slider1 = Slider(f(200))
slider2 = Slider(f(400))

K = Piece("K", image_K, int(WIDTH / 2) - f(100), HEIGHT - f(200))
k = Piece("k", image_k, int(WIDTH / 2) + f(100), HEIGHT - f(200))

pieces = pygame.sprite.Group()
pieces.add(k, K)

while 1:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if game_started:
            pass
        else:
            slider1.handle_event(event)
            slider2.handle_event(event)
            k.handle_event(event, True) # True indicates dragging is disabled
            K.handle_event(event, True)

    screen.blit(image_bg, (0, 0))

    # home screen rendering
    if not game_started:
        slider1.draw()
        slider1.calc_based_on_cursor(1)
        render_text(f"Minutes per player: {minutes}", int(WIDTH / 2), slider1.y - f(40), f(20))

        slider2.draw()
        slider2.calc_based_on_cursor(2)
        render_text(f"Increment in seconds: {increment}", int(WIDTH / 2), slider2.y - f(40), f(20))

        render_text("Choose side", int(WIDTH / 2), k.y - f(150), f(25))
        pieces.draw(screen)

    pygame.display.flip()
    clock.tick(60)

