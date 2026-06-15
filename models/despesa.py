from models.database import db


class Despesa(db.Model):
    __tablename__ = 'despesa'

    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(255), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    data_pagamento = db.Column(db.Date)
    categoria_id = db.Column(db.Integer, nullable=False)
    forma_pagamento = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    observacoes = db.Column(db.Text)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recorrente = db.Column(db.Boolean, default=False)
    data_fim_recorrencia = db.Column(db.Date)
    comprovante = db.Column(db.Text)
