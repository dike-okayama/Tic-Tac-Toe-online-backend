# -*- coding: utf-8 -*-

import subprocess
import time
import typing as t

import pytest
import pytest_asyncio
import websockets.client

URI = "ws://0.0.0.0:5174"

Client: t.TypeAlias = websockets.client.WebSocketClientProtocol
PlayingClients: t.TypeAlias = tuple[Client, Client]


@pytest.fixture(autouse=True)
def setup_server():
    process = subprocess.Popen("python3 -m backend", shell=True)
    time.sleep(0.1)
    yield
    process.kill()


@pytest_asyncio.fixture  # type: ignore
async def client() -> t.AsyncGenerator[Client, None]:
    async with websockets.client.connect(URI) as client:
        yield client


@pytest_asyncio.fixture  # type: ignore
async def playing_clients(client1: Client, client2: Client) -> t.AsyncGenerator[PlayingClients, None]:
    await client1.send("create 1234")
    await client1.recv()
    await client2.send("join 1234")
    await client1.recv()
    await client2.recv()
    await client1.recv()
    await client2.recv()
    yield client1, client2


client1 = client
client2 = client
client3 = client


@pytest.mark.asyncio
async def test_connect_server(client1: Client):
    pass


@pytest.mark.asyncio
async def test_success_to_create_room(client: Client):
    await client.send("create 1234")
    assert await client.recv() == '{"type": "client", "status": "WAITING", "room": "1234"}'


@pytest.mark.asyncio
async def test_fail_to_create_room(client1: Client, client2: Client):
    await client1.send("create 1234")
    await client1.recv()
    await client2.send("create 1234")
    assert await client2.recv() == '{"type": "client", "status": "SEARCHING", "room": null}'


@pytest.mark.asyncio
async def test_success_to_join_room(client1: Client, client2: Client):
    await client1.send("create 1234")
    await client1.recv()
    await client2.send("join 1234")
    assert await client1.recv() == '{"type": "client", "status": "PLAYING", "room": "1234"}'
    assert await client2.recv() == '{"type": "client", "status": "PLAYING", "room": "1234"}'


@pytest.mark.asyncio
async def test_fail_to_join_room_not_exist(client1: Client):
    await client1.send("join 1234")
    assert await client1.recv() == '{"type": "client", "status": "SEARCHING", "room": null}'


@pytest.mark.asyncio
async def test_fail_to_join_room_already_full(client1: Client, client2: Client, client3: Client):
    await client1.send("create 1234")
    await client1.recv()
    await client2.send("join 1234")
    await client2.recv()
    await client3.send("join 1234")
    assert await client3.recv() == '{"type": "client", "status": "SEARCHING", "room": null}'


@pytest.mark.asyncio
async def test_leave(client: Client):
    await client.send("create 1234")
    await client.recv()
    await client.send("leave")
    assert await client.recv() == '{"type": "client", "status": "SEARCHING", "room": null}'


@pytest.mark.asyncio
async def test_starting_game(client1: Client, client2: Client):
    await client1.send("create 1234")
    await client1.recv()
    await client2.send("join 1234")
    await client1.recv()
    await client2.recv()
    assert (
        await client1.recv()
        == '{"type": "game", "board": [[-1, -1, -1], [-1, -1, -1], [-1, -1, -1]], "elapsedTurn": 0, "currentTurn": 0, "isEnded": false}'  # noqa: E501
    )
    assert (
        await client2.recv()
        == '{"type": "game", "board": [[-1, -1, -1], [-1, -1, -1], [-1, -1, -1]], "elapsedTurn": 0, "currentTurn": 0, "isEnded": false}'  # noqa: E501
    )


@pytest.mark.asyncio
async def test_put(playing_clients: PlayingClients):
    client1, client2 = playing_clients

    await client1.send("put 0 0")
    assert (
        await client1.recv()
        == '{"type": "game", "board": [[0, -1, -1], [-1, -1, -1], [-1, -1, -1]], "elapsedTurn": 1, "currentTurn": 1, "isEnded": false}'  # noqa: E501
    )
    assert (
        await client2.recv()
        == '{"type": "game", "board": [[0, -1, -1], [-1, -1, -1], [-1, -1, -1]], "elapsedTurn": 1, "currentTurn": 1, "isEnded": false}'  # noqa: E501
    )


