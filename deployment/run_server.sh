#!/usr/bin/bash
#
# *******************************************************************
# |docname| - Run web2py and BookServer in a deployment configuration
# *******************************************************************
# Prereqs:
#
# - This is being run by Poetry (in the correct virtual environment).
# - This venv also contains all the web2py pip dependencies.
# - The web2py referred to below has ``wsgihandler.py`` in its root directory (you can copy this from ``web2py/handlers``).
#
# This file must be manually edited to provide various settings.
#
# Start servers
# =============
# Echo all commands for debug. Comment out to reduce noise.
set -x

# Edit me: Specify the absolute path to web2py.
WEB2PY_PATH=$PWD/../../web2py
# Edit me: Specify the Postgresql URL.
POSTGRESQL_URL=runestone:bully@localhost/runestone

# The nginx config doesn't allow env vars. Do some specific substitution (don't substitute everything, since this would replace nginx vars like $host). From `SO <https://serverfault.com/a/919212>`_.
SITE_NAME=127.0.0.1 WEB2PY_PATH=$WEB2PY_PATH envsubst '${SITE_NAME} ${WEB2PY_PATH}' < $PWD/nginx.conf > /tmp/nginx.conf

# The user-facing web server. Try stopping it first (which produces an error if it's not started.)
sudo nginx -s stop
sudo nginx -c /tmp/nginx.conf

sudo pkill gunicorn
# This runs web2py. See `uWSGI docs <https://uwsgi-docs.readthedocs.io/en/latest/Configuration.html#loading-configuration-files>`_. TODO: this hard-codes the location of web2py relative to the BookServer.
sudo env \
    "PATH=$PATH" \
    WEB2PY_CONFIG=production \
    WEB2PY_MIGRATE=Yes \
    DBURL=postgresql://$POSTGRESQL_URL \
    gunicorn --config $PWD/gunicorn.conf.py --bind=unix:/run/web2py.sock --chdir=${WEB2PY_PATH} gluon.main:wsgibase &

# This runs the BookServer.
#
# Notes on the command:
#
# - `worker-class <https://docs.gunicorn.org/en/stable/settings.html#worker-class>`_: The type of workers to use. Use `uvicorn's worker class for gunicorn <https://www.uvicorn.org/deployment/#gunicorn>`_.
sudo env \
    "PATH=$PATH" \
    PROD_DBURL=postgresql+asyncpg://$POSTGRESQL_URL \
    BOOK_SERVER_CONFIG=production \
    ROOT_PATH=/ns \
    gunicorn --config $PWD/gunicorn.conf.py --bind=unix:/run/fastapi.sock --worker-class=uvicorn.workers.UvicornWorker bookserver.main:app &
