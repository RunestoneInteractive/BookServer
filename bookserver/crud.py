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
from collections import namedtuple
from typing import List, Optional
import datetime


# Third-party imports
# -------------------
from .db import async_session
from pydal.validators import CRYPT
from fastapi.exceptions import HTTPException

# import sqlalchemy
from sqlalchemy import and_, update
from sqlalchemy.sql import select

# Local application imports
# -------------------------
from .applogger import rslogger
from . import schemas
from .models import (
    Chapter,
    SubChapter,
    Code,
    CodeValidator,
    CourseInstructor,
    CourseInstructorValidator,
    UserChapterProgress,
    UserChapterProgressValidator,
    UserSubChapterProgress,
    UserSubChapterProgressValidator,
    answer_tables,
    AuthUser,
    AuthUserValidator,
    Courses,
    CoursesValidator,
    Useinfo,
    UseinfoValidation,
    UserState,
    UserStateValidator,
    validation_tables,
)
from .config import settings, BookServerConfig
from .internal.utils import http_422error_detail

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
    "unittest": "unittest_answers",
}


# useinfo
# -------
async def create_useinfo_entry(log_entry: UseinfoValidation) -> UseinfoValidation:
    async with async_session.begin() as session:
        new_entry = Useinfo(**log_entry.dict())
        rslogger.debug(f"timestamp = {log_entry.timestamp} ")
        rslogger.debug(f"New Entry = {new_entry}")
        rslogger.debug(f"session = {session}")
        session.add(new_entry)
    rslogger.debug(new_entry)
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
async def fetch_course(course_name: str) -> CoursesValidator:
    query = select(Courses).where(Courses.course_name == course_name)
    async with async_session() as session:
        res = await session.execute(query)
        # When selecting ORM entries it is useful to use the ``scalars`` method
        # This modifies the result so that you are getting the ORM object
        # instead of a Row object. `See <https://docs.sqlalchemy.org/en/14/orm/queryguide.html#selecting-orm-entities-and-attributes>`_
        course = res.scalars().one_or_none()
        return CoursesValidator.from_orm(course)


async def fetch_base_course(base_course: str) -> CoursesValidator:
    query = select(Courses).where(
        (Courses.base_course == base_course) & (Courses.course_name == base_course)
    )
    async with async_session() as session:
        res = await session.execute(query)
        # When selecting ORM entries it is useful to use the ``scalars`` method
        # This modifies the result so that you are getting the ORM object
        # instead of a Row object. `See <https://docs.sqlalchemy.org/en/14/orm/queryguide.html#selecting-orm-entities-and-attributes>`_
        base_course = res.scalars().one_or_none()
        return CoursesValidator.from_orm(base_course)


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
    return AuthUserValidator.from_orm(user)


async def create_user(user: AuthUserValidator) -> Optional[AuthUserValidator]:
    """
    The given user will have the password in plain text.  First we will hash
    the password then add this user to the database.
    """
    if await fetch_user(user.username):
        raise HTTPException(
            status_code=422,
            detail=http_422error_detail(
                ["body", "username"], "duplicate username", "integrity_error"
            ),
        )

    new_user = AuthUser(**user.dict())
    crypt = CRYPT(key=settings.web2py_private_key, salt=True)
    new_user.password = str(crypt(user.password)[0])
    async with async_session.begin() as session:
        session.add(new_user)
    return AuthUserValidator.from_orm(new_user)


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


# Code
# ----


async def create_code_entry(data: CodeValidator):
    new_code = Code(**data.dict())
    async with async_session.begin() as session:
        session.add(new_code)

    return CodeValidator.from_orm(new_code)


async def fetch_code(sid: str, acid: str, course_id: int) -> List[CodeValidator]:
    query = (
        select(Code)
        .where((Code.sid == sid) & (Code.acid == acid) & (Code.course_id == course_id))
        .order_by(Code.id)
    )
    async with async_session() as session:
        res = await session.execute(query)

        code_list = [CodeValidator.from_orm(x) for x in res.scalars().fetchall()]
        return code_list


# Development and Testing Utils
# -----------------------------
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
                login_required=False,
                allow_pairs=False,
                downloads_enabled=False,
                courselevel="",
                institution="",
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
                donated=True,
                active=True,
                accept_tcp=True,
                created_on=datetime.datetime(2020, 1, 1, 0, 0, 0),
                modified_on=datetime.datetime(2020, 1, 1, 0, 0, 0),
                registration_key="",
                registration_id="",
                reset_password_key="",
            )
        )


async def create_user_state_entry(user_id: int, course_name: str) -> UserStateValidator:
    new_us = UserState(user_id=user_id, course_name=course_name)
    async with async_session.begin() as session:
        session.add(new_us)
    return UserStateValidator.from_orm(new_us)


