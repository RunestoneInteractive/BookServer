# *************************************************
# |docname| - reusable functions for our data model
# *************************************************
# :index:`question`: Why is this named crud? It seems more like a db_utils.
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8`_.
#
# Standard library
# ----------------
# For ``time`, ``date``, and ``timedelta``.
from datetime import datetime

# Third-party imports
# -------------------
from databases import Database
from sqlalchemy import and_
from sqlalchemy.sql import select

# Local application imports
# -------------------------
from .applogger import rslogger
from . import models, schemas


# Map from the ``event`` field of a ``LogItemIncoming`` to the database table used to store data associated with this event.
EVENT2TABLE = {
    "clickableArea": "clickablearea_answers",
    "codelens1": "codelens_answers",
    "dragNdrop": "dragndrop_answers",
    "fillb": "fitb_answers",
    "lp": "lp_answers",
    "mChoice": "mchoice_answers",
    "parsons": "parsons_answers",
    "shortanswer": "shortanswer_answers",
    "unittest": "unittest_answers ",
}


# useinfo
# -------
async def create_useinfo_entry(db: Database, log_entry: schemas.LogItemIncoming):
    new_log = dict(
        sid="current_user",
        event=log_entry.event,
        act=log_entry.act,
        div_id=log_entry.div_id,
        timestamp=datetime.utcnow(),
        course_id=log_entry.course_name,
    )
    query = models.logitem.insert()
    await db.execute(query=query, values=new_log)
    return new_log


# xxx_answers
# -----------
async def create_answer_table_entry(db: Database, log_entry: schemas.LogItem):
    values = {
        k: v
        for k, v in log_entry.dict().items()
        # :index:`question`: **Why exclude** ``act``? Some types (clickablearea, shortanswer, etc) use this field. There's probably more conditional logic needed here based on the event type.
        if v is not None and k not in ["event", "act"]
    }
    values["timestamp"] = datetime.utcnow()
    # :index:`TODO`
    values["sid"] = "current_user"
    rslogger.debug(f"hello from create at {values}")
    tbl = models.answer_tables[EVENT2TABLE[log_entry.event]]
    query = tbl.insert()
    res = await db.execute(query=query, values=values)
    return res


# :index:`TODO`: **I think the idea here**, but the implementation will still need some special cases for getting the specific data for all the question types.
async def fetch_last_answer_table_entry(
    db: Database, query_data: schemas.AssessmentRequest
):
    assessment = EVENT2TABLE[query_data.event]
    tbl = models.answer_tables[assessment]
    query = (
        select([tbl])
        .where(
            and_(
                tbl.c.div_id == query_data.div_id,
                tbl.c.course_name == query_data.course,
                tbl.c.sid == query_data.sid,
            )
        )
        .order_by(tbl.c.timestamp.desc())
    )

    res = await db.fetch_one(query)

    return res
