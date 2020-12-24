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

#
# Third-party imports
# -------------------
from databases import Database
from sqlalchemy import and_
from sqlalchemy.sql import select

# Local application imports
# -------------------------
from . import models, schemas

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


async def create_useinfo_entry(db: Database, log_entry: schemas.LogItemIncoming):
    new_log = dict(
        sid="current_user",
        event=log_entry.event,
        act=log_entry.act,
        div_id=log_entry.div_id,
        timestamp=datetime.utcnow(),
    )
    query = models.logitem.insert()
    await db.execute(query=query, values=new_log)
    return new_log


async def create_answer_table_entry(db: Database, log_entry: schemas.LogItem):
    values = {k: v for k, v in log_entry.dict().items() if v is not None}
    tbl = models.answer_tables[EVENT2TABLE[log_entry.event]]
    query = tbl.insert()
    res = await db.execute(query=query, values=values)
    return res


async def fetch_assessment_result(
    db: Database, event: str, course: str, sid: str, div_id: str
):
    assessment = EVENT2TABLE[event]
    tbl = models.answer_tables[assessment]
    query = (
        select([tbl])
        .where(
            and_(
                tbl.c.div_id == div_id,
                tbl.c.course_name == course,
                tbl.c.sid == sid,
            )
        )
        .order_by(tbl.c.timestamp.desc())
    )

    res = await db.fetch_one(query)

    return res
