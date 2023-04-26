import sqlalchemy

from classes.Level import level_structure
from functions.database import db


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
    level = db.Column(db.Integer, nullable=False, default=1)
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
        user = User.query.filter_by(google_id=google_id).first()
        if user is None:
            print("User not found.")
            return
        if not hasattr(user, 'points'):
            print("Points attribute not defined for user.")
            return
        user.points += points
        db.session.commit()
        User.update_level(user)

    @staticmethod
    def update_level(self):
        for level, level_data in level_structure.items():
            if self.points >= level_data["points"]:
                self.level = level
                if level == max(level_structure.keys()):
                    # If we reach the end of the structure, every 5,000 points is a new level
                    self.level += (self.points - level_data["points"]) // 5000
                db.session.commit()
            else:
                break