@pytest.mark.asyncio
async def test_put_until_end(playing_clients: PlayingClients):
    """
    x . .
    o x .
    . o x
    """
    client1, client2 = playing_clients

    await client1.send("put 0 0")
    assert (
        await client1.recv()
        == '{"type": "game", "board": [[0, -1, -1], [-1, -1, -1], [-1, -1, -1]], "elapsedTurn": 1, "currentTurn": 1, "isEnded": false}'  # noqa: E501
    )
    assert (
        await client2.recv()
        == '{"type": "game", "board": [[0, -1, -1], [-1, -1, -1], [-1, -1, -1]], "elapsedTurn": 1, "currentTurn": 1, "isEnded": false}'  # noqa: E501
    )

    await client2.send("put 1 0")
    assert (
        await client1.recv()
        == '{"type": "game", "board": [[0, -1, -1], [1, -1, -1], [-1, -1, -1]], "elapsedTurn": 2, "currentTurn": 0, "isEnded": false}'  # noqa: E501
    )
    assert (
        await client2.recv()
        == '{"type": "game", "board": [[0, -1, -1], [1, -1, -1], [-1, -1, -1]], "elapsedTurn": 2, "currentTurn": 0, "isEnded": false}'  # noqa: E501
    )

    await client1.send("put 2 2")
    assert (
        await client1.recv()
        == '{"type": "game", "board": [[0, -1, -1], [1, -1, -1], [-1, -1, 0]], "elapsedTurn": 3, "currentTurn": 1, "isEnded": false}'  # noqa: E501
    )
    assert (
        await client2.recv()
        == '{"type": "game", "board": [[0, -1, -1], [1, -1, -1], [-1, -1, 0]], "elapsedTurn": 3, "currentTurn": 1, "isEnded": false}'  # noqa: E501
    )

    await client2.send("put 2 0")
    assert (
        await client1.recv()
        == '{"type": "game", "board": [[0, -1, -1], [1, -1, -1], [1, -1, 0]], "elapsedTurn": 4, "currentTurn": 0, "isEnded": false}'  # noqa: E501
    )
    assert (
        await client2.recv()
        == '{"type": "game", "board": [[0, -1, -1], [1, -1, -1], [1, -1, 0]], "elapsedTurn": 4, "currentTurn": 0, "isEnded": false}'  # noqa: E501
    )

    await client1.send("put 1 1")
    assert (
        await client1.recv()
        == '{"type": "game", "board": [[0, -1, -1], [1, 0, -1], [1, -1, 0]], "elapsedTurn": 5, "currentTurn": 1, "isEnded": true}'  # noqa: E501
    )
    assert (
        await client2.recv()
        == '{"type": "game", "board": [[0, -1, -1], [1, 0, -1], [1, -1, 0]], "elapsedTurn": 5, "currentTurn": 1, "isEnded": true}'  # noqa: E501
    )


@pytest.mark.asyncio
async def test_restart1(playing_clients: PlayingClients):
    client1, client2 = playing_clients
    await client1.send("put 0 0")
    await client1.recv()
    await client2.recv()
    await client1.send("restart")
    assert (
        await client1.recv()
        == '{"type": "game", "board": [[-1, -1, -1], [-1, -1, -1], [-1, -1, -1]], "elapsedTurn": 0, "currentTurn": 0, "isEnded": false}'  # noqa: E501
    )
    assert (
        await client2.recv()
        == '{"type": "game", "board": [[-1, -1, -1], [-1, -1, -1], [-1, -1, -1]], "elapsedTurn": 0, "currentTurn": 0, "isEnded": false}'  # noqa: E501
    )


@pytest.mark.asyncio
async def test_restart2(playing_clients: PlayingClients):
    client1, client2 = playing_clients
    await client1.send("put 0 0")
    await client1.recv()
    await client2.recv()
    await client2.send("restart")
    assert (
        await client1.recv()
        == '{"type": "game", "board": [[-1, -1, -1], [-1, -1, -1], [-1, -1, -1]], "elapsedTurn": 0, "currentTurn": 0, "isEnded": false}'  # noqa: E501
    )
    assert (
        await client2.recv()
        == '{"type": "game", "board": [[-1, -1, -1], [-1, -1, -1], [-1, -1, -1]], "elapsedTurn": 0, "currentTurn": 0, "isEnded": false}'  # noqa: E501
    )


@pytest.mark.asyncio
async def test_exit1(playing_clients: PlayingClients):
    client1, client2 = playing_clients
    await client1.send("exit")
    assert await client1.recv() == '{"type": "client", "status": "SEARCHING", "room": null}'
    assert await client2.recv() == '{"type": "client", "status": "SEARCHING", "room": null}'


@pytest.mark.asyncio
async def test_exit2(playing_clients: PlayingClients):
    client1, client2 = playing_clients
    await client2.send("exit")
    assert await client1.recv() == '{"type": "client", "status": "SEARCHING", "room": null}'
    assert await client2.recv() == '{"type": "client", "status": "SEARCHING", "room": null}'
