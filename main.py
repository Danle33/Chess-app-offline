import pygame
import sys
import copy
import weakref
import random
import threading
from stockfish import Stockfish

pygame.init()
pygame.mixer.init()

# Get the user's screen size
info = pygame.display.Info()
max_width, max_height = info.current_w, info.current_h

HEIGHT = max_height - 100
WIDTH = HEIGHT * 9 / 19.5

# aspect ratio 9 : 19.5
'''WIDTH = 450
HEIGHT = 975'''

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Offline Chess")

# pygame clock, handles fps
clock = pygame.time.Clock()

# ASSETS/GLOBALS

available_minutes = [0.25, 0.5, 1, 2, 3, 5, 10, 20, 30, 60, 120, 180]
available_increments = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 30, 60]
available_strengths = range(1, 21)

piece_move = pygame.mixer.Sound("Assets/sounds/piecemove.wav")
piece_capture = pygame.mixer.Sound("Assets/sounds/piececapture.wav")
piece_capture.set_volume(0.6)
game_start = pygame.mixer.Sound("Assets/sounds/gamestart.wav")
game_start.set_volume(0.25)

SQUARE_SIZE = WIDTH / 8

# calculates new dimensions based on initial ones which are 450*975
# enables rescalling while keeping aspect ratio
def f(x):
    return x * WIDTH / 450

# renders string s with (default center) position at (x, y) and given font size
def render_text(s, x, y, font_size, top_left=False, right=False, color=None):
    if color is None:
        color = Assets.WHITE
    font = pygame.font.Font("Assets/shared/fonts\\jetBrainsMono/ttf/JetBrainsMono-Regular.ttf", font_size)
    text_surface = font.render(s, True, color)
    rect_text = text_surface.get_rect()
    if top_left:
        rect_text.topleft = (x, y)
    elif right:
        rect_text.right = x
        rect_text.centery = y
    else:
        rect_text.center = (x, y)

    screen.blit(text_surface, rect_text)
    return rect_text

class Assets:

    theme = "dark"

    WHITE = (255, 255, 255)
    WHITE2 = (170, 170, 170)
    BLACK = (0, 0, 0)
    BLACKY = (30, 30, 30)
    BLACKY1 = (20, 20, 20)
    DARK_GREEN_TRANSPARENT = (0, 50, 0, 50)
    DARK_GREEN_TRANSPARENT1 = (0, 50, 0, 25)
    YELLOW_TRANSPARENT = (255, 255, 0, 20)
    YELLOW_TRANSPARENT1 = (255, 255, 0, 10)
    RED_TRANSPARENT = (255, 0, 0, 50)
    PURPLE_TRANSPARENT = (100, 0, 150, 25)
    GRAY = (128, 128, 128)

    dark_overlay = pygame.Surface((WIDTH, WIDTH))  # Create a surface
    dark_overlay.set_alpha(220)  # Set alpha (0 is transparent, 255 is opaque)
    dark_overlay.fill(BLACK)  # Fill with black

    moving_square_prev = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
    moving_square_prev.fill(YELLOW_TRANSPARENT1)

    moving_square_curr = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
    moving_square_curr.fill(YELLOW_TRANSPARENT)

    check_square = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
    check_square.fill(RED_TRANSPARENT)

    premove_square = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
    premove_square.fill(PURPLE_TRANSPARENT)

    # background image
    image_bg = pygame.image.load("Assets/dark/backgrounds/boje1.png")
    image_bg = pygame.transform.smoothscale(image_bg, (WIDTH, HEIGHT))

    # table
    image_table = pygame.image.load("Assets/dark/boards/board background.png")
    image_table = pygame.transform.smoothscale(image_table, (WIDTH, WIDTH))

    # kings images home screen
    image_K = pygame.image.load("Assets/dark/pieces white/K.png")
    image_K = pygame.transform.smoothscale(image_K, (f(100), f(100)))

    image_k = pygame.image.load("Assets/dark/pieces black/k.png")
    image_k = pygame.transform.smoothscale(image_k, (f(100), f(100)))

    image_N = pygame.image.load("Assets/dark/pieces white/N.png")
    image_N = pygame.transform.smoothscale(image_N, (f(100), f(100)))

    image_unknown_user = pygame.image.load("Assets/dark/users/unknown user.png")
    image_unknown_user = pygame.transform.smoothscale(image_unknown_user, (SQUARE_SIZE * 0.7, SQUARE_SIZE * 0.7 * 93 / 97))

    image_flag_player = pygame.image.load("Assets/shared/flags/64/unknown.png")
    image_flag_player = pygame.transform.smoothscale(image_flag_player, (f(20), f(20)))

    image_flag_opponent = pygame.image.load("Assets/shared/flags/64/unknown.png")
    image_flag_opponent = pygame.transform.smoothscale(image_flag_opponent, (f(20), f(20)))

    image_settings = pygame.image.load("Assets/dark/options.png")
    image_settings = pygame.transform.smoothscale(image_settings, (SQUARE_SIZE * 0.6, SQUARE_SIZE * 0.6 * 55 / 75))

    image_panel = pygame.image.load("Assets/shared/home/Rectangle 28.png")
    image_cursor = pygame.image.load("Assets/shared/home/Rectangle 32.png")

    image_gameover_big = pygame.image.load("Assets/shared/Rectangle 34.png")
    image_gameover_big = pygame.transform.smoothscale(image_gameover_big, (WIDTH * 0.7, WIDTH * 0.7 * 650 / 1200))

    image_gameover_small = pygame.image.load("Assets/shared/Rectangle 35.jpg")
    image_gameover_small = pygame.transform.smoothscale(image_gameover_small, (WIDTH * 0.7, WIDTH * 0.7 * 300 / 1200))

    image_trophy = pygame.image.load("Assets/shared/image 2.png")
    image_trophy = pygame.transform.smoothscale(image_trophy, (image_gameover_big.get_height() - image_gameover_small.get_height() - f(40), 
                                                               (image_gameover_big.get_height() - image_gameover_small.get_height() - f(40)) * 211 / 180))

    image_gameover_button = pygame.image.load("Assets/shared/Rectangle 36.png")
    image_gameover_button = pygame.transform.smoothscale(image_gameover_button, (image_gameover_big.get_width() / 2 - f(20), 
                                                        (image_gameover_big.get_width() / 2 - f(20)) * 150 / 550))

    image_close_button = pygame.image.load("Assets/shared/close.png")
    image_close_button = pygame.transform.smoothscale(image_close_button, (f(10), f(10)))

    image_fast_backward = pygame.image.load("Assets/dark/pgn controlls/first.png")
    image_fast_backward = pygame.transform.smoothscale(image_fast_backward, (f(35), f(35) * 80 / 88))

    image_backward = pygame.image.load("Assets/dark/pgn controlls/previous.png")
    image_backward = pygame.transform.smoothscale(image_backward, (f(35), f(35) * 80 / 88))

    image_forward = pygame.image.load("Assets/dark/pgn controlls/next.png")
    image_forward = pygame.transform.smoothscale(image_forward, (f(35), f(35) * 80 / 88))

    image_fast_forward = pygame.image.load("Assets/dark/pgn controlls/last.png")
    image_fast_forward = pygame.transform.smoothscale(image_fast_forward, (f(35), f(35) * 80 / 88))

    image_moon = pygame.image.load("Assets/shared/moon light.png")
    image_moon = pygame.transform.smoothscale(image_moon, (f(40), f(40)))

    def change_theme(theme=None):
        Assets.WHITE = tuple(255 - x for x in Assets.WHITE[:3]) + Assets.WHITE[3:]
        Assets.WHITE2 = tuple(255 - x for x in Assets.WHITE2[:3]) + Assets.WHITE2[3:]
        Assets.BLACKY = tuple(255 - x for x in Assets.BLACKY[:3]) + Assets.BLACKY[3:]
        #Assets.BLACKY1 = tuple(255 - x for x in Assets.BLACKY1[:3]) + Assets.BLACKY1[3:]
        Assets.DARK_GREEN_TRANSPARENT = tuple(255 - x for x in Assets.DARK_GREEN_TRANSPARENT[:3]) + Assets.DARK_GREEN_TRANSPARENT[3:]
        Assets.DARK_GREEN_TRANSPARENT1 = tuple(255 - x for x in Assets.DARK_GREEN_TRANSPARENT1[:3]) + Assets.DARK_GREEN_TRANSPARENT1[3:]
        Assets.YELLOW_TRANSPARENT = tuple(255 - x for x in Assets.YELLOW_TRANSPARENT[:3]) + Assets.YELLOW_TRANSPARENT[3:]
        Assets.YELLOW_TRANSPARENT1 = tuple(255 - x for x in Assets.YELLOW_TRANSPARENT1[:3]) + Assets.YELLOW_TRANSPARENT1[3:]
        Assets.RED_TRANSPARENT = tuple(255 - x for x in Assets.RED_TRANSPARENT[:3]) + Assets.RED_TRANSPARENT[3:]
        Assets.PURPLE_TRANSPARENT = tuple(255 - x for x in Assets.PURPLE_TRANSPARENT[:3]) + Assets.PURPLE_TRANSPARENT[3:]
        Assets.GRAY = tuple(255 - x for x in Assets.GRAY[:3]) + Assets.GRAY[3:]
        Assets.BLACK = tuple(255 - x for x in Assets.BLACK[:3]) + Assets.BLACK[3:]

        Assets.dark_overlay.fill(Assets.BLACK)

        Assets.image_moon = pygame.image.load(f"Assets/shared/moon {Assets.theme}.png")
        Assets.image_moon = pygame.transform.smoothscale(Assets.image_moon, (f(40), f(40)))

        if Assets.theme == "dark":
            Assets.theme = "light"
        else:
            Assets.theme = "dark"
            
        Assets.image_bg = pygame.image.load(f"Assets/{Assets.theme}/backgrounds/background {Assets.theme}.png")
        Assets.image_bg = pygame.transform.smoothscale(Assets.image_bg, (WIDTH, HEIGHT))

        Assets.image_table = pygame.image.load(f"Assets/{Assets.theme}/boards/board background.png")
        Assets.image_table = pygame.transform.smoothscale(Assets.image_table, (WIDTH, WIDTH))

        Assets.image_unknown_user = pygame.image.load(f"Assets/{Assets.theme}/users/unknown user.png")
        Assets.image_unknown_user = pygame.transform.smoothscale(Assets.image_unknown_user, (SQUARE_SIZE * 0.7, SQUARE_SIZE * 0.7 * 93 / 97))

        Assets.image_fast_backward = pygame.image.load(f"Assets/{Assets.theme}/pgn controlls/first.png")
        Assets.image_fast_backward = pygame.transform.smoothscale(Assets.image_fast_backward, (f(35), f(35) * 80 / 88))

        Assets.image_backward = pygame.image.load(f"Assets/{Assets.theme}/pgn controlls/previous.png")
        Assets.image_backward = pygame.transform.smoothscale(Assets.image_backward, (f(35), f(35) * 80 / 88))

        Assets.image_forward = pygame.image.load(f"Assets/{Assets.theme}/pgn controlls/next.png")
        Assets.image_forward = pygame.transform.smoothscale(Assets.image_forward, (f(35), f(35) * 80 / 88))

        Assets.image_fast_forward = pygame.image.load(f"Assets/{Assets.theme}/pgn controlls/last.png")
        Assets.image_fast_forward = pygame.transform.smoothscale(Assets.image_fast_forward, (f(35), f(35) * 80 / 88))

        Assets.image_N = pygame.image.load("Assets/dark/pieces white/N.png") if Assets.theme == "dark" else pygame.image.load("Assets/light/pieces black/n.png")
        Assets.image_N = pygame.transform.smoothscale(Assets.image_N, (f(100), f(100)))

        Assets.image_settings = pygame.image.load(f"Assets/{Assets.theme}/options.png")
        Assets.image_settings = pygame.transform.smoothscale(Assets.image_settings, (SQUARE_SIZE * 0.6, SQUARE_SIZE * 0.6 * 55 / 75))

        # kings images home screen
        Assets.image_K = pygame.image.load(f"Assets/{Assets.theme}/pieces white/K.png")
        Assets.image_K = pygame.transform.smoothscale(Assets.image_K, (f(100), f(100)))

        Assets.image_k = pygame.image.load(f"Assets/{Assets.theme}/pieces black/k.png")
        Assets.image_k = pygame.transform.smoothscale(Assets.image_k, (f(100), f(100)))

        if game.player_color == "w":
            game.route_player = f"Assets/{Assets.theme}/pieces white/"
            game.route_opponent = f"Assets/{Assets.theme}/pieces black/"
        else:
            game.route_player = f"Assets/{Assets.theme}/pieces black/"
            game.route_opponent = f"Assets/{Assets.theme}/pieces white/"

        for piece in game.pieces_player:
            piece.image = pygame.image.load(game.route_player + piece.name + ".png")
            piece.image = pygame.transform.smoothscale(piece.image, (SQUARE_SIZE * 0.7, SQUARE_SIZE * 0.7))

        for piece in game.pieces_opponent:
            piece.image = pygame.image.load(game.route_opponent + piece.name + ".png")
            piece.image = pygame.transform.smoothscale(piece.image, (SQUARE_SIZE * 0.7, SQUARE_SIZE * 0.7))

        for piece in game.pieces_promotion:
            piece.image = pygame.image.load(game.route_player + piece.name + ".png")
            piece.image = pygame.transform.smoothscale(piece.image, (SQUARE_SIZE * 0.7, SQUARE_SIZE * 0.7))

