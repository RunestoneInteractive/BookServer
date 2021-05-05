# *****************************************
# |docname| - definition of database models
# *****************************************
# In this file we define our SQLAlchemy data models. These get translated into relational database tables.
#
# Many of the models in this file were generated automatically for us by the ``sqlacodegen`` tool
# See `pypi for details <https://pypi.org/project/sqlacodegen/>`_   Although we are defining these using
# the declarative base style we will be using the SQLAlchemy Core for queries.  We are using
# SQLAlchemy 1.4.x in preparation for 2.0 and the more unified interface it provides for mixing
# declarative with core style queries.
#
# The models are created to be backward compatible with our current web2py implementation of
# Runestone.  Some decisions we would make differently but we won't be changing those things
# until we port the instructor interface to the FastAPI framework.
#
# Migrations
# ==========
# We use `Alembic <https://alembic.sqlalchemy.org/en/latest/>`_ for tracking database migration information.
# To create a new migration automatically after you have made changes to this file, run ``alembic revision --autogenerate -m "simple message"``
# this will generate a new file in ``alembic/versions``. To apply changes to the database run ``alembic upgrade head``.
#
# :index:`docs to write`: It is also possible...
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8`_.
#
# Standard library
# ----------------
# None.
#
# Third-party imports
# -------------------
from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    Date,
    DateTime,
    MetaData,
    Text,
    types,
    Float,
    inspect,
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql.schema import UniqueConstraint

# Local application imports
# -------------------------
from .db import Base
from .schemas import sqlalchemy_to_pydantic


# Web2Py boolean type
# ===================
# Define a web2py-compatible Boolean type. See `custom types <http://docs.sqlalchemy.org/en/latest/core/custom_types.html>`_.
class Web2PyBoolean(types.TypeDecorator):
    impl = types.CHAR(1)
    python_type = bool

    def process_bind_param(self, value, dialect):
        if value:
            return "T"
        elif value is None:
            return None
        elif not value:
            return "F"
        else:
            assert False

    def process_result_value(self, value, dialect):
        if value == "T":
            return True
        elif value == "F":
            return False
        elif value is None:
            return None
        else:
            assert False

    def copy(self, **kw):
        return Web2PyBoolean(self.impl.length)


# Schema Definition
# =================
# this object is a container for the table objects and can be used by alembic to autogenerate
# the migration information.
metadata = MetaData()

answer_tables = {}
validation_tables = {}


def register_answer_table(cls):
    global answer_tables, validation_tables

    table_name = cls.__tablename__
    answer_tables[table_name] = cls
    validation_tables[table_name] = sqlalchemy_to_pydantic(cls)
    return cls


# IdMixin
# -------
# Always name a table's ID field the same way.
class IdMixin:
    id = Column(Integer, primary_key=True)


# Useinfo
# -------
# This defines the useinfo table in the database. This table logs nearly every click
# generated by a student. It gets very large and needs a lot of indexes to keep Runestone
# from bogging down.
#
# User info logged by the `log_book_event endpoint`. See there for more info.
class Useinfo(Base, IdMixin):
    __tablename__ = "useinfo"
    # _`timestamp`: when this entry was recorded by this webapp.
    timestamp = Column(DateTime, index=True)
    # _`sid`: TODO: The student id? (user) which produced this row.
    sid = Column(String(512), index=True)
    # The type of question (timed exam, fill in the blank, etc.).
    event = Column(String(512), index=True)
    # TODO: What is this? The action associated with this log entry?
    act = Column(String(512))
    # _`div_id`: the ID of the question which produced this entry.
    div_id = Column(String(512), index=True)
    # _`course_id`: the Courses ``course_name`` **NOT** the ``id`` this row refers to. TODO: Use the ``id`` instead!
    course_id = Column(String(512), ForeignKey("courses.course_name"), index=True)
    # These are not currently in web2py but I'm going to add them
    ##chapter = Column(String, unique=False, index=False)
    ##sub_chapter = Column(String, unique=False, index=False)


UseinfoValidation = sqlalchemy_to_pydantic(Useinfo)


# Answers to specific question types
# ----------------------------------
# Many of the tables containing answers are always accessed by sid, div_id and course_name. Provide this as a default query.
class AnswerMixin(IdMixin):
    # TODO: these entries duplicate Useinfo.timestamp. Why not just have a timestamp_id field?
    #
    # See timestamp_.
    timestamp = Column(DateTime)
    # See div_id_.
    div_id = Column(String(512), index=True)
    # See sid_.
    sid = Column(String(512), index=True)

    # See course_name_. Mixins with foreign keys need `special treatment <http://docs.sqlalchemy.org/en/latest/orm/extensions/declarative/mixins.html#mixing-in-columns>`_.
    @declared_attr
    def course_name(cls):
        return Column(String(512), ForeignKey("courses.course_name"))

    def to_dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class TimedExam(Base, AnswerMixin):
    __tablename__ = "timed_exam"
    # See the `timed exam endpoint parameters <timed exam endpoint parameters>` for documentation on these columns.
    correct = Column(Integer)
    incorrect = Column(Integer)
    skipped = Column(Integer)
    time_taken = Column(Integer)
    # True if the ``act`` endpoint parameter was ``'reset'``; otherwise, False.
    reset = Column(Web2PyBoolean)


