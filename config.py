#
# Configure settings here.
# Settings not set explicitly will be inherited from the environment
#
from pydantic import BaseSettings


class Settings(BaseSettings):
    google_ga: str = ""
    config: str = "production"
    dburl: str = "./test_database.db"
    dev_dburl: str = "./dev_database.db"
    adsenseid: str = ""
    num_banners: int = 0
    serve_ad: bool = False


settings = Settings()
