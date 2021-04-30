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
# None.
#
# Third-party imports
# -------------------
from fastapi import FastAPI, Request, Depends, Cookie, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional
from pydantic.error_wrappers import ValidationError

# Local application imports
# -------------------------
from .routers import assessment
from .routers import auth
from .routers import books
from .routers import rslogging
from .db import init_models
from .session import auth_manager
from .config import settings
from bookserver.applogger import rslogger

# FastAPI setup
# =============
app = FastAPI()
print(f"Serving books from {settings.book_path}.\n")

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


# Defined here
# ^^^^^^^^^^^^
@app.on_event("startup")
async def startup():
    await init_models()


## @app.on_event("shutdown")
## async def shutdown():
##     await database.disconnect()


# this is just a simple example of adding a middleware
# it does not do anything useful.
@app.middleware("http")
async def get_session_object(request: Request, call_next):
    request.state.session = {"sessionid": 1234567}
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


@app.exception_handler(NotAuthenticatedException)
def auth_exception_handler(request: Request, exc: NotAuthenticatedException):
    """
    Redirect the user to the login page if not logged in
    """
    return RedirectResponse(url="/auth/login")


@app.exception_handler(ValidationError)
def level2_validation_handler(request: Request, exc: ValidationError):
    """
    Most validation errors are caught immediately, but we do some
    secondary validation when populating our xxx_answers tables
    this catches those and returns a 422
    """
    rslogger.debug(exc.json),

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors()}),
    )