# Like an AnswerMixin, but also has a boolean correct_ field.
class CorrectAnswerMixin(AnswerMixin):
    # _`correct`: True if this answer is correct.
    correct = Column(Web2PyBoolean)
    percent = Column(Float)


# An answer to a multiple-choice question.
@register_answer_table
class MchoiceAnswers(Base, CorrectAnswerMixin):
    __tablename__ = "mchoice_answers"
    # _`answer`: The answer to this question. TODO: what is the format?
    answer = Column(String(50))
    __table_args__ = (Index("idx_div_sid_course_mc", "sid", "div_id", "course_name"),)


# An answer to a fill-in-the-blank question.
@register_answer_table
class FitbAnswers(Base, CorrectAnswerMixin):
    __tablename__ = "fitb_answers"
    # See answer_. TODO: what is the format?
    answer = Column(String(512))
    __table_args__ = (Index("idx_div_sid_course_fb", "sid", "div_id", "course_name"),)


# An answer to a drag-and-drop question.
@register_answer_table
class DragndropAnswers(Base, CorrectAnswerMixin):
    __tablename__ = "dragndrop_answers"
    # See answer_. TODO: what is the format?
    answer = Column(String(512))
    __table_args__ = (Index("idx_div_sid_course_dd", "sid", "div_id", "course_name"),)


# An answer to a drag-and-drop question.
@register_answer_table
class ClickableareaAnswers(Base, CorrectAnswerMixin):
    __tablename__ = "clickablearea_answers"
    # See answer_. TODO: what is the format?
    answer = Column(String(512))
    __table_args__ = (Index("idx_div_sid_course_ca", "sid", "div_id", "course_name"),)


# An answer to a Parsons problem.
@register_answer_table
class ParsonsAnswers(Base, CorrectAnswerMixin):
    __tablename__ = "parsons_answers"
    # See answer_. TODO: what is the format?
    answer = Column(String(512))
    # _`source`: The source code provided by a student? TODO.
    source = Column(String(512))
    __table_args__ = (Index("idx_div_sid_course_pp", "sid", "div_id", "course_name"),)


# An answer to a Code Lens problem.
@register_answer_table
class CodelensAnswers(Base, CorrectAnswerMixin):
    __tablename__ = "codelens_answers"
    # See answer_. TODO: what is the format?
    answer = Column(String(512))
    # See source_.
    source = Column(String(512))
    __table_args__ = (Index("idx_div_sid_course_cl", "sid", "div_id", "course_name"),)


@register_answer_table
class ShortanswerAnswers(Base, AnswerMixin):
    __tablename__ = "shortanswer_answers"
    # See answer_. TODO: what is the format?
    answer = Column(String(512))
    __table_args__ = (Index("idx_div_sid_course_sa", "sid", "div_id", "course_name"),)


@register_answer_table
class UnittestAnswers(Base, CorrectAnswerMixin):
    __tablename__ = "unittest_answers"
    answer = Column(Text)
    passed = Column(Integer)
    failed = Column(Integer)
    __table_args__ = (Index("idx_div_sid_course_ut", "sid", "div_id", "course_name"),)


@register_answer_table
class LpAnswers(Base, AnswerMixin):
    __tablename__ = "lp_answers"
    # See answer_. A JSON string; see RunestoneComponents for details. TODO: The length seems too short to me.
    answer = Column(String(512))
    # A grade between 0 and 100.
    correct = Column(Float())
    __table_args__ = (Index("idx_div_sid_course_lp", "sid", "div_id", "course_name"),)


# Code
# ----
# The code table captures every run/change of the students code.  It is used to load
# the history slider of the activecode component.
#
class Code(Base, IdMixin):
    __tablename__ = "code"
    timestamp = Column(DateTime, unique=False, index=True)
    sid = Column(String(512), unique=False, index=True)
    acid = Column(
        String(512),
        unique=False,
        index=True,
    )  # unique identifier for a component
    course_name = Column(String, index=True)
    course_id = Column(Integer, index=False)
    code = Column(Text, index=False)
    language = Column(Text, index=False)
    emessage = Column(Text, index=False)
    comment = Column(Text, index=False)


