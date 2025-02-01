import pygame
import sys
import copy

pygame.init()

# aspect ratio 9 : 19.5
WIDTH = 450
HEIGHT = 975

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Offline Chess")

# pygame clock, handles fps
clock = pygame.time.Clock()

# ASSETS/GLOBALS

WHITE = (255, 255, 255)
BLACKY = (30, 30, 30)
DARK_GREEN_TRANSPARENT = (0, 50, 0, 50)
DARK_GREEN_TRANSPARENT1 = (0, 50, 0, 25)
YELLOW_TRANSPARENT = (255, 255, 0, 20)
YELLOW_TRANSPARENT1 = (255, 255, 0, 10)
RED_TRANSPARENT = (255, 0, 0, 50)
GRAY = (128, 128, 128)

availableMinutes = [0.25, 0.5, 1, 2, 3, 5, 10, 20, 30, 60, 120, 180]
availableIncrements = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 30, 60]

SQUARE_SIZE = WIDTH / 8

dark_overlay = pygame.Surface((WIDTH, WIDTH))  # Create a surface
dark_overlay.set_alpha(200)  # Set alpha (0 is transparent, 255 is opaque)
dark_overlay.fill((0, 0, 0))  # Fill with black

moving_square_prev = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
moving_square_prev.fill(YELLOW_TRANSPARENT1)
rect_moving_square_prev = moving_square_prev.get_rect()

moving_square_curr = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
moving_square_curr.fill(YELLOW_TRANSPARENT)
rect_moving_square_curr = moving_square_prev.get_rect()

check_square = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
check_square.fill(RED_TRANSPARENT)
rect_check_square = check_square.get_rect()

image_dot = pygame.image.load("Assets/shared/dot.png")
image_dot = pygame.transform.scale(image_dot, (SQUARE_SIZE * 0.7, SQUARE_SIZE * 0.7))
rect_dot = image_dot.get_rect()

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

# calculates new dimensions based on initial ones which are 450*975
# enables rescalling while keeping aspect ratio
def f(x):
    return x * WIDTH / 450

# background image
image_bg = pygame.image.load("Assets/dark/backgrounds/boje1.png")
image_bg = pygame.transform.scale(image_bg, (WIDTH, HEIGHT))

# table
image_table = pygame.image.load("Assets/dark/boards/tiles.png")
image_table = pygame.transform.scale(image_table, (WIDTH, WIDTH))
rect_table = image_table.get_rect()

# kings images home screen
image_K = pygame.image.load("Assets/dark/pieces white/K.png")
image_K = pygame.transform.scale(image_K, (f(100), f(100)))
rect_K = image_K.get_rect()
rect_K.center = (WIDTH / 2 - f(100), HEIGHT - f(100))

image_k = pygame.image.load("Assets/dark/pieces black/k.png")
image_k = pygame.transform.scale(image_k, (f(100), f(100)))
rect_k = image_k.get_rect()
rect_k.center = (WIDTH / 2 + f(100), HEIGHT - f(100))

image_unknown_user = pygame.image.load("Assets/dark/users/unknown user.png")
image_unknown_user = pygame.transform.smoothscale(image_unknown_user, (SQUARE_SIZE * 0.7, SQUARE_SIZE * 0.7 * 93 / 97))
rect_image_player = image_unknown_user.get_rect()
rect_image_opponent = image_unknown_user.get_rect()

image_flag_player = pygame.image.load("Assets/shared/flags/64/unknown.png")
image_flag_player = pygame.transform.scale(image_flag_player, (f(20), f(20)))
rect_flag_player = image_flag_player.get_rect()

image_flag_opponent = pygame.image.load("Assets/shared/flags/64/unknown.png")
image_flag_opponent = pygame.transform.scale(image_flag_opponent, (f(20), f(20)))
rect_flag_opponent = image_flag_opponent.get_rect()

image_settings = pygame.image.load("Assets/dark/options.png")
image_settings = pygame.transform.scale(image_settings, (SQUARE_SIZE * 0.6, SQUARE_SIZE * 0.6 * 55 / 75))
rect_settings = image_settings.get_rect()

image_panel = pygame.image.load("Assets/shared/home/Rectangle 28.png")
image_cursor = pygame.image.load("Assets/shared/home/Rectangle 32.png")

piece_to_value = dict()
for name, value in zip(["P", "N", "B", "R", "Q", "p", "n", "b", "r", "q"], [1, 3, 3, 5, 9, 1, 3, 3, 5, 9]):
    piece_to_value[name] = value

fen_start = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

