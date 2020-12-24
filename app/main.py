# *********************************
# |docname| - Define the BookServer
# *********************************
# TODO notes on this design

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
from fastapi import FastAPI


# Local application imports
# -------------------------
from .routers import rslogging
from .routers import books
from .routers import assessment
from .db import engine, database
from app.models import metadata


# Code
# ====
# This should be moved to an Alembic function for migration
metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(rslogging.router)
app.include_router(books.router)
app.include_router(assessment.router)


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/")
def read_root():
    return {"Hello": "World"}
