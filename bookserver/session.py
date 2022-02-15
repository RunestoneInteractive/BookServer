# ******************************
# |docname| - Session Management
# ******************************
# The main thing in this file is to create the auth manager and to provide a ``user_loader``
# The auth manager uses the ``user_loader`` on every route that requires authentication.
# The way we do protected routes in FastAPI is to include a parameter on the endpoint
# ``user=Depends(auth_manager)``. This will cause the JWT token (provided in a cookie
# OR in a header) to be validated.  If the token is valid then the user will be looked
# up in the database using the ``load_user`` function in this file.
# see `./routers/auth.py` for more detail.
#
# Imports
# =======
# These are listed in the order prescribed by `PEP 8`_.
#
# Standard library
# ----------------
import inspect
from typing import Any, Awaitable, Callable, cast, Dict

# Third-party imports
# -------------------
from fastapi import Request
from fastapi.exceptions import HTTPException
from fastapi_login import LoginManager

# Local application imports
# -------------------------
from .config import settings
from .crud import fetch_instructor_courses, fetch_user
from .applogger import rslogger
from .models import AuthUserValidator


# TokenLoginManager
# =================
# This auth manager class passes the decoded JWT to ``_load_user``.
class TokenLoginManager(LoginManager):
    # This is copied from ``fastapi_login.py`` v. 1.7.3 and slightly modified to pass the decoded JWT to ``self._load_user``.
    async def get_current_user(self, token: str):
        """
        This decodes the jwt based on the secret and the algorithm set on the instance.
        If the token is correctly formatted and the user is found the user object
        is returned else this raises `LoginManager.not_authenticated_exception`

        Args:
            token (str): The encoded jwt token

        Returns:
            The user object returned by the instances `_user_callback`

        Raises:
            LoginManager.not_authenticated_exception: The token is invalid or None was returned by `_load_user`
        """
        payload = self._get_payload(token)
        # the identifier should be stored under the sub (subject) key
        user_identifier = payload.get("sub")
        if user_identifier is None:
            raise self.not_authenticated_exception

        user = await self._load_user_payload(user_identifier, payload)

        if user is None:
            raise self.not_authenticated_exception

        return user

    # This is copied from ``fastapi_login.py`` v. 1.7.3 and slightly modified to pass the decoded JWT to ``self._user_callback``, which is the ``_load_user`` defined below (outside this class).
    async def _load_user_payload(self, identifier: Any, payload: Dict[str, str]):
        """
        This loads the user using the user_callback

        Args:
            identifier (Any): The user identifier expected by `_user_callback`

        Returns:
            The user object returned by `_user_callback` or None

        Raises:
            Exception: When no ``user_loader`` has been set
        """
        if self._user_callback is None:
            raise Exception("Missing user_loader callback")

        if inspect.iscoroutinefunction(self._user_callback):
            user = await self._user_callback(identifier, payload)
        else:
            user = self._user_callback(identifier, payload)

        return user


# Core code
# =========
auth_manager = TokenLoginManager(settings.jwt_secret, "/auth/validate", use_cookie=True)
auth_manager.cookie_name = "access_token"


@auth_manager.user_loader()  # type: ignore
async def _load_user(user_id: str, payload: Dict[str, str]) -> AuthUserValidator:
    """
    fetch a user object from the database. This is designed to work with the
    original web2py auth_user schema but make it easier to migrate to a new
    database by simply returning a user object.
    """
    rslogger.debug(f"Going to fetch {user_id}")
    res = await fetch_user(user_id)
    res.jwt_payload = payload
    return res


# The ``user_loader`` decorator doesn't propagate type hints. Fix this manually.
load_user = cast(
    Callable[[str, Dict[str, str]], Awaitable[AuthUserValidator]], _load_user
)


async def is_instructor(request: Request) -> bool:
    user = request.state.user
    if user is None:
        raise HTTPException(401)
    elif len(await fetch_instructor_courses(user.id, user.course_id)) > 0:
        return True
    else:
        return False
