#!/usr/bin/env python3
# *******************************************
# |docname| - Formatting, Lint, and Unittests
# *******************************************
# This script runs a series of checks that should all pass before submitting a pull request.
# In a perfect world, these would also pass before every commit. The checks are detailed in `pull requests`.
#
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8`_.
#
# Standard library
# ----------------
# None.

# Third-party imports
# -------------------
# None.
#
# Local application imports
# -------------------------
from test.ci_utils import xqt


# Checks
# ======
def checks():
    xqt(
        # Run this first, since it's quick and should always succeed.
        "black --check .",
        # Do this next -- it should be easy to fix most of these.
        "flake8 .",
        "mypy --install-types --non-interactive",
        # Next, check the docs. Again, these only require fixes to comments, and should still be relatively easy to correct.
        #
        # Force a `full build <https://www.sphinx-doc.org/en/master/man/sphinx-build.html>`_:
        #
        # -E    Don’t use a saved environment (the structure caching all cross-references), but rebuild it completely.
        # -a    If given, always write all output files.
        "sphinx-build -E -a . _build",
        # Finally, unit tests -- the hardest to get right.
        "pytest -v",
    )


# .. attention:: Coverage Reports
#
#     The command ``coverage html`` will generate a test coverage report showing
#     the lines of code that were executed (or not) by the tests. This is a great
#     report to help figure out what new tests should be written to keep our coverage
#     near 100%  You can view the report by opening ``test/htmlcov/index.html`` in
#     your browser.

if __name__ == "__main__":
    checks()
