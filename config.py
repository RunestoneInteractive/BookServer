# ************************************
# |docname| - BookServer configuration
# ************************************
# Configure settings here.
# Settings not set explicitly will be inherited from the environment
#
from pydantic import BaseSettings


class Settings(BaseSettings):
    google_ga: str = ""
    config: str = "development"  # production or test
    prod_dburl: str = "sqlite:///./runestone.db"
    dev_dburl: str = "sqlite:///./runestone_dev.db"
    test_dburl: str = "sqlite:///./runestone_test.db"
    adsenseid: str = ""
    num_banners: int = 0
    serve_ad: bool = False
    library_path: str = "/Users/bmiller/Runestone"


settings = Settings()
