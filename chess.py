import pygame
import sys
import copy
from bot import Bot  # Import the Bot class
from chess_logic import (
    is_valid_move, make_move, undo_move, in_check, get_all_possible_moves, find_king
)

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 640, 680  # Extra space for buttons
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS

# Colors
WHITE = (245, 245, 220)  # Beige color for white squares
BLACK = (139, 69, 19)    # Brown color for black squares
BLUE = (106, 90, 205)    # Highlight color

# Fonts
FONT = pygame.font.SysFont(None, 24)
LARGE_FONT = pygame.font.SysFont(None, 48)

# Load images
def load_images():
    pieces = ['wp', 'bp', 'wR', 'bR', 'wN', 'bN', 'wB', 'bB',
              'wQ', 'bQ', 'wK', 'bK']
    images = {}
    for piece in pieces:
        images[piece] = pygame.transform.scale(
            pygame.image.load(f'images/{piece}.png'), (SQUARE_SIZE, SQUARE_SIZE))
    return images

# Draw the chess board
def draw_board(screen):
    for row in range(ROWS):
        for col in range(COLS):
            color = WHITE if (row + col) % 2 == 0 else BLACK
            pygame.draw.rect(screen, color, pygame.Rect(
                col*SQUARE_SIZE, row*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

# Draw pieces on the board
def draw_pieces(screen, board, images):
    for row in range(ROWS):
        for col in range(COLS):
            piece = board[row][col]
            if piece != '--':
                screen.blit(images[piece], pygame.Rect(
                    col*SQUARE_SIZE, row*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

# Highlight selected square
def highlight_square(screen, pos):
    if pos != ():
        row, col = pos
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
        s.set_alpha(100)  # Transparency
        s.fill(BLUE)
        screen.blit(s, (col*SQUARE_SIZE, row*SQUARE_SIZE))

# Button class
class Button:
    def __init__(self, text, x, y, width, height, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = (200, 200, 200)
        self.text = text
        self.callback = callback

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        text_surf = FONT.render(self.text, True, (0, 0, 0))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.callback()

# Initial board setup
def create_board():
    board = [
        ['bR', 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR'],
        ['bp'] * 8,
        ['--'] * 8,
        ['--'] * 8,
        ['--'] * 8,
        ['--'] * 8,
        ['wp'] * 8,
        ['wR', 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR']
    ]
    return board

# Main function
def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('2D Chess')

    images = load_images()
    board = create_board()
    selected_square = ()
    player_clicks = []
    running = True

    clock = pygame.time.Clock()

    # Game state variables
    move_log = []
    en_passant_possible = ()
    castling_rights = {
        'w': {'king_side': True, 'queen_side': True},
        'b': {'king_side': True, 'queen_side': True}
    }
    turn = 'w'  # 'w' for white, 'b' for black
    game_over = False
    winner = None

    # Choose who plays as white and black
    player_color = 'w'  # Change to 'b' if you want to play as black
    bot_color = 'b' if player_color == 'w' else 'w'
    bot = Bot(bot_color)

    # Undo button
    undo_button = Button('Undo Move', WIDTH - 120, HEIGHT - 40, 100, 30, lambda: undo_last_move())

    def undo_last_move():
        nonlocal en_passant_possible, castling_rights, turn, game_over, winner
        if move_log:
            undo_move(board, move_log, en_passant_possible, castling_rights)
            turn = 'w' if turn == 'b' else 'b'
            game_over = False
            winner = None

    while running:
        draw_board(screen)
        highlight_square(screen, selected_square)
        draw_pieces(screen, board, images)
        undo_button.draw(screen)

        if game_over:
            text_surf = LARGE_FONT.render(winner, True, (0, 0, 0))
            text_rect = text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(text_surf, text_rect)
        else:
            if in_check(board, turn):
                # Highlight the king or display a warning
                king_pos = find_king(board, turn)
                if king_pos:
                    highlight_square(screen, king_pos)
                check_text = FONT.render('Check!', True, (255, 0, 0))
                screen.blit(check_text, (10, 10))

        pygame.display.flip()

        clock.tick(60)  # Limit to 60 FPS

        if game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            continue  # Skip processing further events if game is over

        if turn == player_color:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    sys.exit()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    location = pygame.mouse.get_pos()
                    col = location[0] // SQUARE_SIZE
                    row = location[1] // SQUARE_SIZE

                    # Handle undo button
                    undo_button.handle_event(event)

                    if location[1] >= HEIGHT - 40:
                        continue  # Clicked outside the board

                    if selected_square == (row, col):
                        # Deselect
                        selected_square = ()
                        player_clicks = []
                    else:
                        selected_square = (row, col)
                        player_clicks.append(selected_square)

                    if len(player_clicks) == 2:
                        start_pos = player_clicks[0]
                        end_pos = player_clicks[1]

                        if is_valid_move(board, start_pos, end_pos, turn, en_passant_possible, castling_rights):
                            # Make the move
                            captured_piece, en_passant_possible, castling_rights = make_move(
                                board, start_pos, end_pos, en_passant_possible, castling_rights, move_log
                            )

                            # Check for pawn promotion
                            piece_moved = board[end_pos[0]][end_pos[1]]
                            if piece_moved[1] == 'p' and (end_pos[0] == 0 or end_pos[0] == 7):
                                board[end_pos[0]][end_pos[1]] = piece_moved[0] + 'Q'  # Promote to Queen

                            # Switch turn
                            turn = bot_color

                            # Check for game over
                            if in_check(board, turn):
                                if not get_all_possible_moves(board, turn, en_passant_possible, castling_rights):
                                    game_over = True
                                    winner = 'White wins by checkmate!' if turn == 'b' else 'Black wins by checkmate!'
                            else:
                                if not get_all_possible_moves(board, turn, en_passant_possible, castling_rights):
                                    game_over = True
                                    winner = 'Draw by stalemate.'
                        else:
                            print("Invalid move!")
                        player_clicks = []
                        selected_square = ()

        else:
            # Bot's turn
            pygame.display.flip()
            # Use copies of game state variables
            move_log_copy = move_log.copy()
            en_passant_possible_copy = en_passant_possible
            castling_rights_copy = copy.deepcopy(castling_rights)
            move = bot.get_move(board, turn, en_passant_possible_copy, castling_rights_copy, move_log_copy)
            if move:
                start_pos, end_pos = move
                # Make the move
                captured_piece, en_passant_possible, castling_rights = make_move(
                    board, start_pos, end_pos, en_passant_possible, castling_rights, move_log
                )

                # Check for pawn promotion
                piece_moved = board[end_pos[0]][end_pos[1]]
                if piece_moved[1] == 'p' and (end_pos[0] == 0 or end_pos[0] == 7):
                    board[end_pos[0]][end_pos[1]] = piece_moved[0] + 'Q'  # Promote to Queen

                # Switch turn
                turn = player_color

                # Check for game over
                if in_check(board, turn):
                    if not get_all_possible_moves(board, turn, en_passant_possible, castling_rights):
                        game_over = True
                        winner = 'Black wins by checkmate!' if turn == 'w' else 'White wins by checkmate!'
                else:
                    if not get_all_possible_moves(board, turn, en_passant_possible, castling_rights):
                        game_over = True
                        winner = 'Draw by stalemate.'
            else:
                print("Bot has no legal moves!")
                game_over = True
                winner = 'Draw by stalemate.'

    pygame.quit()

if __name__ == '__main__':
    main()