rect_moving_square_prev = Assets.moving_square_prev.get_rect()
rect_moving_square_curr = Assets.moving_square_prev.get_rect()

rect_check_square = Assets.check_square.get_rect()

rect_table = Assets.image_table.get_rect()

rect_K = Assets.image_K.get_rect()
rect_K.center = (WIDTH / 2 - f(100), HEIGHT - f(100))

rect_k = Assets.image_k.get_rect()
rect_k.center = (WIDTH / 2 + f(100), HEIGHT - f(100))

rect_N = Assets.image_N.get_rect()
rect_N.center = (WIDTH * 0.3, WIDTH * 0.3)

rect_resign = pygame.Rect(0, 0, 1, 1)
rect_draw = pygame.Rect(0, 0, 1, 1)
rect_change_theme = pygame.Rect(0, 0, 1, 1)

rect_image_player = Assets.image_unknown_user.get_rect()
rect_image_opponent = Assets.image_unknown_user.get_rect()

rect_flag_player = Assets.image_flag_player.get_rect()
rect_flag_opponent = Assets.image_flag_opponent.get_rect()

rect_settings = Assets.image_settings.get_rect()

rect_gameover_big = Assets.image_gameover_big.get_rect(center=(WIDTH / 2, HEIGHT / 2))
rect_gameover_small = Assets.image_gameover_small.get_rect(bottomleft=rect_gameover_big.bottomleft)

rect_trophy = Assets.image_trophy.get_rect()
rect_trophy.center = (rect_gameover_big.left + f(50), (rect_gameover_big.top + rect_gameover_small.top) / 2)

rect_gameover_button1 = Assets.image_gameover_button.get_rect()
rect_gameover_button1.center = (rect_gameover_big.left + rect_gameover_big.width / 4, (rect_gameover_small.top + rect_gameover_small.bottom) / 2)
rect_gameover_button2 = Assets.image_gameover_button.get_rect()
rect_gameover_button2.center = (rect_gameover_big.right - rect_gameover_big.width / 4, (rect_gameover_small.top + rect_gameover_small.bottom) / 2)

rect_close_button = Assets.image_close_button.get_rect()

rect_pgn = pygame.Rect(-1, rect_image_player.bottom + f(50), WIDTH + 2, f(30))

rect_fast_backward = Assets.image_fast_backward.get_rect()
rect_backward = Assets.image_backward.get_rect()
rect_forward = Assets.image_forward.get_rect()
rect_fast_forward = Assets.image_fast_forward.get_rect()

rect_moon = Assets.image_moon.get_rect()

piece_to_value = dict()
for name, value in zip(["P", "N", "B", "R", "Q", "p", "n", "b", "r", "q"], [1, 3, 3, 5, 9, 1, 3, 3, 5, 9]):
    piece_to_value[name] = value

file_to_column = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6, "g": 7, "h": 8}
column_to_file = dict()
for file, column in file_to_column.items():
    column_to_file[column] = file

fen_start = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

try_positions = []
try_positions.append("rnbqk1nr/pppp1ppp/4p3/8/1b6/2NP4/PPP1PPPP/R1BQKBNR w KQkq - 1 3") # bishop pinning the knight
try_positions.append("r1bqkbnr/ppppp1pp/2n5/4Pp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3") # en passant possible
try_positions.append("r1bqkbnr/ppppp1pp/2n5/4Pp2/8/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 4") # en passant not possible
try_positions.append("rnbq1rk1/pppp1ppp/5n2/2b1p3/2B1PP2/5N2/PPPP2PP/RNBQK2R w KQ - 5 5") # castling throught the bishop check
try_positions.append("6k1/8/4B3/8/6R1/8/8/6K1 b - - 0 1") # double check
try_positions.append("3k4/8/8/1q6/3B4/8/5n2/3R2K1 w - - 0 1") # double check 2
try_positions.append("8/4k3/8/2q5/8/8/5n2/4R1K1 b - - 1 3") # counter check
try_positions.append("8/1QP3k1/8/8/2q5/8/8/6K1 w - - 0 1") # promotion with check
try_positions.append("8/8/4k3/8/8/5K2/8/8 w - - 0 1") # only 2 kings
try_positions.append("8/8/4k3/8/4K3/8/8/8 b - - 1 1") # kings in opposition
try_positions.append("8/2p5/3p4/KP5r/5p1k/4P3/6P1/8 b - - 0 1") # en passant with pin
try_positions.append("8/8/4k3/8/3P4/4K3/8/8 w - - 0 1") # king vs king draw
try_positions.append("8/8/3k4/8/2B5/4Kb2/8/8 w - - 0 1") # king vs king and bishop draw
try_positions.append("8/4k3/8/8/2N5/4Kb2/8/8 w - - 0 1") # king vs king and knight draw
try_positions.append("8/4k3/2b5/8/2B5/4K3/3r4/8 w - - 0 1") # king and bishop vs king and bishop (same colors) draw
try_positions.append("8/2b1k3/8/8/2B5/4K3/3r4/8 w - - 0 1") # king and bishop vs king and bishop (opposite colors) not draw
try_positions.append("r3k2r/pQp2ppp/4q3/2b1nb2/2Pp3B/P6P/1P1NPPP1/3RKB1R w kq - 0 1") # smothered mate
try_positions.append("8/5P2/8/8/5k2/8/3K4/8 w - - 0 1") # promotion
try_positions.append("8/8/4k3/8/3Q4/8/1Q6/3K4 w - - 0 1") # two queens vs king premoving
try_positions.append("2k5/1n6/8/8/8/8/6p1/4K2R w K - 0 1") # castling through pawn check
try_positions.append("R2Q4/5pbk/2p3p1/3b4/4p1B1/7P/1q1P1P2/4K3 w - - 0 1") # queen giving check being defended by a pinned bishop
try_positions.append("r2k4/1P5R/8/8/8/8/8/3K4 w - - 0 1") # promotion while capturing into a checkmate (hell yeah)
try_positions.append("rnbqkbnr/pPpppppp/p7/8/8/8/PPPP1PPP/RNBQK1NR w KQkq - 0 1") # promotion UI test

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# CLASSES
class Home:
    def __init__(self):
        self.minutes = 3
        self.increment = 2
        self.strength = 10
        self.slider1 = Slider(f(200))
        # set 3+2 mode manually
        self.slider1.rect_cursor.x += f(120)
        self.slider2 = Slider(f(350))
        self.slider2.rect_cursor.x += f(60)
        self.slider3 = Slider(f(500))
        self.slider3.rect_cursor.centerx = WIDTH / 2
    
    def run(self):
        while 1:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                self.slider1.handle_event(event)
                self.slider2.handle_event(event)
                self.slider3.handle_event(event)
                
                # handle clicking on kings
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if rect_K.collidepoint(event.pos):
                        self.player_color = "w"
                        return
                    if rect_k.collidepoint(event.pos):
                        self.player_color = "b"
                        return
            
            screen.fill(Assets.BLACKY)
            screen.blit(Assets.image_bg, (0, 0))

            screen.blit(Assets.image_K, rect_K)
            screen.blit(Assets.image_k, rect_k)

            self.slider1.draw()
            self.slider1.calc_based_on_cursor(self, 1)
            render_text(f"Minutes per player: {self.minutes}", WIDTH / 2, self.slider1.y - f(40), int(f(20)))

            self.slider2.draw()
            self.slider2.calc_based_on_cursor(self, 2)
            render_text(f"Increment in seconds: {self.increment}", WIDTH / 2, self.slider2.y - f(40), int(f(20)))

            self.slider3.draw()
            self.slider3.calc_based_on_cursor(self, 3)
            render_text(f"Stockfish strength: {self.strength}", WIDTH / 2, self.slider3.y - f(40), int(f(20)))

            render_text("Choose side", WIDTH / 2, rect_k.center[1] - f(125), int(f(25)))

            pygame.display.flip()
            clock.tick(60)

