**************************
Testing for the BookServer
**************************
To run the tests, execute ``poetry run pytest`` from this subdirectory. FastAPI takes care of starting up a server!

Here is the `pytest configuration`.

.. toctree::
    :maxdepth: 1

    test_rslogging.py
    test_runestone_components.py
    conftest.py
    ci_utils.py
    ../.github/workflows/python-package.yml
