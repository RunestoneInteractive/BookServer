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
from ..crud import (
    count_useinfo_for,
    fetch_code,
    fetch_course,
    fetch_last_answer_table_entry,
    fetch_last_poll_response,
    fetch_poll_summary,
)
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
    res["acid"] = acid
    res["sid"] = sid
    # get the code they saved in chronological order; id order gets that for us
    r = await fetch_code(sid, acid, course_id)  # type: ignore
    res["history"] = [row.code for row in r]
    res["timestamps"] = [
        row.timestamp.replace(tzinfo=datetime.timezone.utc).isoformat() for row in r
    ]

    return make_json_response(detail=res)


# Used by :ref:`compareAnswers`
@router.get("/getaggregateresults")
async def getaggregateresults(request: Request, div_id: str, course: str):
    question = div_id
    course_name = course

    if not request.state.user:
        return make_json_response(
            status=status.HTTP_401_UNAUTHORIZED,
            detail=dict(answerDict={}, misc={}, emess="You must be logged in"),
        )

    if course_name in (
        "thinkcspy",
        "pythonds",
        "fopp",
        "csawesome",
        "apcsareview",
        "StudentCSP",
    ):
        start_date = datetime.datetime.utcnow() - datetime.timedelta(days=90)
    else:
        course = await fetch_course(course_name)
        start_date = course.term_start_date

    result = await count_useinfo_for(question, course_name, start_date)

    tdata = {}
    tot = 0
    for row in result:
        tdata[row[0]] = row[1]
        tot += row[1]

    tot = float(tot)
    rdata = {}
    miscdata = {}
    correct = ""
    if tot > 0:
        for key in tdata:
            all_a = key.split(":")
            try:
                answer = all_a[1]
                if "correct" in key:
                    correct = answer
                count = int(tdata[key])
                if answer in rdata:
                    count += rdata[answer] / 100.0 * tot
                pct = round(count / tot * 100.0)

                if answer != "undefined" and answer != "":
                    rdata[answer] = pct
            except Exception as e:
                rslogger.error("Bad data for %s data is %s -- %s" % (question, key, e))

    miscdata["correct"] = correct
    miscdata["course"] = course

    returnDict = dict(answerDict=rdata, misc=miscdata)

    # if instructor:
    # There is little value to doing this now when the instructor
    # Dashboard provides more and better detail
    #     resultList = _getStudentResults(question)
    #     returnDict["reslist"] = resultList

    return make_json_response(detail=returnDict)


@router.get("/getpollresults")
async def getpollresults(request: Request, course: str, div_id: str):

    # fetch summary of poll answers
    result = await fetch_poll_summary(div_id, course)

    opt_counts = {}

    for row in result:
        rslogger.debug(row)
        val = int(row[0])
        opt_counts[val] = row[1]

    opt_num = max(opt_counts.keys()) if opt_counts else 0
    for i in range(opt_num):
        if i not in opt_counts:
            opt_counts[i] = 0
    # opt_list holds the option numbers from smallest to largest
    # count_list[i] holds the count of responses that chose option i
    opt_list = sorted(opt_counts.keys())
    count_list = []
    for i in opt_list:
        count_list.append(opt_counts[i])

    total = sum(opt_counts.values())
    user_res = None
    if request.state.user:
        user_res = await fetch_last_poll_response(
            request.state.user.username, course, div_id
        )
    if user_res:
        my_vote = user_res.act
    else:
        my_vote = -1

    return make_json_response(
        detail=dict(total=total, opt_counts=opt_counts, div_id=div_id, my_vote=my_vote)
    )


# def gettop10Answers():
#     course = request.vars.course
#     question = request.vars.div_id
#     response.headers["content-type"] = "application/json"
#     rows = []

#     try:
#         dbcourse = db(db.courses.course_name == course).select(**SELECT_CACHE).first()
#         count_expr = db.fitb_answers.answer.count()
#         rows = db(
#             (db.fitb_answers.div_id == question)
#             & (db.fitb_answers.course_name == course)
#             & (db.fitb_answers.timestamp > dbcourse.term_start_date)
#         ).select(
#             db.fitb_answers.answer,
#             count_expr,
#             groupby=db.fitb_answers.answer,
#             orderby=~count_expr,
#             limitby=(0, 10),
#         )
#         res = [
#             {"answer": clean(row.fitb_answers.answer), "count": row[count_expr]}
#             for row in rows
#         ]
#     except Exception as e:
#         logger.debug(e)
#         res = "error in query"

#     miscdata = {"course": course}
#     _getCorrectStats(
#         miscdata, "fillb"
#     )  # TODO: rewrite _getCorrectStats to use xxx_answers

#     if auth.user and verifyInstructorStatus(course, auth.user.id):  # noqa: F405
#         resultList = _getStudentResults(question)
#         miscdata["reslist"] = resultList

#     return json.dumps([res, miscdata])
