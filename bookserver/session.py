# ******************************
# |docname| - Session Management
# ******************************

from bookserver.config import settings
from fastapi_login import LoginManager
from . import schemas
from .crud import fetch_user
from .applogger import rslogger


def get_session():
    pass


auth_manager = LoginManager(settings.secret, "/auth/validate", use_cookie=True)
auth_manager.cookie_name = "access_token"


@auth_manager.user_loader
async def load_user(user_id: str) -> schemas.User:
    """
    fetch a user object from the database. This is designed to work with the
    original web2py auth_user schema but make it easier to migrate to a new
    database by simply returning a user object.
    """
    rslogger.debug(f"Going to fetch {user_id}")
    user = await fetch_user(user_id)
    if user:
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
