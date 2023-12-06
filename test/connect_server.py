# -*- coding: utf-8 -*-

import asyncio

import websockets.client

URI = "ws://localhost:8000/"


async def main():
    async with (websockets.client.connect(URI) as client1,
                websockets.client.connect(URI) as client2):
        await client1.send("Hello from Python!")
        await client2.send("Hello from Python!")
        print(await client1.recv())
        print(await client2.recv())

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
