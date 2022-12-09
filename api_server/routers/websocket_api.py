from __future__ import annotations
from fastapi import APIRouter, WebSocketDisconnect
from fastapi.websockets import WebSocket

router: APIRouter = APIRouter(prefix="/websocket_api", tags=["WebSocket"])

class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[str, WebSocket] = {}
        self.message_boxes: dict[str, list[str]] = {}
        self._gs_id_list = ['NSU_GS', 'NSU_1A_GS']
        self._gs_ip_list = ['10.6.1.74', '10.6.1.97', '127.0.0.1', 'localhost']

    async def send_stored_messages(self, websocket: WebSocket, client_id: str) -> None:
        stored_messages: list[str] | None = self.message_boxes.get(client_id, None)
        if stored_messages is not None:
            if len(stored_messages) > 0:
                for message in stored_messages:
                    await websocket.send_text(message)
                self.message_boxes.pop(client_id, None)

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        await websocket.accept()
        print(f'connected {websocket.client}')
        if websocket.client is not None:
            if client_id in self._gs_id_list and websocket.client.host not in self._gs_ip_list:
                print(f'{websocket.client} tried to connect as ground station.')
                await websocket.close(reason='Unknown api_server ip address')
                print(f'disconnected {websocket.client}')
                return
        self.active_connections.update({f'{client_id}': websocket})
        await self.send_stored_messages(websocket, client_id)

    def disconnect(self, websocket: WebSocket, client_id: str) -> None:
        print(f'disconnected {websocket.client}')
        self.active_connections.pop(client_id, None)

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        await websocket.send_text(message)

    async def send_message_to_id(self, message: str, target_id: str) -> None:
        ws: WebSocket | None = self.active_connections.get(target_id, None)
        if ws is not None:
            await ws.send_text(message)
        else:  # client not connected. Store message for sending it later
            print(f'Can not send message to {target_id}. Message saved and will be sent after target connection.')
            self.message_boxes.setdefault(target_id, []).append(message)

    async def broadcast(self, message: str) -> None:
        for connection in self.active_connections.values():
            await connection.send_text(message)


manager: ConnectionManager = ConnectionManager()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str) -> None:
    await manager.connect(websocket, client_id)
    try:
        while True:
            data: str = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            # await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
        print(f"Client #{client_id} left the chat")


@router.websocket("/ws/{gs_id}/{user_id}")
async def websocket_gs_endpoint(websocket: WebSocket, gs_id: str, user_id: str) -> None:
    await manager.connect(websocket, gs_id)
    if websocket.client_state.name == 'CONNECTED':
        print(f"Start session on #{gs_id} for {user_id} user.")
        await manager.send_message_to_id(message='start_session', target_id=user_id)
        try:
            while True:
                data: str = await websocket.receive_text()
                await manager.send_message_to_id(data, user_id)
                # await manager.broadcast(f"Client #{client_id} says: {data}")
        except WebSocketDisconnect:
            manager.disconnect(websocket, gs_id)
            print(f"Client #{gs_id} left the chat")