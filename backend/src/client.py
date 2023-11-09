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

    async def send(self, data: wt.Data) -> None:
        """
        Send data to client.
        """
        await self.socket.send(data)

    def serialize(self) -> str:
        """
        Return serialized client status for sending to client.

        >>> client = Client(...)
        >>> client.serialize()
        '{"type": "client", "status": "SEARCHING", "room": null}'
        """
        return json.dumps(self._serialize())

    def _serialize(self) -> dict[str, t.Optional[str]]:
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
