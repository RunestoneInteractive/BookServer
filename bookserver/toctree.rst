**************************
BookServer web application
**************************
TODO: this is how the docs should be organized.

  - (routing/toctree) Endpoints

    - How routing works

      - overview of a request for a page
      - overview of an api call

    - (schema.py) Pydantic to validate/convert from HTTP params to Python vars / database access
    - How Runestone Components interacts with endpoints

      - (routine/books.py) Book routing/interaction with a book built with Runestone Components.
      - (routing/assessment.py) Loading data into Runestone Components
      - (routing/rslogging.py) Storing data from Runestone Components

  - Security

    - (routers/auth.py) Shared authentication -- same password, different cookies. (Does this belong in another section?)

  - (db.py?) Database

    - Why sqlalchemy.

      - Why we use the sqlalchemy core instead of the ORM.
      - Use of _and, _or instead of &&, || operators.

    - Async operations
    - (crud.py) Put queries into crud.py
    - (models.py) web2py instructor interface and this app share the database; each "owns" different tables

      - (alembic/) Migration strategy


.. toctree::
    :maxdepth: 1

    ../docs/design
    ../docs/dev_guide
    main.py
    models.py
    schemas.py
    db.py
    session.py
    applogger.py
    crud.py
    routers/toctree
    internal/toctree
    templates/auth/login.html
    config.py
    __main__.py
