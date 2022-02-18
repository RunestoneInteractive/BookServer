# *****************************
# |docname| - Utility functions
# *****************************
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8`_.
#
# Standard library
# ----------------
import re
from typing import Any, List

# Third-party imports
# -------------------
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

#
# Local application imports
# -------------------------
# None.


# Functions
# =========
def canonicalize_tz(tstring: str) -> str:
    """
    Browsers are not consistent with how they format times with timezones for example
    Safari:  Tue Sep 08 2020 21:13:00 GMT-0500 (CDT)
    Chrome: Tue Sep 08 2020 21:13:00 GMT-0500 (Central Daylight Time)
    This function tries to coerce the time string into the Safari format as it
    is more compatible with other time/date functions
    """
    x = re.search(r"\((.*)\)", tstring)
    if x:
        z = x.group(1)
        y = z.split()
        if len(y) == 1:
            return tstring
        else:
            zstring = "".join([i[0] for i in y])
            return re.sub(r"(.*)\((.*)\)", r"\1({})".format(zstring), tstring)
    return tstring


def make_json_response(
    status: int = status.HTTP_200_OK, detail: Any = None
) -> JSONResponse:
    # Omit the detail if it's none.
    return JSONResponse(
        status_code=status, content=jsonable_encoder({"detail": detail})
    )


def http_422error_detail(
    # Should be a list, the first element indicates where the error occurred for example in the path or in the body of the request. it could also be function I suppose. The second element in the list gives the name of the data element that is not valid.
    loc: List[str],
    # a descriptive message about the error.
    msg: str,
    # this is the specific error that was raised. e.g. value_error, type_error, integrity_error.
    err_type: str,
) -> List[dict]:
    return [{"loc": loc, "msg": msg, "type": err_type}]


# Starlette provides `url_for <https://www.starlette.io/routing/#reverse-url-lookups>`_, but this doesn't work without some `configuration fixes <https://github.com/encode/starlette/issues/538#issuecomment-518748568>`_ I can't seem to accomplish. Instead, the returned URL is **always** http, even when nginx serves https. Here's a kludgy workaround: strip off the scheme, so that ``http://path/to/stuff.html`` becomes ``/path/to/stuff.html``.
def url_for(
    # The request, which is required to perform URL lookups.
    request: Request,
    # The same parameters that `url_for`_ requires.
    name: str,
    **path_params: Any
) -> str:

    return request.url_for(name, **path_params)[6:]
