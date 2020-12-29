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
# :index:`todo`: **Lots of unused imports here...**
from dateutil.parser import parse
from fastapi import APIRouter, Depends

# Local application imports
# -------------------------
from ..applogger import rslogger
from ..crud import create_useinfo_entry, fetch_last_answer_table_entry  # noqa F401
from ..db import database as db
from ..internal.utils import canonicalize_tz
from ..schemas import AssessmentRequest, LogItem, LogItemIncoming  # noqa F401

# Routing
# =======
# See `APIRouter config` for an explanation of this approach.
router = APIRouter(
    prefix="/assessment",
    tags=["assessment"],
)


# getAssessResults
# ----------------
@router.get("/results")
async def get_assessment_results(request_data: AssessmentRequest = Depends()):
    # if (
    #     verifyInstructorStatus(auth.user.course_name, auth.user) and request.vars.sid
    # ):  # retrieving results for grader
    #     sid = request.vars.sid
    # else:
    #     sid = auth.user.username

    # :index:`todo`: **This whole thing is messy - get the deadline from the assignment in the db.**
    if request_data.deadline:
        try:
            deadline = parse(canonicalize_tz(request_data.deadline))
            tzoff = session.timezoneoffset if session.timezoneoffset else 0
            deadline = deadline + datetime.timedelta(hours=float(tzoff))
            deadline = deadline.replace(tzinfo=None)
        except Exception:
            rslogger.error(f"Bad Timezone - {request_data.deadline}")
            deadline = datetime.datetime.utcnow()
    else:
        request_data.deadline = datetime.datetime.utcnow()

    # Identify the correct event and query the database so we can load it from the server

    row = await fetch_last_answer_table_entry(db, request_data)
    if not row:
        return ""  # server doesn't have it so we load from local storage instead

    # construct the return value from the result
    res = dict(row)

    # :index:`todo``: **port the serverside grading** code::
    #
    #   do_server_feedback, feedback = is_server_feedback(div_id, course)
    #   if do_server_feedback:
    #       correct, res_update = fitb_feedback(rows.answer, feedback)
    #       res.update(res_update)

    return res
