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
from enum import Enum
from pathlib import Path

# Third-party imports
# -------------------
from pydantic import BaseSettings

# Local application imports
# -------------------------
# None.


# Settings
# ========
# Define the possible bookserver configurations. The values assigned must  be strings, since Pydantic will match these with environment variables.
class BookServerConfig(Enum):
    development = "development"
    test = "test"
    production = "production"


class Settings(BaseSettings):
    # Pydantic provides a wonderful utility to handle settings.  The beauty of it
    # is that you can specify variables with or without default values, and Pydantic
    # will check your environment variables, in a case insensitive way. So that
    # if you have PROD_DBURL set in the environment it will be set as the value
    # for prod_dburl in settings.
    # This is a really nice way to keep from
    # committing any data you want to keep private.

    google_ga: str = ""

    # This looks a bit odd, since the string value will be parsed by Pydantic into a Config.
    book_server_config: BookServerConfig = "development"  # type: ignore

    # Database setup: this must be an async connection; for example:
    #
    # - ``sqlite+aiosqlite:///./runestone.db``
    # - ``postgresql+asyncpg://postgres:bully@localhost/runestone``
    prod_dburl: str = "sqlite+aiosqlite:///./runestone.db"
    dev_dburl: str = "sqlite+aiosqlite:///./runestone_dev.db"
    test_dburl: str = "sqlite+aiosqlite:///./runestone_test.db"

    # Determine the database URL based on the ``config`` and the dburls above.
    @property
    def database_url(self) -> str:
        return {
            "development": self.dev_dburl,
            "test": self.test_dburl,
            "production": self.prod_dburl,
        }[self.book_server_config.value]

    # Configure ads. TODO: Link to the place in the Runestone Components where this is used.
    adsenseid: str = ""
    num_banners: int = 0
    serve_ad: bool = False

    # _`book_path`: specify the directory to serve books from.
    book_path: Path = Path.home() / "Runestone/books"

    # This is the secret key used for generating the JWT token
    secret: str = "supersecret"

    # The path to web2py.
    web2py_path: str = str(Path(__file__).parents[2] / "web2py")

    # This is the private key web2py uses for hashing passwords.
    @property
    def web2py_private_key(self) -> str:
        authfile = Path(self.web2py_path) / "private" / "auth.key"
        with open(authfile, encoding="utf-8") as f:
            return f.read().strip()

    # web2py_private_key: str = "sha512:16492eda-ba33-48d4-8748-98d9bbdf8d33"
    # if you want to reinitialize your database set this to Yes
    # All data in the database will be lost
    drop_tables: str = "No"


settings = Settings()
