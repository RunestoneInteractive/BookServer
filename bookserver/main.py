# *********************************
# |docname| - Define the BookServer
# *********************************
# :index:`docs to write`: notes on this design. :index:`question`: Why is there an empty module named ``dependencies.py``?
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8`_.
#
# Standard library
# ----------------
import json
import os
import traceback
import datetime

# Third-party imports
# -------------------
from fastapi import FastAPI, Request, Depends, Cookie, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic.error_wrappers import ValidationError
from typing import Optional

# Local application imports
# -------------------------
from .applogger import rslogger
from .config import settings
from .crud import create_initial_courses_users
from .db import init_models, term_models
from .internal.feedback import init_graders
from .routers import assessment
from .routers import auth
from .routers import books
from .routers import rslogging
from .routers import discuss
from .session import auth_manager


# FastAPI setup
# =============
# _`setting root_path`: see `root_path <root_path>`; this approach comes from `github <https://github.com/tiangolo/uvicorn-gunicorn-fastapi-docker/issues/55#issuecomment-879903517>`_.
kwargs = {}
if root_path := os.environ.get("ROOT_PATH"):
    kwargs["root_path"] = root_path
app = FastAPI(**kwargs)  # type: ignore
rslogger.info(f"Serving books from {settings.book_path}.\n")

# Install the auth_manager as middleware This will make the user
# part of the request ``request.state.user`` `See FastAPI_Login Advanced <https://fastapi-login.readthedocs.io/advanced_usage/>`_
auth_manager.useRequest(app)

# Routing
# -------
#
# .. _included routing:
#
# Included
# ^^^^^^^^
app.include_router(rslogging.router)
app.include_router(books.router)
app.include_router(assessment.router)
app.include_router(auth.router)
app.include_router(discuss.router)


# Defined here
# ^^^^^^^^^^^^
@app.on_event("startup")
async def startup():
    # Check/create paths used by the server.
    os.makedirs(settings.book_path, exist_ok=True)
    os.makedirs(settings.error_path, exist_ok=True)
    assert (
        settings.runestone_path.exists()
    ), f"Runestone appplication in web2py path {settings.runestone_path} does not exist."

    await init_models()
    await create_initial_courses_users()
    init_graders()


@app.on_event("shutdown")
async def shutdown():
    await term_models()


#
# If the user supplies a timezone offset we'll store it in the RS_info cookie
# lots of API calls need this so rather than having each process the cookie
# we'll drop the value into request.state this will make it generally avilable
#
@app.middleware("http")
async def get_session_object(request: Request, call_next):
    tz_cookie = request.cookies.get("RS_info")
    if tz_cookie:
        vals = json.loads(tz_cookie)
        request.state.tz_offset = vals["tz_offset"]
        rslogger.info(f"Timzone offset: {request.state.tz_offset}")
    response = await call_next(request)
    return response


@app.get("/protected")
async def protected_route(request: Request, access_token: Optional[str] = Cookie(None)):

    rslogger.debug(access_token)
    res = await auth_manager.get_current_user(access_token)
    rslogger.debug(res)
    return {"user": res}


@app.get("/protected2")
async def protected_route2(request: Request, user=Depends(auth_manager)):
    rslogger.debug("here")
    return {"user": user}


@app.get("/")
def read_root():
    return {"Hello": "World"}


class NotAuthenticatedException(Exception):
    pass


auth_manager.not_authenticated_exception = NotAuthenticatedException


# Fast API makes it very easy to handle different error types in an
# elegant way through the use of middleware to catch particular
# exception types.
@app.exception_handler(NotAuthenticatedException)
def auth_exception_handler(request: Request, exc: NotAuthenticatedException):
    """
    Redirect the user to the login page if not logged in
    """
    rslogger.debug("User is not logged in, redirecting")
    return RedirectResponse(url=f"{settings.login_url}")


# See:  https://fastapi.tiangolo.com/tutorial/handling-errors/#use-the-requestvalidationerror-body
# for more details on validation errors.
@app.exception_handler(ValidationError)
def level2_validation_handler(request: Request, exc: ValidationError):
    """
    Most validation errors are caught immediately, but we do some
    secondary validation when populating our xxx_answers tables
    this catches those and returns a 422
    """
    rslogger.error(exc)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors()}),
    )


@app.exception_handler(Exception)
def generic_error_handler(request: Request, exc: Exception):
    """
    Most validation errors are caught immediately, but we do some
    secondary validation when populating our xxx_answers tables
    this catches those and returns a 422
    """
    rslogger.error("UNHANDLED ERROR")
    rslogger.error(exc)
    date = datetime.datetime.utcnow().strftime("%Y_%m_%d-%I.%M.%S_%p")
    with open(f"{settings.error_path}/{date}_traceback.txt", "w") as f:
        traceback.print_tb(exc.__traceback__, file=f)
        f.write(f"Error Message: \n{str(exc)}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder({"detail": exc}),
    )
