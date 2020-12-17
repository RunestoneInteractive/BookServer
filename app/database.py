#
# Set up database configuration in this file
#
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# SQLALCHEMY_DATABASE_URL = "sqlite:///./bookserver.db"
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"

if settings.config == "development":
    DATABASE_URL = settings.dev_dburl
elif settings.config == "production":
    DATABASE_URL = settings.prod_dburl
else:
    DATABASE_URL = settings.test_dburl
    
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
# This creates the SessionLocal class.  An actual session is an instance of this class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# This creates the base class we will use to create models
Base = declarative_base()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
