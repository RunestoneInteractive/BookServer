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
from fastapi.responses import HTMLResponse  # , RedirectResponse
from fastapi.templating import Jinja2Templates

# Local application imports
# -------------------------
from ..session import load_user, auth_manager
from ..schemas import LogItem, LogItemIncoming  # noqa F401
from pydal.validators import CRYPT
from ..applogger import rslogger
from ..config import settings

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
    """
    This is called as the result of a login form being submitted.

    """
    username = data.username
    password = data.password

    rslogger.debug(f"username = {username}")
    user = await load_user(username)
    # um = UserManagerWeb2Py()
    rslogger.debug(f"{user.username}")
    if not user:
        raise InvalidCredentialsException
    else:
        salt = user.password_hash.split("$")[1]
        crypt = CRYPT(key=settings.web2py_private_key, salt=salt)
        if str(crypt(password)[0]) != user.password_hash:
            raise InvalidCredentialsException

    access_token = auth_manager.create_access_token(data={"sub": user.username})
    auth_manager.set_cookie(response, access_token)

    # todo: I would really rather not return a token here. I would prefer to redirect to
    # the next page.  Not sure if it is possible, this may have to return a token in
    # order for fastapi_login to work.
    return {"token": access_token}
    # return RedirectResponse("http://localhost:8080/books/published/overview/index.html")
