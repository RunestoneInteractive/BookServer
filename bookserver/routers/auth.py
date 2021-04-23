# ******************************************************
# |docname| - Validation and Authentication
# ******************************************************
# Provide a login page and validation endpoint to allow a student to login to the
# Runestone book server.  This assumes that a student has registered using the
# old web2py registration system.  So we provide validation of the user name and
# password.
#
# See:  `FastAPI Login <https://fastapi-login.readthedocs.io/advanced_usage/>`_
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
from fastapi.responses import HTMLResponse, RedirectResponse
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


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/validate")
async def login(
    data: OAuth2PasswordRequestForm = Depends(), response_class=RedirectResponse
):
    """
    This is called as the result of a login form being submitted.
    If authentication is successful an access token is created and stored
    in a session cookie.  This session cookie is used for all protected routes.
    The ``auth_manager`` is provided by `../session.py` which also explains how
    to setup a protected route.
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
        # The password in the web2py database is formatted as follows:
        # alg$salt$hash
        # We need to grab the salt and provide that to the CRYPT function
        # which we import from pydal for now.  Once we are completely off of
        # web2py then this will change.  The ``web2py_private_key`` is an environment
        # variable that comes from the ``private/auth.key`` file.
        salt = user.password_hash.split("$")[1]
        crypt = CRYPT(key=settings.web2py_private_key, salt=salt)
        if str(crypt(password)[0]) != user.password_hash:
            raise InvalidCredentialsException

    access_token = auth_manager.create_access_token(data={"sub": user.username})
    response = RedirectResponse(
        "http://localhost:8080/books/published/overview/index.html"
    )
    # *Important* We need to set the cookie here for the redirect in order for
    # the next page to validate.  This will also set the cookie in the browser
    # for future pages.
    auth_manager.set_cookie(response, access_token)
    return response
