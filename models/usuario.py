from models.database import db
from models.permissoes import Permissoes
from werkzeug.security import generate_password_hash,check_password_hash


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    role_id = db.Column(db.Integer, db.ForeignKey('permission_groups.id'))
    def set_password(self,raw_password):
        self.password = generate_password_hash(raw_password)
    def check_password(self,raw_password):
        return check_password_hash(self.password,raw_password)

    __tablename__ = 'users'