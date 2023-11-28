# -*- coding: utf-8 -*-

import enum
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


class ErrorMessage(enum.Enum):
    ALREADY_EXIST = "The room already exists."
    NOT_EXIST = "The room does not exist."
    ALREADY_FULL = "The room is already full."


async def handle_client(websocket: websockets.server.WebSocketServerProtocol):
    # connected
    client: t.Final = Client(socket=websocket)
    logger.info(f"connected: {client}")

    async for message in websocket:
        message = str(message)
        logger.info(f"{client}> {message}")
        logger.debug(f"{client.status = }")
        logger.debug(f"{client.room_name = }")
        logger.debug(f"{rooms = }")

        match client.status:
            case bt.ClientStatus.SEARCHING:
                query, raw_room_name = message.split(" ", 1)  # expected `(create|join) .*`
                room_name = unicodedata.normalize("NFKC", raw_room_name.strip())

                match query:
                    # create a new room
                    case "create":
                        if room_name in rooms:
                            await client.send(client.serialize() | {"error": ErrorMessage.ALREADY_EXIST.value})
                            continue

                        room = Room(name=room_name, client=client)
                        rooms[room_name] = room

                        client.room_name = room_name
                        client.status = bt.ClientStatus.WAITING
                        await client.send(client.serialize())

                    # join a existing room
                    case "join":
                        room = rooms.get(room_name)

                        if room is None:
                            await client.send(client.serialize() | {"error": ErrorMessage.NOT_EXIST.value})
                            continue

                        if not room.waiting:
                            await client.send(client.serialize() | {"error": ErrorMessage.ALREADY_FULL.value})
                            continue

                        client.room_name = room_name
                        room.nought = client

                        for client_it in room:
                            client_it.status = bt.ClientStatus.PLAYING
                            await client_it.send(client_it.serialize())
                            await client_it.send(room.serialize(target=client_it))

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
                query, *yx = message.split()  # expected `(put|restart|exit) (\d \d)?`

                room = rooms[client.room_name]
                game = room.game

                match query:
                    # put a piece
                    case "put":
                        y, x = map(int, yx)
                        game.put((y, x))

                        for client_it in room:
                            await client_it.send(room.serialize(target=client_it))

                    # restart game
                    case "restart":
                        game.reset()

                        for client_it in room:
                            await client_it.send(room.serialize(target=client_it))

                    # finish game and leave the room
                    case "exit":
                        del rooms[client.room_name]

                        for client_it in room:
                            client_it.status = bt.ClientStatus.SEARCHING
                            client_it.room_name = None
                            await client_it.send(client_it.serialize())

                        del room

                    # invalid query
                    case _:
                        pass

    # disconnected
    if client.room_name in rooms:
        rooms.pop(client.room_name)
    logger.info(f"disconnected: {client}")
