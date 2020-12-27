**********************
Development guidelines
**********************
This document covers guidelines for developers contributing to this project.

Documentation
=============
*   Write documentation using ReStruturedText files instead of Markdown -- RST supports more Sphinx features.
*   Intersphinx is configured, so you can provide hyperlinks directly to Runestone Components. Provide these helps to help illustrate the ways these two codebases interact.
*   Interleave documentation with code based on the `CodeChat style guidelines <https://codechat.readthedocs.io/en/master/docs/style_guide.cpp.html>`_.
*   To add to this program:

    #.  Add comments that describe what you're doing and why.
    #.  Write a function, then write a failing unit test.
    #.  Add comments on your implementation as you write code. Write unit tests as early as possible and test often.
    #.  Add comments after you're finished coding, reflecting on why you chose this particular approach.

*   If you don't understand a part of the code, write documentation for it as you work through the code.


Coding standards
================

.. _pull requests:

Pull requests
-------------
Before submitting code in a pull request, execute `../pre_commit_check.py`. This program will:

*   Verify that `pytest <https://docs.pytest.org/en/stable/>`_ passes. See `../test/toctree` to run the tests.
*   Format your code with `Black <https://github.com/psf/black>`_. From the root directory of the project, run ``black .``.
*   Check that `Flake8 <https://flake8.pycqa.org/en/latest/index.html>`_ finds no problems. See `../.flake8` for directions.
*   `Build the documentation <../conf.py>`, verifying the build produces no errors.

When this passes:

*   Pull from upstream, then `rebase your pull request <https://www.atlassian.com/git/tutorials/merging-vs-rebasing>`_ if necessary to ensure there will be no merge conflicts.
*   Submit your pull request, then verify that CI tests pass.

Imports
-------
Use the following template at the top of each Python source file. Use absolute imports instead of relative imports.

.. code:: Python

    # Imports
    # =======
    # These are listed in the order prescribed by `PEP 8`_.
    #
    # Standard library
    # ----------------
    # None. (Or the imports.)
    #
    # Third-party imports
    # -------------------
    # Here's an example...
    from fastapi import FastAPI

    # Local application imports
    # -------------------------
    from BookServer.app import foo