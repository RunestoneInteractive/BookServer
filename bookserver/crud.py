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
import datetime
import hashlib
import json
from collections import namedtuple
from typing import Dict, List, Optional
import traceback

# Third-party imports
# -------------------
from fastapi.exceptions import HTTPException
from pydal.validators import CRYPT
from sqlalchemy import and_, distinct, func, update
from sqlalchemy.sql import select, text, delete
from starlette.requests import Request

from . import schemas

# Local application imports
# -------------------------
from .applogger import rslogger
from .config import settings
from .db import async_session
from .internal.utils import http_422error_detail
from .models import (
    Assignment,
    AssignmentQuestion,
    AssignmentQuestionValidator,
    AuthUser,
    AuthUserValidator,
    Chapter,
    Code,
    CodeValidator,
    Competency,
    CourseAttribute,
    CourseInstructor,
    CourseInstructorValidator,
    CoursePractice,
    Courses,
    CoursesValidator,
    Library,
    LibraryValidator,
    Question,
    QuestionGrade,
    QuestionGradeValidator,
    QuestionValidator,
    SelectedQuestion,
    SelectedQuestionValidator,
    SubChapter,
    TimedExam,
    TimedExamValidator,
    TraceBack,
    Useinfo,
    UseinfoValidation,
    UserChapterProgress,
    UserChapterProgressValidator,
    UserExperiment,
    UserExperimentValidator,
    UserState,
    UserStateValidator,
    UserSubChapterProgress,
    UserSubChapterProgressValidator,
    UserTopicPractice,
    UserTopicPracticeValidator,
    runestone_component_dict,
)

