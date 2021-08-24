#!/usr/bin/bash
#
# *******************************************************************
# |docname| - Run web2py and BookServer in a deployment configuration
# *******************************************************************
# This assumes the servers below aren't running -- if so, they must be stopped first. It also assumes this is being run by Poetry (in the correct virtual environment).
#
# The user-facing web server.
sudo nginx -c $PWD/nginx.conf

# This runs web2py. See `uWSGI docs <https://uwsgi-docs.readthedocs.io/en/latest/Configuration.html#loading-configuration-files>`_. TODO: this hard-codes the location of web2py relative to the BookServer.
sudo env "PATH=$PATH" uwsgi --ini $PWD/uwsgi.ini --chdir=$PWD/../../web2py &

# This runs the BookServer.
sudo env "PATH=$PATH" gunicorn --config $PWD/gunicorn.conf.py --bind=unix:/run/gunicorn.sock &
