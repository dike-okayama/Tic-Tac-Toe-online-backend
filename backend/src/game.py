# -*- coding: utf-8 -*-

import json
import typing as t

import backend.typing as bt

NOUGHT = bt.CellState.NOUGHT
CROSS = bt.CellState.CROSS
BLANK = bt.CellState.BLANK


class TicTacToe:
    """
    TicTacToe game class.
    """

    LINES = [
        [(0, 0), (0, 1), (0, 2)],
        [(1, 0), (1, 1), (1, 2)],
        [(2, 0), (2, 1), (2, 2)],
        [(0, 0), (1, 0), (2, 0)],
        [(0, 1), (1, 1), (2, 1)],
        [(0, 2), (1, 2), (2, 2)],
        [(0, 0), (1, 1), (2, 2)],
        [(0, 2), (1, 1), (2, 0)],
    ]

    HITS = {
        (NOUGHT, NOUGHT, NOUGHT),
        (CROSS, CROSS, CROSS),
    }

    def __init__(self) -> None:
        self.elapsed_turn: int
        self.board: bt.GameBoardType

        self._initialize_elapsed_turn()
        self._initialize_board()

    @property
    def current_turn(self) -> bt.CellState:
        """
        Return the current turn.
        """
        return (CROSS, NOUGHT)[self.elapsed_turn % 2]

    def is_ended(self) -> bool:
        """
        Return True if the game is ended.
        """
        for target_line in self.LINES:
            line = tuple(self.board[y][x] for y, x in target_line)
            if line in self.HITS:
                return True

        if all(BLANK not in row for row in self.board):
            return True

        return False

    def get_result(self) -> str:
        """
        Return the result of the game.
        """
        if not self.is_ended():
            return "not ended"
        for target_line in self.LINES:
            line = tuple(self.board[y][x] for y, x in target_line)
            if line in self.HITS:
                return f"{line[0].value} win"
        return "draw"

    def put(self, position: bt.PositionType) -> bool:
        """
        Return False if the position is invalid.
        """

        if self.is_ended():
            return False

        y, x = position

        if not (0 <= y < 3 and 0 <= x < 3):
            return False

        if self.board[y][x] != BLANK:
            return False

        self.board[y][x] = self.current_turn

        self.elapsed_turn += 1

        return True

    def reset(self) -> bool:
        self._initialize_elapsed_turn()
        self._initialize_board()

        return True

    def _initialize_elapsed_turn(self) -> None:
        self.elapsed_turn = 0

    def _initialize_board(self) -> None:
        self.board = [
            [BLANK, BLANK, BLANK],
            [BLANK, BLANK, BLANK],
            [BLANK, BLANK, BLANK],
        ]

    def serialize(self) -> str:
        """
        Return json string of serialized game status.
        >>> game = Game(...)
        >>> game.serialize()
        '{"type": "game", "board": [[-1, -1, -1], [-1, -1, -1], [-1, -1, -1]], "elapsedTurn": 0, "currentTurn": 0, "isEnded": false}'  # noqa: E501
        """
        return json.dumps(self._serialize())

    def _serialize(self) -> dict[str, t.Optional[str | int | list[list[int]] | bool]]:
        """
        Return python's dict of serialized game status.
        >>> game = Game(...)
        >>> game._serialize()
        {'type': 'game', 'board': [[-1, -1, -1], [-1, -1, -1], [-1, -1, -1]], 'elapsedTurn': 0, 'currentTurn': 0, 'isEnded': False}  # noqa: E501
        """
        return {
            "type": "game",
            "board": [[cell.value for cell in row] for row in self.board],
            "elapsedTurn": self.elapsed_turn,
            "currentTurn": self.current_turn.value,
            "isEnded": self.is_ended(),
        }
