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
from fastapi import FastAPI, Request, Depends, Cookie
from typing import Optional

# Local application imports
# -------------------------
from .routers import assessment
from .routers import auth
from .routers import books
from .routers import rslogging
from .db import engine, database
from .models import metadata
from .session import auth_manager
from bookserver.applogger import rslogger

# FastAPI setup
# =============
# :index:`todo`: This should be moved to a Alembic function for migration.
metadata.create_all(bind=engine)

app = FastAPI()

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
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port="8080")
