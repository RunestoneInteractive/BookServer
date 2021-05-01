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
# None.

# Third-party imports
# -------------------
from fastapi import APIRouter

# Local application imports
# -------------------------
from ..applogger import rslogger
from ..crud import fetch_last_answer_table_entry
from ..schemas import AssessmentRequest

# Routing
# =======
# See `APIRouter config` for an explanation of this approach.
router = APIRouter(
    prefix="/assessment",
    tags=["assessment"],
)


# getAssessResults
# ----------------
@router.post("/results")
async def get_assessment_results(request_data: AssessmentRequest):
    # if (
    #     verifyInstructorStatus(auth.user.course_name, auth.user) and request.vars.sid
    # ):  # retrieving results for grader
    #     sid = request.vars.sid
    # else:
    #     sid = auth.user.username

    # Identify the correct event and query the database so we can load it from the server

    row = await fetch_last_answer_table_entry(request_data)
    if not row:
        return ""  # server doesn't have it so we load from local storage instead

    # construct the return value from the XXXAnswer class
    # TODO: Seems like something like this should be built in to sqlalchemy?
    res = row.to_dict()

    # :index:`todo``: **port the serverside grading** code::
    #
    #   do_server_feedback, feedback = is_server_feedback(div_id, course)
    #   if do_server_feedback:
    #       correct, res_update = fitb_feedback(rows.answer, feedback)
    #       res.update(res_update)
    rslogger.debug(f"Returning {res}")
    return res
