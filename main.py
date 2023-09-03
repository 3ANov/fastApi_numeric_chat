import logging


from secrets import token_urlsafe
from typing import Dict

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.websockets import WebSocket
from fastapi.websockets import WebSocketDisconnect


logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG)

app = FastAPI()
templates = Jinja2Templates(directory="templates")


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket | None] = {}

    async def connect_client(self, client_cookie_string: str):
        self.active_connections[client_cookie_string] = None

    async def connect_websocket(self, client_cookie_string: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_cookie_string] = websocket

    def disconnect(self, client_cookie_string: str):
        self.active_connections.pop(client_cookie_string)

    async def send_personal_json(self, json_message: dict, websocket: WebSocket):
        await websocket.send_json(json_message)


manager = ConnectionManager()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    client_cookie_string = token_urlsafe(30)
    await manager.connect_client(client_cookie_string)
    logging.info(manager.active_connections)
    return templates.TemplateResponse("home.html", {"request": request, "client_cookie_string": client_cookie_string})


@app.websocket("/ws/{client_cookie_string}")
async def websocket_endpoint(websocket: WebSocket, client_cookie_string: str):
    await manager.connect_websocket(client_cookie_string, websocket)
    try:
        message_count = 0
        while True:
            data = await websocket.receive_json()
            message_count += 1
            data['message_count'] = message_count
            logging.info(manager.active_connections)
            await manager.send_personal_json(data, websocket)
    except WebSocketDisconnect:
            manager.disconnect(client_cookie_string)
            logging.info(manager.active_connections)

