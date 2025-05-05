# crud.py
from sqlalchemy import create_engine
from lingua.database.models import Base
from dotenv import load_dotenv
import os

load_dotenv()

_USER = os.getenv("user")
_PWD = os.getenv("password")
_HOST = os.getenv("host")
_PORT = os.getenv("port")
_DBNAME = os.getenv("dbname")

DATABASE_URL = f"postgresql+psycopg2://{_USER}:{_PWD}@{_HOST}:{_PORT}/{_DBNAME}?sslmode=require"

engine = create_engine(DATABASE_URL)


def init_db():
    # Session = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Tables created!")

if __name__ == "__main__":
    init_db()