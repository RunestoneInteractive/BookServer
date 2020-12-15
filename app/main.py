from fastapi import FastAPI
from .routers import rslogging
from .routers import books
from .database import engine
from app.models import Base

# This should be moved to an Alembic function for migration
Base.metadata.create_all(bind=engine)
app = FastAPI()
app.include_router(rslogging.router)
app.include_router(books.router)


@app.get("/")
def read_root():
    return {"Hello": "World"}
