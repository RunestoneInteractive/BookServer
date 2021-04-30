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

#
# Third-party imports
# -------------------
from bookserver.schemas import LogItem
from ..models import UseinfoValidation, validation_tables
from fastapi import APIRouter

# Local application imports
# -------------------------
from ..crud import EVENT2TABLE, create_answer_table_entry, create_useinfo_entry
from ..applogger import rslogger

# Routing
# =======
# See `APIRouter config` for an explanation of this approach.
router = APIRouter(
    prefix="/logger",
    tags=["logger"],
)


# .. _log_book_event endpoint:
#
# log_book_event endpoint
# -----------------------
# See :ref:`logBookEvent`.
@router.post("/bookevent")
async def log_book_event(entry: LogItem):
    """
    This endpoint is called to log information for nearly every click that happens in the textbook.
    It uses the ``LogItem`` object to define the JSON payload it gets from a page of a book.
    """
    # Always use the server's time.
    entry.timestamp = datetime.utcnow()
    # The endpoint receives a ``course_name``, but the ``useinfo`` table calls this ``course_id``. Rename it.
    useinfo_dict = entry.dict()
    useinfo_dict["course_id"] = useinfo_dict.pop("course_name")
    try:
        useinfo_entry = UseinfoValidation(**useinfo_dict)
    except Exception:
        # TODO!
        raise
    idx = await create_useinfo_entry(useinfo_entry)
    if entry.event in EVENT2TABLE:
        table_name = EVENT2TABLE[entry.event]
        try:
            valid_table = validation_tables[table_name].from_orm(entry)
        except Exception:
            # TODO: report this in some better way.
            raise
        ans_idx = await create_answer_table_entry(valid_table, entry.event)
    else:
        ans_idx = True

    rslogger.debug(ans_idx)
    if idx and ans_idx:
        return {"status": "OK", "idx": idx}
    else:
        return {"status": "FAIL"}
