from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..schemas import LogItem, LogItemIncoming
from ..crud import create_useinfo_entry
from ..database import database as db

#
# Setup the router object for the endpoints defined in this file.  These will
# be connected to the main application in main.py
#
router = APIRouter(
    prefix="/logger",  # shortcut so we don't have to repeat this part
    tags=["logger"],  # groups all logger tags together in the docs
)


@router.post("/bookevent")
async def log_book_event(entry: LogItemIncoming): #, db: Session = Depends(get_db)):
    """
    This endpoint is called to log information for nearly every click that happens in the textbook.
    It uses the `LogItem` object to define the JSON payload it gets from a page of a book.
    """
    idx = await create_useinfo_entry(db, entry)
    if idx:
        return {"status": "OK", "idx": idx}
    else:
        return {"status": "FAIL"}
