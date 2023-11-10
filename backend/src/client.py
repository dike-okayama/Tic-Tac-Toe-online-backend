# -*- coding: utf-8 -*-

import json
import typing as t

import websockets.server
import websockets.typing as wt

import backend.typing as bt


class Client:
    """
    Client class for managing client.
    """

    def __init__(self, socket: websockets.server.WebSocketServerProtocol):
        self.status: bt.ClientStatus = bt.ClientStatus.SEARCHING
        self.socket: t.Final = socket
        self.room_name: t.Optional[str] = None

    async def send(self, data: wt.Data | dict[str, t.Any]) -> None:
        """
        Send data to client.
        """
        if isinstance(data, dict):
            data = json.dumps(data)
        await self.socket.send(data)

    def serialize(self) -> dict[str, t.Optional[str]]:
        """
        Return python's dict of serialized client status.

        >>> client = Client(...)
        >>> client._serialize()
        {'type': 'client', 'status': 'SEARCHING', 'room': None}
        """
        return {
            "type": "client",
            "status": self.status.value,
            "room": self.room_name and self.room_name,
        }
