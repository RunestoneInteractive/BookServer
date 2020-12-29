# **********************************
# |docname| - Database configuration
# **********************************
# Set up database configuration in this file
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
# Enable asyncio for SQLAlchemy -- see `databases <https://www.encode.io/databases/>`_.
import databases
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Local application imports
# -------------------------
# See `../config.py`.
from bookserver.config import settings

# :index:`question`: does this belong in `../config.py`?  Or does it just describe the format of a database URL for two databases?
#
## SQLALCHEMY_DATABASE_URL = "sqlite:///./bookserver.db"
## SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"

# .. _setting.dev_dburl:
if settings.config == "development":
    DATABASE_URL = settings.dev_dburl
elif settings.config == "production":
    DATABASE_URL = settings.prod_dburl
elif settings.config == "test":
    DATABASE_URL = settings.test_dburl
else:
    assert False

if settings.dbserver == "sqlite":
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
# This creates the SessionLocal class.  An actual session is an instance of this class.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# This creates the base class we will use to create models
Base = declarative_base()

database = databases.Database(DATABASE_URL)
