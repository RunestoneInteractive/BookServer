# ******************************************************
# |docname| -
# ******************************************************
# :index:`docs to write`: **Description here...**
#
# See:  `FastAPI Login <https://fastapi-login.readthedocs.io/advanced_usage/>_`
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8`_.
#
# Standard library
# ----------------
# None. (Or the imports.)
#
# Third-party imports
# -------------------
# :index:`todo`: **Lots of unused imports...can we deletet these?**
from fastapi import APIRouter, Depends, Request, Response  # noqa F401
from fastapi_login.exceptions import InvalidCredentialsException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Local application imports
# -------------------------
from ..session import load_user, auth_manager
from ..schemas import LogItem, LogItemIncoming  # noqa F401
from pydal.validators import CRYPT

# Routing
# =======
# See `APIRouter config` for an explanation of this approach.
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

templates = Jinja2Templates(directory=f"bookserver/templates{router.prefix}")


class UserManagerWeb2Py:
    def init_app(self):
        self.crypt = CRYPT(key=settings.WEB2PY_PRIVATE_KEY, salt=settings.WEB2PY_SALT)

    def hash_password(self, password):
        return str(self.crypt(password)[0])

    def verify_password(self, password, user):
        return self.hash_password(password) == self.get_password(user)


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/validate")
async def login(
    response: Response, data: OAuth2PasswordRequestForm = Depends()
) -> dict:
    username = data.username
    password = data.password

    user = await load_user(username)
    um = UserManagerWeb2Py()

    if not user:
        raise InvalidCredentialsException
    else:
        if not um.verify_password(user.password, password):
            raise InvalidCredentialsException

    access_token = auth_manager.create_access_token(data={"sub": user.username})
    auth_manager.set_cookie(response, access_token)

    return {"token": access_token}
