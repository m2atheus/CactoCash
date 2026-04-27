from models.database import db


class Receita(db.Model):
    __tablename__ = 'receita'

    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(255), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    data_recebimento = db.Column(db.Date, nullable=False)
    categoria_id = db.Column(db.Integer, nullable=False)
    forma_recebimento = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    observacoes = db.Column(db.Text)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recorrente = db.Column(db.Boolean, default=False)
    data_fim_recorrencia = db.Column(db.Date)
    comprovante = db.Column(db.Text)
