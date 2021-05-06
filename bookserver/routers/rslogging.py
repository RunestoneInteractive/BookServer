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
from fastapi import APIRouter, Request, Cookie, Response

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
from ..schemas import LogItemIncoming, LogRunIncoming

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
        entry.sid = "Anonymous"

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
        return {"status": "OK", "idx": idx}
    else:
        return {"status": "FAIL"}


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
    return "done"


# runlog endpoint
# ---------------
# The `logRunEvent` client-side function calls this endpoint to record an activecode run
@router.post("/runlog")
def runlog(request: Request, response: Response, data: LogRunIncoming):
    # First add a useinfo entry for this run
    if request.state.user:
        if data.course != request.state.user.course_name:
            return json.dumps(
                dict(
                    log=False,
                    message="You appear to have changed courses in another tab.  Please switch to this course",
                )
            )
        data.sid = request.state.user.username
    else:
        if data.clientLoginStatus == "true":
            rslogger.error("Session Expired")
            return json.dumps(dict(log=False, message="Session Expired"))
        else:
            data.sid = "Anonymous"
    useinfo_dict = data.dict()
    useinfo_dict["course_id"] = useinfo_dict.pop("course")
    useinfo_dict["timestamp"] = datetime.utcnow()
    if data.errinfo != "success":
        useinfo_dict["event"] = "ac_error"
        useinfo_dict["act"] = str(error_info)[:512]
    else:
        useinfo_dict["act"] = "run"
        if "event" not in useinfo_dict:
            useinfo_dict["event"] = "activecode"

    create_useinfo_entry(UseinfoValidation(**useinfo_dict))

    # Now add an entry to the code table
    if request.state.user:
        if "to_save" in data and (data.to_save == "True" or data.to_save == "true"):
            entry = CodeValidator(**useinfo_dict)
            create_code_entry(entry)

            if data.partner:
                if same_class(request.state.username, data.partner):
                    comchar = COMMENT_MAP.get(data.lang, "#")
                    newcode = (
                        "{} This code was shared by {}\n\n".format(comchar, sid) + code
                    )
                    entry.code = newcode
                    create_code_entry(entry)
                else:
                    res = {
                        "message": "You must be enrolled in the same class as your partner"
                    }
                    return res

    res = {"log": True}
    return res


def same_class(user1: AuthUserValidator, user2: str) -> bool:
    user2 = fetch_user(user2)
    return user1.course_id == user2.course_id
