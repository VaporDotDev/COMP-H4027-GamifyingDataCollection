import sqlalchemy

from functions.database import db


class Image(db.Model):
    __tablename__ = "images"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), unique=True, nullable=False)
    hash_string = db.Column(db.String(255), unique=True, nullable=False)
    captured_by = db.Column(db.String(255), db.ForeignKey('users.google_id', name='fk_captured_by'), nullable=False)
    created_at = db.Column(db.DateTime, default=sqlalchemy.func.now())
    updated_at = db.Column(db.DateTime, default=sqlalchemy.func.now(), onupdate=sqlalchemy.func.now())

    @staticmethod
    def create_image(filename="", hash_string="", captured_by=""):
        image = Image(filename=filename, hash_string=hash_string, captured_by=captured_by)
        db.session.add(image)
        db.session.commit()

    @staticmethod
    def find_by_hash(hash_string):
        return Image.query.filter_by(hash_string=hash_string).first()

    @staticmethod
    def get_all_by_user(google_id):
        return Image.query.filter_by(captured_by=google_id).all()
