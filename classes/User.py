import sqlalchemy
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    picture = db.Column(db.String(255), nullable=False)
    interest = db.Column(db.String(255), nullable=False)
    trusted = db.Column(db.Boolean, nullable=False)
    points = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=sqlalchemy.func.now())
    updated_at = db.Column(db.DateTime, default=sqlalchemy.func.now(), onupdate=sqlalchemy.func.now())

    @staticmethod
    def create_user(google_id="", email="", password="", name="", picture="", interest="Un-Set", trusted=False):
        user = User(google_id=google_id, email=email, password=password, name=name, picture=picture, interest=interest,
                    trusted=trusted, points=0)
        db.session.add(user)
        db.session.commit()

    @staticmethod
    def add_points(google_id, points):
        print("Adding points to user: " + str(google_id) + " with " + str(points) + " points")
        user = User.query.filter_by(google_id=google_id).first()
        if user is None:
            print("User not found.")
            return
        if not hasattr(user, 'points'):
            print("Points attribute not defined for user.")
            return
        user.points += points
        db.session.commit()
