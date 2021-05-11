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

# Third-party imports
# -------------------
from fastapi import APIRouter, Request, status

# Local application imports
# -------------------------
from ..applogger import rslogger
from ..crud import fetch_last_answer_table_entry
from ..schemas import AssessmentRequest
from ..session import is_instructor
from ..internal.utils import make_json_response

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
async def get_assessment_results(
    request_data: AssessmentRequest,
    request: Request,
):
    if not request.state.user:
        return make_json_response(
            status=status.HTTP_401_UNAUTHORIZED, detail="not logged in"
        )
    # if the user is not logged in an HTTP 401 will be returned.
    # Otherwise if the user is an instructor then use the provided
    # sid (it could be any student in the class) If none is provided then
    # use the user objects username
    if await is_instructor(request):
        if not request_data.sid:
            request_data.sid = request.state.user.username
    else:
        if request_data.sid:
            # someone is attempting to spoof the api
            return make_json_response(
                status=status.HTTP_401_UNAUTHORIZED, detail="not an instructor"
            )
        request_data.sid = request.state.user.username

    row = await fetch_last_answer_table_entry(request_data)
    if not row or row.id is None:
        return make_json_response(detail="no data")

    # :index:`todo``: **port the serverside grading** code::
    #
    #   do_server_feedback, feedback = is_server_feedback(div_id, course)
    #   if do_server_feedback:
    #       correct, res_update = fitb_feedback(rows.answer, feedback)
    #       res.update(res_update)
    rslogger.debug(f"Returning {row}")
    return make_json_response(detail=row)
