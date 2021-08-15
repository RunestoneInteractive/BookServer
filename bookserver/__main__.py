# *****************************************************
# |docname| - Provide a simple method to run the server
# *****************************************************
# From the terminal / command line, execute either ``bookserver`` or ``python -m bookserver``, which runs the book server.

import multiprocessing
import subprocess
import sys


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
            # Pick the number of workers automatically based on the CPU count.
            f"--workers={multiprocessing.cpu_count()}",
            # Use the `uvicorn's worker class for gunicorn <https://www.uvicorn.org/deployment/#gunicorn>`_.
            "--worker-class=uvicorn.workers.UvicornWorker",
            # By default, server on port 8080.
            "--bind=localhost:8080",
            # Run the bookserver app.
            "bookserver.main:app",
        ]

    # Suppress a traceback on a keyboard interrupt.
    try:
        return subprocess.run(args).returncode
    except KeyboardInterrupt:
        return 1


if __name__ == "__main__":
    sys.exit(run())
