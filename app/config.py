import os

class Config:
    MYSQL_ROOT_PASSWORD = os.getenv("MYSQL_ROOT_PASSWORD")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
    SECRET_KEY = os.getenv("SECRET_KEY")
    ERROR_404_HELP = False

    if not MYSQL_ROOT_PASSWORD:
        raise ValueError("MYSQL_ROOT_PASSWORD not in env")
    if not MYSQL_DATABASE:
        raise ValueError("MYSQL_DATABASE not in env")

    SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://root:{MYSQL_ROOT_PASSWORD}@mysql-db/{MYSQL_DATABASE}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False