# Used for datafiles and storing questions and their suffix separately.
# this maybe redundant TODO: check before we port the api call to get
# a datafile
class SourceCode(Base, IdMixin):
    __tablename__ = "source_code"

    acid = Column(String(512), index=True)
    course_id = Column(String(512), index=True)
    includes = Column(String(512))
    available_files = Column(String(512))
    main_code = Column(Text)
    suffix_code = Column(Text)


# Courses
# -------
# Every Course in the runestone system must have an entry in this table
# the id column is really an artifact of the original web2py/pydal implementation of
# Runestone.  The 'real' primary key of this table is the course_name
# Defines either a base course (which must be manually added to the database) or a derived course created by an instructor.
class Courses(Base, IdMixin):
    __tablename__ = "courses"
    # _`course_name`: The name of this course.
    course_name = Column(String(512), unique=True)
    term_start_date = Column(Date)
    # TODO: Why not use base_course_id instead? _`base_course`: the course from which this course was derived. TODO: If this is a base course, this field should be identical to the course_name_?
    base_course = Column(String(512), ForeignKey("courses.course_name"))
    # TODO: This should go in a different table. Not all courses have a Python/Skuplt component.
    login_required = Column(Web2PyBoolean)
    allow_pairs = Column(Web2PyBoolean)
    student_price = Column(Integer)
    downloads_enabled = Column(Web2PyBoolean)
    courselevel = Column(String)


CoursesValidator = sqlalchemy_to_pydantic(Courses)


# Authentication and Permissions
# ------------------------------
class AuthUser(Base, IdMixin):
    __tablename__ = "auth_user"
    username = Column(String(512), nullable=False, unique=True)
    first_name = Column(String(512))
    last_name = Column(String(512))
    email = Column(String(512), unique=True)
    password = Column(String(512))
    created_on = Column(DateTime())
    modified_on = Column(DateTime())
    registration_key = Column(String(512))
    reset_password_key = Column(String(512))
    registration_id = Column(String(512))
    course_id = Column(Integer)
    course_name = Column(String(512))
    active = Column(Web2PyBoolean)
    donated = Column(Web2PyBoolean)
    accept_tcp = Column(Web2PyBoolean)


AuthUserValidator = sqlalchemy_to_pydantic(AuthUser)


class CourseInstructor(Base, IdMixin):
    __tablename__ = "course_instructor"
    course = Column(Integer, ForeignKey("courses.id"), nullable=False)
    instructor = Column(Integer, ForeignKey("auth_user.id"))
    verified = Column(Web2PyBoolean)
    paid = Column(Web2PyBoolean)


CourseInstructorValidator = sqlalchemy_to_pydantic(CourseInstructor)


# Enrollments
# -----------
#
# Users may be enrolled in more than one course. This table tracks
# all of their enrollments
class UserCourse(Base, IdMixin):
    __tablename__ = "user_courses"

    user_id = Column(ForeignKey("auth_user.id", ondelete="CASCADE"))
    course_id = Column(ForeignKey("courses.id", ondelete="CASCADE"))


# Assignments and Questions
# -------------------------


class Question(Base, IdMixin):
    __tablename__ = "questions"
    __table_args__ = (
        UniqueConstraint("name", "base_course"),
        Index("chap_subchap_idx", "chapter", "subchapter"),
    )

    base_course = Column(String(512), nullable=False, index=True)
    name = Column(String(512), nullable=False, index=True)
    chapter = Column(String(512), index=True)
    subchapter = Column(String(512), index=True)
    author = Column(String(512))
    question = Column(Text)
    timestamp = Column(DateTime)
    question_type = Column(String(512))
    is_private = Column(Web2PyBoolean)
    htmlsrc = Column(Text)
    autograde = Column(String(512))
    practice = Column(Web2PyBoolean)
    topic = Column(String(512))
    feedback = Column(Text)
    from_source = Column(Web2PyBoolean)
    review_flag = Column(Web2PyBoolean)
    qnumber = Column(String(512))
    optional = Column(Web2PyBoolean)
    description = Column(Text)
    difficulty = Column(Float(53))
    pct_on_first = Column(Float(53))
    mean_clicks_to_correct = Column(Float(53))


class Assignment(Base, IdMixin):
    __tablename__ = "assignments"
    __table_args__ = (
        Index("assignments_name_course_idx", "name", "course", unique=True),
    )

    course = Column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    name = Column(String(512))
    points = Column(Integer)
    released = Column(Web2PyBoolean)
    description = Column(Text)
    duedate = Column(DateTime)
    visible = Column(Web2PyBoolean)
    threshold_pct = Column(Float(53))
    allow_self_autograde = Column(Web2PyBoolean)
    is_timed = Column(Web2PyBoolean)
    time_limit = Column(Integer)
    from_source = Column(Web2PyBoolean)
    nofeedback = Column(Web2PyBoolean)
    nopause = Column(Web2PyBoolean)


