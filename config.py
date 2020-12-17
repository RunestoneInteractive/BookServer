#
# Configure settings here.
# Settings not set explicitly will be inherited from the environment
#
from pydantic import BaseSettings


class Settings(BaseSettings):
    google_ga: str = ""
    config: str = "development"  # production or test
    prod_dburl: str = "sqlite:///./prod_database.db"
    dev_dburl: str = "sqlite:///./dev_database.db"
    test_dburl: str = "sqlite:///./test_database.db"
    adsenseid: str = ""
    num_banners: int = 0
    serve_ad: bool = False
    library_path: str = "/Users/bmiller/Runestone"


settings = Settings()
