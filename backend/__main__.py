# -*- coding: utf-8 -*-

import asyncio
import os

import dotenv
import websockets.server

from backend import handle_client

dotenv.load_dotenv()

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", 5174))


async def main():
    async with websockets.server.serve(handle_client, host=HOST, port=PORT) as server:
        for socket in server.sockets:
            host, port, *_ = socket.getsockname()
            print(f"Serving on ws://{host}:{port}")

        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
