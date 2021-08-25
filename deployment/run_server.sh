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
# Start servers
# =============
# Echo all commands for debug. Comment out to reduce noise.
set -x

# The user-facing web server. Try stopping it first (which produces an error if it's not started.)
sudo nginx -s stop
sudo nginx -c $PWD/nginx.conf

# See `stopping the server <https://uwsgi-docs.readthedocs.io/en/latest/Management.html#stopping-the-server>`_.
sudo env "PATH=$PATH" uwsgi --stop /tmp/uwsgi.pid
# This runs web2py. See `uWSGI docs <https://uwsgi-docs.readthedocs.io/en/latest/Configuration.html#loading-configuration-files>`_. TODO: this hard-codes the location of web2py relative to the BookServer.
sudo env \
    "PATH=$PATH" \
    WEB2PY_CONFIG=production \
    WEB2PY_MIGRATE=Yes \
    DBURL=postgresql://runestone:bully@localhost/runestone \
    uwsgi --ini $PWD/uwsgi.ini --chdir=$PWD/../../web2py &

sudo pkill gunicorn
# This runs the BookServer.
sudo env \
    "PATH=$PATH" \
    DBURL=postgresql+asyncpg://runestone:bully@localhost/runestone \
    BOOK_SERVER_CONFIG=production \
    gunicorn --config $PWD/gunicorn.conf.py --bind=unix:/run/gunicorn.sock &
