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

        if target is None:
            return game_status

        target_value = int(target != self.cross)  # 0: cross, 1: nought
        game_status["isMyTurn"] = self.game.current_turn.value == target_value

        if self.game.is_ended():
            match self.game.get_result():
                case -1:
                    pass
                case 0:
                    game_status["result"] = "You Win!" if target_value == 0 else "You Lose"
                case 1:
                    game_status["result"] = "You Win!" if target_value == 1 else "You Lose"
                case 2:
                    game_status["result"] = "Draw"

        return game_status
