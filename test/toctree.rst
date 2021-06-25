**************************
Testing for the BookServer
**************************
To run the tests, execute ``poetry run pytest`` from the parent of this subdirectory; running them here causes code coverage failures.

Here is the `pytest configuration`.

.. toctree::
    :maxdepth: 1

    test_rslogging.py
    test_runestone_components.py
    conftest.py
    ci_utils.py
    ../tox.ini
    ../.coveragerc
    ../.github/workflows/python-package.yml