class Game:
    back_to_home = True

    def __init__(self, home):
        self.player_color = home.player_color
        self.player_to_move = "p" if self.player_color == "w" else "o"

        self.advantage = 0
        self.advantage_x = 0

        self.winner = None

        self.minutes = home.minutes
        self.increment = home.increment
        self.strength = home.strength

        self.SCREEN_OFFSET_X = self.SCREEN_OFFSET_Y = 0
        self.TABLE_X = 0
        self.TABLE_Y = HEIGHT / 2 - WIDTH / 2

        self.promoting = False
        self.pieces_promotion = pygame.sprite.Group()
        self.promotion_square = None

        # clocks are only starting after a pair of moves
        self.clocks_started = False

        self.resigned = False
        self.draw = False

        self.SETTINGS_ANIMATION_SPEED = -f(20) # pixels per frame

        # initializing table matrix, dot represents non occupied square
        self.TABLE_MATRIX = []
        for i in range(8):
            self.TABLE_MATRIX.append(['.'] * 8)

        # fen code, list of strings where every string describes one position
        self.fen = []
        self.move_index = len(self.fen) - 1

        # list of moves represented in extended algebraic notation
        self.algebraic = [""]
        self.curr_algebraic = ""
        self.algebraic_text = ""

        # mapping position to how many times it occured, used for threefold repetition detection
        self.fen_count = dict()

        self.enpassant_square = "-"
        self.halfmoves = 0
        self.fullmoves = 0

        self.game_end_reason = None

        # availability of each of 4 types of castling, used in fen
        self.K = self.k = self.Q = self.q = True

        # dictionary that maps (row, column) to piece instance
        self.matrix_to_piece = {}
        for row in range(0, 8):
            for column in range(0, 8):
                self.matrix_to_piece[(row, column)] = None
        
        self.SETTINGS_ANIMATION_RUNNING = False
        self.IN_SETTINGS = False

        self.IN_PARALLEL_UNIVERSE = False

        rect_table.topleft = (self.TABLE_X, self.TABLE_Y)

        # assuming player is white
        if self.player_color == "w":
            self.route_player = f"Assets/{Assets.theme}/pieces white/"
            self.route_opponent = f"Assets/{Assets.theme}/pieces black/"
        else:
            self.route_player = f"Assets/{Assets.theme}/pieces black/"
            self.route_opponent = f"Assets/{Assets.theme}/pieces white/"

        # SETTING PIECES UP
        self.pieces_player = pygame.sprite.Group()
        self.pieces_opponent = pygame.sprite.Group()

        self.captured_pieces_player = []
        self.captured_pieces_opponent = []

        rect_image_player.topleft = (self.SCREEN_OFFSET_X + f(10), self.TABLE_Y + 8 * SQUARE_SIZE + f(15))
        rect_image_opponent.bottomleft = (self.SCREEN_OFFSET_X  + f(10), self.TABLE_Y - f(15))
        rect_flag_player.topleft = (self.SCREEN_OFFSET_X + f(200), rect_image_player.top)
        rect_flag_opponent.topleft = (self.SCREEN_OFFSET_X + f(200), rect_image_opponent.top)
        rect_settings.topleft = (self.SCREEN_OFFSET_X + f(30), self.SCREEN_OFFSET_Y + f(30))
        rect_pgn.topleft = (-1, rect_image_player.bottom + f(30))
        rect_moving_square_prev.center = (-1, -1)
        rect_check_square.center = (-1, -1)
        rect_close_button.topright = (rect_gameover_big.right - f(10), rect_gameover_big.top + f(10))
        rect_fast_backward.topleft = (f(10), rect_pgn.bottom + f(10))
        rect_backward.topleft = (rect_fast_backward.right + f(10), rect_pgn.bottom + f(10))
        rect_fast_forward.topright = (rect_pgn.right - f(10), rect_pgn.bottom + f(10))
        rect_forward.topright = (rect_fast_forward.left - f(10), rect_pgn.bottom + f(10))
        rect_moon.bottom = rect_settings.bottom + f(10)
        rect_moon.right = WIDTH - f(30)

        self.clock_player = Clock(self, self.SCREEN_OFFSET_X + WIDTH - 2 * SQUARE_SIZE - f(20), rect_image_player.top, True)
        self.clock_opponent = Clock(self, self.SCREEN_OFFSET_X + WIDTH - 2 * SQUARE_SIZE - f(20), rect_image_opponent.top, False)

        # assuming player is white
        self.names_player = ['P', 'N', 'B', 'R', 'Q', 'K']
        self.names_opponent = [piece.lower() for piece in self.names_player]

        # if player is indeed black, switch player route to blacks
        if self.player_color == "b":
            self.player_to_move = "o"
            (self.names_player, self.names_opponent) = (self.names_opponent, self.names_player)
        
        self.best_move_stockfish = None

        # used only for testing premoves, doesnt affect the game logic
        self.move_cooldown = 2

        self.stockfish_active = True

        self.premoves = []

        self.fen.append(fen_start)
        self.convert_fen(fen_start)

        self.stockfish = Stockfish(path="stockfish/stockfish-windows-x86-64-avx2.exe")
        self.stockfish.set_skill_level(self.strength)
        self.stockfish_elo = 135 * self.strength + 800  # linear estimate
        self.stockfish.set_fen_position(fen_start)
        self.thread = None
        if self.stockfish_active:
            self.lock = threading.Lock()
        if self.player_to_move == "o" and self.stockfish_active:
            self.get_move_in_background()

    
    def run(self):
        while 1:
            # rendering "behind" the gameplay
            screen.fill(Assets.BLACKY)
            if self.SETTINGS_ANIMATION_RUNNING or self.IN_SETTINGS:
                screen.blit(Assets.image_N, rect_N)
            rect_resign = render_text("Resign", WIDTH * 0.3, rect_N.bottom + f(100), int(f(25)))
            rect_draw = render_text("Offer draw", WIDTH * 0.3, rect_N.bottom + f(200), int(f(25)))
            rect_change_theme = render_text("Switch theme", WIDTH * 0.3, rect_N.bottom + f(300), int(f(25)))

            screen.blit(Assets.image_bg, (self.SCREEN_OFFSET_X, self.SCREEN_OFFSET_Y))
            screen.blit(Assets.image_table, rect_table)

            if self.SETTINGS_ANIMATION_RUNNING:
                self.reset_premoves()

                self.SCREEN_OFFSET_X += self.SETTINGS_ANIMATION_SPEED
                self.TABLE_X += self.SETTINGS_ANIMATION_SPEED
                rect_table.x += self.SETTINGS_ANIMATION_SPEED
                rect_settings.x += self.SETTINGS_ANIMATION_SPEED
                rect_image_player.x += self.SETTINGS_ANIMATION_SPEED
                rect_image_opponent.x += self.SETTINGS_ANIMATION_SPEED
                rect_flag_player.x += self.SETTINGS_ANIMATION_SPEED
                rect_flag_opponent.x += self.SETTINGS_ANIMATION_SPEED
                rect_moving_square_prev.x += self.SETTINGS_ANIMATION_SPEED
                rect_moving_square_curr.x += self.SETTINGS_ANIMATION_SPEED
                rect_check_square.x += self.SETTINGS_ANIMATION_SPEED
                rect_pgn.x += self.SETTINGS_ANIMATION_SPEED
                rect_fast_backward.x += self.SETTINGS_ANIMATION_SPEED
                rect_backward.x += self.SETTINGS_ANIMATION_SPEED
                rect_forward.x += self.SETTINGS_ANIMATION_SPEED
                rect_fast_forward.x += self.SETTINGS_ANIMATION_SPEED
                rect_moon.x += self.SETTINGS_ANIMATION_SPEED
                
                for piece in self.pieces_player:
                    piece.update_rect_position()
                    piece.rect.center = piece.calc_position_screen(piece.row, piece.column)
                    piece.rect_square.center = piece.rect.center

                for piece in self.pieces_opponent:
                    piece.update_rect_position()
                    piece.rect.center = piece.calc_position_screen(piece.row, piece.column)
                    piece.rect_square.center = piece.rect.center
                
                for piece in self.pieces_promotion:
                    piece.update_rect_position()
                
                for piece in self.captured_pieces_player:
                    piece.update_rect_position()
                for piece in self.captured_pieces_opponent:
                    piece.update_rect_position()
                
                self.advantage_x += self.SETTINGS_ANIMATION_SPEED

                self.clock_player.update_rect_position()
                self.clock_opponent.update_rect_position()
            
            if self.SCREEN_OFFSET_X > WIDTH * 0.6:
                self.SETTINGS_ANIMATION_RUNNING = False
                self.IN_SETTINGS = True
            if self.SCREEN_OFFSET_X + self.SETTINGS_ANIMATION_SPEED < 0:
                self.SETTINGS_ANIMATION_RUNNING = False
                self.IN_SETTINGS = False
            
            if self.player_to_move == "p":
                for piece in self.pieces_player:
                    if piece.selected:
                        piece.display_available_squares()
            else:
                for piece in self.pieces_opponent:
                    if piece.selected:
                        piece.display_available_squares()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN: 
                    clickable_area = rect_settings.inflate(f(15), f(15))
                    if clickable_area.collidepoint(event.pos):
                        self.SETTINGS_ANIMATION_RUNNING = True
                        self.SETTINGS_ANIMATION_SPEED *= -1
                    
                    if self.IN_SETTINGS and rect_resign.collidepoint(event.pos):
                        self.resigned = True
                    
                    if self.IN_SETTINGS and rect_draw.collidepoint(event.pos):
                        self.draw = True
                    
                    clickable_area = rect_moon.inflate((f(10), f(10)))
                    if (self.IN_SETTINGS and rect_change_theme.collidepoint(event.pos)) or clickable_area.collidepoint(event.pos):
                        Assets.change_theme()
                    
                    # handle parallel universe
                    if rect_fast_backward.collidepoint(event.pos):
                        self.move_index = 0
                        self.reset_premoves()
                        self.IN_PARALLEL_UNIVERSE = not (self.move_index == len(self.fen) - 1)
                        self.convert_fen(self.fen[self.move_index])
                        self.algebraic_to_text()
                    
                    if rect_backward.collidepoint(event.pos):
                        if self.move_index >= 1:
                            self.move_index -= 1
                        self.reset_premoves()
                        self.IN_PARALLEL_UNIVERSE = not (self.move_index == len(self.fen) - 1)
                        self.convert_fen(self.fen[self.move_index])
                        self.algebraic_to_text()
                    
                    if rect_forward.collidepoint(event.pos):
                        if self.move_index <= len(self.fen) - 2:
                            self.move_index += 1
                        self.reset_premoves()
                        self.IN_PARALLEL_UNIVERSE = not (self.move_index == len(self.fen) - 1)
                        self.convert_fen(self.fen[self.move_index])
                        self.algebraic_to_text()
                    
                    if rect_fast_forward.collidepoint(event.pos):
                        self.move_index = len(self.fen) - 1
                        self.reset_premoves()
                        self.IN_PARALLEL_UNIVERSE = not (self.move_index == len(self.fen) - 1)
                        self.convert_fen(self.fen[self.move_index])
                        self.algebraic_to_text()
                
                if event.type == pygame.KEYDOWN and not self.promoting:
                    if event.key == pygame.K_LEFT:
                        if self.move_index >= 1:
                            self.move_index -= 1

                    if event.key == pygame.K_RIGHT:
                        if self.move_index <= len(self.fen) - 2:
                            self.move_index += 1
                    
                    if event.key == pygame.K_DOWN:
                        self.move_index = 0
                    
                    if event.key == pygame.K_UP:
                        self.move_index = len(self.fen) - 1
                
                    self.reset_premoves()

                    self.IN_PARALLEL_UNIVERSE = not (self.move_index == len(self.fen) - 1)
                    self.convert_fen(self.fen[self.move_index])
                    self.algebraic_to_text()

                for piece in self.pieces_player:
                    piece.handle_event(event)
                
                if self.player_to_move == "o" and not self.stockfish_active:
                    for piece in self.pieces_opponent:
                        piece.handle_event(event)
                    
                if self.player_to_move == "p" and self.promoting:
                    for piece in self.pieces_promotion:
                        piece.handle_event_promotion(event)
            
            if self.player_to_move == "o" and self.stockfish_active and self.is_move_ready() and self.best_move_stockfish is not None:
                if self.IN_PARALLEL_UNIVERSE:
                    self.convert_fen(self.fen[-1])
                self.move_index = len(self.fen) - 1
                self.IN_PARALLEL_UNIVERSE = False
                self.play_move_stockfish()
                self.post_move_processing()
                
                if len(self.premoves) > 0:
                    (piece, center) = self.premoves[0]
                    square = piece.calc_position_matrix(center)
                    if piece.available_move(square):
                        piece.selected = False
                        piece.dragging = False
                        piece.holding = False
                        piece.unselecting_downclick = False
                        piece.make_move(square)
                        if piece.name in ["P", "p"] and (piece.row == 0 or piece.row == 7):
                            piece.handle_event_promotion(None, premoved=True)
                        self.premoves.pop(0)                        
                        self.post_move_processing()
                    else:
                        self.reset_premoves()

            dt = clock.tick(60) / 1000
            if self.player_to_move == "o":
                self.move_cooldown -= dt

            screen.blit(Assets.image_settings, rect_settings)
            screen.blit(Assets.image_moon, rect_moon)

            if rect_moving_square_prev.center[0] >= self.SCREEN_OFFSET_X and rect_moving_square_prev.center[1] >= self.SCREEN_OFFSET_Y and not self.IN_PARALLEL_UNIVERSE:
                screen.blit(Assets.moving_square_prev, rect_moving_square_prev)
                screen.blit(Assets.moving_square_curr, rect_moving_square_curr)
            
            if rect_check_square.center[0] >= self.SCREEN_OFFSET_X and rect_check_square.center[1] >= self.SCREEN_OFFSET_Y and not self.IN_PARALLEL_UNIVERSE:
                screen.blit(Assets.check_square, rect_check_square)

            self.pieces_player.draw(screen)
            self.pieces_opponent.draw(screen)

            for piece in self.captured_pieces_player:
                screen.blit(piece.image, piece.rect)
            for piece in self.captured_pieces_opponent:
                screen.blit(piece.image, piece.rect)

            # rendering off table stuff
            screen.blit(Assets.image_unknown_user, rect_image_player)
            screen.blit(Assets.image_unknown_user, rect_image_opponent)

            render_text("Username", rect_image_player.right + f(15), rect_image_player.top + f(1), int(f(14)), top_left=True)
            render_text("(3500)", self.SCREEN_OFFSET_X + f(138), rect_image_player.top + f(1), int(f(14)), top_left=True, color=Assets.GRAY)
            render_text("Computer", rect_image_opponent.right + f(15), rect_image_opponent.top + f(1), int(f(14)), top_left=True)
            render_text(f"({self.stockfish_elo})", self.SCREEN_OFFSET_X  + f(138), rect_image_opponent.top + f(1), int(f(14)), top_left=True, color=Assets.GRAY)

            screen.blit(Assets.image_flag_player, rect_flag_player)
            screen.blit(Assets.image_flag_opponent, rect_flag_opponent)

            if self.advantage > 0:
                render_text(f"+{self.advantage}", self.advantage_x, rect_image_player.top + f(24), int(f(10)), top_left=True)
            elif self.advantage < 0:
                render_text(f"+{-self.advantage}", self.advantage_x, rect_image_opponent.top + f(24), int(f(10)), top_left=True)

            self.clock_player.draw()
            self.clock_opponent.draw()

            self.clock_player.update(dt)
            self.clock_opponent.update(dt)

            # render premoving squares
            for (piece, center) in self.premoves:
                rect_premove_square = Assets.premove_square.get_rect()
                rect_premove_square.center = (center[0] + self.SCREEN_OFFSET_X, center[1])
                screen.blit(Assets.premove_square, rect_premove_square)

            if self.promoting:
                #self.promote_random_piece()
                screen.blit(Assets.dark_overlay, (self.SCREEN_OFFSET_X, self.TABLE_Y))
                self.pieces_promotion.draw(screen)

            if not (self.SETTINGS_ANIMATION_RUNNING or self.IN_SETTINGS):
                pygame.draw.rect(screen, Assets.WHITE2, rect_pgn, width=1)
                render_text(self.algebraic_text, rect_pgn.right, rect_pgn.y + rect_pgn.height / 2, int(f(12)), right=True)
                screen.blit(Assets.image_fast_backward, rect_fast_backward)
                screen.blit(Assets.image_backward, rect_backward)
                screen.blit(Assets.image_forward, rect_forward)
                screen.blit(Assets.image_fast_forward, rect_fast_forward)

            # these situations have to be checked every frame, whereas set_game_reason() gets called only after a move
            if self.clock_player.seconds_left <= 0:
                self.game_end_reason = "timeout"
                self.clock_player.seconds_left = 0
                self.winner = "o"

            if self.clock_opponent.seconds_left <= 0:
                self.game_end_reason = "timeout"
                self.clock_opponent.seconds_left = 0
                self.winner = "p"

            elif self.resigned:
                self.game_end_reason = "resignation"
                self.winner = "o"

            elif self.draw: self.game_end_reason = "mutual agreement"

            if self.game_end_reason is not None:
                break

            pygame.display.flip()
        
        # rendering game over screen
        if self.winner == "p":
            self.winner = "You"
        elif self.winner == "o":
            if self.player_color == "w":
                self.winner = "Black"
            else:
                self.winner = "White"
        
        self.promoting = False
        self.clock_player.locked = True
        self.clock_opponent.locked = True
        
        closed_dialog = False
        self.reset_premoves()
        # -------------------------------------------------------------------------------------------------------------------
        pygame.time.wait(100)
        game_start.play()
        while 1:
            # rendering "behind" the gameplay
            screen.fill(Assets.BLACKY)
            if self.SETTINGS_ANIMATION_RUNNING or self.IN_SETTINGS:
                screen.blit(Assets.image_N, rect_N)
            rect_resign = render_text("Rematch", WIDTH * 0.3, rect_N.bottom + f(100), int(f(25))) # now its rect_rematch
            rect_draw = render_text("Home", WIDTH * 0.3, rect_N.bottom + f(200), int(f(25))) # rect_home
            rect_change_theme = render_text("Switch theme", WIDTH * 0.3, rect_N.bottom + f(300), int(f(25))) # rect_home

            screen.blit(Assets.image_bg, (self.SCREEN_OFFSET_X, self.SCREEN_OFFSET_Y))
            screen.blit(Assets.image_table, rect_table)

            if self.SETTINGS_ANIMATION_RUNNING:
                self.reset_premoves()
                
                self.SCREEN_OFFSET_X += self.SETTINGS_ANIMATION_SPEED
                self.TABLE_X += self.SETTINGS_ANIMATION_SPEED
                rect_table.x += self.SETTINGS_ANIMATION_SPEED
                rect_settings.x += self.SETTINGS_ANIMATION_SPEED
                rect_image_player.x += self.SETTINGS_ANIMATION_SPEED
                rect_image_opponent.x += self.SETTINGS_ANIMATION_SPEED
                rect_flag_player.x += self.SETTINGS_ANIMATION_SPEED
                rect_flag_opponent.x += self.SETTINGS_ANIMATION_SPEED
                rect_moving_square_prev.x += self.SETTINGS_ANIMATION_SPEED
                rect_moving_square_curr.x += self.SETTINGS_ANIMATION_SPEED
                rect_check_square.x += self.SETTINGS_ANIMATION_SPEED
                rect_pgn.x += self.SETTINGS_ANIMATION_SPEED
                rect_fast_backward.x += self.SETTINGS_ANIMATION_SPEED
                rect_backward.x += self.SETTINGS_ANIMATION_SPEED
                rect_forward.x += self.SETTINGS_ANIMATION_SPEED
                rect_fast_forward.x += self.SETTINGS_ANIMATION_SPEED
                rect_moon.x += self.SETTINGS_ANIMATION_SPEED

                for piece in self.pieces_player:
                    piece.update_rect_position()
                    piece.rect.center = piece.calc_position_screen(piece.row, piece.column)
                    piece.rect_square.center = piece.rect.center

                for piece in self.pieces_opponent:
                    piece.update_rect_position()
                    piece.rect.center = piece.calc_position_screen(piece.row, piece.column)
                    piece.rect_square.center = piece.rect.center
                
                for piece in self.pieces_promotion:
                    piece.update_rect_position()
                
                for piece in self.captured_pieces_player:
                    piece.update_rect_position()
                for piece in self.captured_pieces_opponent:
                    piece.update_rect_position()
                
                self.advantage_x += self.SETTINGS_ANIMATION_SPEED

                self.clock_player.update_rect_position()
                self.clock_opponent.update_rect_position()

            if self.SCREEN_OFFSET_X > WIDTH * 0.6:
                self.SETTINGS_ANIMATION_RUNNING = False
                self.IN_SETTINGS = True
            if self.SCREEN_OFFSET_X + self.SETTINGS_ANIMATION_SPEED < 0:
                self.SETTINGS_ANIMATION_RUNNING = False
                self.IN_SETTINGS = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    clickable_area = rect_settings.inflate(f(15), f(15))
                    if clickable_area.collidepoint(event.pos):
                        self.SETTINGS_ANIMATION_RUNNING = True
                        self.SETTINGS_ANIMATION_SPEED *= -1
                    
                    if (not closed_dialog and rect_gameover_button1.collidepoint(event.pos)) or rect_resign.collidepoint(event.pos):
                        Game.back_to_home = False
                        return

                    if (not closed_dialog and rect_gameover_button2.collidepoint(event.pos)) or rect_draw.collidepoint(event.pos):
                        Game.back_to_home = True
                        return
                    
                    clickable_area = rect_moon.inflate((f(10), f(10)))
                    if (self.IN_SETTINGS and rect_change_theme.collidepoint(event.pos)) or clickable_area.collidepoint(event.pos):
                        Assets.change_theme()
                    
                    clickable_area = rect_close_button.inflate(f(10), f(10))
                    if not closed_dialog and clickable_area.collidepoint(event.pos):
                        closed_dialog = True
                
                # handle parallel universe
                    if rect_fast_backward.collidepoint(event.pos):
                        self.move_index = 0
                        self.reset_premoves()
                        self.IN_PARALLEL_UNIVERSE = not (self.move_index == len(self.fen) - 1)
                        self.convert_fen(self.fen[self.move_index])
                        self.algebraic_to_text()
                    
                    if rect_backward.collidepoint(event.pos):
                        if self.move_index >= 1:
                            self.move_index -= 1
                        self.reset_premoves()
                        self.IN_PARALLEL_UNIVERSE = not (self.move_index == len(self.fen) - 1)
                        self.convert_fen(self.fen[self.move_index])
                        self.algebraic_to_text()
                    
                    if rect_forward.collidepoint(event.pos):
                        if self.move_index <= len(self.fen) - 2:
                            self.move_index += 1
                        self.reset_premoves()
                        self.IN_PARALLEL_UNIVERSE = not (self.move_index == len(self.fen) - 1)
                        self.convert_fen(self.fen[self.move_index])
                        self.algebraic_to_text()
                    
                    if rect_fast_forward.collidepoint(event.pos):
                        self.move_index = len(self.fen) - 1
                        self.reset_premoves()
                        self.IN_PARALLEL_UNIVERSE = not (self.move_index == len(self.fen) - 1)
                        self.convert_fen(self.fen[self.move_index])
                        self.algebraic_to_text()
                
                if event.type == pygame.KEYDOWN and not self.promoting:
                    if event.key == pygame.K_LEFT:
                        if self.move_index >= 1:
                            self.move_index -= 1

                    if event.key == pygame.K_RIGHT:
                        if self.move_index <= len(self.fen) - 2:
                            self.move_index += 1
                    
                    if event.key == pygame.K_DOWN:
                        self.move_index = 0
                    
                    if event.key == pygame.K_UP:
                        self.move_index = len(self.fen) - 1
                
                    self.reset_premoves()

                    self.IN_PARALLEL_UNIVERSE = not (self.move_index == len(self.fen) - 1)
                    self.convert_fen(self.fen[self.move_index])
                    self.algebraic_to_text()
            
            clock.tick(60)

            screen.blit(Assets.image_settings, rect_settings)
            screen.blit(Assets.image_moon, rect_moon)

            for piece in self.captured_pieces_player:
                screen.blit(piece.image, piece.rect)
            for piece in self.captured_pieces_opponent:
                screen.blit(piece.image, piece.rect)

            if self.advantage > 0:
                render_text(f"+{self.advantage}", self.advantage_x, rect_image_player.top + f(24), int(f(10)), top_left=True)
            elif self.advantage < 0:
                render_text(f"+{-self.advantage}", self.advantage_x, rect_image_opponent.top + f(24), int(f(10)), top_left=True)

            if rect_moving_square_prev.center[0] >= self.SCREEN_OFFSET_X and rect_moving_square_prev.center[1] >= self.SCREEN_OFFSET_Y and not self.IN_PARALLEL_UNIVERSE:
                screen.blit(Assets.moving_square_prev, rect_moving_square_prev)
                screen.blit(Assets.moving_square_curr, rect_moving_square_curr)

            self.pieces_player.draw(screen)
            self.pieces_opponent.draw(screen)

            # rendering off table stuff
            screen.blit(Assets.image_unknown_user, rect_image_player)
            screen.blit(Assets.image_unknown_user, rect_image_opponent)

            render_text("Username", rect_image_player.right + f(15), rect_image_player.top + f(1), int(f(14)), top_left=True)
            render_text("(3500)", self.SCREEN_OFFSET_X + f(138), rect_image_player.top + f(1), int(f(14)), top_left=True, color=Assets.GRAY)
            render_text("Computer", rect_image_opponent.right + f(15), rect_image_opponent.top + f(1), int(f(14)), top_left=True)
            render_text(f"({self.stockfish_elo})", self.SCREEN_OFFSET_X  + f(138), rect_image_opponent.top + f(1), int(f(14)), top_left=True, color=Assets.GRAY)

            screen.blit(Assets.image_flag_player, rect_flag_player)
            screen.blit(Assets.image_flag_opponent, rect_flag_opponent)

            self.clock_player.draw()
            self.clock_opponent.draw()

            if not closed_dialog:
                screen.blit(Assets.image_gameover_big, rect_gameover_big)
                screen.blit(Assets.image_gameover_small, rect_gameover_small)

                if self.winner is None:
                    render_text("Draw", WIDTH / 2, rect_gameover_big.top + f(25), int(f(23)))
                else:
                    render_text(f"{self.winner} won!", WIDTH / 2, rect_gameover_big.top + f(25), int(f(23)), color=(255, 255, 255))
                render_text(f"by {self.game_end_reason}", WIDTH / 2, rect_gameover_big.top + f(55), int(f(12)), color=Assets.GRAY)

                if self.winner == "You":
                    screen.blit(Assets.image_trophy, rect_trophy)
                
                screen.blit(Assets.image_gameover_button, rect_gameover_button1)
                render_text("Rematch", rect_gameover_big.left + rect_gameover_big.width / 4, (rect_gameover_small.top + rect_gameover_small.bottom) / 2, int(f(16)), color=(255, 255, 255))

                screen.blit(Assets.image_gameover_button, rect_gameover_button2)
                render_text("Home", rect_gameover_big.right - rect_gameover_big.width / 4, (rect_gameover_small.top + rect_gameover_small.bottom) / 2, int(f(16)), color=(255, 255, 255))

                screen.blit(Assets.image_close_button, rect_close_button)

            if not (self.SETTINGS_ANIMATION_RUNNING or self.IN_SETTINGS):
                pygame.draw.rect(screen, Assets.WHITE2, rect_pgn, width=1)
                render_text(self.algebraic_text, rect_pgn.right, rect_pgn.y + rect_pgn.height / 2, int(f(12)), right=True)
                screen.blit(Assets.image_fast_backward, rect_fast_backward)
                screen.blit(Assets.image_backward, rect_backward)
                screen.blit(Assets.image_forward, rect_forward)
                screen.blit(Assets.image_fast_forward, rect_fast_forward)

            pygame.display.flip()

    def play_move_stockfish(self):
        move = self.best_move_stockfish
        prev_row = int(move[1]) - 1 if self.player_color == "b" else 7 - (int(move[1]) - 1)
        prev_column = file_to_column[move[0]] - 1 if self.player_color == "w" else 7 - (file_to_column[move[0]] - 1)
        curr_row = int(move[3]) - 1 if self.player_color == "b" else 7 - (int(move[3]) - 1)
        curr_column = file_to_column[move[2]] - 1 if self.player_color == "w" else 7 - (file_to_column[move[2]] - 1)
        piece = self.matrix_to_piece[(prev_row, prev_column)]
        piece.make_move((curr_row, curr_column))

        # promotion
        if len(move) == 5:
            (row, column) = self.promotion_square
            for piecee in self.pieces_promotion:
                if piecee.name.lower() == move[-1].lower():
                    piece = piecee
                    break
            piece.row = row
            piece.column = column
            self.TABLE_MATRIX[row][column] = piece.name

            pawn = self.matrix_to_piece[((row, column))]
            pawn.kill()

            new_piece = Piece(piece.game, piece.name, piece.image, piece.row, piece.column, piece.names)
            self.curr_algebraic += f"={new_piece.name.upper()}"
            self.matrix_to_piece[((row, column))] = new_piece
            if piece.row == 0:
                self.pieces_player.add(new_piece)
            elif piece.row == 7:
                self.pieces_opponent.add(new_piece)

            # promoting a piece is equivalent to losing a pawn but capturing opponents piece (chosen one), materialwise
            self.process_captured_piece(new_piece.name)

            # lil simulation
            if self.player_to_move == "p":
                self.player_to_move = "o"
            else:
                self.player_to_move = "p"

            self.process_captured_piece("p")

            if self.player_to_move == "p":
                self.player_to_move = "o"
            else:
                self.player_to_move = "p"
            
            # update advantage
            if new_piece.names == self.names_player:
                self.advantage += piece_to_value[new_piece.name]
                self.advantage -= piece_to_value["p"]
            else:
                self.advantage -= piece_to_value[new_piece.name]
                self.advantage += piece_to_value["p"]

            for piecee in self.pieces_promotion:
                piecee.kill()
            
            self.pieces_promotion = pygame.sprite.Group()
            self.promoting = False
    
    def reset_premoves(self):
        for piece in self.pieces_player:
            piece.rect.center = piece.calc_position_screen(piece.row, piece.column)
            piece.rect_square.center = piece.rect.center
            piece.selected = False
            piece.dragging = False
            piece.holding = False

        self.premoves = []
    
    def is_move_ready(self):
        if self.thread is None:
            return False
        return not self.thread.is_alive()

    def play_random_move(self):
        moves = []
        if self.player_to_move == "o":
            for piece in self.pieces_opponent:
                for square in piece.available_squares:
                    moves.append((piece, square))
            if len(moves) == 0:
                self.post_move_processing()
                return
            idx = random.randint(0, len(moves) - 1)
            piece = moves[idx][0]
            square = moves[idx][1]
            piece.make_move(square)
            self.post_move_processing()

    def promote_random_piece(self):
            idx = random.randint(0, 3)
            pieces_promotion_list = list(self.pieces_promotion)
            piece = pieces_promotion_list[idx]
            (row, column) = self.promotion_square
            piece.row = row
            piece.column = column
            self.TABLE_MATRIX[row][column] = piece.name

            pawn = self.matrix_to_piece[((row, column))]
            pawn.kill()

            new_piece = Piece(piece.game, piece.name, piece.image, piece.row, piece.column, piece.names)
            self.matrix_to_piece[((row, column))] = new_piece
            if self.player_to_move == "p":
                self.pieces_player.add(new_piece)            
            else:
                self.pieces_opponent.add(new_piece)

            for piece in self.pieces_promotion:
                piece.kill()
            
            self.pieces_promotion = pygame.sprite.Group()
            self.promoting = False
            
            self.post_move_processing()

    def simulate_move(self, square1, square2):
        (prev_row, prev_column) = square1
        (curr_row, curr_column) = square2

        # Save the piece's name before marking the square as available
        piece_name = self.TABLE_MATRIX[prev_row][prev_column]

        # Mark the previous square as available
        self.TABLE_MATRIX[prev_row][prev_column] = '.'

        # Handle castling by checking if the king moved two squares
        if piece_name in ["K", "k"]:
            # Left castling
            if curr_column + 2 == prev_column:
                ((rook_prev_row, rook_prev_column), (rook_curr_row, rook_curr_column)) = ((curr_row, 0), (curr_row, curr_column + 1))

                rook = self.matrix_to_piece[(rook_prev_row, rook_prev_column)]
                self.TABLE_MATRIX[rook_curr_row][rook_curr_column] = rook.name
                # Updating rook's previous square
                self.TABLE_MATRIX[rook_prev_row][rook_prev_column] = '.'

            # Right castling
            if prev_column + 2 == curr_column:
                ((rook_prev_row, rook_prev_column), (rook_curr_row, rook_curr_column)) = ((curr_row, 7), (curr_row, curr_column - 1))

                rook = self.matrix_to_piece[(rook_prev_row, rook_prev_column)]
                self.TABLE_MATRIX[rook_curr_row][rook_curr_column] = rook.name
                # Updating rook's previous square
                self.TABLE_MATRIX[rook_prev_row][rook_prev_column] = '.'

        # Handle en passant capture by checking if a pawn moved diagonally to an empty square
        if piece_name in ["P", "p"] and prev_column != curr_column and self.TABLE_MATRIX[curr_row][curr_column] == '.':
            if self.TABLE_MATRIX[curr_row + 1][curr_column] in ["P", "p"]:
                self.TABLE_MATRIX[curr_row + 1][curr_column] = '.'
            if self.TABLE_MATRIX[curr_row - 1][curr_column] in ["P", "p"]:
                self.TABLE_MATRIX[curr_row - 1][curr_column] = '.'

        # Update the target square with the piece's name
        self.TABLE_MATRIX[curr_row][curr_column] = piece_name

    # updates available squares after every move for each piece
    def update_available_squares(self):
        if self.player_to_move == "p":
            for piece in self.pieces_opponent:
                piece.update_available_squares()
            for piece in self.pieces_player:
                piece.update_available_squares()
            
            TABLE_MATRIX_ORIGINAL = copy.deepcopy(self.TABLE_MATRIX)
            for piece in self.pieces_player:
                available_squares_new = set()
                for square in piece.available_squares:
                    square_orig = (piece.row, piece.column)
                    self.simulate_move(square_orig, square)
                    #print_table_state()
                    (piece.row, piece.column) = square
                    for piece2 in self.pieces_opponent:
                        piece2.update_available_squares()
                    if not self.in_check():
                        available_squares_new.add(square)
                    self.TABLE_MATRIX = copy.deepcopy(TABLE_MATRIX_ORIGINAL)
                    (piece.row, piece.column) = square_orig
                piece.available_squares = copy.deepcopy(available_squares_new)
                piece.attacking_squares = copy.deepcopy(piece.available_squares)
            
            for piece in self.pieces_opponent:
                piece.update_available_squares()
        else:
            for piece in self.pieces_player:
                piece.update_available_squares()
            for piece in self.pieces_opponent:
                piece.update_available_squares()
            
            TABLE_MATRIX_ORIGINAL = copy.deepcopy(self.TABLE_MATRIX)
            for piece in self.pieces_opponent:
                available_squares_new = set()
                for square in piece.available_squares:
                    square_orig = (piece.row, piece.column)
                    self.simulate_move(square_orig, square)
                    (piece.row, piece.column) = square
                    for piece2 in self.pieces_player:
                        piece2.update_available_squares()
                    if not self.in_check():
                        available_squares_new.add(square)
                    self.TABLE_MATRIX = copy.deepcopy(TABLE_MATRIX_ORIGINAL)
                    (piece.row, piece.column) = square_orig
                piece.available_squares = copy.deepcopy(available_squares_new)
                piece.attacking_squares = copy.deepcopy(piece.available_squares)
            
            for piece in self.pieces_player:
                piece.update_available_squares()

    def print_table_state(self):
        for row in self.TABLE_MATRIX:
            print(*row)
        print("\n")

    def post_move_processing(self):
        if self.promoting:
            return
        piece_move.play()
        # next player
        if self.player_to_move == "p":
            self.player_to_move = "o"
        else:
            self.player_to_move = "p"
            self.move_cooldown = 2
        
        # start clocks
        if len(self.fen) == 2:
            if self.player_to_move == "p":
                self.clock_opponent.locked = False
            else:
                self.clock_player.locked = False
            self.clocks_started = True

        # update fen
        self.scan_fen()
        self.move_index = len(self.fen) - 1
        self.stockfish.set_fen_position(self.fen[-1])

        #self.convert_fen(self.fen[-1])

        self.update_available_squares()
        self.mark_check()
        self.set_game_end_reason()
        if self.player_to_move == "o" and self.game_end_reason is None and self.stockfish_active:
            self.get_move_in_background()
        self.enpassant_square = "-"
        
        if self.clocks_started:
            if self.player_to_move == "p":
                self.clock_opponent.seconds_left += self.increment
            else:
                self.clock_player.seconds_left += self.increment
            self.clock_player.locked = not self.clock_player.locked
            self.clock_opponent.locked = not self.clock_opponent.locked
        # mark algebraic
        self.algebraic.append(self.curr_algebraic)
        self.algebraic_to_text()

    def algebraic_to_text(self):
        self.algebraic_text = ""
        move_number = 1
        for i in range(self.move_index + 1):
            if i % 2 == 1:
                self.algebraic_text += f"{move_number}. "
                self.algebraic_text += f"{self.algebraic[i]} "
                move_number += 1
            else:
                self.algebraic_text += f"{self.algebraic[i]}  "

    def get_best_move(self):
        with self.lock:
            wtime = self.clock_player.seconds_left * 1000 if self.player_color == "w" else self.clock_opponent.seconds_left * 1000
            btime = self.clock_player.seconds_left * 1000 if self.player_color == "b" else self.clock_opponent.seconds_left * 1000
            self.best_move_stockfish = self.stockfish.get_best_move(wtime=min(45*1000, wtime), btime=min(45*1000, btime))

    def get_move_in_background(self):
        self.best_move_stockfish = None
        self.thread = threading.Thread(target=self.get_best_move, daemon=True)
        self.thread.start()

    def mark_check(self):
        if self.player_to_move == "p":
            for piece in self.pieces_player:
                if piece.name in ["K", "k"]:
                    king = piece
                    break
            
            for piece in self.pieces_opponent:
                if (king.row, king.column) in piece.available_squares:
                    rect_check_square.center = king.calc_position_screen(king.row, king.column)
                    self.curr_algebraic += "+"
                    return
        else:
            for piece in self.pieces_opponent:
                if piece.name in ["K", "k"]:
                    king = piece
                    break
            
            for piece in self.pieces_player:
                if (king.row, king.column) in piece.available_squares:
                    rect_check_square.center = king.calc_position_screen(king.row, king.column)
                    self.curr_algebraic += "+"
                    return
        
        rect_check_square.center = (-1, -1)

    def in_check(self):
        if self.player_to_move == "p":
            for piece in self.pieces_player:
                if piece.name in ["K", "k"]:
                    king = piece
                    break
            
            for piece in self.pieces_opponent:
                # while simulating, maybe piece giving a check is overwritten in a TABLE_MATRIX
                if self.TABLE_MATRIX[piece.row][piece.column] not in self.names_opponent:
                    continue
                if (king.row, king.column) in piece.available_squares:
                    return True
            return False
        
        else:
            for piece in self.pieces_opponent:
                if piece.name in ["K", "k"]:
                    king = piece
                    break
            
            for piece in self.pieces_player:
                if self.TABLE_MATRIX[piece.row][piece.column] not in self.names_player:
                    continue
                if (king.row, king.column) in piece.available_squares:
                    return True
            return False

    def checkmate(self):
        if self.player_to_move == "p":
            for piece in self.pieces_player:
                if len(piece.available_squares) > 0:
                    return False
            
            if self.in_check():
                # its mate
                self.curr_algebraic = self.curr_algebraic[:-1] + "#"
                return True
            return False
        else:
            for piece in self.pieces_opponent:
                if len(piece.available_squares) > 0:
                    return False
            if self.in_check():
                # its mate
                self.curr_algebraic = self.curr_algebraic[:-1] + "#"
                return True
            return False

    def stalemate(self):
        if self.player_to_move == "p":
            for piece in self.pieces_player:
                if len(piece.available_squares) > 0:
                    return False
            return not self.in_check()
        else:
            for piece in self.pieces_opponent:
                if len(piece.available_squares) > 0:
                    return False
            return not self.in_check()

    def insufficient_material(self):
        pieces_player_left = len(self.pieces_player)
        pieces_opponent_left = len(self.pieces_opponent)

        # king vs king
        if pieces_player_left == pieces_opponent_left == 1:
            return True

        if pieces_player_left + pieces_opponent_left == 3:
            # king vs king and bishop or king vs king and knight
            for piece in self.pieces_player:
                if piece.name in ["B", "b", "N", "n"]:
                    return True
            for piece in self.pieces_opponent:
                if piece.name in ["B", "b", "N", "n"]:
                    return True
        if pieces_player_left == pieces_opponent_left == 2:
            # get the non king pieces
            for piece in self.pieces_player:
                if piece.name not in ["K", "k"]:
                    piece_player = piece
                    break
            for piece in self.pieces_opponent:
                if piece.name not in ["K", "k"]:
                    piece_opponent = piece
                    break

            # check for two bishops
            # white squares have sum of coordinates being even, blacks odd
            if piece_player.name in ["B", "b"] and piece_opponent.name in ["B", "b"] and (piece_player.row + piece_player.column) % 2 == (piece_opponent.row + piece_opponent.column) % 2:
                return True
            
        return False

    def fifty_move_rule(self):
        return self.halfmoves == 100

    def threefold_repetition(self):
        # checking if fen position without halfmoves and fullmoves happened 3 times
        curr_fen = " ".join(self.fen[-1].split()[:4])
        return self.fen_count[curr_fen] == 3

    def set_game_end_reason(self):
        if self.checkmate():
            self.game_end_reason = "checkmate"
            self.winner = "p" if self.player_to_move == "o" else "o"
        elif self.stalemate(): self.game_end_reason = "stalemate"
        elif self.insufficient_material(): self.game_end_reason = "insufficient material"
        elif self.fifty_move_rule(): self.game_end_reason = "50-move rule"
        elif self.threefold_repetition(): self.game_end_reason = "threefold repetition"

    def scan_fen(self):
        # table is seen from whites perspective
        curr_fen = ""
        blank_squares_counter = 0
        (start, end, step) = (0, 8, 1)
        if self.player_color == "b":
            (start, end, step) = (7, -1, -1)
        
        for row in range(start, end, step):
                curr_fen += "/"
                blank_squares_counter = 0
                for column in range(start, end, step):
                    if self.TABLE_MATRIX[row][column] != '.':
                        if blank_squares_counter > 0:
                            curr_fen += str(blank_squares_counter)
                        curr_fen += self.TABLE_MATRIX[row][column]
                        blank_squares_counter = 0
                    else:
                        blank_squares_counter += 1
                if blank_squares_counter > 0:
                    curr_fen += str(blank_squares_counter)

        # remove first slash
        curr_fen = curr_fen[1:]

        if self.player_to_move == "p":
            if self.player_color == "w":
                curr_fen += " w"
                self.fullmoves += 1
            else:
                curr_fen += " b"
        else:
            if self.player_color == "w":
                curr_fen += " b"
            else:
                curr_fen += " w"
                self.fullmoves += 1
        
        curr_fen += " "

        if not self.K and not self.k and not self.Q and not self.q:
            curr_fen += "-"
        else:
            if self.K: curr_fen += "K"
            if self.Q: curr_fen += "Q"
            if self.k: curr_fen += "k"
            if self.q: curr_fen += "q"
        
        curr_fen += " "
        curr_fen += self.enpassant_square

        # store fen without halfomves and fullmoves
        if curr_fen not in self.fen_count:
            self.fen_count[curr_fen] = 0
        self.fen_count[curr_fen] += 1

        curr_fen += f" {self.halfmoves} {self.fullmoves}"

        self.fen.append(curr_fen)

    def convert_fen(self, fen_string):
        # first destroy everything
        self.TABLE_MATRIX = []
        for i in range(8):
            self.TABLE_MATRIX.append(['.'] * 8)
        for row in range(0, 8):
            for column in range(0, 8):
                if self.matrix_to_piece[(row, column)] is not None:
                    self.matrix_to_piece[(row, column)].kill()
                self.matrix_to_piece[(row, column)] = None
        self.pieces_player = pygame.sprite.Group()
        self.pieces_opponent = pygame.sprite.Group()

        data = fen_string.split("/")

        if self.player_color == "w":
            for row in range(7):
                column = 0
                for c in data[row]:
                    if c.isnumeric():
                        column += int(c)
                        continue
                    elif c.isupper():
                        # white piece
                        piece = Piece(self, c, pygame.image.load(self.route_player + f"{c}.png"), row, column, self.names_player)
                        self.pieces_player.add(piece)
                        self.TABLE_MATRIX[row][column] = c
                        self.matrix_to_piece[(row, column)] = piece
                        column += 1
                    elif c.islower():
                        # black piece
                        piece = Piece(self, c, pygame.image.load(self.route_opponent + f"{c}.png"), row, column, self.names_opponent)
                        self.pieces_opponent.add(piece)
                        self.TABLE_MATRIX[row][column] = c
                        self.matrix_to_piece[(row, column)] = piece
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
                    piece = Piece(self, c, pygame.image.load(self.route_player + f"{c}.png"), row, column, self.names_player)
                    self.pieces_player.add(piece)
                    self.TABLE_MATRIX[row][column] = c
                    self.matrix_to_piece[(row, column)] = piece
                    column += 1
                elif c.islower():
                    # black piece
                    piece = Piece(self, c, pygame.image.load(self.route_opponent + f"{c}.png"), row, column, self.names_opponent)
                    self.pieces_opponent.add(piece)
                    self.TABLE_MATRIX[row][column] = c
                    self.matrix_to_piece[(row, column)] = piece
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
                        piece = Piece(self, c, pygame.image.load(self.route_opponent + f"{c}.png"), 7 - row, column, self.names_opponent)
                        self.pieces_opponent.add(piece)
                        self.TABLE_MATRIX[7 - row][column] = c
                        self.matrix_to_piece[(7 - row, column)] = piece
                        column -= 1
                    elif c.islower():
                        # black piece
                        piece = Piece(self, c, pygame.image.load(self.route_player + f"{c}.png"), 7 - row, column, self.names_player)
                        self.pieces_player.add(piece)
                        self.TABLE_MATRIX[7 - row][column] = c
                        self.matrix_to_piece[(7 - row, column)] = piece
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
                    piece = Piece(self, c, pygame.image.load(self.route_opponent + f"{c}.png"), 7 - row, column, self.names_opponent)
                    self.pieces_opponent.add(piece)
                    self.TABLE_MATRIX[7 - row][column] = c
                    self.matrix_to_piece[(7 - row, column)] = piece
                    column -= 1
                elif c.islower():
                    # black piece
                    piece = Piece(self, c, pygame.image.load(self.route_player + f"{c}.png"), 7 - row, column, self.names_player)
                    self.pieces_player.add(piece)
                    self.TABLE_MATRIX[7 - row][column] = c
                    self.matrix_to_piece[(7 - row, column)] = piece
                    column -= 1
        
        data = rest.split(" ")
        (mover, castling_rights, ep_square, self.halfmoves, self.fullmoves) = (data[0], data[1], data[2], int(data[3]), int(data[4]))

        if not self.IN_PARALLEL_UNIVERSE:
            if self.player_color == "w":
                if mover == "w":
                    self.player_to_move = "p"
                else:
                    self.player_to_move = "o"
            else:
                if mover == "w":
                    self.player_to_move = "o"
                else:
                    self.player_to_move = "p"
        
        if castling_rights == "-":
            self.K = self.Q = self.k = self.q = False
        else:
            for right in castling_rights:
                if right == "K": self.K = True
                if right == "k": self.k = True
                if right == "Q": self.Q = True
                if right == "q": self.q = True

        if not self.IN_PARALLEL_UNIVERSE:
            self.update_available_squares()

    def process_captured_piece(self, piece_name):
        removed = False
        if self.player_to_move == "p":
            for piece in self.captured_pieces_opponent:
                if piece.name == piece_name.upper():
                    self.captured_pieces_opponent.remove(piece)
                    removed = True
                    break
            if not removed:
                piece = Piece(self, piece_name.upper(), pygame.image.load(f"Assets/neutral/{piece_name.upper()}.png"), 0, 0, [])
                piece.image = pygame.transform.smoothscale(piece.image, (f(12), f(12)))
                self.captured_pieces_player.append(piece)
        else:
            for piece in self.captured_pieces_player:
                if piece.name == piece_name.upper():
                    self.captured_pieces_player.remove(piece)
                    removed = True
                    break
            if not removed:
                piece = Piece(self, piece_name.upper(), pygame.image.load(f"Assets/neutral/{piece_name.upper()}.png"), 0, 0, [])
                piece.image = pygame.transform.smoothscale(piece.image, (f(12), f(12)))
                self.captured_pieces_opponent.append(piece)
        
        self.captured_pieces_player.sort(key=lambda piece : -piece_to_value[piece.name])
        x = rect_image_player.right + f(15)
        y = rect_image_player.top + f(25)
        for piece in self.captured_pieces_player:
            piece.rect.topleft = (x, y)
            x += f(12)
        
        if self.advantage > 0:
            self.advantage_x = x + f(5)
        
        self.captured_pieces_opponent.sort(key=lambda piece : -piece_to_value[piece.name])
        x = rect_image_opponent.right + f(15)
        y = rect_image_opponent.top + f(25)
        for piece in self.captured_pieces_opponent:
            piece.rect.topleft = (x, y)
            x += f(12)
        
        if self.advantage < 0:
            self.advantage_x = x + f(5)

