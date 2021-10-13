# ***********************************
# |docname| - gunincorn configuration
# ***********************************
# This file configures gunicorn to use Uvicorn to run FastAPI which runs the BookServer.
#
# See also the `gunicorn config docs <https://docs.gunicorn.org/en/stable/configure.html#configuration-file>`_.
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8`_.
#
# Standard library
# ----------------
import multiprocessing

# Third-party imports
# -------------------
# None.
#
# Local application imports
# -------------------------
# None.
#
#
# Configuration
# =============
# `user <https://docs.gunicorn.org/en/stable/settings.html#user>`_: Switch worker processes to run as this user.
user = "www-data"

# `group <https://docs.gunicorn.org/en/stable/settings.html#group>`_: Switch worker process to run as this group.
group = "www-data"

# `workers <https://docs.gunicorn.org/en/stable/settings.html#workers>`_: The number of worker processes for handling requests. Pick this based on CPU count.
workers = multiprocessing.cpu_count() + 1
