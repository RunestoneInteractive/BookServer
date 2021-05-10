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

#
# Third-party imports
# -------------------
# Use asyncio for SQLAlchemy -- see `SQLAlchemy Asynchronous I/O (asyncio) <https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html>`_.
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Local application imports
# -------------------------
from .config import settings, BookServerConfig, DatabaseType


if settings.database_type == DatabaseType.SQLite:
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

# TODO: Remove the ``echo=True`` when done debugging.
engine = create_async_engine(
    settings.database_url, connect_args=connect_args, #echo=True
)
# This creates the SessionLocal class.  An actual session is an instance of this class.
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# This creates the base class we will use to create models
Base = declarative_base()


async def init_models():
    async with engine.begin() as conn:
        if (
            settings.book_server_config
            in [BookServerConfig.development, BookServerConfig.test]
            and settings.drop_tables == "Yes"
        ):
            await conn.run_sync(Base.metadata.drop_all)

        await conn.run_sync(Base.metadata.create_all)


# If the engine isn't disposed of, then a PostgreSQL database will remain in a pseudo-locked state, refusing to drop of truncate tables (see `bookserver_session`).
async def term_models():
    await engine.dispose()


# Dependency
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
