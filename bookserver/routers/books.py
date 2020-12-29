# ***********************************
# |docname| - Serve pages from a book
# ***********************************
# :index:`docs to write`: how this works...
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
# :index:`todo`: **Lots of unused imports here...can we remove them?***

from fastapi import APIRouter, Depends, Request  # noqa F401
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

# Local application imports
# -------------------------
from bookserver.config import settings
from ..applogger import rslogger
from ..crud import create_useinfo_entry  # noqa F401
from ..schemas import LogItem, LogItemIncoming  # noqa F401

# .. _APIRouter config:
#
# Routing
# =======
# Setup the router object for the endpoints defined in this file.  These will
# be `connected <included routing>` to the main application in `../main.py`.
router = APIRouter(
    # shortcut so we don't have to repeat this part
    prefix="/books",
    # groups all logger `tags <https://fastapi.tiangolo.com/tutorial/path-operation-configuration/#tags>`_ together in the docs.
    tags=["books"],
)


# Options for static asset renderers:
#
# - `StaticFiles <https://fastapi.tiangolo.com/tutorial/static-files/?h=+staticfiles#use-staticfiles>`_. However, this assumes the static routes are known *a priori*, in contrast to books (with their static assets) that are dynamically added and removed.
# - Manually route static files, returning them using a `FileResponse <https://fastapi.tiangolo.com/advanced/custom-response/#fileresponse>`_. This is the approach taken.
#
# for paths like: ``/books/published/basecourse/_static/rest``.
# If it is fast and efficient to handle it here it would be great.  We currently avoid
# any static file contact with web2py and handle static files upstream with nginx directly; therefore, this is useful only for testing/a non-production environment.
# Note the use of the ``path``` type for filepath in the decoration.  If you don't use path it
# seems to only get you the ``next`` part of the path ``/pre/vious/next/the/rest``.
#
# :index:`todo`: **Routes for draft (instructor-only) books.**
@router.get("/published/{course:str}/_static/{filepath:path}")
async def get_static(course: str, filepath: str):
    # :index:`FIXME`: **Find a way to avoid a hard-coded path.** This fix is needed for the route below as well.
    #
    # :index:`todo`: **Are there any security concerns?** Could a malicious user pass a "path" of ``../../../private_files`` and access anything on the server?
    filepath = f"/Users/bmiller/Runestone/{course}/build/{course}/_static/{filepath}"
    rslogger.debug(f"GETTING: {filepath}")
    return FileResponse(filepath)


@router.get("/published/{course:str}/_images/{filepath:path}")
async def get_image(course: str, filepath: str):
    filepath = f"/Users/bmiller/Runestone/{course}/build/{course}/_images/{filepath}"
    rslogger.debug(f"GETTING: {filepath}")
    return FileResponse(filepath)


# Basic page renderer
# ===================
# To see the output of this endpoint, see http://localhost:8080/books/published/overview/index.html.
@router.get(
    "/published/{course:str}/{pagepath:path}",
    response_class=HTMLResponse,
)
async def serve_page(request: Request, course: str, pagepath: str):
    templates = Jinja2Templates(
        directory=f"/Users/bmiller/Runestone/{course}/build/{course}"
    )
    # :index:`todo`: **Fill in this from the database...**
    #
    # Notes::
    #
    #   request.application -- NA for FastAPI
    #   course_name
    #   base_course
    #   user_email
    #   user_id
    #   downloads_enabled
    #   allow_pairs
    #   activity_info
    #   settings.google_ga
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
        readings=[],
    )
    # See `templates <https://fastapi.tiangolo.com/advanced/templates/>`_.
    return templates.TemplateResponse(pagepath, context)
