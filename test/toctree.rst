**************************
Testing for the BookServer
**************************
To run the tests, execute ``poetry run pytest`` from this subdirectory. FastAPI takes care of starting up a server!

Here is the `pytest configuration`.

TODO: the doc structure should be

- Testing

  - (test/) Unit test approach
  - (.github/workflow) CI

- Coding style

  - (pyproject.toml) poetry instead of setup.py for dependency management.
  - (pre_commit_hook.py) use black, flake8, mypy?
  - (conf.py) Docs using CodeChat, posted on readthedocs. Hyperlinks between projects.

.. toctree::
    :maxdepth: 1

    test_rslogging.py
    test_runestone_components.py
    conftest.py
    ci_utils.py
    ../.github/workflows/python-package.yml
