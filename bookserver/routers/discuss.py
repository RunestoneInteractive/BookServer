#
# Third-party imports
# -------------------
from typing import Dict, Optional
from fastapi import (
    APIRouter,
    Cookie,
    Depends,
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
from ..session import auth_manager

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
        await self.active_connections[to].send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)


# this is good for prototyping, but we will need to integrate with
# Redis or a DB for production where we have multiple servers
manager = ConnectionManager()
# partner pairs can similarly be manged in the database
partnerdb = {"testuser1": "testuser2", "testuser2": "testuser1"}


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
async def websocket_endpoint(
    websocket: WebSocket, uname: str, user: str = Depends(get_cookie_or_token)
):
    rslogger.debug("f{uname=}")
    rslogger.debug(f"IN WEBSOCKET {user=}")
    res = await auth_manager.get_current_user(user)
    username = res.username
    rslogger.debug(f"{res=}")
    await manager.connect(username, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # await manager.broadcast(f"Message sent from {user} was {data}")
            await manager.send_personal_message(
                partnerdb[username], f"from {username} : {data}"
            )
    except WebSocketDisconnect:
        manager.disconnect(username)
        await manager.broadcast(f"Client {username} left the chat")
