import asyncio
import sys
import json
import uuid

import websockets
from websockets import serve

from .scoreboard import ScoreBoard

class WsClient:
    def start(self, host="0.0.0.0", port=19132):
        self.ws = websockets.serve(self.receive, host, port)
        self.host = host
        self.port = port
        self.ScoreBoard = ScoreBoard
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.ws)
        self.event_ready()
        self.loop.run_forever()

    async def receive(self, websocket, path):
        self.ws = websocket
        await self.listen_event()
        await self.event("connect")#self.event_connect()
        try:
            while True:
                data = await self.ws.recv()
                msg = json.loads(data)
                await self.parse_command(msg)
        except (
                websockets.exceptions.ConnectionClosedOK,
                websockets.exceptions.ConnectionClosedError,
                websockets.exceptions.ConnectionClosed):
            await self.event("disconnect")#self.event_disconnect()
            sys.exit()

    async def listen_event(self):
        for event in self.events:
            await self.ws.send(json.dumps({
                "body": {
                    "eventName": event
                },
                "header": {
                    "requestId": "00000000-0000-0000-0000-000000000000",
                    "messagePurpose": "subscribe",
                    "version": 1,
                    "messageType": "commandRequest"
                }
            }))

    async def parse_command(self, message):
        if message["header"]["messagePurpose"] == "event":
            event_name = message["body"]["eventName"]
            await self.event(event_name, message)
            if message["body"]["eventName"] == "PlayerMessage" and message["body"]["properties"]['MessageType'] == 'chat':
                pass

    async def command(self, cmd):
        cmd_json = json.dumps({
            "body": {
                "origin": {
                    "type": "player"
                },
                "commandLine": cmd,
                "version": 1
            },
            "header": {
                "requestId": str(uuid.uuid4()),
                "messagePurpose": "commandRequest",
                "version": 1,
                "messageType": "commandRequest"
            }
        })
        return await self.ws.send(cmd_json)

    async def event(self, name, *args):
        func = f"self.event_{name}"
        try:
            await eval(f"{func}({args})")
        except:
            print(f"event_{name}")
