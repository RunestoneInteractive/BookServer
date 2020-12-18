from fastapi import FastAPI
from .routers import rslogging
from .routers import books
from .db import engine, database
from app.models import metadata

# This should be moved to an Alembic function for migration
metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(rslogging.router)
app.include_router(books.router)

@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/")
def read_root():
    return {"Hello": "World"}