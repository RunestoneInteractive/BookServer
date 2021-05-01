**************************
Testing for the BookServer
**************************
To run the tests, execute ``poetry run pytest`` from this subdirectory. FastAPI takes care of starting up a server!

.. toctree::
    :maxdepth: 1

    test_rslogging.py
    conftest.py

Continuous Integration
----------------------
.. toctree::
    :maxdepth: 1

    ../ci_utils/ci_utils.py
    ../.github/workflows/python-package.yml