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
from datetime import datetime
import json
import os.path
import posixpath

# Third-party imports
# -------------------
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2.exceptions import TemplateNotFound
from pydantic import constr

# Local application imports
# -------------------------
from ..applogger import rslogger
from ..config import settings
from ..crud import (
    create_useinfo_entry,
    fetch_course,
    fetch_page_activity_counts,
    fetch_all_course_attributes,
)
from ..models import UseinfoValidation
from ..session import auth_manager, is_instructor

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


async def return_static_asset(course, kind, filepath):
    course_row = await fetch_course(course)
    filepath = safe_join(
        settings.book_path,
        course_row.base_course,
        "build",
        course_row.base_course,
        kind,
        filepath,
    )
    rslogger.debug(f"GETTING: {filepath}")
    if os.path.exists(filepath):
        return FileResponse(filepath)
    else:
        raise HTTPException(404)


# Todo: **Routes for draft (instructor-only) books.**
@router.get("/published/{course:str}/_images/{filepath:path}")
async def get_image(course: str, filepath: str):
    # Get the course row so we can use the base_course
    # We would like to serve book pages with the actual course name in the URL
    # instead of the base course.  This is a necessary step.
    return await return_static_asset(course, "_images", filepath)


@router.get("/published/{course:str}/_static/{filepath:path}")
async def get_static(course: str, filepath: str):
    # Get the course row so we can use the base_course
    # We would like to serve book pages with the actual course name in the URL
    # instead of the base course.  This is a necessary step.
    return await return_static_asset(course, "_static", filepath)


# Basic page renderer
# ===================
# To see the output of this endpoint, see http://localhost:8080/books/published/overview/index.html.
@router.api_route(
    "/published/{course_name:str}/{pagepath:path}",
    methods=["GET", "POST"],
    response_class=HTMLResponse,
)
async def serve_page(
    request: Request,
    course_name: constr(max_length=512),  # type: ignore
    pagepath: constr(max_length=512),  # type: ignore
    user=Depends(auth_manager),
):
    rslogger.debug(f"user = {user}, course name = {course_name}")
    # Make sure this course exists, and look up its base course.
    # Since these values are going to be read by javascript we
    # need to use lowercase true and false.
    if user:
        logged_in = "true"
        user_is_instructor = await is_instructor(request)
    else:
        logged_in = "false"
        activity_info = {}
        user_is_instructor = False

    course_row = await fetch_course(user.course_name)
    if not course_row:
        raise HTTPException(status_code=404, detail=f"Course {course_name} not found")
    rslogger.debug(f"Base course = {course_row.base_course}")
    chapter = os.path.split(os.path.split(pagepath)[0])[1]
    subchapter = os.path.basename(os.path.splitext(pagepath)[0])
    if user:
        activity_info = await fetch_page_activity_counts(
            chapter, subchapter, course_row.base_course, user.username, course_name
        )

    # The template path comes from the base course's name.
    templates = Jinja2Templates(
        directory=safe_join(
            settings.book_path,
            course_row.base_course,
            "published",
            course_row.base_course,
        )
    )
    course_attrs = await fetch_all_course_attributes(course_row.id)
    rslogger.debug(f"HEY COURSE ATTRS: {course_attrs}")
    # TODO set custom delimiters for PreTeXt books (https://stackoverflow.com/questions/33775085/is-it-possible-to-change-the-default-double-curly-braces-delimiter-in-polymer)
    # Books built with lots of LaTeX math in them are troublesome as they tend to have many instances
    # of `{{` and `}}` wich conflicts with the default Jinja2 start stop delimiters. Rather than
    # escaping all of the latex math the PreTeXt built books use different delimiters for the templates
    # templates.env is a reference to a Jinja2 Environment object
    # try - templates.env.block_start_string = "@@@+"
    # try - templates.env.block_end_string = "@@@-"

    if course_attrs.get("markup_system", "RST") == "PreTeXt":
        rslogger.debug(f"PRETEXT book found at path {pagepath}")
        templates.env.variable_start_string = "~._="
        templates.env.variable_end_string = "_.~"
        templates.env.globals.update({"URL": URL})

    #   TODO: provide the template google_ga as well as ad servings stuff
    #   settings.google_ga
    await create_useinfo_entry(
        UseinfoValidation(
            event="page",
            act="view",
            div_id=pagepath,
            course_id=course_name,
            sid=user.username,
            timestamp=datetime.utcnow(),
        )
    )
    context = dict(
        request=request,
        course_name=user.course_name,
        base_course=course_row.base_course,
        user_id=user.username,
        # _`root_path`: The server is mounted in a different location depending on how it's run (directly from gunicorn/uvicorn or under the ``/ns`` prefix using nginx). Tell the JS what prefix to use for Ajax requests. See also `setting root_path <setting root_path>` and the `FastAPI docs <https://fastapi.tiangolo.com/advanced/behind-a-proxy/>`_. This is then used in the ``eBookConfig`` of :doc:`runestone/common/project_template/_templates/plugin_layouts/sphinx_bootstrap/layout.html`.
        new_server_prefix=request.scope.get("root_path"),
        user_email=user.email if user else "",
        downloads_enabled="true" if course_row.downloads_enabled else "false",
        allow_pairs="true" if course_row.allow_pairs else "false",
        activity_info=json.dumps(activity_info),
        settings=settings,
        is_logged_in=logged_in,
        is_instructor="true" if user_is_instructor else "false",
        enable_compare_me="true"
        if course_attrs.get("enable_compare_me", False)
        else "false",
        readings=[],
        **course_attrs,
    )
    # See `templates <https://fastapi.tiangolo.com/advanced/templates/>`_.
    try:
        return templates.TemplateResponse(pagepath, context)
    except TemplateNotFound:
        raise HTTPException(
            status_code=404,
            detail=f"Page {pagepath} not found in base course {course_row.base_course}.",
        )


# Utilities
# =========
# This is copied verbatim from https://github.com/pallets/werkzeug/blob/master/werkzeug/security.py#L30.
_os_alt_seps = list(
    sep for sep in [os.path.sep, os.path.altsep] if sep not in (None, "/")
)


def URL(*argv):
    return "/".join(argv)


def XML(arg):
    return arg


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
