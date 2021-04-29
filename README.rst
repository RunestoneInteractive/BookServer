*******************************************
New FastAPI-based Book Server for Runestone
*******************************************

The goal of this project is to replace the parts of the web2py-based RunestoneServer.

We would love development help on this.  Please see our docs including information on contributing to this project `on readthedocs <https://bookserver.readthedocs.io/en/latest/>`_.


Quickstart
==========
First, install BookServer.

Installation options
--------------------
For development:

-   Clone this repository.
-   `Install poetry <https://python-poetry.org/docs/#installation>`_.
-   From the command line / terminal, change to the directory containing this repo then execute ``poetry install``.

To install from PyPi:
-   From the command line / terminal, execute ``python -m pip install -U BookServer`` or ``python3 -m pip install -U BookServer``.

Building books
--------------
-   Check out the ``bookserver`` branch of the Ruestone Components repo and install it.
-   Build a book with this branch.
-   Copy it the `book path <book_path>` or update the book path to point to the location of a built book.
-   Add the book's info to the database.

Running the server
------------------
From the command line / terminal, execute ``poetry run uvicorn bookserver.main:app --reload --port 8080``. If running in development mode, this must be executed from the directory containing the repo.
