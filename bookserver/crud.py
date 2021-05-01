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
# None.

# Third-party imports
# -------------------
from .db import async_session

# import sqlalchemy
from sqlalchemy import and_
from sqlalchemy.sql import select

# Local application imports
# -------------------------
from .applogger import rslogger
from . import schemas
from .models import (
    AuthUserValidator,
    Useinfo,
    AuthUser,
    Courses,
    UseinfoValidation,
    answer_tables,
)


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
# TODO: mypy can't use this Pydantic class as a validator.Per https://pydantic-docs.helpmanual.io/usage/mypy/, perhaps this class contains annotations that are not the "annotation-only version of required fields", such as ``constr``?
async def create_useinfo_entry(log_entry: UseinfoValidation):  # type: ignore
    async with async_session() as session:
        new_entry = Useinfo(**log_entry.dict())  # type: ignore
        rslogger.debug(f"New Entry = {new_entry}")
        rslogger.debug(f"session = {session}")
        async with session.begin():
            r = session.add(new_entry)
            rslogger.debug(r)

    return new_entry


# xxx_answers
# -----------
async def create_answer_table_entry(
    # The correct type is one of the validators for an answer table; we use LogItemIncoming as a generalization of this.
    log_entry: schemas.LogItemIncoming,
    # The event type.
    event: str,
):
    rslogger.debug(f"hello from create at {log_entry}")
    tbl = answer_tables[EVENT2TABLE[event]]
    new_entry = tbl(**log_entry.dict())
    async with async_session() as session:
        async with session.begin():
            session.add(new_entry)
    rslogger.debug(f"returning {new_entry}")
    return new_entry


async def fetch_last_answer_table_entry(query_data: schemas.AssessmentRequest):
    assessment = EVENT2TABLE[query_data.event]
    tbl = answer_tables[assessment]
    query = (
        select(tbl)
        .where(
            and_(
                tbl.div_id == query_data.div_id,
                tbl.course_name == query_data.course,
                tbl.sid == query_data.sid,
            )
        )
        .order_by(tbl.timestamp.desc())
    )
    async with async_session() as session:
        res = await session.execute(query)
        rslogger.debug(f"res = {res}")

    return res.scalars().first()


async def fetch_course(course_name: str):
    query = select(Courses).where(Courses.course_name == course_name)
    async with async_session() as session:
        res = await session.execute(query)
    # When selecting ORM entries it is useful to use the ``scalars`` method
    # This modifies the result so that you are getting the ORM object
    # instead of a Row object. `See <https://docs.sqlalchemy.org/en/14/orm/queryguide.html#selecting-orm-entities-and-attributes>`_
    return res.scalars().first()


async def fetch_user(user_name: str):
    query = select(AuthUser).where(AuthUser.username == user_name)
    async with async_session() as session:
        res = await session.execute(query)
        rslogger.debug(f"res = {res}")
    user = res.scalars().first()
    return AuthUserValidator.from_orm(user) if user else None
