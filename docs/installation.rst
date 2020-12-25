************
Installation
************
#.  `Install Python <https://www.python.org/downloads/>`_.
#.  `Install poetry <https://python-poetry.org/docs/#installation>`_.
#.  Git clone the `book server <https://github.com/bnmnetp/BookServer>`_.
#.  Open a terminal/command prompt, then navigate to the ``BookServer`` subdirectory.
#.  Run ``poetry install``.
#.  Run ``poetry run uvicorn app.main:app --reload``. See `Using your virtual environment <https://python-poetry.org/docs/basic-usage/#using-your-virtual-environment>`_ for more information.
#.  Navigate to http://localhost:8000/docs.