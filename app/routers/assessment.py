from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..schemas import LogItem, LogItemIncoming
from ..crud import create_useinfo_entry
from ..db import database as db

#
# Setup the router object for the endpoints defined in this file.  These will
# be connected to the main application in main.py
#
router = APIRouter(
    prefix="/assessment",  # shortcut so we don't have to repeat this part
    tags=["logger"],  # groups all logger tags together in the docs
)


@router.get("/results")
def getAssessResults():
    pass
