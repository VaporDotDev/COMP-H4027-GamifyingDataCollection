import os

# Load the .env file
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

cwd = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(cwd, "../.env"))
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

db = SQLAlchemy()


def init_app(app):
    app.config[
        "SQLALCHEMY_DATABASE_URI"
    ] = f"mariadb+mariadbconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    db.init_app(app)

    # Create all tables
    with app.app_context():
        db.create_all()
