#!/usr/bin/env python3
# ****************************************************************************************
# |docname| - Run a series of checks that should all pass before submitting a pull request
# ****************************************************************************************
# In a perfect world, these would also pass before every commit. The checks are detailed in `pull requests`.
#
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8`_.
#
# Standard library
# ----------------
from pathlib import Path
import sys

# Third-party imports
# -------------------
# None.
#
# Local application imports
# -------------------------
# This isn't in the path, since it's used only for development.
sys.path.insert(0, str(Path(__file__).parent / "ci_utils"))
from ci_utils import xqt, pushd  # noqa: E402


# Checks
# ======
def checks():
    xqt(
        # Run this first, since it's quick and should always succeed.
        "black --check .",
        # Do this next -- it should be easy to fix most of these.
        "flake8 .",
        # Next, check the docs. Again, these only require fixes to comments, and should still be relatively easy to correct.
        #
        # Force a `full build <https://www.sphinx-doc.org/en/master/man/sphinx-build.html>`_:
        #
        # -E    Don’t use a saved environment (the structure caching all cross-references), but rebuild it completely.
        # -a    If given, always write all output files.
        "sphinx-build -E -a . _build",
    )
    # Finally, unit tests -- the hardest to get right.
    with pushd("test"):
        xqt("pytest --cov=bookserver")


# .. attention:: Coverage Reports
#
#     The command ``coverage html`` will generate a test coverage report showing
#     the lines of code that were executed (or not) by the tests. This is a great
#     report to help figure out what new tests should be written to keep our coverage
#     near 100%  You can view the report by opening ``test/htmlcov/index.html`` in
#     your browser.

if __name__ == "__main__":
    checks()
