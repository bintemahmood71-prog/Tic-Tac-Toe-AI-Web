import streamlit as st
from ai_engine import AI, EMPTY, HUMAN, SIZE, CELLS, choose_move, winner_line

st.set_page_config(page_title="Tic-Tac-Toe AI", page_icon="⭕", layout="centered")

#  Game state 
def initialize_game():
    defaults = {
        "board": [EMPTY] * CELLS,
        "scores": {"human": 0, "ai": 0, "draw": 0},
        "game_over": False,
        "result": "",
        "winning_line": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def finish_round(winner):
    st.session_state.game_over = True
    st.session_state.winning_line = winner_line(st.session_state.board)
    if winner == HUMAN:
        st.session_state.result = "You win!"
        st.session_state.scores["human"] += 1
    elif winner == AI:
        st.session_state.result = "AI wins this round."
        st.session_state.scores["ai"] += 1
    else:
        st.session_state.result = "It's a draw!"
        st.session_state.scores["draw"] += 1


def check_round_end():
    line = winner_line(st.session_state.board)
    if line:
        finish_round(st.session_state.board[line[0]])
        return True
    if EMPTY not in st.session_state.board:
        finish_round(None)
        return True
    return False


def human_move(index):
    board = st.session_state.board
    if st.session_state.game_over or board[index] != EMPTY:
        return

    board[index] = HUMAN
    if check_round_end():
        return

    # The original Python Minimax + Alpha-Beta AI chooses the reply.
    ai_index = choose_move(board)
    if ai_index is not None:
        board[ai_index] = AI
    check_round_end()


def new_round():
    st.session_state.board = [EMPTY] * CELLS
    st.session_state.game_over = False
    st.session_state.result = ""
    st.session_state.winning_line = None


def reset_scores():
    st.session_state.scores = {"human": 0, "ai": 0, "draw": 0}
    new_round()


initialize_game()

# Page 
st.title("⭕ Tic-Tac-Toe")
st.caption("4 × 4 board  ·  Four symbols in a row to win  ·  Python AI opponent")
st.info("You are **X**. The computer is **O**. You play first.")

score_cols = st.columns(3)
score_cols[0].metric("Your wins", st.session_state.scores["human"])
score_cols[1].metric("AI wins", st.session_state.scores["ai"])
score_cols[2].metric("Draws", st.session_state.scores["draw"])

if st.session_state.game_over:
    if st.session_state.result == "You win!":
        st.success(st.session_state.result)
    elif st.session_state.result == "It's a draw!":
        st.warning(st.session_state.result)
    else:
        st.error(st.session_state.result)
else:
    st.write("### Your turn — choose an empty cell")

#  4 x 4 interactive board 
for row in range(SIZE):
    cols = st.columns(SIZE, gap="small")
    for col in range(SIZE):
        index = row * SIZE + col
        value = st.session_state.board[index]
        label = value if value != EMPTY else "·"
        cols[col].button(
            label,
            key=f"cell_{index}",
            on_click=human_move,
            args=(index,),
            disabled=(value != EMPTY or st.session_state.game_over),
            use_container_width=True,
        )

if st.session_state.game_over and st.session_state.winning_line:
    st.caption("Winning cells: " + ", ".join(str(i + 1) for i in st.session_state.winning_line))

left, right = st.columns(2)
left.button("↻ New Round", on_click=new_round, use_container_width=True)
right.button("Reset Scores", on_click=reset_scores, use_container_width=True)

with st.expander("How does the AI work?"):
    st.write(
        "The AI analyzes the board, evaluates possible moves, and selects the most suitable move. " 
        "It prioritizes winning opportunities, blocks the opponent's immediate winning moves, "
        "and uses the Minimax algorithm with Alpha-Beta pruning to explore future possibilities"
        " and make strategic decisions.. "
        
    )

st.divider()
st.caption("Built with Python and Streamlit.")
