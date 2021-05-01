# ***************************************
# |docname| - pytest fixtures for testing
# ***************************************
#
# ``conftest.py`` is the standard file for defining **fixtures**
# for `pytest <https://docs.pytest.org/en/stable/fixture.html>`_.
# One job of a fixture is to arrange and set up the environment
# for the actual test.
# It may seem a bit mysterious to newcomers that you define
# fixtures in here and use them in your various ``xxx_test.py`` files
# especially because you do not need to import the fixtures they just
# magically show up.  Bizarrely fixtures are called into action on
# behalf of a test by adding them as a parameter to that test.

# from subprocess import run
import re
import os
from pathlib import Path

import pytest


# Create a fixture! This fixture will ensure the sqlite database is removed
# To use this fixture just add ``init_sqlite`` to the parameter list of
# your function.
@pytest.fixture
def init_sqlite():
    os.environ["CONFIG"] = "test"
    assert os.environ["TEST_DBURL"]
    dburl = os.environ["TEST_DBURL"]
    if dburl.startswith("sqlite"):
        # This is such a beautiful use case for the walrus := operator
        # sqlite urls have 4 slashes for an absolute path and 3 slashes
        # for a relative url.  Some like ///./ to be clear.
        if match := re.match(r"sqlite.*?///(.*)", dburl):
            path = match.group(1)
            if Path(path).exists():
                os.unlink(path)
