# ******************************
# |docname| - Session Management
# ******************************
# The main thing in this file is to create the auth manager and to provide a ``user_loader``
# The auth manager uses the ``user_loader`` on every route that requires authentication
# The way we do protected routes in FastAPI is to include a parameter on the endpoint
# ``user=Depends(auth_manager)`` This will cause the JWT token (provided in a cookie)
# OR in a header to be validated.  If the token is valid then the user will be looked
# up in the database using the ``load_user`` function in this file.
# see `./routers/auth.py` for more detail.

# Imports
# =======
# These are listed in the order prescribed by `PEP 8`_.
#
# Standard library
# ----------------
from typing import Optional

# Third-party imports
# -------------------
from fastapi_login import LoginManager

# Local application imports
# -------------------------
from .config import settings
from . import schemas
from .crud import fetch_user
from .applogger import rslogger


auth_manager = LoginManager(settings.secret, "/auth/validate", use_cookie=True)
auth_manager.cookie_name = "access_token"


@auth_manager.user_loader
async def load_user(user_id: str) -> Optional[schemas.User]:
    """
    fetch a user object from the database. This is designed to work with the
    original web2py auth_user schema but make it easier to migrate to a new
    database by simply returning a user object.
    """
    rslogger.debug(f"Going to fetch {user_id}")
    user = await fetch_user(user_id)
    rslogger.debug(f"user = {str(user)}")
    if user:
        # TODO: I don't understand -- why do this here? Are we validating an existing user object?
        return schemas.User(
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            password_hash=user.password,
            course_name=user.course_name,
            course_id=user.course_id,
        )
    else:
        return None
