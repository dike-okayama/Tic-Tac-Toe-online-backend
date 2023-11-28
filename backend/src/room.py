# -*- coding: utf-8 -*-

import typing as t

from .client import Client
from .game import TicTacToe


class Room:
    """
    Room class for managing clients and game.
    """

    def __init__(self, name: str, client: Client):
        self.name: t.Final = name
        self.cross: Client = client
        self.nought: t.Optional[Client] = None
        self.game: t.Final = TicTacToe()

    @property
    def waiting(self) -> bool:
        """
        Return True if the room is waiting for another player.
        """
        return self.nought is None

    def __iter__(self) -> t.Iterator[Client]:
        """
        Iterate over the clients in the room.
        """
        yield self.cross
        if self.nought is not None:
            yield self.nought

    def serialize(self, target: t.Optional[Client] = None):
        """
        Return python's dict of serialized game status wrapped in room status.
        """
        game_status = self.game.serialize()
        if target == self.cross:
            game_status["isMyTurn"] = game_status["currentTurn"] == 0
        if target == self.nought:
            game_status["isMyTurn"] = game_status["currentTurn"] == 1
        return game_status
