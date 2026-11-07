import sys
import time
import random
import queue
import threading

try:
    import tkinter as tk
    from tkinter import font as tkfont
except ImportError:
    tk = None
    tkfont = None


# ============================================================
# 1. GAME CONFIGURATION
# ============================================================

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


# ============================================================
# 2. AI ENGINE
# ============================================================

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


# ============================================================
# 3. AI SELF-TEST
# ============================================================

def selftest():

    print("Running Tic-Tac-Toe AI tests...")

    board = [EMPTY] * CELLS

    for i in (0, 1, 2):
        board[i] = AI

    assert choose_move(board) == 3

    board = [EMPTY] * CELLS

    for i in (4, 5, 6):
        board[i] = HUMAN

    board[0] = AI

    assert choose_move(board) == 7

    print("[OK] Winning move detection")
    print("[OK] Opponent threat blocking")

    def play(ai_first, opponent):
        board = [EMPTY] * CELLS
        turn = AI if ai_first else HUMAN
        worst_time = 0

        while True:

            if turn == AI:
                start = time.time()
                move = choose_move(board)
                worst_time = max(worst_time, time.time() - start)
                board[move] = AI

            else:
                board[opponent(board)] = HUMAN

            line = winner_line(board)

            if line:
                return board[line[0]], worst_time

            if EMPTY not in board:
                return "draw", worst_time

            turn = HUMAN if turn == AI else AI

    def random_opponent(board):
        return random.choice([
            i for i in range(CELLS)
            if board[i] == EMPTY
        ])

    def ai_opponent(board):
        swapped = [
            HUMAN if c == AI else AI if c == HUMAN else EMPTY
            for c in board
        ]
        return choose_move(swapped)

    results = {"X": 0, "O": 0, "draw": 0}
    worst = 0

    for game in range(60):
        result, elapsed = play(game % 2 == 0, random_opponent)
        results[result] += 1
        worst = max(worst, elapsed)

    print("Against random player (60 games):", results)
    print(f"Slowest AI move: {worst:.2f}s")

    results = {"X": 0, "O": 0, "draw": 0}

    for game in range(6):
        result, elapsed = play(game % 2 == 0, ai_opponent)
        results[result] += 1

    print("Against another AI (6 games):", results)
    print("All tests completed.")


# ============================================================
# 4. SOUND MANAGER
# ============================================================

class SoundManager:

    PATTERNS = {
        "place": [(660, 60)],
        "ai": [(440, 70)],
        "win": [(523, 110), (659, 110), (784, 220)],
        "lose": [(392, 160), (330, 160), (262, 280)],
        "draw": [(440, 130), (440, 130)],
        "click": [(880, 30)],
    }

    def __init__(self, root):
        self.root = root
        self.enabled = True

        try:
            import winsound
            self.winsound = winsound
        except ImportError:
            self.winsound = None

    def play(self, kind):

        if not self.enabled:
            return

        if self.winsound:

            def play_sequence():
                for frequency, duration in self.PATTERNS.get(kind, []):
                    try:
                        self.winsound.Beep(frequency, duration)
                    except Exception:
                        break

            threading.Thread(
                target=play_sequence,
                daemon=True
            ).start()

        elif kind in ("win", "lose", "draw"):
            try:
                self.root.bell()
            except tk.TclError:
                pass


# ============================================================
# 5. CUSTOM BUTTON
# ============================================================

if tk is not None:

    class FlatButton(tk.Label):

        def __init__(
            self, master, text, command,
            bg, hover, press,
            fg=COLORS["text"], **kwargs
        ):

            super().__init__(
                master,
                text=text,
                bg=bg,
                fg=fg,
                cursor="hand2",
                padx=10,
                pady=10,
                **kwargs
            )

            self.bg = bg
            self.hover = hover
            self.press = press
            self.command = command

            self.bind("<Enter>", lambda e: self.config(bg=self.hover))
            self.bind("<Leave>", lambda e: self.config(bg=self.bg))
            self.bind("<ButtonPress-1>", lambda e: self.config(bg=self.press))
            self.bind("<ButtonRelease-1>", self.release)

        def release(self, event):

            inside = (
                0 <= event.x < self.winfo_width()
                and 0 <= event.y < self.winfo_height()
            )

            self.config(bg=self.hover if inside else self.bg)

            if inside:
                self.command()


