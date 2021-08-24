# *****************************************************
# |docname| - Provide a simple method to run the server
# *****************************************************
# From the terminal / command line, execute either ``bookserver`` or ``python -m bookserver``, which runs the book server.
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8`_.
#
# Standard library
# ----------------
from pathlib import Path
import subprocess
import sys

# Third-party imports
# -------------------
# None.
#
# Local application imports
# -------------------------
# None.
#
#
# Code
# ====
def run():
    is_win = sys.platform == "win32"
    # gnuicorn doesn't `run on Windows <https://github.com/benoitc/gunicorn/issues/524>`_.
    if is_win:
        args = [
            sys.executable,
            "-m",
            "uvicorn",
            # See the `uvicorn command-line docs <https://www.uvicorn.org/#command-line-options>`_.
            "--port",
            "8080",
            "bookserver.main:app",
        ]
    else:
        args = [
            sys.executable,
            "-m",
            # See the `gunicorn command-line docs <https://docs.gunicorn.org/en/latest/run.html#commonly-used-arguments>`_.
            "gunicorn",
            # `-c <https://docs.gunicorn.org/en/stable/settings.html#config>`_: The Gunicorn config file. Use `deployment/gunicorn.conf.py`.
            "--config",
            # Provide an absolute path to the Gunicorn config file.
            Path(__file__).parents[1] / "deployment/gunicorn.conf.py",
            # Serve on port 8080.
            "--bind=localhost:8080",
        ]

    # Suppress a traceback on a keyboard interrupt.
    try:
        return subprocess.run(args).returncode
    except KeyboardInterrupt:
        return 1


if __name__ == "__main__":
    sys.exit(run())