# Map from the ``event`` field of a ``LogItemIncoming`` to the database table used to store data associated with this event.
EVENT2TABLE = {
    "clickableArea": "clickablearea_answers",
    "codelens1": "codelens_answers",
    "dragNdrop": "dragndrop_answers",
    "fillb": "fitb_answers",
    "lp_build": "lp_answers",
    "mChoice": "mchoice_answers",
    "parsons": "parsons_answers",
    "shortanswer": "shortanswer_answers",
    "unittest": "unittest_answers",
    "timedExam": "timed_exam",
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


async def count_useinfo_for(
    div_id: str, course_name: str, start_date: datetime.datetime
) -> List[tuple]:
    """
    return a list of tuples that include the [(act, count), (act, count)]
    act is a freeform field in the useinfo table that varies from event
    type to event type.
    """

    query = (
        select(Useinfo.act, func.count(Useinfo.act).label("count"))
        .where(
            (Useinfo.div_id == div_id)
            & (Useinfo.course_id == course_name)
            & (Useinfo.timestamp > start_date)
        )
        .group_by(Useinfo.act)
    )
    async with async_session() as session:
        res = await session.execute(query)
        rslogger.debug(f"res = {res}")
        return res.all()


async def fetch_chapter_for_subchapter(subchapter: str, base_course: str) -> str:
    """
    Used for pretext books where the subchapter is unique across the book
    due to the flat structure produced by pretext build.  In this case the
    old RST structure where we get the chapter and subchapter from the URL
    /book/chapter/subchapter.html gives us the wrong answer of the book.
    select chapter_label
        from sub_chapters join chapters on chapter_id = chapters.id
        where course_id = <base_course> and sub_chapter_label = <subchapter>
    """

    query = (
        select(Chapter.chapter_label)
        .join(SubChapter, Chapter.id == SubChapter.chapter_id)
        .where(
            (Chapter.course_id == base_course)
            & (SubChapter.sub_chapter_label == subchapter)
        )
    )
    async with async_session() as session:
        chapter_label = await session.execute(query)
        return chapter_label.scalars().first()


async def fetch_page_activity_counts(
    chapter: str, subchapter: str, base_course: str, course_name: str, username: str
) -> Dict[str, int]:
    """
    Used for the progress bar at the bottom of each page.  This function
    finds all of the components for a particular page (chaper/subchapter)
    and then finds out which of those elements the student has interacted
    with.  It returns a dictionary of {divid: 0/1}
    """

    where_clause_common = (
        (Question.subchapter == subchapter)
        & (Question.chapter == chapter)
        & (Question.from_source == True)  # noqa: E712
        & (
            (Question.optional == False)  # noqa: E712
            | (Question.optional == None)  # noqa: E711
        )
        & (Question.base_course == base_course)
    )

    query = select(Question).where(where_clause_common)

    async with async_session() as session:
        page_divids = await session.execute(query)
    rslogger.debug(f"PDVD {page_divids}")
    div_counts = {q.name: 0 for q in page_divids.scalars()}
    query = select(distinct(Useinfo.div_id)).where(
        where_clause_common
        & (Question.name == Useinfo.div_id)
        & (Useinfo.course_id == course_name)
        & (Useinfo.sid == username)
    )
    async with async_session() as session:
        sid_counts = await session.execute(query)

    # doing a call to scalars() on a single column join query like this reduces
    # the row to just the string.  So each row is just a string representing a unique
    # div_id the user has interacted with on this page.
    for row in sid_counts.scalars():
        div_counts[row] = 1

    return div_counts


async def fetch_poll_summary(div_id: str, course_name: str) -> List[tuple]:
    """
    find the last answer for each student and then aggregate
    those answers to provide a summary of poll responses for the
    given question.  for a poll the value of act is a response
    number 0--N where N is the number of different choices.
    """
    query = text(
        """select act, count(*) from useinfo
        join (select sid,  max(id) mid
        from useinfo where event='poll' and div_id = :div_id and course_id = :course_name group by sid) as T
        on id = T.mid group by act"""
    )

    async with async_session() as session:
        rows = await session.execute(
            query, params=dict(div_id=div_id, course_name=course_name)
        )
        return rows.all()


async def fetch_top10_fitb(dbcourse: CoursesValidator, div_id: str) -> List[tuple]:
    "Return the top 10 answers to a fill in the blank question"
    rcd = runestone_component_dict["fitb_answers"]
    tbl = rcd.model
    query = (
        select(tbl.answer, func.count(tbl.answer).label("count"))
        .where(
            (tbl.div_id == div_id)
            & (tbl.course_name == dbcourse.course_name)
            & (tbl.timestamp > dbcourse.term_start_date)
        )
        .group_by(tbl.answer)
        .order_by(func.count(tbl.answer).desc())
        .limit(10)
    )
    async with async_session() as session:
        rows = await session.execute(query)
        return rows.all()


# xxx_answers
# -----------
async def create_answer_table_entry(
    # The correct type is one of the validators for an answer table; we use LogItemIncoming as a generalization of this.
    log_entry: schemas.LogItemIncoming,
    # The event type.
    event: str,
) -> schemas.LogItemIncoming:
    rslogger.debug(f"hello from create at {log_entry}")
    rcd = runestone_component_dict[EVENT2TABLE[event]]
    new_entry = rcd.model(**log_entry.dict())  # type: ignore
    async with async_session.begin() as session:
        session.add(new_entry)

    rslogger.debug(f"returning {new_entry}")
    return rcd.validator.from_orm(new_entry)  # type: ignore


async def fetch_last_answer_table_entry(
    query_data: schemas.AssessmentRequest,
) -> schemas.LogItemIncoming:
    rcd = runestone_component_dict[EVENT2TABLE[query_data.event]]
    tbl = rcd.model
    deadline_offset_naive = query_data.deadline.replace(tzinfo=None)
    query = (
        select(tbl)
        .where(
            and_(
                tbl.div_id == query_data.div_id,
                tbl.course_name == query_data.course,
                tbl.sid == query_data.sid,
                tbl.timestamp <= deadline_offset_naive,
            )
        )
        .order_by(tbl.timestamp.desc())
    )
    async with async_session() as session:
        res = await session.execute(query)
        rslogger.debug(f"res = {res}")
        return rcd.validator.from_orm(res.scalars().first())  # type: ignore


async def fetch_last_poll_response(sid: str, course_name: str, poll_id: str) -> str:
    """
    Return a student's (sid) last response to a given poll (poll_id)
    """
    query = (
        select(Useinfo.act)
        .where(
            (Useinfo.sid == sid)
            & (Useinfo.course_id == course_name)
            & (Useinfo.div_id == poll_id)
        )
        .order_by(Useinfo.id.desc())
    )
    async with async_session() as session:
        res = await session.execute(query)
        return res.scalars().first()


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


async def create_course(course_info: CoursesValidator) -> None:
    new_course = Courses(**course_info.dict())
    async with async_session.begin() as session:
        session.add(new_course)


# course_attributes
# -----------------


async def fetch_all_course_attributes(course_id: int) -> dict:
    query = select(CourseAttribute).where(CourseAttribute.course_id == course_id)

    async with async_session() as session:
        res = await session.execute(query)
        return {row.attr: row.value for row in res.scalars().fetchall()}


async def fetch_one_course_attribute():
    raise NotImplementedError()


async def create_course_attribute():
    raise NotImplementedError()


async def get_course_origin(base_course):
    query = select(CourseAttribute).where(
        (CourseAttribute.course_id == base_course)
        & (CourseAttribute.attr == "markup_system")
    )

    async with async_session() as session:
        res = await session.execute(query)
        ca = res.scalars().first()
        return ca.value


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
    If the optional course_id value is included then return the row for that
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
async def create_code_entry(data: CodeValidator) -> CodeValidator:
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


# Server-side grading
# -------------------
# Return the feedback associated with this question if this question should be graded on the server instead of on the client; otherwise, return None.
async def is_server_feedback(div_id, course):
    # Get the information about this question.
    query = (
        select(Question, Courses)
        .where(Question.name == div_id)
        .join(Courses, Question.base_course == Courses.base_course)
        .where(Courses.course_name == course)
    )
    async with async_session() as session:
        query_results = (await session.execute(query)).first()

        # Get the feedback, if it exists.
        feedback = query_results and query_results.Question.feedback
        # If there's feedback and a login is required (necessary for server-side grading), return the decoded feedback.
        if feedback and query_results.Courses.login_required:
            return json.loads(feedback)
        # Otherwise, grade on the client.
        return None


# Development and Testing Utils
# -----------------------------
# This function populates the database with the common base courses and creates a test user.
async def create_initial_courses_users():
    BASE_COURSES = [
        "boguscourse",
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
        "test_course_1",
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
            new_server=True,
        )
        await create_course(new_course)
    # Make a user. TODO: should we not do this for production?
    await create_user(
        AuthUserValidator(
            username="testuser1",
            first_name="test",
            last_name="user",
            password="xxx",
            email="testuser1@example.com",
            course_name="overview",
            course_id=BASE_COURSES.index("overview") + 1,
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


# User Progress
# -------------


async def create_user_state_entry(user_id: int, course_name: str) -> UserStateValidator:
    new_us = UserState(user_id=user_id, course_name=course_name)
    async with async_session.begin() as session:
        session.add(new_us)
    return UserStateValidator.from_orm(new_us)


async def update_user_state(user_data: schemas.LastPageData):
    ud = user_data.dict()
    # LastPageData contains information for both user_state and user_sub_chapter_progress tables
    # we do not need the completion flag in the user_state table
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
        await session.execute(stmt)
    rslogger.debug("SUCCESS")


async def update_sub_chapter_progress(user_data: schemas.LastPageData):
    ud = user_data.dict()
    ud.pop("last_page_url")
    ud.pop("last_page_scroll_location")
    ud.pop("last_page_accessed_on")
    ud["status"] = ud.pop("completion_flag")
    ud["chapter_id"] = ud.pop("last_page_chapter")
    ud["sub_chapter_id"] = ud.pop("last_page_subchapter")
    if ud["status"] > -1:
        ud["end_date"] = datetime.datetime.utcnow()

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
) -> UserSubChapterProgressValidator:

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
) -> UserSubChapterProgressValidator:

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


async def fetch_user_chapter_progress(
    user, last_page_chapter: str
) -> UserChapterProgressValidator:
    query = select(UserChapterProgress).where(
        (
            UserChapterProgress.user_id == str(user.id)
        )  # TODO: this is bad! the DB has user.id as a string!
        & (UserChapterProgress.chapter_id == last_page_chapter)
    )

    async with async_session() as session:
        res = await session.execute(query)
        rslogger.debug(f"{res=}")
        return UserChapterProgressValidator.from_orm(res.scalars().first())


async def create_user_chapter_progress_entry(
    user, last_page_chapter, status
) -> UserChapterProgressValidator:
    new_ucp = UserChapterProgress(
        user_id=str(user.id),
        chapter_id=last_page_chapter,
        status=status,
        start_date=datetime.datetime.utcnow(),
    )
    async with async_session.begin() as session:
        session.add(new_ucp)
    return UserChapterProgressValidator.from_orm(new_ucp)


#
# Select Question Support
# -----------------------


async def create_selected_question(
    sid: str,
    selector_id: str,
    selected_id: str,
    points: Optional[int] = None,
    competency: Optional[str] = None,
) -> SelectedQuestionValidator:
    new_sqv = SelectedQuestion(
        sid=sid,
        selector_id=selector_id,
        selected_id=selected_id,
        points=points,
        competency=competency,
    )
    async with async_session.begin() as session:
        session.add(new_sqv)
    return SelectedQuestionValidator.from_orm(new_sqv)


async def fetch_selected_question(
    sid: str, selector_id: str
) -> SelectedQuestionValidator:
    """
    Used with selectquestions.  This returns the information about
    a question previously chosen for the given (selector_id) question
    for a particular student (sid) - see `get_question_source` for
    more info on select questions.
    """
    query = select(SelectedQuestion).where(
        (SelectedQuestion.sid == sid) & (SelectedQuestion.selector_id == selector_id)
    )

    async with async_session() as session:
        res = await session.execute(query)
        rslogger.debug(f"{res=}")
        return SelectedQuestionValidator.from_orm(res.scalars().first())


async def update_selected_question(sid: str, selector_id: str, selected_id: str):
    """
    Used in conjunction with the toggle feature of select question to update
    which question the student has chosen to work on.
    """
    stmt = (
        update(SelectedQuestion)
        .where(
            (SelectedQuestion.sid == sid)
            & (SelectedQuestion.selector_id == selector_id)
        )
        .values(selected_id=selected_id)
    )
    async with async_session.begin() as session:
        await session.execute(stmt)
    rslogger.debug("SUCCESS")


# Questions and Assignments
# -------------------------


async def fetch_question(
    name: str, basecourse: Optional[str] = None, assignment: Optional[str] = None
) -> QuestionValidator:
    """
    Fetch a single matching question row from the database that matches
    the name (div_id) of the question.  If the base course is provided
    make sure the question comes from that basecourse. basecourse,name pairs
    are guaranteed to be unique in the questions table

    More and more questions have globally unique names in the runestone
    database and that is definitely a direction to keep pushing.  But
    it is possible that there are duplicates but we are not going to
    worry about that we are just going to return the first one we find.
    """
    where_clause = Question.name == name
    if basecourse:
        where_clause = where_clause & (Question.base_course == basecourse)

    query = select(Question).where(where_clause)

    async with async_session() as session:
        res = await session.execute(query)
        rslogger.debug(f"{res=}")
        return QuestionValidator.from_orm(res.scalars().first())


async def count_matching_questions(name: str) -> int:

    query = select(func.count(Question.name)).where(Question.name == name)

    async with async_session() as session:
        res = await session.execute(query)
        return res.scalars().first()


auto_gradable_q = [
    "clickablearea",
    "mchoice",
    "parsonsprob",
    "dragndrop",
    "fillintheblank",
    "lp",
]


async def fetch_matching_questions(request_data: schemas.SelectQRequest) -> List[str]:
    """
    Return a list of question names (div_ids) that match the criteria
    for a particular question. This is used by select questions and in
    particular `get_question_source`
    """
    if request_data.questions:
        questionlist = request_data.questions.split(",")
        questionlist = [q.strip() for q in questionlist]
    elif request_data.proficiency:
        prof = request_data.proficiency.strip()
        rslogger.debug(prof)
        where_clause = (Competency.competency == prof) & (
            Competency.question == Question.id
        )
        if request_data.primary:
            where_clause = where_clause & (Competency.is_primary == True)  # noqa E712
        if request_data.min_difficulty:
            where_clause = where_clause & (
                Question.difficulty >= float(request_data.min_difficulty)
            )
        if request_data.max_difficulty:
            where_clause = where_clause & (
                Question.difficulty <= float(request_data.max_difficulty)
            )
        if request_data.autogradable:
            where_clause = where_clause & (
                (Question.autograde == "unittest")
                | Question.question_type.in_(auto_gradable_q)
            )
        if request_data.limitBaseCourse:
            where_clause = where_clause & (
                Question.base_course == request_data.limitBaseCourse
            )
        query = select(Question.name).where(where_clause)

        async with async_session() as session:
            res = await session.execute(query)
            rslogger.debug(f"{res=}")
            questionlist = []
            for row in res:
                questionlist.append(row[0])

    return questionlist


async def fetch_assignment_question(
    assignment_name: str, question_name: str
) -> AssignmentQuestionValidator:
    """
    Get an assignment question row object
    """
    query = select(AssignmentQuestion).where(
        (Assignment.name == assignment_name)
        & (Assignment.id == AssignmentQuestion.assignment_id)
        & (AssignmentQuestion.question_id == Question.id)
        & (Question.name == question_name)
    )

    async with async_session() as session:
        res = await session.execute(query)
        rslogger.debug(f"{res=}")
        return AssignmentQuestionValidator.from_orm(res.scalars().first())


async def fetch_question_grade(sid: str, course_name: str, qid: str):
    """
    Get the grade and any comments for this question
    """
    query = (
        select(QuestionGrade)
        .where(
            (QuestionGrade.sid == sid)
            & (QuestionGrade.course_name == course_name)
            & (QuestionGrade.div_id == qid)
        )
        .order_by(
            QuestionGrade.id.desc(),
        )
    )
    async with async_session() as session:
        res = await session.execute(query)
        return QuestionGradeValidator.from_orm(res.scalars().one_or_none())


async def fetch_user_experiment(sid: str, ab_name: str) -> int:
    """
    When a question is part of an AB experiement (ab_name) get the experiment
    group for a particular student (sid).  The group number will have
    been randomly assigned by the initial question selection.

    This number indicates whether the student will see the 1st or 2nd
    question in the question list.
    """
    query = (
        select(UserExperiment.exp_group)
        .where((UserExperiment.sid == sid) & (UserExperiment.experiment_id == ab_name))
        .order_by(UserExperiment.id)
    )
    async with async_session() as session:
        res = await session.execute(query)
        r = res.scalars().first()
        rslogger.debug(f"{r=}")
        return r


async def create_user_experiment_entry(
    sid: str, ab: str, group: int
) -> UserExperimentValidator:
    """
    Store the number of the group number (group) this student (sid) hass been assigned to
    for this particular experiment (ab)
    """
    new_ue = UserExperiment(sid=sid, exp_group=group, experiment_id=ab)
    async with async_session.begin() as session:
        session.add(new_ue)
    return UserExperimentValidator.from_orm(new_ue)


async def fetch_viewed_questions(sid: str, questionlist: List[str]) -> List[str]:
    """
    Used for the selectquestion `get_question_source` to filter out questions
    that a student (sid) has seen before.  One criteria of a select question
    is to make sure that a student has never seen a question before.

    The best approximation we have for that is that they will have clicked on the
    run button for that quesiton.  Of course they may have seen said question
    but not run it but this is the best we can do.
    """
    query = select(Useinfo).where(
        (Useinfo.sid == sid) & (Useinfo.div_id.in_(questionlist))
    )
    async with async_session() as session:
        res = await session.execute(query)
        rslogger.debug(f"{res=}")
        rlist = [row.div_id for row in res]
    return rlist


async def fetch_previous_selections(sid) -> List[str]:
    query = select(SelectedQuestion).where(SelectedQuestion.sid == sid)
    async with async_session() as session:
        res = await session.execute(query)
        rslogger.debug(f"{res=}")
        return [row.selected_id for row in res.scalars().fetchall()]


async def fetch_timed_exam(
    sid: str, exam_id: str, course_name: str
) -> TimedExamValidator:
    query = (
        select(TimedExam)
        .where(
            (TimedExam.div_id == exam_id)
            & (TimedExam.sid == sid)
            & (TimedExam.course_name == course_name)
        )
        .order_by(TimedExam.id.desc())
    )
    async with async_session() as session:
        res = await session.execute(query)
        rslogger.debug(f"{res=}")
        return TimedExamValidator.from_orm(res.scalars().first())


async def fetch_subchapters(course, chap):
    """
    Fetch all subchapters for a given chapter
    """
    # Note: we are joining two tables so this query will not result in an defined in schemas.py
    # instead it will simply produce a bunch of tuples with the columns in the order given in the
    # select statement.
    query = (
        select(SubChapter.sub_chapter_label, SubChapter.sub_chapter_name)
        .where(
            (Chapter.id == SubChapter.chapter_id)
            & (Chapter.course_id == course)
            & (Chapter.chapter_label == chap)
        )
        .order_by(SubChapter.sub_chapter_num)
    )

    async with async_session() as session:
        res = await session.execute(query)
        rslogger.debug(f"{res=}")
        # **Note** with this kind of query you do NOT want to call ``.scalars()`` on the result
        return res


async def create_traceback(exc: Exception, request: Request, host: str):
    async with async_session.begin() as session:
        tbtext = "".join(traceback.format_tb(exc.__traceback__))
        new_entry = TraceBack(
            traceback=tbtext,
            timestamp=datetime.datetime.utcnow(),
            err_message=str(exc),
            path=request.url.path,
            query_string=str(request.query_params),
            hash=hashlib.md5(tbtext.encode("utf8")).hexdigest(),
            hostname=host,
        )
        session.add(new_entry)


async def fetch_library_books():
    query = (
        select(Library)
        .where(Library.is_visible == True)  # noqa: E712
        .order_by(Library.shelf_section, Library.title)
    )
    async with async_session() as session:
        res = await session.execute(query)
        rslogger.debug(f"{res=}")
        book_list = [LibraryValidator.from_orm(x) for x in res.scalars().fetchall()]
        return book_list


async def create_library_book():
    ...


async def fetch_course_practice(course_name: str) -> CoursePractice:
    """
    Fetch the course_practice row for a given course.  The course practice row
    contains the configuration of the practice feature for the given course.
    """
    query = (
        select(CoursePractice)
        .where(CoursePractice.course_name == course_name)
        .order_by(CoursePractice.id.desc())
    )
    async with async_session() as session:
        res = await session.execute(query)
        return res.scalars().first()


async def fetch_one_user_topic_practice(
    user: AuthUserValidator,
    last_page_chapter: str,
    last_page_subchapter: str,
    qname: str,
) -> UserTopicPracticeValidator:
    """
    The user_topic_practice table contains information about each question (flashcard)
    that a student is eligible to see for a given topic in a course.
    A particular question should ony be in the table once per student.  This row also contains
    information about scheduling and correctness to help the practice algorithm select the
    best question to show a student.
    """
    query = select(UserTopicPractice).where(
        (UserTopicPractice.user_id == user.id)
        & (UserTopicPractice.course_name == user.course_name)
        & (UserTopicPractice.chapter_label == last_page_chapter)
        & (UserTopicPractice.sub_chapter_label == last_page_subchapter)
        & (UserTopicPractice.question_name == qname)
    )
    async with async_session() as session:
        res = await session.execute(query)
        rslogger.debug(f"{res=}")
        utp = res.scalars().one_or_none()
        return UserTopicPracticeValidator.from_orm(utp)


async def delete_one_user_topic_practice(qid: int) -> None:
    """
    Used by ad hoc question selection.  If a student un-marks a page as completed then if there
    is a question from the page it will be removed from the set of possible flashcards a student
    can see.
    """
    query = delete(UserTopicPractice).where(UserTopicPractice.id == qid)
    async with async_session.begin() as session:
        await session.execute(query)


async def create_user_topic_practice(
    user: AuthUserValidator,
    last_page_chapter: str,
    last_page_subchapter: str,
    qname: str,
    now_local: datetime.datetime,
    now: datetime.datetime,
    tz_offset: float,
):
    """
    Add a question for the user to practice on
    """
    async with async_session.begin() as session:
        new_entry = UserTopicPractice(
            user_id=user.id,
            course_name=user.course_name,
            chapter_label=last_page_chapter,
            sub_chapter_label=last_page_subchapter,
            question_name=qname,
            # Treat it as if the first eligible question is the last one asked.
            i_interval=0,
            e_factor=2.5,
            next_eligible_date=now_local.date(),
            # add as if yesterday, so can practice right away
            last_presented=now - datetime.timedelta(1),
            last_completed=now - datetime.timedelta(1),
            creation_time=now,
            timezoneoffset=tz_offset,
        )
        session.add(new_entry)


async def fetch_qualified_questions(
    base_course, chapter_label, sub_chapter_label
) -> list[QuestionValidator]:
    """
    Return a list of possible questions for a given chapter and subchapter.  These
    questions will all have the practice flag set to true.
    """
    query = select(Question).where(
        (Question.base_course == base_course)
        & (
            (Question.topic == "{}/{}".format(chapter_label, sub_chapter_label))
            | (
                (Question.chapter == chapter_label)
                & (Question.topic == None)  # noqa: E711
                & (Question.subchapter == sub_chapter_label)
            )
        )
        & (Question.practice == True)  # noqa: E712
        & (Question.review_flag == False)  # noqa: E712
    )
    async with async_session() as session:
        res = await session.execute(query)
        rslogger.debug(f"{res=}")
        questionlist = [QuestionValidator.from_orm(x) for x in res.scalars().fetchall()]

    return questionlist
