from fastapi import WebSocket

class WSManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)


    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected_conn = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected_conn.append(connection)

        for connection in disconnected_conn:
            self.disconnect(connection)

ws_manager = WSManager()