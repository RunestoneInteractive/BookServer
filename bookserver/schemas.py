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
from pydantic import BaseModel, BaseConfig, create_model, constr, validator, Field

# Local application imports
# -------------------------
from .internal.utils import canonicalize_tz


# Schema generation
# =================
# This creates then returns a Pydantic schema from a SQLAlchemy Table or ORM class.
#
# This is copied from https://github.com/tiangolo/pydantic-sqlalchemy/blob/master/pydantic_sqlalchemy/main.py then lightly modified.
class OrmConfig(BaseConfig):
    orm_mode = True


def sqlalchemy_to_pydantic(
    # The SQLAlchemy model -- either a Table object or a class derived from a declarative base.
    db_model: Type,
    *,
    # An optional Pydantic `model config <https://pydantic-docs.helpmanual.io/usage/model_config/>`_ class to embed in the resulting schema.
    config: Type = OrmConfig,
    # The base class from which the Pydantic model will inherit.
    base: Optional[Type] = None,
    # SQLAlchemy fields to exclude from the resulting schema, provided as a sequence of field names. Ignore the id field by default.
    exclude: Container[str] = tuple(),
):

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

        # Determine if the column can be null, meaning it's optional from a Pydantic perspective. Make the id column optional, since it won't be present when inserting values to the database.
        if column.nullable or name == "id":
            python_type = Optional[python_type]

        # Determine the default value for the column. Allow the id column to be null.
        default = column.default
        if callable(default):
            default = column.default()
        if column.default is None and not column.nullable and name != "id":
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


# Schemas
# =======
class LogItemIncoming(BaseModel):
    """
    This class defines the schema for what we can expect to get from a logging event.
    Because we are using pydantic type verification happens automatically, if we want
    to add additional constraints we can do so.
    """

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
    This may seem like overkill but it illustrates a point.  The schema for the incoming log data will not contain a timestamp.  We could make it optional there, but then that would imply that it is optional which it most certainly is not.  We could add timestamp as part of a LogItemCreate class similar to how password is handled in the tutorial: https://fastapi.tiangolo.com/tutorial/sql-databases/. But there is no security reason to exclude timestamp.  So I think this is a reasonable compromise.
    """

    timestamp: datetime


class AssessmentRequest(BaseModel):
    course: str
    div_id: str
    event: str
    sid: Optional[str] = None
    # See `Field with dynamic default value <https://pydantic-docs.helpmanual.io/usage/models/#required-optional-fields>`_.
    deadline: datetime = Field(default_factory=datetime.utcnow)

    @validator("deadline")
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
