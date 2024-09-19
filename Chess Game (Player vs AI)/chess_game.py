import pygame
import subprocess
import time
import os
import sys

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 800
DIMENSION = 8
SQ_SIZE = WIDTH // DIMENSION
MAX_FPS = 15
IMAGES = {}

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)

# Initialize the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess Game")
clock = pygame.time.Clock()




def initialize_stockfish():
    stockfish_path = r"C:\Users\astha\OneDrive\Desktop\trialchess\stockfish\stockfish-windows-x86-64-avx2.exe"
    
    if not os.path.exists(stockfish_path):
        print(f"Stockfish executable not found at {stockfish_path}")
        print("Please make sure the Stockfish executable is in the correct location and has the correct name.")
        sys.exit(1)
    
    try:
        return subprocess.Popen(
            stockfish_path,
            universal_newlines=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as e:
        print(f"Error initializing Stockfish: {e}")
        sys.exit(1)

stockfish_process = initialize_stockfish()

def load_images():
    pieces = ['wp', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bp', 'bR', 'bN', 'bB', 'bQ', 'bK']
    for piece in pieces:
        try:
            IMAGES[piece] = pygame.transform.scale(
                pygame.image.load(f"images/{piece}.png"), (SQ_SIZE, SQ_SIZE)
            )
        except pygame.error:
            print(f"Error loading image: images/{piece}.png")
            print("Please ensure all piece images are in the 'images' folder.")
            sys.exit(1)

class GameState:
    def __init__(self):
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]
        self.white_to_move = True
        self.move_log = []

    def make_move(self, start, end):
        start_row, start_col = start
        end_row, end_col = end
        moved_piece = self.board[start_row][start_col]
        self.board[end_row][end_col] = moved_piece
        self.board[start_row][start_col] = "--"
        self.move_log.append((start, end, moved_piece))
        self.white_to_move = not self.white_to_move

def draw_board(screen):
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            color = WHITE if (row + col) % 2 == 0 else GRAY
            pygame.draw.rect(screen, color, pygame.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def draw_pieces(screen, board):
    for row in range(DIMENSION):
        for col in range(DIMENSION):
            piece = board[row][col]
            if piece != "--":
                screen.blit(IMAGES[piece], pygame.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def get_square_under_mouse(pos):
    x, y = pos
    row = y // SQ_SIZE
    col = x // SQ_SIZE
    return row, col if row >= 0 and row < 8 and col >= 0 and col < 8 else None

def send_to_stockfish(command):
    stockfish_process.stdin.write(f"{command}\n")
    stockfish_process.stdin.flush()

def get_best_move_stockfish(fen):
    send_to_stockfish(f"position fen {fen}")
    send_to_stockfish("go depth 15")
    
    best_move = None
    start_time = time.time()
    while time.time() - start_time < 5:  # Wait for up to 5 seconds
        output = stockfish_process.stdout.readline().strip()
        if output.startswith("bestmove"):
            best_move = output.split()[1]
            break
    
    return best_move

def main():
    load_images()
    game_state = GameState()
    running = True
    selected_square = None
    player_clicks = []

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                location = get_square_under_mouse(pygame.mouse.get_pos())
                if location:
                    if selected_square is None:
                        selected_square = location
                        player_clicks.append(selected_square)
                    else:
                        player_clicks.append(location)
                        if len(player_clicks) == 2:
                            game_state.make_move(player_clicks[0], player_clicks[1])
                            selected_square = None
                            player_clicks = []
                            
                            # AI's turn
                            fen = board_to_fen(game_state.board)
                            best_move = get_best_move_stockfish(fen)
                            if best_move:
                                start = (ord(best_move[1]) - ord('1'), ord(best_move[0]) - ord('a'))
                                end = (ord(best_move[3]) - ord('1'), ord(best_move[2]) - ord('a'))
                                game_state.make_move(start, end)

        screen.fill(pygame.Color("white"))
        draw_board(screen)
        draw_pieces(screen, game_state.board)
        
        if selected_square:
            row, col = selected_square
            pygame.draw.rect(screen, (255, 0, 0, 50), 
                             pygame.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE), 2)

        pygame.display.flip()
        clock.tick(MAX_FPS)

    pygame.quit()
    stockfish_process.terminate()

def board_to_fen(board):
    fen = ""
    for row in board:
        empty = 0
        for piece in row:
            if piece == "--":
                empty += 1
            else:
                if empty > 0:
                    fen += str(empty)
                    empty = 0
                fen += piece[1].lower() if piece[0] == "b" else piece[1]
        if empty > 0:
            fen += str(empty)
        fen += "/"
    fen = fen[:-1]  # remove the last '/'
    return fen + " w KQkq - 0 1"  # Assuming it's white's turn and all castling is allowed

if __name__ == "__main__":
    main()