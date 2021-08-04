#
# Third-party imports
# -------------------
from fastapi import APIRouter, Request, Response, WebSocket  # noqa F401
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Local application imports
# -------------------------
from ..applogger import rslogger
from ..config import settings

# Routing
# =======
# See `APIRouter config` for an explanation of this approach.
# Remove the "discuss" prefix until PR #2640 of FastAPI is merged
router = APIRouter(
    tags=["discuss"],
)

templates = Jinja2Templates(directory=f"{settings._book_server_path}/templates/discuss")


# .. _login:
#
# login
# -----
@router.get("/home.html", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@router.websocket_route("/ws")
async def websocket_endpoint(websocket: WebSocket):
    rslogger.debug("IN WEBSOCKET")
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message sent was {data}")
