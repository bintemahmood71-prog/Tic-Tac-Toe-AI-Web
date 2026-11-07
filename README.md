# Tic-Tac-Toe AI — Python Web Version

A browser-playable 4×4 Tic-Tac-Toe game. Four matching symbols in a row are required to win. The computer opponent uses the Python Minimax algorithm with Alpha-Beta pruning.

## Features
- 4×4 board and four-in-a-row win condition
- Human (X) versus AI (O)
- Immediate win detection and threat blocking
- Minimax search with Alpha-Beta pruning and a heuristic board evaluation
- Score tracking, new round, and score reset
- Browser interface built with Streamlit; game and AI logic remain in Python

## Run locally
1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. (Recommended) Create and activate a virtual environment.
4. Install dependencies: `pip install -r requirements.txt`
5. Start the app: `streamlit run app.py`
6. Open the local URL printed in the terminal.

## Project files
- `app.py` — Streamlit interface and game state
- `ai_engine.py` — Python game rules and AI algorithm
- `Tic_Tac_Toe_corrected.py` — original Tkinter desktop version
- `requirements.txt` — deployment dependency

## Deployment
Push this folder to GitHub, then deploy `app.py` using Streamlit Community Cloud.
