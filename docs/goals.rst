*****
Goals
*****
The goals of this project are as follows:

-   Split the Runestone Server into two parts:

    -   The instructor web app -- low volume fewer users.
    -   The book server -- high volume many many users.

-   Begin migrating to a modern development framework

    -   FastAPI - an async web framework in the spirit of Flask
    -   SQLAlchemy or another database layer that will support tracking of indices and migrations

-   The server should be pip installable and run with SQLLite out of the box for small installations. This server will become the ``runestone serve`` server.
-   Build in ``pytest`` tests and documentation from the ground up with full coverage.
