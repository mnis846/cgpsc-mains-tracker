"""Embed stress-relief mini-games and chess puzzles in Streamlit."""

import io
import json
import urllib.request
from pathlib import Path

from break_games_config import BREAK_GAMES, GAME_GROUPS

GAMES_DIR = Path(__file__).resolve().parent / "games"
_PUZZLE_TEMPLATE = GAMES_DIR / "lichess_puzzle.html"

__all__ = ["BREAK_GAMES", "GAME_GROUPS", "embed_game", "render_break_game"]


def _load_chess():
    """Import python-chess only when puzzles are used (keeps the rest of the app bootable)."""
    try:
        import chess
        import chess.pgn
    except ImportError:
        return None, None
    return chess, chess.pgn


def fetch_daily_puzzle():
    """Load today's Lichess puzzle server-side (iframe cannot reach the API)."""
    chess, chess_pgn = _load_chess()
    if chess is None:
        return None

    try:
        req = urllib.request.Request(
            "https://lichess.org/api/puzzle/daily",
            headers={"Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except OSError:
        return None

    try:
        game = chess_pgn.read_game(io.StringIO(data["game"]["pgn"]))
        if game is None:
            return None
        board = game.board()
        for i, move in enumerate(game.mainline_moves()):
            if i >= data["puzzle"]["initialPly"]:
                break
            board.push(move)
        puzzle = data["puzzle"]
        return {
            "fen": board.fen(),
            "turn": "white" if board.turn == chess.WHITE else "black",
            "solution": puzzle["solution"],
            "rating": puzzle["rating"],
            "plays": puzzle["plays"],
            "themes": puzzle.get("themes", []),
            "id": puzzle["id"],
        }
    except (ValueError, KeyError, AttributeError):
        return None


def embed_game(filename: str, height: int = 520) -> None:
    import streamlit as st

    path = GAMES_DIR / filename
    st.iframe(path, height=height, width="stretch")


def embed_chess_puzzle(height: int = 600) -> None:
    import streamlit as st

    chess, _ = _load_chess()
    if chess is None:
        st.warning(
            "Chess puzzles need the `python-chess` package. "
            "Install with: `pip install python-chess`"
        )
        st.link_button("Open Lichess training", "https://lichess.org/training")
        return

    payload = fetch_daily_puzzle()
    if payload is None:
        st.info("Could not load today's puzzle (offline or Lichess unavailable).")
        st.link_button("Open Lichess training", "https://lichess.org/training")
        return

    template = _PUZZLE_TEMPLATE.read_text(encoding="utf-8")
    safe_json = json.dumps(payload).replace("</", "<\\/")
    html = template.replace("/*PUZZLE_DATA*/null", safe_json)
    st.iframe(html, height=height, width="stretch")


def render_break_game(game_name: str) -> None:
    kind, target, height = BREAK_GAMES[game_name]
    if game_name == "Chess Puzzles":
        embed_chess_puzzle(height=height)
    else:
        embed_game(target, height=height)
