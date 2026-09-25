import asyncio
from collections import defaultdict
from fastapi import WebSocket
class Hub:
    def __init__(self): self.connections: dict[str, set[WebSocket]] = defaultdict(set)
    async def connect(self, token: str, socket: WebSocket): await socket.accept(); self.connections[token].add(socket)
    def disconnect(self, token: str, socket: WebSocket): self.connections[token].discard(socket)
    async def publish(self, token: str, payload: dict):
        dead = []
        for socket in self.connections[token]:
            try: await socket.send_json(payload)
            except Exception: dead.append(socket)
        for socket in dead: self.disconnect(token, socket)
hub = Hub()
