**************************
Testing for the BookServer
**************************
To run the tests, execute ``poetry run pytest`` from the parent of this subdirectory; running them here causes code coverage failures. There are several important command-line options:

* ``--skipdbinit``    Skip initialization of the test database. This makes the tests start much faster, at the risk of a corrupt database causing spurious test failures.
* ``--server_debug``  Enable server debug mode. This runs the server in a separate terminal/console, which allow you to set breakpoints, stop the code, etc.
* ``--log-cli-level LEVEL``   Set the `pytest logging level <https://docs.pytest.org/en/6.2.x/logging.html#live-logs>`_. This level affects not just pytest, but the server and all tools run by the tests. Use ``--log-cli-level=INFO`` to provide complete output from the server; the `default logging level <default logging level>` is ``WARNING``.
* ``--k EXPRESSION``   Only run tests which match the given substring expression. For example, ``-k test_foo`` only runs tests named ``test_foo``, ``test_foo_1``, etc. See the `pytest docs <https://docs.pytest.org/en/6.2.x/usage.html#specifying-tests-selecting-tests>`_ for more possibilities.

Testing and debugging tips:

-   To help track down errors, you may insert a breakpoint at any point in the test code; simply insert the line ``import pdb; pdb.set_trace()`` and the test will enter the `Python debugger <https://docs.python.org/3/library/pdb.html#debugger-commands>`_.
-   The same technique works on the server, but you must also specify the ``--server_debug`` option so you can debug the server in its own window.
-   For Selenium-based tests (which run in a separate Chrome browser), you can also interact with Chrome as usual -- open the JavaScript console, set breakpoints, etc. Be sure to set a breakpoint in the test code, so you'll have more than the default 10 second timeout to explore. When done, navigate to the window you ran pytest in then type ``c`` and press enter to tell the Python debugger to continue running tests.

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
    ../tox.ini
    ../.coveragerc
    ../.github/workflows/python-package.yml
