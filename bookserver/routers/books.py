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
import os.path
import posixpath
from datetime import datetime

# Third-party imports
# -------------------
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import constr

# Local application imports
# -------------------------
from ..applogger import rslogger
from ..config import settings
from ..crud import create_useinfo_entry, fetch_course
from ..models import UseinfoValidation
from ..session import auth_manager

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
    filepath = safe_join(
        settings.book_path, course, "build", course, "_static", filepath
    )
    rslogger.debug(f"GETTING: {filepath}")
    return FileResponse(filepath)


@router.get("/published/{course:str}/_images/{filepath:path}")
async def get_image(course: str, filepath: str):
    filepath = safe_join(
        settings.book_path, course, "build", course, "_images", filepath
    )
    rslogger.debug(f"GETTING: {filepath}")
    return FileResponse(filepath)


# Basic page renderer
# ===================
# To see the output of this endpoint, see http://localhost:8080/books/published/overview/index.html.
@router.api_route(
    "/published/{course:str}/{pagepath:path}",
    methods=["GET", "POST"],
    response_class=HTMLResponse,
)
async def serve_page(
    request: Request,
    course: constr(max_length=512),  # type: ignore
    pagepath: constr(max_length=512),  # type: ignore
    user=Depends(auth_manager),
):
    rslogger.debug(f"user = {user}")
    course_row = await fetch_course(course)
    if not course_row:
        raise HTTPException(status_code=404, detail=f"Course {course} not found")

    templates = Jinja2Templates(
        directory=safe_join(settings.book_path, course_row.base_course, "build", course)
    )
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
    await create_useinfo_entry(
        UseinfoValidation(
            event="page",
            act="view",
            div_id=pagepath,
            course_id=course,
            sid=user.username,
            timestamp=datetime.utcnow(),
        )
    )
    context = dict(
        request=request,
        course_name=course,
        base_course=course,
        user_id=user.username,
        # TODO
        user_email="bonelake@mac.com",
        downloads_enabled="false",
        allow_pairs="false",
        activity_info={},
        settings=settings,
        is_logged_in="false",
        is_instructor="true",
        enable_compare_me="true",
        readings=[],
    )
    # See `templates <https://fastapi.tiangolo.com/advanced/templates/>`_.
    return templates.TemplateResponse(pagepath, context)


# Utilities
# =========
# This is copied verbatim from https://github.com/pallets/werkzeug/blob/master/werkzeug/security.py#L30.
_os_alt_seps = list(
    sep for sep in [os.path.sep, os.path.altsep] if sep not in (None, "/")
)


# This is copied verbatim from https://github.com/pallets/werkzeug/blob/master/werkzeug/security.py#L216.
def safe_join(directory, *pathnames):
    """Safely join ``directory`` and one or more untrusted ``pathnames``.  If this
    cannot be done, this function returns ``None``.

    :directory: the base directory.
    :pathnames: the untrusted pathnames relative to that directory.
    """
    parts = [directory]
    for filename in pathnames:
        if filename != "":
            filename = posixpath.normpath(filename)
        for sep in _os_alt_seps:
            if sep in filename:
                return None
        if os.path.isabs(filename) or filename == ".." or filename.startswith("../"):
            return None
        parts.append(filename)
    return posixpath.join(*parts)
