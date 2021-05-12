# ******************************************************
# |docname| - Provide the ``hsblog`` (kind of) endpoint?
# ******************************************************
# :index:`docs to write`: **Description here...**
#
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8`_.
#
# Standard library
# ----------------
from datetime import datetime
import json
from typing import Optional

#
# Third-party imports
# -------------------
from fastapi import APIRouter, Request, Cookie, Response, status

# Local application imports
# -------------------------
from ..applogger import rslogger
from ..crud import (
    EVENT2TABLE,
    create_answer_table_entry,
    create_code_entry,
    create_useinfo_entry,
    fetch_user,
)
from ..models import (
    AuthUserValidator,
    CodeValidator,
    UseinfoValidation,
    validation_tables,
)
from ..schemas import LogItemIncoming, LogRunIncoming, TimezoneRequest
from ..internal.utils import make_json_response

# Routing
# =======
# See `APIRouter config` for an explanation of this approach.
router = APIRouter(
    prefix="/logger",
    tags=["logger"],
)

COMMENT_MAP = {
    "sql": "--",
    "python": "#",
    "java": "//",
    "javascript": "//",
    "c": "//",
    "cpp": "//",
}


# .. _log_book_event endpoint:
#
# log_book_event endpoint
# -----------------------
# See :ref:`logBookEvent`.
@router.post("/bookevent")
async def log_book_event(entry: LogItemIncoming, request: Request):
    """
    This endpoint is called to log information for nearly every click that happens in the textbook.
    It uses the ``LogItemIncoming`` object to define the JSON payload it gets from a page of a book.
    """
    # The middleware will set the user if they are logged in.
    if request.state.user:
        entry.sid = request.state.user.username
    else:
        return make_json_response(status.HTTP_401_UNAUTHORIZED, detail="Not logged in")

    # Always use the server's time.
    entry.timestamp = datetime.utcnow()
    # The endpoint receives a ``course_name``, but the ``useinfo`` table calls this ``course_id``. Rename it.
    useinfo_dict = entry.dict()
    useinfo_dict["course_id"] = useinfo_dict.pop("course_name")
    # This will validate the fields.  If a field does not validate
    # an error will be raised and a 422 response code will be returned
    # to the caller of the API
    useinfo_entry = UseinfoValidation(**useinfo_dict)
    rslogger.debug(useinfo_entry)
    idx = await create_useinfo_entry(useinfo_entry)
    if entry.event in EVENT2TABLE:
        table_name = EVENT2TABLE[entry.event]
        valid_table = validation_tables[table_name].from_orm(entry)
        ans_idx = await create_answer_table_entry(valid_table, entry.event)
        rslogger.debug(ans_idx)

    if idx:
        return make_json_response(status=status.HTTP_201_CREATED, detail=idx)
    else:
        return make_json_response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/set_tz_offset")
def set_tz_offset(
    response: Response, tzreq: TimezoneRequest, RS_info: Optional[str] = Cookie(None)
):
    if RS_info:
        values = json.loads(RS_info)
    else:
        values = {}
    values["tz_offset"] = tzreq.timezoneoffset
    response.set_cookie(key="RS_info", value=str(json.dumps(values)))
    rslogger.debug("setting timezone offset in session %s hours" % tzreq.timezoneoffset)

    return make_json_response()


# runlog endpoint
# ---------------
# The :ref:`logRunEvent` client-side function calls this endpoint to record an activecode run
@router.post("/runlog")
async def runlog(request: Request, response: Response, data: LogRunIncoming):
    # First add a useinfo entry for this run
    if request.state.user:
        if data.course != request.state.user.course_name:
            return make_json_response(
                status=status.HTTP_401_UNAUTHORIZED,
                detail="You appear to have changed courses in another tab.  Please switch to this course",
            )
        data.sid = request.state.user.username
    else:
        if data.clientLoginStatus == "true":
            rslogger.error("Session Expired")
            return make_json_response(
                status=status.HTTP_401_UNAUTHORIZED, detail="Session Expired"
            )
        else:
            return make_json_response(status=status.HTTP_401_UNAUTHORIZED)

    # everything after this assumes that the user is logged in

    useinfo_dict = data.dict()
    useinfo_dict["course_id"] = useinfo_dict.pop("course")
    useinfo_dict["timestamp"] = datetime.utcnow()
    if data.errinfo != "success":
        useinfo_dict["event"] = "ac_error"
        useinfo_dict["act"] = str(data.errinfo)[:512]
    else:
        useinfo_dict["act"] = "run"
        if "event" not in useinfo_dict:
            useinfo_dict["event"] = "activecode"

    await create_useinfo_entry(UseinfoValidation(**useinfo_dict))

    # Now add an entry to the code table

    if data.to_save:
        useinfo_dict["course_id"] = request.state.user.course_id
        entry = CodeValidator(**useinfo_dict)
        await create_code_entry(entry)

        if data.partner:
            if await same_class(request.state.username, data.partner):
                comchar = COMMENT_MAP.get(data.lang, "#")
                newcode = f"{comchar} This code was shared by {data.sid}\n\n{data.code}"
                entry.code = newcode
                await create_code_entry(entry)
            else:
                return make_json_response(
                    status=status.HTTP_207_MULTI_STATUS,
                    detail=[
                        {
                            "result": status.HTTP_401_UNAUTHORIZED,
                            "detail": "Partner data not saved, you must be enrolled in the same class as your partner",
                        },
                        {"result": status.HTTP_200_OK, "detail": None},
                    ],
                )

    return make_json_response(status=status.HTTP_201_CREATED)


async def same_class(user1: AuthUserValidator, user2: str) -> bool:
    u2 = await fetch_user(user2)
    return user1.course_id == u2.course_id
