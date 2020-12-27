import logging
import sys

rslogger = logging.getLogger("runestone")
rslogger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(levelname)s - %(asctime)s - %(funcName)s - %(message)s"
)
handler.setFormatter(formatter)
rslogger.addHandler(handler)

# To turn on debugging for FastAPI and the database package
# from fastapi.logger import logger
# import logging
# logger.setLevel(logging.DEBUG)
# otherwise FastAPI logs at the default level
# There is good info here: https://medium.com/@PhilippeGirard5/fastapi-logging-f6237b84ea64 on setting up logging.  There is also good info on hooking into the gunicorn logging system when you deploy here:  https://pawamoy.github.io/posts/unify-logging-for-a-gunicorn-uvicorn-app/
