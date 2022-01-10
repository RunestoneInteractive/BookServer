.. include:: README.rst

.. contents:: Table of Contents
    :local:

.. toctree::
    :hidden:

    README
    docs/dev_toctree


Installation
============

Instructors
-----------
These instructions enable you to install the BookServer and books of your choice, so that you and your students can use them.

TODO: This hasn't been published on PyPI yet.

#.   From the command line / terminal, execute ``python -m pip install -U BookServer`` (Windows) or ``python3 -m pip install -U BookServer`` (Linux/Mac).
#.  TODO: install books. Ideally, the websever would have a "install book" GUI to handle this. A secondary choice: download and unzip a built book from GitHub. For now: follow the author directions.
#.  Execute ``bookserver`` from a terminal / command prompt to start the server. `Browse to the bookserver <http://127.0.0.1:8080/>`_ then view the book. TODO: create an initial admin account if the db is empty.

Congratulations! The BookServer is up and running. Next, follow the `instructor's guide <https://runestone.academy/runestone/books/published/instructorguide/index.html>`_.

Authors
-------
These instructors enable you to install the BookServer, then author or edit books for it.

#.   From the command line / terminal, execute ``python -m pip install -U BookServer`` (Windows) or ``python3 -m pip install -U BookServer`` (Linux/Mac).
#.  To edit an exiting book, first clone it from the `RunestoneInteractive Github page <https://github.com/RunestoneInteractive>`_. Otherwise, create a new directory then execute ``runestone init`` at a terminal / command prompt.
#.  `Author the book <https://runestone.academy/runestone/books/published/overview/index.html>`_; the `CodeChat System <https://codechat-system.readthedocs.io/en/latest/>`_ provides a GUI to make this easier, but a text editor plus running ``runestone build --all`` from the terminal / command prompt also works.
#.  Deploy the book using ``runestone deploy``. TODO: this should automatically add the book to the courses table, and copy it to the correct `book path <book_path>`.
#.  Execute ``bookserver`` from a terminal / command prompt to start the server. `Browse to the bookserver <http://127.0.0.1:8080/>`_ then view the book.  Running ``bookserver`` requires a few environment variables be set up, you can also start it by supplying key parameters on the command line:

.. code-block:: bash

    bookserver --gconfig gdev.conf.py \
                --bks_config development \
                --dburl sqlite+aiosqlite:////path/to/runestone_dev.db \
                --reload

This configuration is very simple and uses a sqlite database, suitable for experiments or development work.  The ``gdev.conf.py`` file has just a few lines that you can modify.  You can copy ``deployment/gunicorn.conf.py`` and edit it if you wish.

.. code-block:: python

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

    # Configuration
    # =============
    # `wsgi_app <https://docs.gunicorn.org/en/stable/settings.html#wsgi-app>`_: A WSGI application path in pattern ``$(MODULE_NAME):$(VARIABLE_NAME)``.
    wsgi_app = "bookserver.main:app"

    # `workers <https://docs.gunicorn.org/en/stable/settings.html#workers>`_: The number of worker processes for handling requests. Pick this based on CPU count.
    workers = multiprocessing.cpu_count() * 2 + 1

    # `worker_class <https://docs.gunicorn.org/en/stable/settings.html#worker-class>`_: The type of workers to use. Use `uvicorn's worker class for gunicorn <https://www.uvicorn.org/deployment/#gunicorn>`_.
    worker_class = "uvicorn.workers.UvicornWorker"

License
=======
.. toctree::
    :maxdepth: 1

    LICENSE


Indices and tables
==================
*   `genindex`
*   `search`