class Slider():

    def __init__(self, y):
        self.y = y
        self.height = f(15)
        self.width_panel = WIDTH * 3 / 4
        self.image_panel = pygame.transform.smoothscale(Assets.image_panel, (self.width_panel, self.height))
        self.rect_panel = self.image_panel.get_rect()
        self.rect_panel.center = (int(WIDTH / 2), y)

        self.width_cursor = f(30)
        self.image_cursor = pygame.transform.smoothscale(Assets.image_cursor, (self.width_cursor, self.height))
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
    
    def calc_based_on_cursor(self, home, num):
        # if num is 1, calculate minutes, if 2, increment and 3 strength
        if num == 1: total = len(available_minutes) - 1
        elif num == 2: total = len(available_increments) - 1
        else: total = len(available_strengths) - 1

        unitLength = (self.right_bound - self.left_bound) // total
        i = (self.rect_cursor.x - self.left_bound) // unitLength
        if num == 1:
            home.minutes = available_minutes[i]
        elif num == 2:
            home.increment = available_increments[i]
        else:
            home.strength = available_strengths[i]

class Piece(pygame.sprite.Sprite):
    def __init__(self, game, name, image, row, column, names):
        super().__init__()
        self.game = game
        self.name = name

        self.image = pygame.transform.smoothscale(image, (int(SQUARE_SIZE * 0.7), int(SQUARE_SIZE * 0.7)))  # Scale image
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
        self.rect.x += self.game.SETTINGS_ANIMATION_SPEED
        #self.rect.y += SETTINGS_ANIMATION_SPEED / 2
        self.rect_square.x += self.game.SETTINGS_ANIMATION_SPEED
        #self.rect_square.y += SETTINGS_ANIMATION_SPEED / 2

    # caluclates screen position of a piece based on matrix position
    def calc_position_screen(self, row, column):
        x = self.game.TABLE_X + column * SQUARE_SIZE + SQUARE_SIZE / 2
        y = self.game.TABLE_Y + row * SQUARE_SIZE + SQUARE_SIZE / 2
        return (int(x), int(y))
    
    # calculates row and column for a given screen position
    # inverse function of the calc_position_screen()
    def calc_position_matrix(self, center):
        (x, y) = center
        row = (y + self.game.SCREEN_OFFSET_Y - self.game.TABLE_Y) / SQUARE_SIZE
        column = (x + self.game.SCREEN_OFFSET_X - self.game.TABLE_X) / SQUARE_SIZE
        return (int(row), int(column))
    
    # initializes pairs of (row, column) coordinates of available squares after every move for a current piece
    def update_available_squares(self):
        self.available_squares = set() 
        self.attacking_squares = set() # only difference is when piece is pawn, since pawn attacks diagonally but can move forward

        if self.name == 'P' or self.name == 'p':
            # pawns only go forward
            if self.names == self.game.names_player:
                next_row = self.row - 1
                if next_row >= 0:
                    # square in front of the pawn
                    if self.game.TABLE_MATRIX[self.row - 1][self.column] == '.':
                        self.available_squares.add((self.row - 1, self.column))

                    # two squares from starting position
                    if self.row == 6 and self.game.TABLE_MATRIX[self.row - 2][self.column] == '.':
                        self.available_squares.add((self.row - 2, self.column))

                    # capturing opponents piece, one square diagonally, with bound check

                    # enpassant square
                    if len(self.game.fen) > 0:
                        ep_square = self.game.fen[-1].split(" ")[-3]
                        if ep_square != "-":
                            if self.game.player_color == "w" :
                                row = 7 - (int(ep_square[1]) - 1)
                                column = ord(ep_square[0]) - ord("a")
                            else:
                                row = (int(ep_square[1]) - 1)
                                column = 7 - (ord(ep_square[0]) - ord("a"))
                            if self.row == row + 1 and (self.column == column - 1 or self.column == column + 1):
                                self.available_squares.add((row, column))
                                self.attacking_squares.add((row, column))


                    if self.column - 1 >= 0:
                        capture_left = self.game.TABLE_MATRIX[self.row - 1][self.column - 1]
                        if capture_left not in self.names:
                            self.attacking_squares.add((self.row - 1, self.column - 1))
                            if capture_left != '.':
                                self.available_squares.add((self.row - 1, self.column - 1))
                    if self.column + 1 <= 7:
                        capture_right = self.game.TABLE_MATRIX[self.row - 1][self.column + 1]
                        if capture_right not in self.names:
                            self.attacking_squares.add((self.row - 1, self.column + 1))
                            if capture_right != '.':
                                self.available_squares.add((self.row - 1, self.column + 1))
            else:
                next_row = self.row + 1
                if next_row <= 7:
                    # square in front of the pawn
                    if self.game.TABLE_MATRIX[self.row + 1][self.column] == '.':
                        self.available_squares.add((self.row + 1, self.column))

                    # two squares from starting position
                    if self.row == 1 and self.game.TABLE_MATRIX[self.row + 2][self.column] == '.':
                        self.available_squares.add((self.row + 2, self.column))
                    
                    # capturing opponents piece, one square diagonally, with bound check

                    # enpassant square
                    if len(self.game.fen) > 0:
                        ep_square = self.game.fen[-1].split(" ")[-3]
                        if ep_square != "-":
                            if self.game.player_color == "w":
                                row = 7 - (int(ep_square[1]) - 1)
                                column = ord(ep_square[0]) - ord("a")
                            else:
                                row = (int(ep_square[1]) - 1)
                                column = 7 - (ord(ep_square[0]) - ord("a"))
                            if self.row == row - 1 and (self.column == column - 1 or self.column == column + 1):
                                self.available_squares.add((row, column))
                                self.attacking_squares.add((row, column))
                            
                    if self.column - 1 >= 0:
                        capture_left = self.game.TABLE_MATRIX[self.row + 1][self.column - 1]
                        if capture_left not in self.names:
                            self.attacking_squares.add((self.row + 1, self.column - 1))
                            if capture_left != '.':
                                self.available_squares.add((self.row + 1, self.column - 1))
                    if self.column + 1 <= 7:
                        capture_right = self.game.TABLE_MATRIX[self.row + 1][self.column + 1]
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
                if 0 <= try_row <= 7 and 0 <= try_column <= 7 and self.game.TABLE_MATRIX[try_row][try_column] not in self.names:
                    self.available_squares.add((try_row, try_column))
        
        if self.name == "B" or self.name == 'b':
            # up left
            curr_row = self.row - 1
            curr_column = self.column - 1

            # loop stops when bishop encounters a piece, unlike knight which jumps above pieces
            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                # if current square is not player's and its not a dot -> its capturing square, break after
                if self.game.TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row -= 1
                curr_column -= 1
            
            # up right
            curr_row = self.row - 1
            curr_column = self.column + 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if self.game.TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row -= 1
                curr_column += 1
            
            # down left
            curr_row = self.row + 1
            curr_column = self.column - 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if self.game.TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row += 1
                curr_column -= 1
            
            # down right
            curr_row = self.row + 1
            curr_column = self.column + 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if self.game.TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row += 1
                curr_column += 1

        if self.name == "R" or self.name == 'r':
            # up
            curr_row = self.row - 1
            curr_column = self.column

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if self.game.TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row -= 1
            
            # down
            curr_row = self.row + 1
            curr_column = self.column

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if self.game.TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row += 1
            
            # left
            curr_row = self.row
            curr_column = self.column - 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if self.game.TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_column -= 1
            
            # right
            curr_row = self.row
            curr_column = self.column + 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if self.game.TABLE_MATRIX[curr_row][curr_column] != '.':
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
            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                # if current square is not player's and its not a dot -> its capturing square, break after
                if self.game.TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row -= 1
                curr_column -= 1
            
            # up right
            curr_row = self.row - 1
            curr_column = self.column + 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if self.game.TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row -= 1
                curr_column += 1
            
            # down left
            curr_row = self.row + 1
            curr_column = self.column - 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if self.game.TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row += 1
                curr_column -= 1
            
            # down right
            curr_row = self.row + 1
            curr_column = self.column + 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if self.game.TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row += 1
                curr_column += 1
            
            # up
            curr_row = self.row - 1
            curr_column = self.column

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if self.game.TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row -= 1
            
            # down
            curr_row = self.row + 1
            curr_column = self.column

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if self.game.TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_row += 1
            
            # left
            curr_row = self.row
            curr_column = self.column - 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if self.game.TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_column -= 1
            
            # right
            curr_row = self.row
            curr_column = self.column + 1

            while 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                if self.game.TABLE_MATRIX[curr_row][curr_column] != '.':
                    self.available_squares.add((curr_row, curr_column))
                    break
                self.available_squares.add((curr_row, curr_column))
                curr_column += 1
        
        if self.name == "K" or self.name == "k":
            # get all the attacking squares from other player
            attacked_squares = set()
            if self.names == self.game.names_player:
                for piece in self.game.pieces_opponent:
                    for square in piece.attacking_squares:
                        attacked_squares.add(square)
            else:
                for piece in self.game.pieces_player:
                    for square in piece.attacking_squares:
                        attacked_squares.add(square)

            # handle castling
            if not self.moved and not self.game.in_check():
                # king is on the starting position

                # left castling

                # check if leftmost piece in the row is rook with the same color, and hasnt moved
                if self.game.TABLE_MATRIX[self.row][0] in ["R", "r"] and self.game.TABLE_MATRIX[self.row][0] in self.names and not self.game.matrix_to_piece[(self.row, 0)].moved:
                    # check if all squares between are free and not attacked by pieces
                    free = True
                    curr_column = 1
                    while curr_column < self.column:
                        if self.game.TABLE_MATRIX[self.row][curr_column] != '.' or (self.row, curr_column) in attacked_squares:
                            free = False
                            break
                        curr_column += 1
                    if free:
                        self.available_squares.add((self.row, self.column - 2))
                
                # right castling

                # check if rightmost piece in the row is rook with the same color, and hasnt moved
                if self.game.TABLE_MATRIX[self.row][7] in ["R", "r"] and self.game.TABLE_MATRIX[self.row][7] in self.names and not self.game.matrix_to_piece[(self.row, 7)].moved:
                    # check if all squares between are free and not attacked by pieces
                    free = True
                    curr_column = self.column + 1
                    while curr_column <= 6:
                        if self.game.TABLE_MATRIX[self.row][curr_column] != '.' or (self.row, curr_column) in attacked_squares:
                            free = False
                            break
                        curr_column += 1
                    if free:
                        self.available_squares.add((self.row, self.column + 2))

            # same as queen, but range is only 1 square

            # up left
            curr_row = self.row - 1
            curr_column = self.column - 1

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.add((curr_row, curr_column))
            
            # up right
            curr_row = self.row - 1
            curr_column = self.column + 1

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.add((curr_row, curr_column))
            
            # down left
            curr_row = self.row + 1
            curr_column = self.column - 1

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.add((curr_row, curr_column))
            
            # down right
            curr_row = self.row + 1
            curr_column = self.column + 1

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.add((curr_row, curr_column))
            
            # up
            curr_row = self.row - 1
            curr_column = self.column

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.add((curr_row, curr_column))
            
            # down
            curr_row = self.row + 1
            curr_column = self.column

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.add((curr_row, curr_column))
            
            # left
            curr_row = self.row
            curr_column = self.column - 1

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.add((curr_row, curr_column))
            
            # right
            curr_row = self.row
            curr_column = self.column + 1

            if 0 <= curr_row <= 7 and 0 <= curr_column <= 7 and self.game.TABLE_MATRIX[curr_row][curr_column] not in self.names:
                self.available_squares.add((curr_row, curr_column))

        if self.name not in ["P", "p"]:
            self.attacking_squares = copy.deepcopy(self.available_squares)

    def display_available_squares(self):
        # and also mark selected square
        marked_square = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        marked_square.fill(Assets.DARK_GREEN_TRANSPARENT)

        rect_marked_square = marked_square.get_rect()
        (x, y) = self.calc_position_screen(self.row, self.column)
        rect_marked_square.center = (x, y)

        screen.blit(marked_square, rect_marked_square)

        for (row, column) in self.available_squares:
            (x, y) = self.calc_position_screen(row, column)
            # if its not empty square, then player is capturing
            # marking it green
            if self.game.TABLE_MATRIX[row][column] != '.':
                marked_square.fill(Assets.DARK_GREEN_TRANSPARENT1)
                (x, y) = self.calc_position_screen(row, column)
                rect_marked_square.center = (x, y)
                screen.blit(marked_square, rect_marked_square)
            # else display a dot
            else:
                pygame.draw.circle(screen, Assets.BLACKY1, (x, y), f(7), 0)
    
    def available_move(self, square=None):
        # catches the current (x, y) coordinates of a piece while being dragged accross the board and checks if the chosen square is available
        (row_try, column_try) = self.calc_position_matrix(self.rect_square.center)
        return (row_try, column_try) in self.available_squares if square is None else square in self.available_squares
    
    def make_move(self, square=None):
        
        self.game.curr_algebraic = ""
        if self.name not in ["P", "p"]:
            self.game.curr_algebraic += self.name.upper()
        
        column = self.column + 1 if self.game.player_color == "w" else 8 - self.column
        file = column_to_file[column]
        row = self.row + 1 if self.game.player_color == "b" else 8 - self.row
        self.game.curr_algebraic += (file + str(row))

        # mark previous square as available
        self.game.TABLE_MATRIX[self.row][self.column] = '.'
        self.game.matrix_to_piece[(self.row, self.column)] = None

        (x, y) = self.calc_position_screen(self.row, self.column)
        rect_moving_square_prev.center = (x, y)

        # if it was king or a rook, disable castling rights by alerting that either moved
        if self.name in ["K", "k", "R", "r"]:

            if not self.moved:
                if self.name == "K":
                    # disable both sides white
                    self.game.K = self.game.Q = False
                elif self.name == "k":
                    # disable both sides black
                    self.game.k = self.game.q = False
            
                elif self.name == "R":
                    # check king side by comparing distance to the king
                    if (0 <= self.column + 3 <= 7 and self.game.TABLE_MATRIX[self.row][self.column + 3] == "K") or (0 <= self.column - 3 <= 7 and self.game.TABLE_MATRIX[self.row][self.column - 3] == "K"):
                        self.game.K = False
                    else:
                        self.game.Q = False

                elif self.name == "r":
                    # check king side by comparing distance to the king
                    if (0 <= self.column + 3 <= 7 and self.game.TABLE_MATRIX[self.row][self.column + 3] == "k") or (0 <= self.column - 3 <= 7 and self.game.TABLE_MATRIX[self.row][self.column - 3] == "k"):
                        self.game.k = False
                    else:
                        self.game.q = False
            self.moved = True

        # save previous position to handle castling and en passant
        prev_row = self.row
        prev_column = self.column

        # if the moving square is not explicitely passed as an argument, catch the mouse position
        (self.row, self.column) = self.calc_position_matrix(self.rect_square.center) if square is None else square
        (x, y) = self.calc_position_screen(self.row, self.column)
        rect_moving_square_curr.center = (x, y)

        # check if current piece is waiting in premoves
        in_premoves = False
        for (piece, square) in self.game.premoves:
            if self is piece:
                in_premoves = True
                break
        if not in_premoves:
            self.rect.center = self.calc_position_screen(self.row, self.column)
            self.rect_square.center = self.rect.center

        # mark en passant square
        if self.name in ["P", "p"]:
            self.game.halfmoves = 0
            if abs(prev_row - self.row) == 2:
                if self.game.player_color == "w":
                    # enpassant square (for example e3) is constructed by converting a row to a file and getting the average of the two movement squares
                    # adding 7 to rows cause table begin is up not down
                    self.game.enpassant_square = chr(ord('a') + self.column) + str((7 - prev_row + 7 - self.row) // 2 + 1)
                else:
                    self.game.enpassant_square = chr(ord('a') + 7 - self.column) + str((prev_row + self.row) // 2 + 1)
        
        # capturing enpassant by checking if pawn moved diagonally to an empty square
        if self.name in ["P", "p"] and prev_column != self.column and self.game.TABLE_MATRIX[self.row][self.column] == '.':
            self.game.curr_algebraic += "x"
            if self.game.TABLE_MATRIX[self.row + 1][self.column] in ["P", "p"]:
                self.game.halfmoves = 0
                captured_piece = self.game.matrix_to_piece[((self.row + 1, self.column))]
                if self.names == self.game.names_player:
                    self.game.advantage += piece_to_value[captured_piece.name]
                else:
                    self.game.advantage -= piece_to_value[captured_piece.name]
                self.game.process_captured_piece(captured_piece.name)
                captured_piece.kill()
                self.game.TABLE_MATRIX[self.row + 1][self.column] = '.'
                self.game.matrix_to_piece[(self.row, self.column)] = None
            if self.game.TABLE_MATRIX[self.row - 1][self.column] in ["P", "p"]:
                self.game.halfmoves = 0
                captured_piece = self.game.matrix_to_piece[((self.row - 1, self.column))]
                if self.names == self.game.names_player:
                    self.game.advantage += piece_to_value[captured_piece.name]
                else:
                    self.game.advantage -= piece_to_value[captured_piece.name]
                self.game.process_captured_piece(captured_piece.name)
                captured_piece.kill()
                self.game.TABLE_MATRIX[self.row - 1][self.column] = '.'
                self.game.matrix_to_piece[(self.row, self.column)] = None

        # check if it was capture
        if self.game.TABLE_MATRIX[self.row][self.column] != '.': # if its available move and not empty square -> its capture
            
            piece_capture.play()
            captured_piece = self.game.matrix_to_piece[((self.row, self.column))]
            self.game.curr_algebraic += "x"
            self.game.halfmoves = 0
            if self.names == self.game.names_player:
                self.game.advantage += piece_to_value[captured_piece.name]
            else:
                self.game.advantage -= piece_to_value[captured_piece.name]
            self.game.process_captured_piece(captured_piece.name)

            # disable capturing when rook gets taken
            if self.game.TABLE_MATRIX[self.row][self.column] in ["R", "r"] and not captured_piece.moved:
                if captured_piece.name == "R":
                    # check king side by comparing distance to the king
                    if (0 <= captured_piece.column + 3 <= 7 and self.game.TABLE_MATRIX[captured_piece.row][captured_piece.column + 3] == "K") or (0 <= captured_piece.column - 3 <= 7 and self.game.TABLE_MATRIX[captured_piece.row][captured_piece.column - 3] == "K"):
                        self.game.K = False
                    else:
                        self.game.Q = False

                elif captured_piece.name == "r":
                    # check king side by comparing distance to the king
                    if (0 <= captured_piece.column + 3 <= 7 and self.game.TABLE_MATRIX[captured_piece.row][captured_piece.column + 3] == "k") or (0 <= captured_piece.column - 3 <= 7 and self.game.TABLE_MATRIX[captured_piece.row][captured_piece.column - 3] == "k"):
                        self.game.k = False
                    else:
                        self.game.q = False
            
            captured_piece.kill()
            self.game.matrix_to_piece[(self.row, self.column)] = None
        
        column = self.column + 1 if self.game.player_color == "w" else 8 - self.column
        file = column_to_file[column]
        row = self.row + 1 if self.game.player_color == "b" else 8 - self.row
        self.game.curr_algebraic += (file + str(row))

        # handle castling by checking if king somehow "moved" two squares
        if self.name in ["K", "k"]:
            # left castling
            if self.column + 2 == prev_column:
                ((rook_prev_row, rook_prev_column), (rook_curr_row, rook_curr_column)) = ((self.row, 0), (self.row, self.column + 1))

                if abs(rook_prev_column - rook_curr_column) == 3:
                    self.game.curr_algebraic = "0-0-0"
                else:
                    self.game.curr_algebraic = "0-0"

                rook = self.game.matrix_to_piece[(rook_prev_row, rook_prev_column)]
                # updating rooks current square
                rook.rect.center = rook.calc_position_screen(rook_curr_row, rook_curr_column)
                rook.rect_square.center = rook.rect.center
                (rook.row, rook.column) = rook.calc_position_matrix(rook.rect_square.center)
                self.game.TABLE_MATRIX[rook_curr_row][rook_curr_column] = rook.name
                self.game.matrix_to_piece[(rook_curr_row, rook_curr_column)] = rook
                # updating rooks previous square
                self.game.TABLE_MATRIX[rook_prev_row][rook_prev_column] = '.'
                self.game.matrix_to_piece[(rook_prev_row, rook_prev_column)] = None
                rook.update_available_squares()

            # right castling
            if prev_column + 2 == self.column:
                ((rook_prev_row, rook_prev_column), (rook_curr_row, rook_curr_column)) = ((self.row, 7), (self.row, self.column - 1))

                if abs(rook_prev_column - rook_curr_column) == 3:
                    self.game.curr_algebraic = "0-0-0"
                else:
                    self.game.curr_algebraic = "0-0"

                rook = self.game.matrix_to_piece[(rook_prev_row, rook_prev_column)]
                # updating rooks current square
                rook.rect.center = rook.calc_position_screen(rook_curr_row, rook_curr_column)
                rook.rect_square.center = rook.rect.center
                (rook.row, rook.column) = rook.calc_position_matrix(rook.rect_square.center)
                self.game.TABLE_MATRIX[rook_curr_row][rook_curr_column] = rook.name
                self.game.matrix_to_piece[(rook_curr_row, rook_curr_column)] = rook
                # updating rooks previous square
                self.game.TABLE_MATRIX[rook_prev_row][rook_prev_column] = '.'
                self.game.matrix_to_piece[(rook_prev_row, rook_prev_column)] = None
                rook.update_available_squares()
        
        # if its not a pawn move nor a capture, increment halfmoves
        if not self.name in ["P", "p"] and not self.game.TABLE_MATRIX[self.row][self.column] != '.':
            self.game.halfmoves += 1

        # updating the position matrix
        self.game.TABLE_MATRIX[self.row][self.column] = self.name

        # updating position dictionary
        self.game.matrix_to_piece[(self.row, self.column)] = self

        # handling promotion
        if self.name in ["P", "p"]:
            row = self.row
            if self.row == 0:
                self.game.promotion_square = (self.row, self.column)
                self.game.promoting = not in_premoves
                names_list = ["Q", "R", "N", "B"]
                if self.game.player_color == "b":
                    names_list = [name.lower() for name in names_list]
                for name in names_list:
                    self.game.pieces_promotion.add(Piece(self.game, name, pygame.image.load(self.game.route_player + f"{name}.png"), row, self.column, self.names))
                    row += 1

            if self.row == 7:
                self.game.promotion_square = (self.row, self.column)
                self.game.promoting = not in_premoves
                names_list = ["Q", "R", "N", "B"]
                if self.game.player_color == "w":
                    names_list = [name.lower() for name in names_list]
                for name in names_list:
                    self.game.pieces_promotion.add(Piece(self.game, name, pygame.image.load(self.game.route_opponent + f"{name}.png"), row, self.column, self.names))
                    row -= 1

    def make_premove(self):
        (row, column) = self.calc_position_matrix(self.rect.center)
        piece_below = None
        for piece in self.game.pieces_player:
            if piece is not self and piece.calc_position_matrix(piece.rect.center) == (row, column):
                piece_below = piece
                break
        
        for piece in self.game.pieces_opponent:
            if piece is not self and piece.calc_position_matrix(piece.rect.center) == (row, column):
                piece_below = piece
                break

        if piece_below is not None:
            # render piece in the back off screen
            piece_below.rect.center = (-SQUARE_SIZE, -SQUARE_SIZE)
            piece_below.rect_square.center = (-SQUARE_SIZE, -SQUARE_SIZE)

        self.rect.center = self.calc_position_screen(row, column)
        self.rect_square.center = self.rect.center            
        self.game.premoves.append((self, self.rect.center))

        # castling, gotta move the rook too
        if self.name in ["K", "k"] and not self.moved:
            # left castling
            if column + 2 == self.column:
                ((rook_prev_row, rook_prev_column), (rook_curr_row, rook_curr_column)) = ((self.row, 0), (self.row, column + 1))

                rook = self.game.matrix_to_piece[(rook_prev_row, rook_prev_column)]
                # updating rooks current square
                rook.rect.center = rook.calc_position_screen(rook_curr_row, rook_curr_column)
                rook.rect_square.center = rook.rect.center
            
            # right castling
            if self.column + 2 == column:
                ((rook_prev_row, rook_prev_column), (rook_curr_row, rook_curr_column)) = ((self.row, 7), (self.row, column - 1))

                rook = self.game.matrix_to_piece[(rook_prev_row, rook_prev_column)]
                # updating rooks current square
                rook.rect.center = rook.calc_position_screen(rook_curr_row, rook_curr_column)
                rook.rect_square.center = rook.rect.center

    def handle_event(self, event):
        if self.game.IN_SETTINGS or self.game.IN_PARALLEL_UNIVERSE:
            return
        
        (mouse_x, mouse_y) = pygame.mouse.get_pos()
        mouse_on_piece = self.rect_square.collidepoint((mouse_x, mouse_y))
        left_click = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
        right_click = event.type == pygame.MOUSEBUTTONDOWN and event.button == 3

        # handle premoves
        if self.game.player_to_move == "o" and self.game.stockfish_active:
            if right_click:
                # reset premove queue
                for piece in self.game.pieces_player:
                    piece.rect.center = piece.calc_position_screen(piece.row, piece.column)
                    piece.rect_square.center = piece.rect.center
                    piece.selected = False
                    piece.dragging = False
                    piece.holding = False

                self.game.premoves = []
                return

            if left_click:
                # if out of screen bounds
                if not (self.game.TABLE_X  <= mouse_x <= self.game.TABLE_X + 8 * SQUARE_SIZE and self.game.TABLE_Y <= mouse_y <= self.game.TABLE_Y + 8 * SQUARE_SIZE):
                    return

                if mouse_on_piece:
                    self.selected = True
                    self.holding = True

                # handle making a move by clicking at available square
                elif self.selected:

                    #center = self.calc_position_screen(self.row, self.column)
                    #self.game.premoves.append((None, center))

                    curr_x = max(mouse_x, self.rect.size[0] / 2)
                    curr_x = min(curr_x, WIDTH - self.rect.size[0] / 2)
                    curr_y = max(mouse_y, self.game.TABLE_Y + self.rect.size[1] / 2)
                    curr_y = min(curr_y, self.game.TABLE_Y + 8 * SQUARE_SIZE - self.rect.size[1] / 2)

                    self.rect.center = (curr_x, curr_y)
                    self.rect_square.center = self.rect.center

                    self.selected = False
                    self.dragging = False
                    self.holding = False
                    self.unselecting_downclick = False
                    self.make_premove()
                    
                    return
            
            if event.type == pygame.MOUSEBUTTONUP and mouse_on_piece:
                if self.dragging:
                    #center = self.calc_position_screen(self.row, self.column)
                    #self.game.premoves.append((None, center))
                    self.dragging = False
                    self.selected = False
                    self.make_premove()
                self.holding = False

            if event.type == pygame.MOUSEMOTION and mouse_on_piece and self.holding:
                self.dragging = True

            if self.dragging and self.selected:
                # Update the position of the piece while dragging
                curr_x = max(mouse_x, self.game.SCREEN_OFFSET_X + self.rect.size[0] / 2)
                curr_x = min(curr_x, WIDTH - self.rect.size[0] / 2)
                curr_y = max(mouse_y, self.game.TABLE_Y + self.rect.size[1] / 2)
                curr_y = min(curr_y, self.game.TABLE_Y + 8 * SQUARE_SIZE - self.rect.size[1] / 2)

                self.rect.center = (curr_x, curr_y)
                self.rect_square.center = self.rect.center
                
                return
            return

        # else players turn handling
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
            if not (self.game.TABLE_X  <= mouse_x <= self.game.TABLE_X + 8 * SQUARE_SIZE and self.game.TABLE_Y <= mouse_y <= self.game.TABLE_Y + 8 * SQUARE_SIZE):
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
                curr_y = max(mouse_y, self.game.TABLE_Y + self.rect.size[1] / 2)
                curr_y = min(curr_y, self.game.TABLE_Y + 8 * SQUARE_SIZE - self.rect.size[1] / 2)

                self.rect.center = (curr_x, curr_y)
                self.rect_square.center = self.rect.center

                if self.available_move():
                    self.selected = False
                    self.dragging = False
                    self.holding = False
                    self.unselecting_downclick = False
                    self.make_move()                        
                    self.game.post_move_processing()
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
                    self.game.post_move_processing()
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
            curr_x = max(mouse_x, self.game.SCREEN_OFFSET_X + self.rect.size[0] / 2)
            curr_x = min(curr_x, WIDTH - self.rect.size[0] / 2)
            curr_y = max(mouse_y, self.game.TABLE_Y + self.rect.size[1] / 2)
            curr_y = min(curr_y, self.game.TABLE_Y + 8 * SQUARE_SIZE - self.rect.size[1] / 2)

            self.rect.center = (curr_x, curr_y)
            self.rect_square.center = self.rect.center

    def handle_event_promotion(self, event, premoved=False):
        if self.game.IN_SETTINGS:
            return

        if premoved:
            (row, column) = self.game.promotion_square
            print(self.game.TABLE_MATRIX[row][column])
            pawn = self.game.matrix_to_piece[((row, column))]
            #pawn.kill()

            for piece in self.game.pieces_promotion:
                if piece.name in ["Q", "q"]:
                    queen = piece
                    break

            self.game.curr_algebraic += f"={queen.name.upper()}"

            pawn.name = queen.name
            pawn.image = queen.image
            pawn.row = row
            pawn.column = column
            pawn.selected = False

            self.game.TABLE_MATRIX[row][column] = pawn.name
            # promoting a piece is equivalent to losing a pawn but capturing opponents piece (chosen one), materialwise
            self.game.process_captured_piece(queen.name)
            # lil simulation
            if self.game.player_to_move == "p":
                self.game.player_to_move = "o"
            else:
                self.game.player_to_move = "p"

            self.game.process_captured_piece("p")

            if self.game.player_to_move == "p":
                self.game.player_to_move = "o"
            else:
                self.game.player_to_move = "p"
            
            # update advantage
            if self.names == self.game.names_player:
                self.game.advantage += piece_to_value[self.name]
                self.game.advantage -= piece_to_value["p"]
            else:
                self.game.advantage -= piece_to_value[self.name]
                self.game.advantage += piece_to_value["p"]

            for piece in self.game.pieces_promotion:
                piece.kill()
            
            self.game.pieces_promotion = pygame.sprite.Group()
            self.game.promoting = False
            return
        
        (mouse_x, mouse_y) = pygame.mouse.get_pos()
        mouse_on_piece = self.rect_square.collidepoint((mouse_x, mouse_y))
        left_click = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1

        if left_click and mouse_on_piece:

            (row, column) = self.game.promotion_square

            pawn = self.game.matrix_to_piece[((row, column))]
            #pawn.kill()

            self.game.curr_algebraic += f"={self.name.upper()}"

            pawn.name = self.name
            pawn.image = self.image
            pawn.row = row
            pawn.column = column
            pawn.selected = False

            self.game.TABLE_MATRIX[row][column] = pawn.name

            # promoting a piece is equivalent to losing a pawn but capturing opponents piece (chosen one), materialwise
            self.game.process_captured_piece(self.name)

            # lil simulation
            if self.game.player_to_move == "p":
                self.game.player_to_move = "o"
            else:
                self.game.player_to_move = "p"

            self.game.process_captured_piece("p")

            if self.game.player_to_move == "p":
                self.game.player_to_move = "o"
            else:
                self.game.player_to_move = "p"
            
            # update advantage
            if self.names == self.game.names_player:
                self.game.advantage += piece_to_value[self.name]
                self.game.advantage -= piece_to_value["p"]
            else:
                self.game.advantage -= piece_to_value[self.name]
                self.game.advantage += piece_to_value["p"]

            for piece in self.game.pieces_promotion:
                piece.kill()
            
            self.game.pieces_promotion = pygame.sprite.Group()
            self.game.promoting = False

            self.game.post_move_processing()

class Clock():
    def __init__(self, game, x, y, player):
        self.game = game
        self.start_seconds = game.minutes * 60
        self.seconds_left = self.start_seconds
        self.rect = pygame.Rect(x, y, WIDTH - x - f(10), SQUARE_SIZE * 0.7)
        self.low_time_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        self.low_time_surface.fill((255, 0, 0, 50))
        self.locked = True
        self.player = player
    def draw(self):
        render_color = Assets.WHITE
        if self.locked:
            render_color = Assets.GRAY
        minutes = int(self.seconds_left // 60)
        seconds = self.seconds_left % 60
        if self.seconds_left > 10:
            pygame.draw.rect(screen, render_color, self.rect, width=1)
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
            self.rect.y += self.game.SETTINGS_ANIMATION_SPEED / 4
        else:
            self.rect.y -= self.game.SETTINGS_ANIMATION_SPEED / 4

# manager loop, controls current state: home or gameplay
home = Home()
i = 0
while 1:
    if Game.back_to_home:
        home.run()

    pygame.time.wait(100)
    game = Game(home)
    game_start.play()
    game.run()

    # tracks garbage collection, doesnt affect the game logic
    wk1 = weakref.ref(home)
    wk2 = weakref.ref(game)

    # dereference everything
    for piece in game.pieces_player:
        piece.game = None
    for piece in game.pieces_opponent:
        piece.game = None
    for piece in game.captured_pieces_player:
        piece.game = None
    for piece in game.captured_pieces_opponent:
        piece.game = None
    for piece in game.pieces_promotion:
        piece.game = None
    clocks = [game.clock_player, game.clock_opponent]
    for clockk in clocks:
        clockk.game = None
    
    game = None
    
    #print(wk1(), wk2())
    



