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
#.  Execute ``bookserver`` from a terminal / command prompt to start the server. `Browse to the bookserver <http://127.0.0.1:8080/>`_ then view the book.

License
=======
.. toctree::
    :maxdepth: 1

    LICENSE

Indices and tables
==================
*   `genindex`
*   `search`