# ********************************************
# |docname| - Configuring Runestone BookServer
# ********************************************
# Many thing about Runestone BookServer are configurable. This is the place to change
# the configuration for most things.  **Private** things should be configured in the
# environment so they are not accidentally committed to Github.
# Defaults provided here may be overridden by environment variables `Per <https://fastapi.tiangolo.com/advanced/settings/>`_.
#
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8`_.
#
# Standard library
# ----------------
from pathlib import Path

# Third-party imports
# -------------------
from pydantic import BaseSettings

# Local application imports
# -------------------------
# None.


# Settings
# ========
class Settings(BaseSettings):
    # Pydantic provides a wonderful utility to handle settings.  The beauty of it
    # is that you can specify variables with or without default values, and Pydantic
    # will check your environment variables, in a case insensitive way. So that
    # if you have PROD_DBURL set in the environment it will be set as the value
    # for prod_dburl in settings.
    # This is a really nice way to keep from
    # committing any data you want to keep private.

    google_ga: str = ""

    # Either ``development``, ``production``, or ``test``, per `this code <setting.dev_dburl>`. TODO: Use an Enum for this instead! (Will that work with env vars?)
    config: str = "development"

    # `Database setup <setting.dev_dburl>`. It must be an async connection; for example:
    #
    # - ``sqlite+aiosqlite:///./runestone.db``
    # - ``postgresql+asyncpg://postgres:bully@localhost/runestone``
    prod_dburl: str = "sqlite+aiosqlite:///./runestone.db"
    dev_dburl: str = "sqlite+aiosqlite:///./runestone_dev.db"
    test_dburl: str = "sqlite+aiosqlite:///./runestone_test.db"

    # Configure ads. TODO: Link to the place in the Runestone Components where this is used.
    adsenseid: str = ""
    num_banners: int = 0
    serve_ad: bool = False

    # :index:`docs to write`: **What's this?**
    library_path: str = "/Users/bmiller/Runestone"
    dbserver: str = "sqlite"

    # Specify the directory to serve books from.
    book_path: Path = Path(__file__).parents[1] / "books"

    # This is the secret key used for generating the JWT token
    secret: str = "supersecret"

    # This is the private key web2py uses for hashing passwords.
    # For CI purposes this matches my private dev server.
    web2py_private_key: str = "sha512:16492eda-ba33-48d4-8748-98d9bbdf8d33"


settings = Settings()
