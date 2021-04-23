New FastAPI-based Book Server for Runestone

The goal of this project is to replace the parts of the web2py-based RunestoneServer.

We would love development help on this.  Please see our docs including information on contributing to this project [on readthedocs](https://bookserver.readthedocs.io/en/latest/)


Getting up and Running
======================

1. clone this repository
2. pip install poetry
3. run poetry install
4. run uvicorn bookserver.main:app --reload --port 8080

By default this will run with a small sqllite database for development.
