# In this file we define our SQLAlchemy data models. These get translated into relational database tables.

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship

from .database import Base


#
# This defines the useinfo table in the database
#
class LogItem(Base):
    __tablename__ = "useinfo"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, unique=False, index=True)
    sid = Column(String, unique=False, index=True)
    event = Column(String, unique=False, index=True)
    act = Column(String, unique=False, index=False)
    div_id = Column(
        String, unique=False, index=True
    )  # unique identifier for a component
    course_id = Column(String, unique=False, index=True)
    chapter = Column(String, unique=False, index=False)
    sub_chapter = Column(String, unique=False, index=False)
