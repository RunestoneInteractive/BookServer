# *************************
# |docname| - Runestone API
# *************************
# This module implements the API that the Runestone Components use to get results from assessment components
#
# *     multiple choice
# *     fill in the blank
# *     parsons problems
# *     drag and dorp
# *     clickable area
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8`_.
#
# Standard library
# ----------------
import datetime

# Third-party imports
# -------------------
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

# Local application imports
# -------------------------
from ..schemas import LogItem, LogItemIncoming
from ..crud import create_useinfo_entry, fetch_assessment_result
from ..db import database as db

# Setup
# =====
# Setup the router object for the endpoints defined in this file.  These will
# be connected to the main application in main.py
#
router = APIRouter(
    prefix="/assessment",  # shortcut so we don't have to repeat this part
    tags=["logger"],  # groups all logger tags together in the docs
)


@router.get("/results")
# getAssessResults
# ----------------
#
async def getAssessResults(
    course: str,
    div_id: str,
    event: str,
    sid: Optional[str] = None,
    deadline: Optional[str] = None,
):
    # if (
    #     verifyInstructorStatus(auth.user.course_name, auth.user) and request.vars.sid
    # ):  # retrieving results for grader
    #     sid = request.vars.sid
    # else:
    #     sid = auth.user.username

    # TODO This whole thing is messy - get the deadline from the assignment in the db
    if deadline:
        try:
            deadline = parse(_canonicalize_tz(request.vars.deadline))
            tzoff = session.timezoneoffset if session.timezoneoffset else 0
            deadline = deadline + datetime.timedelta(hours=float(tzoff))
            deadline = deadline.replace(tzinfo=None)
        except Exception:
            logger.error("Bad Timezone - {}".format(request.vars.deadline))
            deadline = datetime.datetime.utcnow()
    else:
        deadline = datetime.datetime.utcnow()

    # Identify the correct event and query the database so we can load it from the server

    row = await fetch_assessment_result(db, event, course, sid, div_id)
    if not row:
        return ""  # server doesn't have it so we load from local storage instead

    # construct the return value from the result
    res = dict(row)

    # TODO: port the serverside grading code::
    #
    #   do_server_feedback, feedback = is_server_feedback(div_id, course)
    #   if do_server_feedback:
    #       correct, res_update = fitb_feedback(rows.answer, feedback)
    #       res.update(res_update)

    return res
