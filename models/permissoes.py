from models.database import db

class Permissoes(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    access_user = db.Column(db.Boolean, default=False)
    access_permissions = db.Column(db.Boolean, default=False)
    access_revenue = db.Column(db.Boolean, default=False)
    access_expense = db.Column(db.Boolean, default=False)
    users = db.relationship('User', backref='group', lazy=True)

    __tablename__ = 'permission_groups'