async def update_user_state(user_data: schemas.LastPageData):
    ud = user_data.dict()
    ud.pop("completion_flag")
    rslogger.debug(f"user data = {ud}")
    stmt = (
        update(UserState)
        .where(
            (UserState.user_id == user_data.user_id)
            & (UserState.course_name == user_data.course_name)
        )
        .values(**ud)
    )
    async with async_session.begin() as session:
        res = await session.execute(stmt)
    rslogger.debug("SUCCESS")


async def update_sub_chapter_progress(user_data: schemas.LastPageData):
    ud = user_data.dict()
    ud.pop("last_page_url")
    ud.pop("last_page_scroll_location")
    ud.pop("last_page_accessed_on")
    ud["status"] = ud.pop("completion_flag")
    ud["chapter_id"] = ud.pop("last_page_chapter")
    ud["sub_chapter_id"] = ud.pop("last_page_subchapter")
    stmt = (
        update(UserSubChapterProgress)
        .where(
            (UserSubChapterProgress.user_id == user_data.user_id)
            & (UserSubChapterProgress.chapter_id == user_data.last_page_chapter)
            & (UserSubChapterProgress.sub_chapter_id == user_data.last_page_subchapter)
            & (
                (UserSubChapterProgress.course_name == user_data.course_name)
                | (
                    UserSubChapterProgress.course_name == None  # noqa 711
                )  # Back fill for old entries without course
            )
        )
        .values(**ud)
    )
    async with async_session.begin() as session:
        await session.execute(stmt)


async def fetch_last_page(user: AuthUserValidator, course_name: str):
    course = await fetch_course(course_name)

    query = (
        select(
            [
                UserState.last_page_url,
                UserState.last_page_hash,
                Chapter.chapter_name,
                UserState.last_page_scroll_location,
                SubChapter.sub_chapter_name,
            ]
        )
        .where(
            (UserState.user_id == user.id)
            & (UserState.last_page_chapter == Chapter.chapter_label)
            & (UserState.course_name == course.course_name)
            & (SubChapter.chapter_id == Chapter.id)
            & (UserState.last_page_subchapter == SubChapter.sub_chapter_label)
            & (Chapter.course_id == course.base_course)
        )
        .order_by(UserState.last_page_accessed_on.desc())
    )

    async with async_session() as session:
        res = await session.execute(query)
        # for A query like this one with columns from multiple tables
        # res.first() returns a tuple
        rslogger.debug(f"LP {res}")
        PageData = namedtuple("PageData", [col for col in res.keys()])  # type: ignore
        rdata = res.first()
        rslogger.debug(f"{rdata=}")
        if rdata:
            return PageData(*rdata)
        else:
            return None


async def fetch_user_sub_chapter_progress(
    user, last_page_chapter=None, last_page_subchapter=None
):

    where_clause = (UserSubChapterProgress.user_id == user.id) & (
        UserSubChapterProgress.course_name == user.course_name
    )

    if last_page_chapter:
        where_clause = (
            where_clause
            & (UserSubChapterProgress.chapter_id == last_page_chapter)
            & (UserSubChapterProgress.sub_chapter_id == last_page_subchapter)
        )

    query = select(UserSubChapterProgress).where(where_clause)

    async with async_session() as session:
        res = await session.execute(query)
        rslogger.debug(f"{res=}")
        return [
            UserSubChapterProgressValidator.from_orm(x)
            for x in res.scalars().fetchall()
        ]


async def create_user_sub_chapter_progress_entry(
    user, last_page_chapter, last_page_subchapter, status=-1
):

    new_uspe = UserSubChapterProgress(
        user_id=user.id,
        chapter_id=last_page_chapter,
        sub_chapter_id=last_page_subchapter,
        status=status,
        start_date=datetime.datetime.utcnow(),
        course_name=user.course_name,
    )
    async with async_session.begin() as session:
        session.add(new_uspe)
    return UserSubChapterProgressValidator.from_orm(new_uspe)


async def fetch_user_chapter_progress(user, last_page_chapter):
    query = select(UserChapterProgress).where(
        (UserChapterProgress.user_id == user.id)
        & (UserChapterProgress.chapter_id == last_page_chapter)
    )

    async with async_session() as session:
        res = await session.execute(query)
        rslogger.debug(f"{res=}")
        return UserChapterProgressValidator.from_orm(res.scalars().first())


async def create_user_chapter_progress_entry(user, last_page_chapter, status):
    new_ucp = UserChapterProgress(
        user_id=user.id,
        chapter_id=last_page_chapter,
        status=status,
        start_date=datetime.datetime.utcnow(),
    )
    async with async_session.begin() as session:
        session.add(new_ucp)
    return UserChapterProgressValidator.from_orm(new_ucp)
