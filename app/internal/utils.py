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

# Third-party imports
# -------------------
# None.
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
    x = x.group(1)
    y = x.split()
    if len(y) == 1:
        return tstring
    else:
        zstring = "".join([i[0] for i in y])
        return re.sub(r"(.*)\((.*)\)", r"\1({})".format(zstring), tstring)
