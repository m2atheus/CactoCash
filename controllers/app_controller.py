from flask import render_template, request, redirect, session, flash
from models.usuario import User
from models.database import db
from models.permissoes import Permissoes


class AppController:
    @staticmethod
    def index():
        if 'usuario_logado' in session:
            return redirect('/dashboard')
        return render_template('index.html', titulo_index='CactoCash')

    @staticmethod
    def autenticar():
        if request.method == 'POST':
            username = request.form.get('user')
            password = request.form.get('pass')

            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password) and user.is_active:
                session['usuario_logado'] = username
                session['user_id'] = user.id
                return redirect('/dashboard')
            elif not user.is_active:
                flash('Usuário inativo','erro')
            else:
                flash('Usuário ou senha incorretos.','erro')
                return redirect('/')

        return redirect('/')
    @staticmethod
    def cadastrar():
        if 'usuario_logado' in session:
            return redirect('/dashboard')
        if request.method == 'POST':
            usuario = request.form.get('username')
            senha = request.form.get('password')
            senha_confirme = request.form.get('password_confirm')
            if senha != senha_confirme:
                flash('As senhas não conferem','erro')
                return redirect('/cadastrar')
            usuario_existe = User.query.filter_by(username=usuario).first()
            if usuario_existe:
                flash('Usuário já cadastrado','erro')
                return redirect('/cadastrar')
            else:
                novo_usuario=User(username=usuario,role_id=3)
                novo_usuario.set_password(senha)
                db.session.add(novo_usuario)
                db.session.commit()
                flash('Cadastro feito com sucesso','success')
                return redirect('/')
        return render_template('cadastrar.html')
    @staticmethod
    def logout():
        session.clear()
        flash('Logout com sucesso','success')
        return redirect('/')
    @staticmethod
    def dashboard():
        return render_template('dashboard.html')