# ============================================================
# 6. MAIN APPLICATION
# ============================================================

    class App:

        BASE_FONTS = {
             "title": (40, "bold"),
             "subtitle": (16, "normal"),
             "badge": (46, "bold"),
             "turn": (22, "bold"),
             "think": (16, "bold"),
             "score_num": (38, "bold"),
             "score_lbl": (13, "bold"),
             "status": (18, "normal"),
             "button": (17, "bold"),
             "hint": (13, "normal"),
        }       
        def __init__(self, root):

            self.root = root

            root.title("Tic-Tac-Toe")
            root.configure(bg=COLORS["bg"])
            root.minsize(900, 600)

            self.create_fonts()

            self.sound = SoundManager(root)

            self.scores = {
                HUMAN: 0,
                AI: 0,
                "draw": 0
            }

            self.starter = HUMAN
            self.round_id = 0
            self.fullscreen = False

            self.last_size = (0, 0)
            self.status_token = 0
            self.think_token = 0

            self.build_ui()
            self.bind_keys()

            self.toggle_fullscreen(True)
            self.start_round()

        # ----------------------------------------------------
        # FONT MANAGEMENT
        # ----------------------------------------------------

        def create_fonts(self):

            families = set(tkfont.families(self.root))

            family = next(
                (f for f in (
                    "Segoe UI",
                    "SF Pro Display",
                    "Helvetica Neue",
                    "Ubuntu",
                    "Noto Sans",
                    "DejaVu Sans",
                    "Arial"
                ) if f in families),
                "TkDefaultFont"
            )

            self.fonts = {
                name: tkfont.Font(
                    family=family,
                    size=size,
                    weight=weight
                )
                for name, (size, weight) in self.BASE_FONTS.items()
            }

        # ----------------------------------------------------
        # UI HELPERS
        # ----------------------------------------------------

        def card(self, parent, **grid):

            frame = tk.Frame(
                parent,
                bg=COLORS["panel"],
                highlightbackground=COLORS["edge"],
                highlightthickness=1
            )

            frame.grid(sticky="nsew", pady=7, **grid)

            return frame

        def build_ui(self):

            root = self.root

            root.grid_columnconfigure(0, weight=1)
            root.grid_rowconfigure(1, weight=1)

            # Header
            header = tk.Frame(root, bg=COLORS["bg"])
            header.grid(row=0, column=0, sticky="ew", pady=(14, 4))

            tk.Label(
                header,
                text="TIC-TAC-TOE",
                bg=COLORS["bg"],
                fg=COLORS["text"],
                font=self.fonts["title"]
            ).pack()

            tk.Label(
                header,
                text="Connect four in a row before the AI does",
                bg=COLORS["bg"],
                fg=COLORS["muted"],
                font=self.fonts["subtitle"]
            ).pack()

            tk.Frame(
                header,
                bg=COLORS["purple"],
                height=3,
                width=90
            ).pack(pady=(8, 0))

            # Main content
            content = tk.Frame(root, bg=COLORS["bg"])

            content.grid(
                row=1,
                column=0,
                sticky="nsew",
                padx=20
            )

            content.grid_columnconfigure(0, weight=3)
            content.grid_columnconfigure(1, weight=2, minsize=360)
            content.grid_rowconfigure(0, weight=1)

            # Game board
            self.canvas = tk.Canvas(
                content,
                bg=COLORS["bg"],
                highlightthickness=0
            )

            self.canvas.grid(
                row=0,
                column=0,
                sticky="nsew",
                padx=(0, 14)
            )

            self.canvas.bind("<Configure>", lambda e: self.draw())
            self.canvas.bind("<Motion>", self.on_motion)
            self.canvas.bind("<Leave>", self.on_leave)
            self.canvas.bind("<Button-1>", self.on_click)

            # Dashboard
            panel = tk.Frame(content, bg=COLORS["bg"])
            panel.grid(row=0, column=1, sticky="nsew")

            panel.grid_columnconfigure(0, weight=1)
            panel.grid_rowconfigure(2, weight=1)

            self.panel = panel

            self.build_turn_card(panel)
            self.build_scoreboard(panel)
            self.build_status(panel)
            self.build_buttons(panel)

            # Footer
            tk.Label(
                root,
                text=(
                    "F11 Full Screen  ·  Esc Exit  ·  "
                    "N New Round  ·  R Reset Scores  ·  M Sound"
                ),
                bg=COLORS["bg"],
                fg=COLORS["muted"],
                font=self.fonts["hint"]
            ).grid(row=2, column=0, pady=(2, 8))

            root.bind("<Configure>", self.on_resize)

        def build_turn_card(self, panel):

            card = self.card(panel, row=0, column=0)
            card.grid_columnconfigure(1, weight=1)

            self.badge = tk.Label(
                card,
                text="X",
                width=2,
                bg=COLORS["panel"],
                fg=COLORS["x"],
                font=self.fonts["badge"]
            )

            self.badge.grid(
                row=0, column=0, rowspan=2,
                padx=(14, 6), pady=8
            )

            self.turn_lbl = tk.Label(
                card,
                text="",
                anchor="w",
                bg=COLORS["panel"],
                fg=COLORS["text"],
                font=self.fonts["turn"]
            )

            self.turn_lbl.grid(
                row=0, column=1,
                sticky="sew", padx=6, pady=(10, 0)
            )

            self.think_lbl = tk.Label(
                card,
                text="",
                anchor="w",
                bg=COLORS["panel"],
                fg=COLORS["o"],
                font=self.fonts["think"]
            )

            self.think_lbl.grid(
                row=1, column=1,
                sticky="new", padx=6, pady=(0, 10)
            )

        def build_scoreboard(self, panel):

            card = self.card(panel, row=1, column=0)

            self.score_nums = {}

            entries = (
                (HUMAN, "YOU (X)", COLORS["x"]),
                ("draw", "DRAWS", COLORS["gold"]),
                (AI, "COMPUTER (O)", COLORS["o"])
            )

            for col, (key, name, color) in enumerate(entries):

                card.grid_columnconfigure(
                    col, weight=1, uniform="score"
                )

                tk.Label(
                    card,
                    text=name,
                    bg=COLORS["panel"],
                    fg=COLORS["muted"],
                    font=self.fonts["score_lbl"]
                ).grid(row=0, column=col, pady=(10, 0))

                number = tk.Label(
                    card,
                    text="0",
                    bg=COLORS["panel"],
                    fg=color,
                    font=self.fonts["score_num"]
                )

                number.grid(row=1, column=col, pady=(0, 8))

                self.score_nums[key] = number

        def build_status(self, panel):

            card = self.card(panel, row=2, column=0)

            card.grid_columnconfigure(0, weight=1)
            card.grid_rowconfigure(0, weight=1)

            self.status = tk.Label(
                card,
                text="",
                bg=COLORS["panel"],
                fg=COLORS["text"],
                font=self.fonts["status"],
                justify="center",
                wraplength=300
            )

            self.status.grid(
                row=0, column=0,
                sticky="nsew",
                padx=12, pady=10
            )

            self.status.bind(
                "<Configure>",
                lambda e: self.status.config(
                    wraplength=max(120, e.width - 8)
                )
            )

        def build_buttons(self, panel):

            card = self.card(panel, row=3, column=0)

            card.grid_columnconfigure(
                (0, 1), weight=1, uniform="buttons"
            )

            button_font = self.fonts["button"]

            buttons = (
                ("New Round", self.new_round,
                 COLORS["purple"], COLORS["purple_hover"],
                 COLORS["purple_press"]),

                ("Reset Scores", self.reset_scores,
                 COLORS["cell"], COLORS["hover"],
                 COLORS["edge"]),

                ("Sound: On", self.toggle_sound,
                 COLORS["cell"], COLORS["hover"],
                 COLORS["edge"]),

                ("Exit Full Screen", self.toggle_fullscreen,
                 COLORS["cell"], COLORS["hover"],
                 COLORS["edge"])
            )

            self.btn_new = None
            self.btn_reset = None
            self.btn_sound = None
            self.btn_full = None

            for index, (name, command, bg, hover, press) in enumerate(buttons):

                button = FlatButton(
                    card,
                    name,
                    command,
                    bg,
                    hover,
                    press,
                    font=button_font
                )

                button.grid(
                    row=index // 2,
                    column=index % 2,
                    sticky="ew",
                    padx=8,
                    pady=6
                )

                if index == 0:
                    self.btn_new = button
                elif index == 1:
                    self.btn_reset = button
                elif index == 2:
                    self.btn_sound = button
                else:
                    self.btn_full = button

        # ----------------------------------------------------
        # KEYBOARD CONTROLS
        # ----------------------------------------------------

        def bind_keys(self):

            self.root.bind(
                "<F11>",
                lambda e: self.toggle_fullscreen()
            )

            self.root.bind(
                "<Escape>",
                lambda e: self.toggle_fullscreen(False)
                if self.fullscreen else None
            )

            self.root.bind("<Key-n>", lambda e: self.new_round())
            self.root.bind("<Key-r>", lambda e: self.reset_scores())
            self.root.bind("<Key-m>", lambda e: self.toggle_sound())

        # ----------------------------------------------------
        # RESPONSIVE WINDOW
        # ----------------------------------------------------

        def on_resize(self, event):

            if event.widget is not self.root:
                return

            size = (event.width, event.height)

            if size == self.last_size:
                return

            self.last_size = size

            scale = max(
                     0.75,
                    min(
                        1.5,
                    min(
                        event.height / 800,
                        event.width / 1280 * 1.15
                      )
                    )
                )
            

            for name, (base, _) in self.BASE_FONTS.items():
                self.fonts[name].configure(
                    size=max(8, int(base * scale))
                )

        def toggle_fullscreen(self, force=None):

            self.fullscreen = (
                not self.fullscreen if force is None
                else bool(force)
            )

            try:
                self.root.attributes(
                    "-fullscreen",
                    self.fullscreen
                )
            except tk.TclError:
                pass

            if not self.fullscreen:

                sw = self.root.winfo_screenwidth()
                sh = self.root.winfo_screenheight()

                width = min(1180, sw - 80)
                height = min(780, sh - 120)

                self.root.geometry(
                    f"{width}x{height}+"
                    f"{(sw-width)//2}+"
                    f"{max(0, (sh-height)//2-20)}"
                )

            if hasattr(self, "btn_full"):
                self.btn_full.config(
                    text=(
                        "Exit Full Screen"
                        if self.fullscreen
                        else "Full Screen"
                    )
                )

        def toggle_sound(self):

            self.sound.enabled = not self.sound.enabled

            self.btn_sound.config(
                text=(
                    "Sound: On"
                    if self.sound.enabled
                    else "Sound: Off"
                )
            )

            self.sound.play("click")

        # ----------------------------------------------------
        # GAME STATE
        # ----------------------------------------------------

        def start_round(self):

            self.round_id += 1

            self.board = [EMPTY] * CELLS
            self.game_over = False
            self.thinking = False

            self.win_cells = ()
            self.flash_on = False
            self.anim = {}
            self.hover = -1

            self.border = COLORS["purple"]
            self.turn = self.starter

            self.refresh_scores()
            self.status.config(fg=COLORS["text"])

            self.draw()
            self.update_turn_ui()

            if self.turn == AI:
                self.start_ai()

        def new_round(self):

            self.sound.play("click")

            self.starter = (
                AI if self.starter == HUMAN else HUMAN
            )

            self.start_round()

        def reset_scores(self):

            self.sound.play("click")

            self.scores = {
                HUMAN: 0,
                AI: 0,
                "draw": 0
            }

            self.starter = HUMAN
            self.start_round()

        def refresh_scores(self):

            for key, label in self.score_nums.items():
                label.config(text=str(self.scores[key]))

        def set_status(self, message, color=None):

            self.status_token += 1

            self.status.config(
                text=message,
                fg=color or COLORS["text"]
            )

        def update_turn_ui(self):

            if self.turn == HUMAN:

                self.badge.config(
                    text="X",
                    fg=COLORS["x"]
                )

                self.turn_lbl.config(text="Your turn")
                self.think_lbl.config(text="")

                self.set_status(
                    "Your move - pick any empty cell."
                )

            else:

                self.badge.config(
                    text="O",
                    fg=COLORS["o"]
                )

                self.turn_lbl.config(text="Computer's turn")

                self.set_status(
                    "The computer is thinking...",
                    COLORS["muted"]
                )

        # ----------------------------------------------------
        # BOARD GEOMETRY
        # ----------------------------------------------------

        def geometry(self):

            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()

            size = max(100, min(width, height) - 12)

            ox = (width - size) / 2
            oy = (height - size) / 2

            gap = size * 0.026
            cell_size = (size - (SIZE + 1) * gap) / SIZE

            return ox, oy, size, gap, cell_size

        def cell_rect(self, index):

            ox, oy, size, gap, cell_size = self.geometry()

            row, col = divmod(index, SIZE)

            x1 = ox + gap + col * (cell_size + gap)
            y1 = oy + gap + row * (cell_size + gap)

            return (
                x1,
                y1,
                x1 + cell_size,
                y1 + cell_size
            )

        def cell_at(self, x, y):

            for index in range(CELLS):

                x1, y1, x2, y2 = self.cell_rect(index)

                if x1 <= x <= x2 and y1 <= y <= y2:
                    return index

            return -1

        # ----------------------------------------------------
        # DRAWING HELPERS
        # ----------------------------------------------------

        @staticmethod
        def round_rect(canvas, x1, y1, x2, y2, radius, **kwargs):

            points = [
                x1 + radius, y1,
                x2 - radius, y1,
                x2, y1,
                x2, y1 + radius,
                x2, y2 - radius,
                x2, y2,
                x2 - radius, y2,
                x1 + radius, y2,
                x1, y2,
                x1, y2 - radius,
                x1, y1 + radius,
                x1, y1
            ]

            return canvas.create_polygon(
                points,
                smooth=True,
                **kwargs
            )

        def draw(self):

            canvas = self.canvas

            if canvas.winfo_width() < 20 or canvas.winfo_height() < 20:
                return

            canvas.delete("all")

            ox, oy, size, gap, cell_size = self.geometry()

            self.round_rect(
                canvas,
                ox, oy,
                ox + size, oy + size,
                size * 0.03,
                fill=COLORS["panel"],
                outline=self.border,
                width=3
            )

            playable = (
                not self.game_over
                and self.turn == HUMAN
                and not self.thinking
            )

            for index, symbol in enumerate(self.board):

                x1, y1, x2, y2 = self.cell_rect(index)

                in_win = index in self.win_cells

                if in_win and self.flash_on:
                    fill = COLORS["win"]

                elif symbol == EMPTY and index == self.hover and playable:
                    fill = COLORS["hover"]

                else:
                    fill = COLORS["cell"]

                self.round_rect(
                    canvas,
                    x1, y1, x2, y2,
                    cell_size * 0.12,
                    fill=fill,
                    outline=COLORS["win"] if in_win else fill,
                    width=2 if in_win else 1
                )

                if symbol != EMPTY:

                    color = (
                        COLORS["bg"] if fill == COLORS["win"]
                        else COLORS["x"] if symbol == HUMAN
                        else COLORS["o"]
                    )

                    self.draw_symbol(
                        canvas,
                        symbol,
                        (x1 + x2) / 2,
                        (y1 + y2) / 2,
                        cell_size,
                        self.anim.get(index, 1.0),
                        color
                    )

        def draw_symbol(self, canvas, symbol, cx, cy, size, progress, color):

            ease = 1 - (1 - progress) ** 3

            width = max(4, size * 0.09)
            half = size * 0.26 * (0.7 + 0.3 * ease)

            if symbol == HUMAN:

                first = min(1.0, ease * 2)
                second = max(0.0, ease * 2 - 1)

                x1, y1 = cx - half, cy - half

                canvas.create_line(
                    x1, y1,
                    x1 + 2 * half * first,
                    y1 + 2 * half * first,
                    fill=color,
                    width=width,
                    capstyle="round"
                )

                if second > 0:

                    canvas.create_line(
                        cx + half, cy - half,
                        cx + half - 2 * half * second,
                        cy - half + 2 * half * second,
                        fill=color,
                        width=width,
                        capstyle="round"
                    )

            else:

                box = (
                    cx - half,
                    cy - half,
                    cx + half,
                    cy + half
                )

                if ease >= 0.999:

                    canvas.create_oval(
                        *box,
                        outline=color,
                        width=width
                    )

                else:

                    canvas.create_arc(
                        *box,
                        start=90,
                        extent=-359.9 * ease,
                        style="arc",
                        outline=color,
                        width=width
                    )

        # ----------------------------------------------------
        # CELL ANIMATION
        # ----------------------------------------------------

        def animate_cell(self, index, round_id):

            if round_id != self.round_id:
                return

            progress = self.anim.get(index, 0.0) + 0.1

            if progress >= 1.0:

                self.anim.pop(index, None)
                self.draw()
                return

            self.anim[index] = progress
            self.draw()

            self.root.after(
                16,
                lambda: self.animate_cell(index, round_id)
            )

        # ----------------------------------------------------
        # MOUSE CONTROLS
        # ----------------------------------------------------

        def on_motion(self, event):

            index = self.cell_at(event.x, event.y)

            if index != self.hover:
                self.hover = index
                self.draw()

            playable = (
                not self.game_over
                and self.turn == HUMAN
                and not self.thinking
            )

            valid = (
                playable
                and index >= 0
                and self.board[index] == EMPTY
            )

            self.canvas.config(
                cursor="hand2" if valid else ""
            )

        def on_leave(self, event):

            if self.hover != -1:
                self.hover = -1
                self.draw()

        def on_click(self, event):

            if self.game_over or self.turn != HUMAN or self.thinking:
                return

            index = self.cell_at(event.x, event.y)

            if index < 0:
                return

            if self.board[index] != EMPTY:

                self.set_status(
                    "That cell is already taken - choose an empty one.",
                    COLORS["gold"]
                )

                token = self.status_token

                self.root.after(
                    1400,
                    lambda: self.restore_status(token)
                )

                return

            self.place(index, HUMAN)

        def restore_status(self, token):

            if (
                token == self.status_token
                and not self.game_over
                and self.turn == HUMAN
            ):
                self.set_status(
                    "Your move - pick any empty cell."
                )

        # ----------------------------------------------------
        # GAME MOVES
        # ----------------------------------------------------

        def place(self, index, player):

            self.board[index] = player
            self.anim[index] = 0.0

            self.sound.play(
                "place" if player == HUMAN else "ai"
            )

            self.animate_cell(index, self.round_id)

            line = winner_line(self.board)

            if line:

                self.end_game(player, line)

            elif EMPTY not in self.board:

                self.end_game("draw", ())

            else:

                self.turn = AI if player == HUMAN else HUMAN
                self.update_turn_ui()

                if self.turn == AI:
                    self.start_ai()

        # ----------------------------------------------------
        # AI THREAD
        # ----------------------------------------------------

        def start_ai(self):

            self.thinking = True
            self.turn = AI

            self.think_token += 1
            token = self.think_token

            self.think_tick(token, 0)

            round_id = self.round_id
            snapshot = list(self.board)
            result_queue = queue.Queue()

            def calculate():
                result_queue.put(choose_move(snapshot))

            threading.Thread(
                target=calculate,
                daemon=True
            ).start()

            self.poll_ai(
                round_id,
                result_queue,
                time.time(),
                None
            )

        def poll_ai(self, round_id, result_queue, started, move):

            if round_id != self.round_id:
                return

            if move is None:

                try:
                    move = result_queue.get_nowait()

                except queue.Empty:

                    self.root.after(
                        40,
                        lambda: self.poll_ai(
                            round_id,
                            result_queue,
                            started,
                            None
                        )
                    )

                    return

            if time.time() - started < MIN_AI_DELAY:

                self.root.after(
                    40,
                    lambda: self.poll_ai(
                        round_id,
                        result_queue,
                        started,
                        move
                    )
                )

                return

            self.thinking = False
            self.think_token += 1

            self.think_lbl.config(text="")

            if move is not None:
                self.place(move, AI)

        def think_tick(self, token, count):

            if token != self.think_token or not self.thinking:
                return

            dots = (
                "●○○",
                "○●○",
                "○○●",
                "○●○"
            )[count % 4]

            self.think_lbl.config(
                text=f"AI thinking  {dots}"
            )

            self.badge.config(
                fg=COLORS["o"] if count % 2 == 0
                else COLORS["panel"]
            )

            self.root.after(
                160,
                lambda: self.think_tick(token, count + 1)
            )

        # ----------------------------------------------------
        # GAME END
        # ----------------------------------------------------

        def end_game(self, result, line):

            self.game_over = True
            self.thinking = False

            self.think_token += 1
            self.think_lbl.config(text="")

            self.win_cells = tuple(line)

            self.scores[result] += 1
            self.refresh_scores()

            if result == HUMAN:

                self.badge.config(
                    text="✔",
                    fg=COLORS["win"]
                )

                self.turn_lbl.config(text="You win!")

                message = "You win! Four in a row - nicely played."
                color = COLORS["win"]
                sound = "win"

            elif result == AI:

                self.badge.config(
                    text="O",
                    fg=COLORS["o"]
                )

                self.turn_lbl.config(text="Computer wins")

                message = (
                    "The computer wins this round. "
                    "Press New Round to try again."
                )

                color = COLORS["o"]
                sound = "lose"

            else:

                self.badge.config(
                    text="=",
                    fg=COLORS["gold"]
                )

                self.turn_lbl.config(text="It's a draw")

                message = (
                    "Draw - the board is full "
                    "with no four in a row."
                )

                color = COLORS["gold"]
                sound = "draw"

            self.border = color

            self.set_status(message, color)
            self.sound.play(sound)

            self.flash_on = True

            self.flash(
                self.round_id,
                0,
                color
            )

        def flash(self, round_id, count, color):

            if round_id != self.round_id:
                return

            if count >= 9:

                self.flash_on = bool(self.win_cells)
                self.status.config(fg=color)
                self.draw()

                return

            self.flash_on = count % 2 == 0

            self.status.config(
                fg=color if count % 2 == 0
                else COLORS["text"]
            )

            self.draw()

            self.root.after(
                170,
                lambda: self.flash(
                    round_id,
                    count + 1,
                    color
                )
            )


# ============================================================
# 7. PROGRAM ENTRY POINT
# ============================================================

def main():

    if "--selftest" in sys.argv:
        selftest()
        return

    if tk is None:

        print(
            "Tkinter is not installed. "
            "Install Python Tk support to run the game."
        )

        sys.exit(1)

    root = tk.Tk()

    App(root)

    root.mainloop()


if __name__ == "__main__":
    main()
