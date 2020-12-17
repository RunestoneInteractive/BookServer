# In this file we define our SQLAlchemy data models. These get translated into relational database tables.

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, MetaData, Table
from sqlalchemy.orm import relationship

from .database import Base

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
    Column("div_id",
        String, unique=False, index=True,
    ),  # unique identifier for a component
    Column("course_id", String, unique=False, index=True),
    Column("chapter", String, unique=False, index=False),
    Column("sub_chapter", String, unique=False, index=False),
)
