#
# Serve book pages from their template
#
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..schemas import LogItem, LogItemIncoming
from ..crud import create_useinfo_entry
from ..database import get_db
from config import settings

#
# Setup the router object for the endpoints defined in this file.  These will
# be connected to the main application in main.py
#
router = APIRouter(
    prefix="/books",  # shortcut so we don't have to repeat this part
    tags=["books"],  # groups all logger tags together in the docs
)


@router.get(
    "/published/{course:str}/{chapter:str}/{subchapter:str}",
    response_class=HTMLResponse,
)
async def serve_page(request: Request, course: str, chapter: str, subchapter: str):
    templates = Jinja2Templates(
        directory=f"/Users/bmiller/Runestone/{course}/build/{course}/{chapter}"
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
    print(course, chapter, subchapter)
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
    )
    return templates.TemplateResponse(subchapter, context)
