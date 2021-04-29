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
from datetime import datetime, timedelta
from dateutil.parser import parse
from typing import Container, Optional, Type, Dict, Tuple, Union, Any

# Third-party imports
# -------------------
from pydantic import BaseModel, create_model, constr, validator, Field

# Local application imports
# -------------------------
from . import models
from .internal.utils import canonicalize_tz


# Schema generation
# =================
# This creates then returns a Pydantic schema from a SQLAlchemy Table or ORM class.
#
# This is copied from https://github.com/tiangolo/pydantic-sqlalchemy/blob/master/pydantic_sqlalchemy/main.py then lightly modified.
def sqlalchemy_to_pydantic(
    # The SQLAlchemy model -- either a Table object or a class derived from a declarative base.
    db_model: Type,
    *,
    # An optional Pydantic `model config <https://pydantic-docs.helpmanual.io/usage/model_config/>`_ class to embed in the resulting schema.
    config: Optional[Type] = None,
    # The base class from which the Pydantic model will inherit.
    base: Optional[Type] = None,
    # SQLAlchemy fields to exclude from the resulting schema, provided as a sequence of field names.
    exclude: Container[str] = [],
) -> Type[BaseModel]:

    # If provided an ORM model, get the underlying Table object.
    db_model = getattr(db_model, "__table__", db_model)

    fields: Dict[str, Union[Tuple[str, Any], Type]] = {}
    for column in db_model.columns:
        # Determine the name of this column.
        name = column.key
        if name in exclude:
            continue

        # Determine the Python type of the column.
        python_type = column.type.python_type
        if python_type == str and hasattr(column.type, "length"):
            python_type = constr(max_length=column.type.length)

        # Determine the default value for the column.
        default = None
        if column.default is None and not column.nullable:
            default = ...

        # Build the schema based on this info.
        fields[name] = (python_type, default)

    # Optionally include special key word arguments. See `create_model <https://pydantic-docs.helpmanual.io/usage/models/#dynamic-model-creation>`_.
    if config:
        fields["__config__"] = config
    if base:
        fields["__base__"] = base
    pydantic_model = create_model(str(db_model.name), **fields)  # type: ignore
    return pydantic_model


Useinfo = sqlalchemy_to_pydantic(models.Useinfo.__table__)


# Schemas
# =======
class LogItemIncoming(BaseModel):
    """
    This class defines the schema for what we can expect to get from a logging event.
    Because we are using pydantic type verification happens automatically, if we want
    to add additional constraints we can do so.
    """

    # FIXME: Use max lengths for strings based on the actual lengths from the database using `Pydantic constraints <https://pydantic-docs.helpmanual.io/usage/types/#constrained-types>`_. Is there any way to query the database for these, instead of manually keeping them in sync?
    event: str
    act: str
    div_id: str
    sid: str
    course_name: str
    answer: Optional[str]
    correct: Optional[bool]
    percent: Optional[float]
    clientLoginStatus: Optional[bool]
    timezoneoffset: Optional[int]
    chapter: Optional[str]
    subchapter: Optional[str]
    # used by parsons
    source: Optional[str]


class LogItem(LogItemIncoming):
    """
    This may seem like overkill but it illustrates a point.  The schema for the incoming log data will not contain a timestamp.  We could make it optional there, but then that would imply that it is optional which it most certainly is not.  We could add timestamp as part of a LogItemCreate class similar to how password is handled in the tutorial: https://fastapi.tiangolo.com/tutorial/sql-databases/ But there is no security reason to exclude timestamp.  So I think this is a reasonable compromise.
    """

    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @validator("timestamp")
    def str_to_datetime(cls, value: str) -> datetime:
        # TODO: this code probably doesn't work.
        try:
            deadline = parse(canonicalize_tz(value))
            # TODO: session isn't defined. Here's a temporary fix
            # tzoff = session.timezoneoffset if session.timezoneoffset else 0
            tzoff = 0
            deadline = deadline + timedelta(hours=float(tzoff))
            deadline = deadline.replace(tzinfo=None)
        except Exception:
            # TODO: can this enclose just the parse code? Or can an error be raised in other cases?
            raise ValueError(f"Bad Timezone - {value}")
        return deadline


class AssessmentRequest(BaseModel):
    course: str
    div_id: str
    event: str
    sid: Optional[str] = None
    # See `Field with dynamic default value <https://pydantic-docs.helpmanual.io/usage/models/#required-optional-fields>`_.
    deadline: Optional[str] = None


class User(BaseModel):
    username: str
    course_name: str
    course_id: int
    first_name: str
    last_name: str
    email: str
    password_hash: str
