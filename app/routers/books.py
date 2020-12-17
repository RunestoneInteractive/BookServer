#
# Serve book pages from their template
#
import logging

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse

from ..schemas import LogItem, LogItemIncoming
from ..crud import create_useinfo_entry
from ..database import get_db
from config import settings

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

#
# Setup the router object for the endpoints defined in this file.  These will
# be connected to the main application in main.py
#
router = APIRouter(
    prefix="/books",  # shortcut so we don't have to repeat this part
    tags=["books"],  # groups all logger tags together in the docs
)

# Static Asset renderers
# https://fastapi.tiangolo.com/tutorial/static-files/?h=+staticfiles#use-staticfiles
# https://fastapi.tiangolo.com/advanced/custom-response/?h=+filere#fileresponse
# for paths like: /books/published/basecourse/_static/rest
# If it is fast and efficient to handle it here it would be great.  We currently avoid
# any static file contact with web2py and handle static files upstream with nginx directly
# Note the use of the path type for filepath in the decoration.  If you don't use path it
# seems to only get you the `next` part of the path /pre/vious/next/the/rest
@router.get("/published/{course:str}/_static/{filepath:path}")
async def get_static(course:str, filepath:str):
    filepath = f"/Users/bmiller/Runestone/{course}/build/{course}/_static/{filepath}"
    logger.debug(f"GETTING: {filepath}")
    return FileResponse(filepath)
    
@router.get("/published/{course:str}/_images/{filepath:path}")
async def get_image(course:str, filepath:str):
    filepath = f"/Users/bmiller/Runestone/{course}/build/{course}/_images/{filepath}"
    logger.debug(f"GETTING: {filepath}")
    return FileResponse(filepath)

# Basic page renderer
# http://localhost:8080/books/published/overview/index.html
# https://fastapi.tiangolo.com/advanced/templates/?h=+template
@router.get(
    "/published/{course:str}/{pagepath:path}",
    response_class=HTMLResponse,
)
async def serve_page(request: Request, course: str, pagepath: str):
    templates = Jinja2Templates(
        directory=f"/Users/bmiller/Runestone/{course}/build/{course}"
    )
    # request.application -- NA for FastAPI
    # course_name
    # base_course
    # user_email
    # user_id
    # downloads_enabled
    # allow_pairs
    # activity_info
    # settings.google_ga
    context = dict(
        request=request,
        course_name=course,
        base_course=course,
        user_id="bmiller",
        user_email="bonelake@mac.com",
        downloads_enabled="false",
        allow_pairs="false",
        activity_info={},
        settings=settings,
        is_logged_in="false",
        is_instructor="true",
        readings = [],
    )
    return templates.TemplateResponse(pagepath, context)
