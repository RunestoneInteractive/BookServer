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
# None. (Or the imports.)
#
# Third-party imports
# -------------------
# :index:`todo`: **Lots of unused imports...can we deletet these?**
from fastapi import APIRouter, Depends  # noqa F401

# Local application imports
# -------------------------
from ..crud import EVENT2TABLE, create_answer_table_entry, create_useinfo_entry
from ..schemas import LogItem, LogItemIncoming  # noqa F401
from ..applogger import rslogger

# Routing
# =======
# See `APIRouter config` for an explanation of this approach.
router = APIRouter(
    prefix="/logger",
    tags=["logger"],
)


@router.post("/bookevent")
async def log_book_event(entry: LogItem):
    """
    This endpoint is called to log information for nearly every click that happens in the textbook.
    It uses the ``LogItem`` object to define the JSON payload it gets from a page of a book.
    """
    idx = await create_useinfo_entry(entry)
    if entry.event in EVENT2TABLE:
        ans_idx = await create_answer_table_entry(entry)
    else:
        ans_idx = True

    rslogger.debug(ans_idx)
    if idx and ans_idx:
        return {"status": "OK", "idx": idx}
    else:
        return {"status": "FAIL"}