'''
# try positions
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

#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# CLASSES
class Home:
    def __init__(self):
        self.minutes = 3
        self.increment = 2
        self.slider1 = Slider(f(200))
        # set 3+2 mode manually
        self.slider1.rect_cursor.x += f(120)
        self.slider2 = Slider(f(400))
        self.slider2.rect_cursor.x += f(60)
    
    def run(self):
        while 1:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                self.slider1.handle_event(event)
                self.slider2.handle_event(event)
                
                # handle clicking on kings
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if rect_K.collidepoint(event.pos):
                        self.player_color = "w"
                        return
                    if rect_k.collidepoint(event.pos):
                        self.player_color = "b"
                        return
            
            screen.fill(BLACKY)
            screen.blit(image_bg, (0-f(0), 0-f(0)))

            screen.blit(image_K, rect_K)
            screen.blit(image_k, rect_k)

            self.slider1.draw()
            self.slider1.calc_based_on_cursor(self, 1)
            render_text(f"Minutes per player: {self.minutes}", WIDTH / 2, self.slider1.y - f(40), int(f(20)))

            self.slider2.draw()
            self.slider2.calc_based_on_cursor(self, 2)
            render_text(f"Increment in seconds: {self.increment}", WIDTH / 2, self.slider2.y - f(40), int(f(20)))

            render_text("Choose side", WIDTH / 2, rect_k.center[1] - f(150), int(f(25)))

            pygame.display.flip()
            clock.tick(60)

class Game:
    def __init__(self, home):
        self.player_to_move = "p"
        self.player_color = home.player_color

        self.advantage = 0

        self.minutes = home.minutes
        self.increment = home.increment

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

        rect_moving_square_prev.center = (-1, -1)

        rect_check_square.center = (-1, -1)

        # initializing table matrix, dot represents non occupied square
        self.TABLE_MATRIX = []
        for i in range(8):
            self.TABLE_MATRIX.append(['.'] * 8)

        # fen code, list of strings where every string describes one position
        self.fen = []

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

        rect_table.topleft = (self.TABLE_X, self.TABLE_Y)

        # assuming player is white
        self.route_player = "Assets/dark/pieces white/"
        self.route_opponent = "Assets/dark/pieces black/"

        # SETTING PIECES UP
        self.pieces_player = pygame.sprite.Group()
        self.pieces_opponent = pygame.sprite.Group()

        self.captured_pieces_player = pygame.sprite.Group()
        self.captured_pieces_opponent = pygame.sprite.Group()

        rect_image_player.topleft = (self.SCREEN_OFFSET_X + f(10), self.TABLE_Y + 8 * SQUARE_SIZE + f(15))
        rect_image_opponent.bottomleft = (self.SCREEN_OFFSET_X  + f(10), self.TABLE_Y - f(15))

        rect_flag_player.topleft = (self.SCREEN_OFFSET_X + f(200), rect_image_player.top)

        rect_flag_opponent.topleft = (self.SCREEN_OFFSET_X + f(192), rect_image_opponent.top)

        rect_settings.topleft = (self.SCREEN_OFFSET_X + f(30), self.SCREEN_OFFSET_Y + f(30))

        self.clock_player = Clock(self, self.SCREEN_OFFSET_X + WIDTH - 2 * SQUARE_SIZE - f(20), rect_image_player.top, True)
        self.clock_opponent = Clock(self, self.SCREEN_OFFSET_X + WIDTH - 2 * SQUARE_SIZE - f(20), rect_image_opponent.top, False)

        # assuming player is white
        self.names_player = ['P', 'N', 'B', 'R', 'Q', 'K']
        self.names_opponent = [piece.lower() for piece in self.names_player]

        # if player is indeed black, switch player route to blacks and change piece names to lowercase, also replace king and queen
        if self.player_color == "b":
            self.player_to_move = "o"
            (self.names_player, self.names_opponent) = (self.names_opponent, self.names_player)
            (self.route_player, self.route_opponent) = (self.route_opponent, self.route_player)

        self.fen.append(fen_start)
        self.convert_fen(fen_start)
    
    def run(self):
        # game loop
        while 1:
            # rendering "behind" the gameplay
            screen.fill(BLACKY)
            screen.blit(image_bg, (self.SCREEN_OFFSET_X, self.SCREEN_OFFSET_Y))
            screen.blit(image_table, rect_table)

            if self.SETTINGS_ANIMATION_RUNNING:
                self.SCREEN_OFFSET_X += self.SETTINGS_ANIMATION_SPEED
                rect_table.x += self.SETTINGS_ANIMATION_SPEED
                rect_settings.x += self.SETTINGS_ANIMATION_SPEED
                rect_image_player.x += self.SETTINGS_ANIMATION_SPEED
                rect_image_opponent.x += self.SETTINGS_ANIMATION_SPEED
                rect_flag_player.x += self.SETTINGS_ANIMATION_SPEED
                rect_flag_opponent.x += self.SETTINGS_ANIMATION_SPEED
                rect_moving_square_prev.x += self.SETTINGS_ANIMATION_SPEED
                rect_moving_square_curr.x += self.SETTINGS_ANIMATION_SPEED
                rect_check_square.x += self.SETTINGS_ANIMATION_SPEED

                for piece in self.pieces_player:
                    piece.update_rect_position()
                for piece in self.pieces_opponent:
                    piece.update_rect_position()
                
                for piece in self.pieces_promotion:
                    piece.update_rect_position()
                
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
                    rect_settings_bigger = rect_settings.copy()
                    rect_settings_bigger.width *= 1.5
                    rect_settings_bigger.height *= 1.5
                    rect_settings_bigger.center = rect_settings.center 
                    if rect_settings_bigger.collidepoint(event.pos):
                        self.SETTINGS_ANIMATION_RUNNING = True
                        self.SETTINGS_ANIMATION_SPEED *= -1
                if self.player_to_move == "p":
                    for piece in self.pieces_player:
                        piece.handle_event(event)
                else:
                    for piece in self.pieces_opponent:
                        piece.handle_event(event)
                    
                if self.promoting:
                    for piece in self.pieces_promotion:
                        piece.handle_event_promotion(event)
            
            dt = clock.tick(60) / 1000
            # after 2 moves, lenght will be 3 since starting position is also in fen
            if len(self.fen) == 3:
                if self.player_to_move == "p":
                    self.clock_player.locked = False
                else:
                    self.clock_opponent.locked = False
                self.clocks_started = True
            
            screen.blit(image_settings, rect_settings)

            if rect_moving_square_prev.center[0] >= self.SCREEN_OFFSET_X and rect_moving_square_prev.center[1] >= self.SCREEN_OFFSET_Y:
                screen.blit(moving_square_prev, rect_moving_square_prev)
                screen.blit(moving_square_curr, rect_moving_square_curr)
            
            if rect_check_square.center[0] >= self.SCREEN_OFFSET_X and rect_check_square.center[1] >= self.SCREEN_OFFSET_Y:
                screen.blit(check_square, rect_check_square)

            self.pieces_player.draw(screen)
            self.pieces_opponent.draw(screen)

            # rendering off table stuff
            screen.blit(image_unknown_user, rect_image_player)
            screen.blit(image_unknown_user, rect_image_opponent)

            render_text("Username", rect_image_player.right + f(15), rect_image_player.top + f(1), int(f(14)), True)
            render_text("(3500)", self.SCREEN_OFFSET_X + f(138), rect_image_player.top + f(1), int(f(14)), True, GRAY)
            render_text("Computer", rect_image_opponent.right + f(15), rect_image_opponent.top + f(1), int(f(14)), True)
            render_text("(987)", self.SCREEN_OFFSET_X  + f(138), rect_image_opponent.top + f(1), int(f(14)), True, GRAY)

            screen.blit(image_flag_player, rect_flag_player)
            screen.blit(image_flag_opponent, rect_flag_opponent)

            if self.advantage > 0:
                render_text(f"+{self.advantage}", rect_image_player.right + f(15), rect_image_player.top + f(25), int(f(10)), True)
            elif self.advantage < 0:
                render_text(f"+{-self.advantage}", rect_image_opponent.right + f(15), rect_image_opponent.top + f(25), int(f(10)), True)

            self.clock_player.draw()
            self.clock_opponent.draw()

            if self.promoting:
                # darken the screen
                screen.blit(dark_overlay, (self.TABLE_X + self.SCREEN_OFFSET_X, self.TABLE_Y + self.SCREEN_OFFSET_Y))
                self.pieces_promotion.draw(screen)
            self.clock_player.update(dt)
            self.clock_opponent.update(dt)

            # these situations have to be checked every frame, whereas set_game_reason() gets called only after a move
            if self.clock_player.seconds_left < 0 or self.clock_opponent.seconds_left < 0: self.game_end_reason = "timeout"
            elif self.resigned: self.game_end_reason = "resignation"
            elif self.draw: self.game_end_reason = "mutual agreement"

            if self.game_end_reason is not None:
                print(self.game_end_reason)
                return

            pygame.display.flip()

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
        # next player
        if self.player_to_move == "p":
            self.player_to_move = "o"
        else:
            self.player_to_move = "p"
        
        # update fen history
        if not self.promoting:
            self.scan_fen()
            self.enpassant_square = "-"
        
        self.update_available_squares()
        if self.clocks_started:
            if self.player_to_move == "p":
                self.clock_opponent.seconds_left += self.increment
            else:
                self.clock_player.seconds_left += self.increment
            self.clock_player.locked = not self.clock_player.locked
            self.clock_opponent.locked = not self.clock_opponent.locked
        self.set_game_end_reason()
        self.mark_check()

    def mark_check(self):
        if self.player_to_move == "p":
            for piece in self.pieces_player:
                if piece.name in ["K", "k"]:
                    king = piece
                    break
            
            for piece in self.pieces_opponent:
                if (king.row, king.column) in piece.available_squares:
                    rect_check_square.center = king.calc_position_screen(king.row, king.column)
                    return
        else:
            for piece in self.pieces_opponent:
                if piece.name in ["K", "k"]:
                    king = piece
                    break
            
            for piece in self.pieces_player:
                if (king.row, king.column) in piece.available_squares:
                    rect_check_square.center = king.calc_position_screen(king.row, king.column)
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
            return self.in_check()
        else:
            for piece in self.pieces_opponent:
                if len(piece.available_squares) > 0:
                    return False
            return self.in_check()

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
        if self.checkmate(): self.game_end_reason = "checkmate"
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
        print(self.fen[-1])

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

        self.update_available_squares()

class Slider(pygame.sprite.Sprite):

    def __init__(self, y):
        super().__init__()
        self.y = y
        self.height = f(15)
        self.width_panel = WIDTH * 3 / 4
        self.image_panel = pygame.transform.scale(image_panel, (self.width_panel, self.height))
        self.rect_panel = self.image_panel.get_rect()
        self.rect_panel.center = (int(WIDTH / 2), y)

        self.width_cursor = f(30)
        self.image_cursor = pygame.transform.scale(image_cursor, (self.width_cursor, self.height))
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
        # if num is 1, calculate minutes, else increment
        total = len(availableMinutes) - 1 if num == 1 else len(availableIncrements) - 1
        unitLength = (self.right_bound - self.left_bound) // total
        i = (self.rect_cursor.x - self.left_bound) // unitLength
        if num == 1:
            home.minutes = availableMinutes[i]
        else:
            home.increment = availableIncrements[i]

class Piece(pygame.sprite.Sprite):
    def __init__(self, game, name, image, row, column, names):
        super().__init__()
        self.game = game
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
        self.rect.x += self.game.SETTINGS_ANIMATION_SPEED
        #self.rect.y += SETTINGS_ANIMATION_SPEED / 2
        self.rect_square.x += self.game.SETTINGS_ANIMATION_SPEED
        #self.rect_square.y += SETTINGS_ANIMATION_SPEED / 2

    # caluclates screen position of a piece based on matrix position
    def calc_position_screen(self, row, column):
        x = self.game.TABLE_X + column * SQUARE_SIZE + SQUARE_SIZE / 2 + self.game.SCREEN_OFFSET_X
        y = self.game.TABLE_Y + row * SQUARE_SIZE + SQUARE_SIZE / 2 + self.game.SCREEN_OFFSET_Y
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
            if self.game.TABLE_MATRIX[row][column] != '.':
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

        # handle castling by checking if king somehow "moved" two squares
        if self.name in ["K", "k"]:
            # left castling
            if self.column + 2 == prev_column:
                ((rook_prev_row, rook_prev_column), (rook_curr_row, rook_curr_column)) = ((self.row, 0), (self.row, self.column + 1))

                rook = self.game.matrix_to_piece[(rook_prev_row, rook_prev_column)]
                # updating rooks current square
                rook.rect.center = rook.calc_position_screen(rook_curr_row, rook_curr_column)
                rook.rect_square.center = rook.rect.center
                (rook.row, rook.column) = rook.calc_position_matrix(rook.rect_square.center)
                self.game.TABLE_MATRIX[rook_curr_row][rook_curr_column] = rook.name
                self.game.matrix_to_piece[(rook_curr_row, rook_curr_column)] = rook
                # updating rooks previous square
                self.game.TABLE_MATRIX[rook_prev_row][rook_prev_column] = '.'
                self.game.matrix_to_piece[(rook_prev_row, rook_curr_column)] = None
                rook.update_available_squares()

            # right castling
            if prev_column + 2 == self.column:
                ((rook_prev_row, rook_prev_column), (rook_curr_row, rook_curr_column)) = ((self.row, 7), (self.row, self.column - 1))

                rook = self.game.matrix_to_piece[(rook_prev_row, rook_prev_column)]
                # updating rooks current square
                rook.rect.center = rook.calc_position_screen(rook_curr_row, rook_curr_column)
                rook.rect_square.center = rook.rect.center
                (rook.row, rook.column) = rook.calc_position_matrix(rook.rect_square.center)
                self.game.TABLE_MATRIX[rook_curr_row][rook_curr_column] = rook.name
                self.game.matrix_to_piece[(rook_curr_row, rook_curr_column)] = rook
                # updating rooks previous square
                self.game.TABLE_MATRIX[rook_prev_row][rook_prev_column] = '.'
                self.game.matrix_to_piece[(rook_prev_row, rook_curr_column)] = None
                rook.update_available_squares()

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
            if self.game.TABLE_MATRIX[self.row + 1][self.column] in ["P", "p"]:
                self.game.halfmoves = 0
                captured_piece = self.game.matrix_to_piece[((self.row + 1, self.column))]
                captured_piece.kill()
                self.game.TABLE_MATRIX[self.row + 1][self.column] = '.'
                self.game.matrix_to_piece[(self.row, self.column)] = None
            if self.game.TABLE_MATRIX[self.row - 1][self.column] in ["P", "p"]:
                self.game.halfmoves = 0
                captured_piece = self.game.matrix_to_piece[((self.row - 1, self.column))]
                captured_piece.kill()
                self.game.TABLE_MATRIX[self.row - 1][self.column] = '.'
                self.game.matrix_to_piece[(self.row, self.column)] = None

        self.rect.center = self.calc_position_screen(self.row, self.column)
        self.rect_square.center = self.rect.center

        # check if it was capture
        if self.game.TABLE_MATRIX[self.row][self.column] != '.': # if its available move and not empty square -> its capture
            self.game.halfmoves = 0
            captured_piece = self.game.matrix_to_piece[((self.row, self.column))]
            if self.names == self.game.names_player:
                self.game.advantage += piece_to_value[captured_piece.name]
            else:
                self.game.advantage -= piece_to_value[captured_piece.name]
            print(self.game.advantage)
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
                self.game.promoting = True
                names_list = ["Q", "R", "N", "B"]
                if self.game.player_color == "b":
                    names_list = [name.lower() for name in names_list]
                for name in names_list:
                    self.game.pieces_promotion.add(Piece(self.game, name, pygame.image.load(self.game.route_player + f"{name}.png"), row, self.column, self.names))
                    row += 1
            if self.row == 7:
                self.game.promotion_square = (self.row, self.column)
                self.game.promoting = True
                names_list = ["Q", "R", "N", "B"]
                if self.game.player_color == "w":
                    names_list = [name.lower() for name in names_list]
                for name in names_list:
                    self.game.pieces_promotion.add(Piece(self.game, name, pygame.image.load(self.game.route_opponent + f"{name}.png"), row, self.column, self.names))
                    row -= 1

    def handle_event(self, event):
        if self.game.IN_SETTINGS:
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

    def handle_event_promotion(self, event):
        if self.game.IN_SETTINGS:
            return
        (mouse_x, mouse_y) = pygame.mouse.get_pos()
        mouse_on_piece = self.rect_square.collidepoint((mouse_x, mouse_y))
        left_click = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1

        if left_click and mouse_on_piece:

            (row, column) = self.game.promotion_square
            self.row = row
            self.column = column
            self.game.TABLE_MATRIX[row][column] = self.name

            pawn = self.game.matrix_to_piece[((row, column))]
            pawn.kill()

            new_piece = Piece(self.game, self.name, self.image, self.row, self.column, self.names)
            self.game.matrix_to_piece[((row, column))] = new_piece
            if self.row == 0:
                self.game.pieces_player.add(new_piece)
            elif self.row == 7:
                self.game.pieces_opponent.add(new_piece)

            for piece in self.game.pieces_promotion:
                piece.kill()
            
            self.game.pieces_promotion = pygame.sprite.Group()
            self.game.promoting = False
            self.game.scan_fen()
            
            self.game.post_move_processing()

class Clock(pygame.sprite.Sprite):
    def __init__(self, game, x, y, player):
        super().__init__()
        self.game = game
        self.start_seconds = game.minutes * 60
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
            self.rect.y += self.game.SETTINGS_ANIMATION_SPEED / 4
        else:
            self.rect.y -= self.game.SETTINGS_ANIMATION_SPEED / 4

home = Home()
home.run()

game = Game(home)
game.run()
del game

