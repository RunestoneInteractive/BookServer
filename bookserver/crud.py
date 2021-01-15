# *************************************************
# |docname| - reusable functions for our data model
# *************************************************
# Create Retrieve Update and Delete (CRUD) functions for database tables
#
# Rather than litter the code with raw database queries the vast majority should be
# turned into reusable functions that are defined in this file.
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
from .db import database as db
import sqlalchemy
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
async def create_useinfo_entry(log_entry: schemas.LogItemIncoming):
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
async def create_answer_table_entry(log_entry: schemas.LogItem):
    values = {
        k: v
        for k, v in log_entry.dict().items()
        # filter out fields that do not go in an answer table
        if v is not None
        and k not in ["event", "act", "timezoneoffset", "clientLoginStatus"]
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
    query_data: schemas.AssessmentRequest,
) -> list[sqlalchemy.engine.RowProxy]:
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


async def fetch_course(course_name: str) -> sqlalchemy.engine.RowProxy:
    query = select([models.courses]).where(models.courses.c.course_name == course_name)
    res = await db.fetch_one(query)

    return res
