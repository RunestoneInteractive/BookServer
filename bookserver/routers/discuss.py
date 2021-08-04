#
# Third-party imports
# -------------------
from typing import Dict, Optional
import json
import os
import redis

from fastapi import (
    APIRouter,
    Cookie,
    #    Depends,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)  # noqa F401
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Local application imports
# -------------------------
from ..applogger import rslogger
from ..config import settings

# from ..session import auth_manager

# Routing
# =======
# See `APIRouter config` for an explanation of this approach.
router = APIRouter(
    tags=["discuss"],
)

templates = Jinja2Templates(directory=f"{settings._book_server_path}/templates/discuss")


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, user: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user] = websocket

    def disconnect(self, sockid: str):
        del self.active_connections[sockid]

    async def send_personal_message(
        self,
        to: str,
        message: str,
    ):
        if to in self.active_connections:
            await self.active_connections[to].send_text(message)
        else:
            rslogger.error(f"{to} is not connected")

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)


# this is good for prototyping, but we will need to integrate with
# Redis or a DB for production where we have multiple servers
manager = ConnectionManager()


# .. _login:
#
# login
# -----
@router.get("/home.html", response_class=HTMLResponse)
def chat_page(request: Request, foo: Optional[str] = Query(None)):
    rslogger.debug(f"{foo=}")
    return templates.TemplateResponse("home.html", {"request": request})


async def get_cookie_or_token(
    websocket: WebSocket,
    access_token: Optional[str] = Cookie(None),
    user: Optional[str] = Query(None),
):
    rslogger.debug(f"HELLO {access_token=} or {user=}")
    if access_token is None and user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    return access_token or user


# It seems that ``@router.websocket`` is much better than the documented
# ``websocket_route``
@router.websocket("/chat/{uname}/ws")
async def websocket_endpoint(websocket: WebSocket, uname: str):
    rslogger.debug("f{uname=}")
    rslogger.debug(f"IN WEBSOCKET {uname=}")
    # res = await auth_manager.get_current_user(user)
    # username = res.username
    # rslogger.debug(f"{res=}")
    username = uname
    await manager.connect(username, websocket)
    r = redis.from_url(os.environ.get("REDIS_URI", "redis://localhost:6379/0"))
    try:
        while True:
            data = await websocket.receive_json()
            if data["broadcast"]:
                await manager.broadcast(json.dumps(data))
            else:
                await manager.send_personal_message(
                    r.hget("partnerdb", username), f"from {username} : {data}"
                )
    except WebSocketDisconnect:
        manager.disconnect(username)
        await manager.broadcast(f"Client {username} left the chat")
