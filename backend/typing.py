# -*- coding: utf-8 -*-

import enum
import typing as t


class CellState(enum.Enum):
    BLANK = -1
    CROSS = 0
    NOUGHT = 1


class ClientStatus(enum.Enum):
    SEARCHING = "SEARCHING"
    WAITING = "WAITING"
    PLAYING = "PLAYING"


QueryType: t.TypeAlias = t.Literal["create", "join", "leave", "put", "restart", "exit"]
GameBoardType: t.TypeAlias = list[list[CellState]]
PositionType: t.TypeAlias = tuple[int, int]
