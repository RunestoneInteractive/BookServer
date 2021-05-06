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
from typing import List, Optional
import datetime


# Third-party imports
# -------------------
from .db import async_session
from pydal.validators import CRYPT

# import sqlalchemy
from sqlalchemy import and_
from sqlalchemy.sql import select
from sqlalchemy.exc import IntegrityError

# Local application imports
# -------------------------
from .applogger import rslogger
from . import schemas
from .models import (
    CourseInstructor,
    CourseInstructorValidator,
    answer_tables,
    AuthUser,
    AuthUserValidator,
    Courses,
    CoursesValidator,
    Useinfo,
    UseinfoValidation,
    validation_tables,
)
from .config import settings, BookServerConfig

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
async def create_useinfo_entry(log_entry: UseinfoValidation) -> UseinfoValidation:
    async with async_session.begin() as session:
        new_entry = Useinfo(**log_entry.dict())
        rslogger.debug(f"timestamp = {log_entry.timestamp} ")
        rslogger.debug(f"New Entry = {new_entry}")
        rslogger.debug(f"session = {session}")
        r = session.add(new_entry)
        rslogger.debug(r)
        return UseinfoValidation.from_orm(new_entry)


# xxx_answers
# -----------
async def create_answer_table_entry(
    # The correct type is one of the validators for an answer table; we use LogItemIncoming as a generalization of this.
    log_entry: schemas.LogItemIncoming,
    # The event type.
    event: str,
) -> schemas.LogItemIncoming:
    rslogger.debug(f"hello from create at {log_entry}")
    table_name = EVENT2TABLE[event]
    tbl = answer_tables[table_name]
    new_entry = tbl(**log_entry.dict())
    async with async_session.begin() as session:
        session.add(new_entry)
        rslogger.debug(f"returning {new_entry}")
        return validation_tables[table_name].from_orm(new_entry)


async def fetch_last_answer_table_entry(
    query_data: schemas.AssessmentRequest,
) -> schemas.LogItemIncoming:
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
        return validation_tables[assessment].from_orm(res.scalars().first())


# Courses
# -------
async def fetch_base_course(base_course: str) -> CoursesValidator:
    query = select(Courses).where(Courses.base_course == base_course)
    async with async_session() as session:
        res = await session.execute(query)
        # When selecting ORM entries it is useful to use the ``scalars`` method
        # This modifies the result so that you are getting the ORM object
        # instead of a Row object. `See <https://docs.sqlalchemy.org/en/14/orm/queryguide.html#selecting-orm-entities-and-attributes>`_
        course = res.scalars().one_or_none()
        return CoursesValidator.from_orm(course) if course else None


async def create_course(course_info: CoursesValidator) -> CoursesValidator:
    new_course = Courses(**course_info.dict())
    async with async_session.begin() as session:
        session.add(new_course)
        return CoursesValidator.from_orm(new_course)


# auth_user
# ---------
async def fetch_user(user_name: str) -> AuthUserValidator:
    query = select(AuthUser).where(AuthUser.username == user_name)
    async with async_session() as session:
        res = await session.execute(query)
        user = res.scalars().one_or_none()
        return AuthUserValidator.from_orm(user) if user else None


async def create_user(user: AuthUserValidator) -> bool:
    """
    The given user will have the password in plain text.  First we will hash
    the password then add this user to the database.
    """
    new_user = AuthUser(**user.dict())
    crypt = CRYPT(key=settings.web2py_private_key, salt=True)
    new_user.password = str(crypt(user.password)[0])
    try:
        async with async_session.begin() as session:
            session.add(new_user)
            return AuthUserValidator.from_orm(new_user)
    except IntegrityError:
        rslogger.error("Failed to add a duplicate user")
        return False


# instructor_courses
# ------------------
async def fetch_instructor_courses(
    instructor_id: int, course_id: Optional[int] = None
) -> List[CourseInstructorValidator]:
    """
    return a list of courses for which the given userid is an instructor.
    If the optional course_id value is included then retur the row for that
    course to verify that instructor_id is an instructor for course_id
    """
    query = select(CourseInstructor)
    if course_id is not None:
        query = query.where(
            and_(
                CourseInstructor.instructor == instructor_id,
                CourseInstructor.course == course_id,
            )
        )
    else:
        query = query.where(CourseInstructor.instructor == instructor_id)
    async with async_session() as session:
        res = await session.execute(query)

        course_list = [
            CourseInstructorValidator.from_orm(x) for x in res.scalars().fetchall()
        ]
        return course_list


# Development and Testing Utils
# -----------------------------
#
# This function is useful for development.  It recreates the database
# and populates it with the common base courses and creates a test user
#
async def create_initial_courses_users():
    # never ever drop tables in a production environment
    rslogger.debug(f"HELLO {settings.book_server_config} - {settings.drop_tables}")
    if (
        settings.book_server_config
        in [BookServerConfig.development, BookServerConfig.test]
        and settings.drop_tables == "Yes"
    ):
        rslogger.debug("Populating Courses")
        BASE_COURSES = [
            "ac1",
            "cppds",
            "cppforpython",
            "csawesome",
            "csjava",
            "fopp",
            "httlads",
            "java4python",
            "JS4Python",
            "learnwebgl2",
            "MasteringDatabases",
            "overview",
            "py4e-int",
            "pythonds",
            "pythonds3",
            "StudentCSP",
            "TeacherCSP",
            "thinkcpp",
            "thinkcspy",
            "webfundamentals",
        ]

        for c in BASE_COURSES:
            new_course = CoursesValidator(
                course_name=c,
                base_course=c,
                term_start_date=datetime.date(2000, 1, 1),
            )
            await create_course(new_course)
        # make a user
        await create_user(
            AuthUserValidator(
                username="testuser1",
                first_name="test",
                last_name="user",
                password="xxx",
                email="testuser1@example.com",
                course_name="overview",
                course_id=12,
            )
        )
