# *********************************
# |docname| - Alembic configuration
# *********************************
# Set up Alembic for migrating only tables managed by this server. It does not migrate tables managed by the web2py admin interface.
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8`_.
#
# Standard library
# ----------------
from logging.config import fileConfig
from textwrap import dedent

# Third-party imports
# -------------------
from alembic import context
from sqlalchemy import create_engine

# Local application imports
# -------------------------
from bookserver import models
from bookserver.applogger import rslogger
from bookserver.config import settings

# Configuration
# =============
# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = models.Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# Use the non-async flavor of the provided database URL.
dburl = settings.database_url.replace("+asyncpg", "").replace("+aiosqlite", "")
rslogger.info(f"Using DBURL of {dburl}.")

# Compute tables not to migrate
# -----------------------------
# We want to include all tables not managed by web2py. To get this list, compute (all tables in a working Runestone Server instance) - (all tables in a working Bookserver instance). To gather these lists of tables, the query is:
## SELECT input_table_name AS truncate_query FROM(SELECT table_name AS input_table_name FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog', 'information_schema') AND table_schema NOT LIKE 'pg_toast%') AS information order by input_table_name;
#
# The data below was copied and pasted from psql output of these queries.
web2py_tables = dedent(
    """
 acerror_log
 alembic_version
 assignment_questions
 assignments
 auth_cas
 auth_event
 auth_group
 auth_membership
 auth_permission
 auth_user
 book_author
 page_views
 user_activity
 chapters
 clickablearea_answers
 code
 codelens_answers
 competency
 course_attributes
 course_instructor
 course_lti_map
 course_practice
 courses
 dragndrop_answers
 editor_basecourse
 fitb_answers
 grades
 invoice_request
 lp_answers
 lti_keys
 mchoice_answers
 parsons_answers
 payments
 practice_grades
 question_grades
 question_tags
 questions
 scheduler_run
 scheduler_task
 scheduler_task_deps
 scheduler_worker
 selected_questions
 shortanswer_answers
 source_code
 sub_chapter_taught
 sub_chapters
 tags
 timed_exam
 unittest_answers
 useinfo
 user_biography
 user_chapter_progress
 user_courses
 user_experiment
 user_state
 user_sub_chapter_progress
 user_topic_practice
 user_topic_practice_completion
 user_topic_practice_feedback
 user_topic_practice_log
 user_topic_practice_survey
 web2py_session_exam_runestone
 web2py_session_runestone
"""
).split()


bookserver_tables = dedent(
    """
 assignment_questions
 assignments
 auth_user
 chapters
 clickablearea_answers
 code
 codelens_answers
 competency
 course_attributes
 course_instructor
 course_lti_map
 course_practice
 courses
 dragndrop_answers
 fitb_answers
 grades
 library
 lp_answers
 lti_keys
 mchoice_answers
 parsons_answers
 payments
 question_grades
 questions
 selected_questions
 shortanswer_answers
 source_code
 sub_chapters
 timed_exam
 traceback
 unittest_answers
 useinfo
 user_chapter_progress
 user_courses
 user_experiment
 user_state
 user_sub_chapter_progress
 user_topic_practice
"""
).split()


web2py_only_tables = set(web2py_tables) - set(bookserver_tables)


# Ignore tables used only by the admin interface.
def include_name(name, type_, parent_names):
    if type_ == "table":
        return name not in web2py_only_tables
    else:
        return True


# Define and run migrations
# =========================
def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = dburl
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_engine(dburl)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_name=include_name,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
