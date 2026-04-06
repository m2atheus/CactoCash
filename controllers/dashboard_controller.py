from flask import Flask, render_template, session, redirect
from models.usuario import User
from models.database import db

class DashboardController:

    @staticmethod
    def listar_usuarios():
        if 'user_id' not in session:
            return redirect('/')
        usuario_no_banco = User.query.all()
        usuario_logado = User.query.get(session['user_id'])

        usuario_no_banco = []
        mensagem_bloqueio = None

        if usuario_logado.group.access_user:
            usuario_no_banco = User.query.all()
        else:
            mensagem_bloqueio = "Acesso Restrito: Você não tem permissão para visualizar a lista de usuários."

        return render_template('dashboard.html', usuarios=usuario_no_banco,mensagem_bloqueio=mensagem_bloqueio)
    @staticmethod
    def alternar_status(id_alvo):
        if 'user_id' not in session:
            return redirect('/')
        user_para_mudar=User.query.get(id_alvo)
        if user_para_mudar:
            user_para_mudar.is_active=not user_para_mudar.is_active
            db.session.commit()
        return redirect('/dashboard')
    @staticmethod
    def listar_permissoes():
        return None