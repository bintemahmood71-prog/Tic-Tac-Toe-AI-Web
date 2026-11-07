"""Python AI engine for 4x4 Tic-Tac-Toe (four in a row).

The game logic below is extracted from the original desktop project.
"""
import random

# 1. GAME CONFIGURATION

SIZE = 4
CELLS = SIZE * SIZE

EMPTY, HUMAN, AI = " ", "X", "O"

WIN_SCORE = 100_000
INF = float("inf")
MIN_AI_DELAY = 0.65

COLORS = {
    "bg": "#101827",
    "panel": "#1C293B",
    "cell": "#26364A",
    "hover": "#354A63",
    "x": "#38D9C5",
    "o": "#FF806E",
    "win": "#32D583",
    "purple": "#8175F5",
    "purple_hover": "#9A90FF",
    "purple_press": "#6A5DE0",
    "gold": "#FFD166",
    "text": "#F1F5F9",
    "muted": "#9FB0C7",
    "edge": "#2B3B52",
}

LINE_VALUE = (0, 1, 8, 64)

# All possible winning combinations.
WIN_LINES = (
    [tuple(r * SIZE + c for c in range(SIZE)) for r in range(SIZE)]
    + [tuple(r * SIZE + c for r in range(SIZE)) for c in range(SIZE)]
    + [tuple(i * SIZE + i for i in range(SIZE))]
    + [tuple(i * SIZE + SIZE - 1 - i for i in range(SIZE))]
)

CENTER_CELLS = (5, 6, 9, 10)

# Give strategically useful positions higher priority.
POS_WEIGHT = [
    sum(i in line for line in WIN_LINES)
    for i in range(CELLS)
]

MOVE_ORDER = sorted(
    range(CELLS),
    key=lambda i: -POS_WEIGHT[i]
)

# 2. AI ENGINE

def winner_line(board):
    """Return the winning line or None."""

    for line in WIN_LINES:
        first = board[line[0]]

        if first != EMPTY and all(board[i] == first for i in line):
            return line

    return None


def evaluate(board):
    """Evaluate the board from the AI's perspective."""

    score = 0

    for line in WIN_LINES:
        ai_count = sum(board[i] == AI for i in line)
        human_count = sum(board[i] == HUMAN for i in line)

        if ai_count and human_count:
            continue

        if ai_count:
            score += LINE_VALUE[ai_count]

        elif human_count:
            score -= LINE_VALUE[human_count] + (human_count == 3)

    for i, cell in enumerate(board):
        if cell == AI:
            score += POS_WEIGHT[i]
        elif cell == HUMAN:
            score -= POS_WEIGHT[i]

    return score


def minimax(board, depth, alpha, beta, maximizing):
    """Minimax algorithm with Alpha-Beta pruning."""

    line = winner_line(board)

    if line:
        return (
            WIN_SCORE + depth
            if board[line[0]] == AI
            else -(WIN_SCORE + depth)
        )

    if EMPTY not in board:
        return 0

    if depth == 0:
        return evaluate(board)

    player = AI if maximizing else HUMAN
    best = -INF if maximizing else INF

    for move in MOVE_ORDER:
        if board[move] != EMPTY:
            continue

        board[move] = player

        score = minimax(
            board,
            depth - 1,
            alpha,
            beta,
            not maximizing
        )

        board[move] = EMPTY

        if maximizing:
            best = max(best, score)
            alpha = max(alpha, best)
        else:
            best = min(best, score)
            beta = min(beta, best)

        if alpha >= beta:
            break

    return best


def search_depth(empty_count):
    """Adjust AI search depth according to available moves."""

    if empty_count >= 13:
        return 5
    if empty_count >= 10:
        return 6
    if empty_count == 9:
        return 7

    return empty_count


def completes_move(board, move, player):
    """Check whether a move immediately wins."""

    board[move] = player
    won = winner_line(board) is not None
    board[move] = EMPTY

    return won


def choose_move(board):
    """Choose the best move without modifying the original board."""

    board = list(board)

    empty_cells = [
        i for i, cell in enumerate(board)
        if cell == EMPTY
    ]

    if not empty_cells:
        return None

    # Opening move: prefer the central cells.
    if len(empty_cells) == CELLS:
        return random.choice(CENTER_CELLS)

    # 1. Win immediately if possible.
    for move in empty_cells:
        if completes_move(board, move, AI):
            return move

    # 2. Block the opponent's immediate win.
    for move in empty_cells:
        if completes_move(board, move, HUMAN):
            return move

    # 3. Use Minimax with Alpha-Beta pruning.
    depth = search_depth(len(empty_cells))

    best_score = -INF
    best_moves = []

    for move in MOVE_ORDER:
        if board[move] != EMPTY:
            continue

        board[move] = AI

        score = minimax(
            board,
            depth - 1,
            best_score - 1,
            INF,
            False
        )

        board[move] = EMPTY

        if score > best_score:
            best_score = score
            best_moves = [move]

        elif score == best_score:
            best_moves.append(move)

    return random.choice(best_moves)


