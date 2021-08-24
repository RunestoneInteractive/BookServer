#!/usr/bin/bash
#
# *******************************************************************
# |docname| - Run web2py and BookServer in a deployment configuration
# *******************************************************************
#
# The user-facing web server.
sudo nginx -c $PWD/nginx.conf

# This runs web2py. See `uWSGI docs <https://uwsgi-docs.readthedocs.io/en/latest/Configuration.html#loading-configuration-files>`_. TODO: this hard-codes the location of web2py relative to the BookServer.
sudo uwsgi --ini $PWD/uwsgi.ini --chdir=$PWD/../../web2py &

# This runs the BookServer. TODO: update socket address.
sudo env "PATH=$PATH" python -m gunicorn --config $PWD/gunicorn.conf.py --bind=unix:/run/uwsgi/web2py.sock &
