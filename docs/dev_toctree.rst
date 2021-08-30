***********************
Developer documentation
***********************
Begin by reading the `dev_guide`.

Introduction
============
The bookserver is the student-facing web app for Runestone.

  - History: it was ported from web2py
  - Design goals: modern, fast, well-architected

    - Use a modern, high-performance web framework (FastAPI). Compare to other options and explain why this.
    - async approach
    - Goal of 100% test coverage (do we agree on this?)
    - Well-documented in the code to enable collaboration / improve code quality

  - How it fits with both Runestone Components and with the web2py instructor interface
  - Roadmap

Web application
===============
.. toctree::
    :maxdepth: 1

    ../bookserver/toctree
    ../alembic/toctree
    ../deployment/toctree


Development support
===================
.. toctree::
    :maxdepth: 1

    ../test/toctree
    ../pre_commit_check.py
    ../pyproject.toml
    ../.gitignore
    ../.flake8
    ../mypy.ini
    ../tox.ini
    ../.coveragerc


Documentation generation
========================
.. toctree::
    :maxdepth: 1

    ../conf.py
    ../codechat_config.json
    ../.readthedocs.yml