class AssignmentQuestion(Base, IdMixin):
    __tablename__ = "assignment_questions"

    assignment_id = Column(ForeignKey("assignments.id", ondelete="CASCADE"))
    question_id = Column(ForeignKey("questions.id", ondelete="CASCADE"))
    points = Column(Integer)
    timed = Column(Web2PyBoolean)
    autograde = Column(String(512))
    which_to_grade = Column(String(512))
    reading_assignment = Column(Web2PyBoolean)
    sorting_priority = Column(Integer)
    activities_required = Column(Integer)


# Grading
# -------
# The QuestionGrade table holds the score and any comments for a particular
# student,question,course triple
# TODO: this actually seems wrong -- it should be student,question,assignment
# otherwise a student can only have a single grade for a particular question
# what if an instructor assigns the same question more than once??
class QuestionGrade(Base, IdMixin):
    __tablename__ = "question_grades"
    __table_args__ = (
        Index(
            "question_grades_sid_course_name_div_id_idx",
            "sid",
            "course_name",
            "div_id",
            unique=True,
        ),
    )

    sid = Column(String(512), nullable=False)
    course_name = Column(String(512), nullable=False)
    div_id = Column(String(512), nullable=False)
    score = Column(Float(53))
    comment = Column(Text)
    deadline = Column(DateTime)
    answer_id = Column(Integer)


# The Grade table holds the grade for an entire assignment
class Grade(Base, IdMixin):
    __tablename__ = "grades"
    __table_args__ = (UniqueConstraint("auth_user", "assignment"),)

    auth_user = Column(ForeignKey("auth_user.id", ondelete="CASCADE"))
    assignment = Column(ForeignKey("assignments.id", ondelete="CASCADE"))
    score = Column(Float(53))
    manual_total = Column(Web2PyBoolean)
    projected = Column(Float(53))
    lis_result_sourcedid = Column(String(1024))
    lis_outcome_url = Column(String(1024))


# Book Structure Tables
# ---------------------
class Chapter(Base, IdMixin):
    __tablename__ = "chapters"

    chapter_name = Column(String(512))
    course_id = Column(String(512), index=True)
    chapter_label = Column(String(512))
    chapter_num = Column(Integer)


class SubChapter(Base, IdMixin):
    __tablename__ = "sub_chapters"

    sub_chapter_name = Column(String(512))
    chapter_id = Column(ForeignKey("chapters.id", ondelete="CASCADE"), index=True)
    sub_chapter_label = Column(String(512))
    skipreading = Column(Web2PyBoolean)
    sub_chapter_num = Column(Integer)


# Tracking User Progress
# ----------------------
class UserSubChapterProgres(Base, IdMixin):
    __tablename__ = "user_sub_chapter_progress"

    user_id = Column(ForeignKey("auth_user.id", ondelete="CASCADE"), index=True)
    chapter_id = Column(String(512), index=True)
    sub_chapter_id = Column(String(512), index=True)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(Integer)
    course_name = Column(String(512))


class UserChapterProgres(Base, IdMixin):
    __tablename__ = "user_chapter_progress"

    user_id = Column(String(512))
    chapter_id = Column(String(512))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(Integer)


# Tables used by the ``selectquestion`` directive
# -----------------------------------------------


class UserExperiment(Base, IdMixin):
    __tablename__ = "user_experiment"

    experiment_id = Column(String(512))
    sid = Column(String(512))
    exp_group = Column(Integer)


class SelectedQuestion(Base, IdMixin):
    __tablename__ = "selected_questions"

    selector_id = Column(String(512))
    sid = Column(String(512))
    selected_id = Column(String(512))
    points = Column(Integer)
    competency = Column(String(512))


class Competency(Base, IdMixin):
    __tablename__ = "competency"

    question = Column(ForeignKey("questions.id", ondelete="CASCADE"))
    competency = Column(String(512))
    is_primary = Column(Web2PyBoolean)
    question_name = Column(String(512))


# Course Parameters
# -----------------
class CourseAttribute(Base, IdMixin):
    __tablename__ = "course_attributes"
    __table_args__ = (Index("course_attr_idx", "course_id", "attr"),)

    course_id = Column(ForeignKey("courses.id", ondelete="CASCADE"))
    attr = Column(String(512))
    value = Column(Text)


class CourseLtiMap(Base, IdMixin):
    __tablename__ = "course_lti_map"

    lti_id = Column(Integer)
    course_id = Column(Integer)


class LtiKey(Base, IdMixin):
    __tablename__ = "lti_keys"

    consumer = Column(String(512))
    secret = Column(String(512))
    application = Column(String(512))


class Payment(Base, IdMixin):
    __tablename__ = "payments"

    user_courses_id = Column(ForeignKey("user_courses.id", ondelete="CASCADE"))
    charge_id = Column(String(255))
