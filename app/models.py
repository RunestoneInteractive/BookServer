# In this file we define our SQLAlchemy data models. These get translated into relational database tables.

# Because of the interface with the `databases package <https://www.encode.io/databases/>`_ we will use the `SQLAlchemy core API <https://docs.sqlalchemy.org/en/14/core/>`_

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    DateTime,
    MetaData,
    Table,
)
from sqlalchemy.orm import relationship

metadata = MetaData()
#
# This defines the useinfo table in the database
#
logitem = Table(
    "useinfo",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("timestamp", DateTime, unique=False, index=True),
    Column("sid", String, unique=False, index=True),
    Column("event", String, unique=False, index=True),
    Column("act", String, unique=False, index=False),
    Column(
        "div_id",
        String,
        unique=False,
        index=True,
    ),  # unique identifier for a component
    Column("course_id", String, unique=False, index=True),
    Column("chapter", String, unique=False, index=False),
    Column("sub_chapter", String, unique=False, index=False),
)

# Each gradable Runestone component has its own answer table.  Most of them are identical
ANSWER_TABLE_NAMES = [
    "mchoice_answers",
    "clickablearea_answers",
    "codelens_answers",
    "dragndrop_answers",
    "fitb_answers",
    " lp_answers",
    "parsons_answers",
    "shortanswer_answers",
    "unittest_answers",
]

answer_columns = []

# This should make working with answer tables much easier across the board as we can now just access them by name instead of duplicating code for each case.
answer_tables = {}

for tbl in ANSWER_TABLE_NAMES:
    answer_tables[tbl] = Table(
        tbl,
        metadata,
        Column("id", Integer, primary_key=True, index=True),
        Column("timestamp", DateTime, unique=False, index=True),
        Column("sid", String, unique=False, index=True),
        Column(
            "div_id",
            String,
            unique=False,
            index=True,
        ),  # unique identifier for a component
        Column("course_name", String, index=True),
        Column("correct", Boolean),
        Column("answer", String),
    )

# The parsons_answers table is the only outlier in that it adds a source column to keep
# track of which blocks were not used in the answer.
answer_tables["parsons_answers"] = Table(
    "parsons_answers", metadata, Column("source", String), extend_existing=True
)
