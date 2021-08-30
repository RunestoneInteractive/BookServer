**********
Deployment
**********
The files below allow deployment of both the old web2py server and this new BookServer side-by-side. This is necessary, since much of the web2py code hasn't been ported. They are designed to run in this configuration to facilitate the long-term porting process.

.. toctree::
    :maxdepth: 1

    run_server.sh
    nginx.conf
    uwsgi.ini
    gunicorn.conf.py
