# -*- coding: utf-8 -*-

import logging
import typing as t
import unicodedata

import websockets
import websockets.server

import backend.typing as bt
from backend.src import Client, Room

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if __debug__ else logging.INFO)
handler = logging.FileHandler("./logs/server.log")
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s: %(message)s"))
handler.setLevel(logging.DEBUG if __debug__ else logging.INFO)
logger.addHandler(handler)


rooms: dict[str, Room] = {}
query: bt.QueryType


async def handle_client(websocket: websockets.server.WebSocketServerProtocol):
    # connected
    client: t.Final = Client(socket=websocket)

    async for message in websocket:
        message = str(message)
        logger.debug(f"{rooms = }")

        match client.status:
            case bt.ClientStatus.SEARCHING:
                query, raw_room_name = message.split(" ", 1)  # expected `(create|join) .*`
                room_name = unicodedata.normalize("NFKC", raw_room_name.strip())

                match query:
                    # create a new room
                    case "create":
                        if room_name in rooms:
                            await client.send(client.serialize())
                            continue

                        room = Room(name=room_name, client_id=client)
                        rooms[room_name] = room

                        client.room_name = room_name
                        client.status = bt.ClientStatus.WAITING
                        await client.send(client.serialize())

                    # join a existing room
                    case "join":
                        room = rooms.get(room_name)

                        if room is None or not room.waiting:
                            await client.send(client.serialize())
                            continue

                        client.room_name = room_name
                        room.nought = client

                        for client_ in room:
                            client_.status = bt.ClientStatus.PLAYING
                            await client_.send(client_.serialize())
                            await client_.send(room.game.serialize())

                    # invalid query
                    case _:
                        pass

            case bt.ClientStatus.WAITING:
                assert client.room_name is not None
                query = message

                match query:
                    # leave the room
                    case "leave":
                        del rooms[client.room_name]
                        client.room_name = None
                        client.status = bt.ClientStatus.SEARCHING

                        await client.send(client.serialize())

                    # invalid query
                    case _:
                        pass

            case bt.ClientStatus.PLAYING:
                assert client.room_name is not None
                query, *yx = message.split()  # expected `(put|restart|finish) (\d \d)?`

                room = rooms[client.room_name]
                game = room.game

                match query:
                    # put a piece
                    case "put":
                        y, x = map(int, yx)
                        game.put((y, x))

                        for client_ in room:
                            await client_.send(game.serialize())

                    # restart game
                    case "restart":
                        game.reset()

                        for client_ in room:
                            await client_.send(game.serialize())

                    # finish game and leave the room
                    case "exit":
                        del rooms[client.room_name]

                        for client_ in room:
                            client_.status = bt.ClientStatus.SEARCHING
                            client_.room_name = None
                            await client_.send(client_.serialize())

                        del room

                    # invalid query
                    case _:
                        pass

    # disconnected
    if client.room_name in rooms:
        del rooms[client.room_name]
