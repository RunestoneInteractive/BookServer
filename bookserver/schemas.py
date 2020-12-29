# ************************************************************
# |docname| -- Define validation for endpoint query parameters
# ************************************************************
# This file contains the models we use for post requests and for type checking throughout the application.
# These object models should be used wherever possible to ensure consistency

# Imports
# =======
# These are listed in the order prescribed by `PEP 8`_.
#
# Standard library
# ----------------
# For ``time`, ``date``, and ``timedelta``.
from datetime import datetime

# For ``List``.
from typing import Optional

# Third-party imports
# -------------------
# See: https://pydantic-docs.helpmanual.io/usage/types/#datetime-types for field types
from pydantic import BaseModel

# Local application imports
# -------------------------
# None.


# Schemas
# =======
class LogItemIncoming(BaseModel):
    """
    This class defines the schema for what we can expect to get from a logging event.
    Because we are using pydantic type verification happens automatically, if we want
    to add additional constraints we can do so.
    """

    # :index:`TODO`: Is there any way to specify max string lengths? The database has fixed-length fields for some of these.
    event: str
    act: str
    div_id: str
    course_name: str
    answer: Optional[str]
    correct: Optional[bool]
    chapter: Optional[str]
    subchapter: Optional[str]
    # used by parsons
    source: Optional[str]


class LogItem(LogItemIncoming):
    """
    This may seem like overkill but it illustrates a point.  The schema for the incoming log data will not contain a timestamp.  We could make it optional there, but then that would imply that it is optional which it most certainly is not.  We could add timestamp as part of a LogItemCreate class similar to how password is handled in the tutorial: https://fastapi.tiangolo.com/tutorial/sql-databases/ But there is no security reason to exclude timestamp.  So I think this is a reasonable compromise.
    """

    timestamp: datetime

    class Config:
        orm_mode = True
        # this tells pydantic to try read anything with attributes we give it as a model


class AssessmentRequest(BaseModel):
    course: str
    div_id: str
    event: str
    sid: Optional[str] = None
    deadline: Optional[str] = None
