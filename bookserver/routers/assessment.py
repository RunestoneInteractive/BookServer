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
from typing import Optional, Dict, Any

# Third-party imports
# -------------------
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

# Local application imports
# -------------------------
from ..applogger import rslogger
from ..crud import fetch_code, fetch_last_answer_table_entry
from ..internal.utils import make_json_response
from ..schemas import AssessmentRequest
from ..session import is_instructor

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
    # mypy complains that ``row.id`` doesn't exist (true, but the return type wasn't exact and this does exist).
    if not row or row.id is None:  # type: ignore
        return make_json_response(detail="no data")

    # :index:`todo``: **port the serverside grading** code::
    #
    #   do_server_feedback, feedback = is_server_feedback(div_id, course)
    #   if do_server_feedback:
    #       correct, res_update = fitb_feedback(rows.answer, feedback)
    #       res.update(res_update)
    rslogger.debug(f"Returning {row}")
    return make_json_response(detail=row)


# Define a simple model for the gethist request.
# If you just try to specify the two fields as parameters it expects
# them to be in a query string.
class HistoryRequest(BaseModel):
    # ``acid`` : id of the active code block also called div_id
    acid: str
    # ``sid``: optional identifier for the owner of the code (username)
    sid: Optional[str] = None


@router.post("/gethist")
async def get_history(request: Request, request_data: HistoryRequest):
    """
    return the history of saved code by this user for a particular
    active code id (acid) -- known as div_id elsewhere
    See :ref:`addHistoryScrubber`

    :Parameters:
        - See HistoryRequest

    :Return:
        - json object with a detail key that references a dictionary

        ::

            { "acid": div_id,
              "sid" : id of student requested,
              "history": [code, code, code],
              "timestamps": [ts, ts, ts]
            }
    """
    acid = request_data.acid
    sid = request_data.sid
    # if request_data.sid then we know this is being called from the grading interface
    # so verify that the actual user is an instructor.
    if sid:
        if request.state.user and request.state.user.username != sid:
            if await is_instructor(request):
                course_id = request.state.user.course_id
            else:
                raise HTTPException(401)
        else:
            raise HTTPException(401)
    # In this case, the request is simply from a student, so we will use
    # their logged in username
    elif request.state.user:
        sid = request.state.user.username
        course_id = request.state.user.course_id
    else:
        raise HTTPException(401)

    res: Dict[str, Any] = {}
    if sid:
        res["acid"] = acid
        res["sid"] = sid
        # get the code they saved in chronological order; id order gets that for us
        r = await fetch_code(sid, acid, course_id)
        res["history"] = [row.code for row in r]
        res["timestamps"] = [
            row.timestamp.replace(tzinfo=datetime.timezone.utc).isoformat() for row in r
        ]

    return make_json_response(detail=res)
