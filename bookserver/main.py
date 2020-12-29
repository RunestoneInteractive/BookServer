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
from fastapi import FastAPI

# Local application imports
# -------------------------
from .routers import rslogging
from .routers import books
from .routers import assessment
from .db import engine, database
from .models import metadata

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


# Defined here
# ^^^^^^^^^^^^
@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/")
def read_root():
    return {"Hello": "World"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port="8080")
