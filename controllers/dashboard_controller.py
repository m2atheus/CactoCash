from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import render_template, session, redirect, flash, request
from sqlalchemy.exc import IntegrityError

from models.categoria import Categoria
from models.database import db
from models.controle_permissoes import ControlePermissoesUsuarios
from models.receita import Receita
from models.usuario import User

class DashboardController:

    @staticmethod
    def _obter_usuario_logado():
        if 'user_id' not in session:
            return None

        usuario_logado = User.query.get(session['user_id'])
        if usuario_logado is None:
            session.clear()

        return usuario_logado

    @staticmethod
    def _obter_ou_criar_categoria_receita(usuario_alvo):
        categoria = Categoria.query.filter(
            Categoria.tipo == 'receita',
            Categoria.ativo.is_(True),
            (Categoria.user_id == usuario_alvo.id) | (Categoria.user_id.is_(None)),
        ).order_by(Categoria.user_id.desc(), Categoria.id.asc()).first()

        if categoria is not None:
            return categoria

        categoria = Categoria(
            nome='Receitas Gerais',
            tipo='receita',
            user_id=usuario_alvo.id,
            ativo=True,
        )
        db.session.add(categoria)
        db.session.flush()
        return categoria

    @staticmethod
    def listar_usuarios():
        usuario_logado = DashboardController._obter_usuario_logado()
        if usuario_logado is None:
            return redirect('/')

        usuario_no_banco = []
        receitas_do_usuario = Receita.query.filter_by(usuario_id=usuario_logado.id).order_by(
            Receita.data_recebimento.desc(),
            Receita.id.desc(),
        ).all()
        mensagem_bloqueio = None
        pode_gerenciar_permissoes = ControlePermissoesUsuarios.usuario_eh_administrador(usuario_logado)
        mensagem_bloqueio_permissoes = None
        grupos_permissao = []
        usuarios_gerenciaveis = []
        pode_cadastrar_receita = ControlePermissoesUsuarios.usuario_pode_lancar_receita(usuario_logado)
        usuarios_receita = []

        if usuario_logado.group and usuario_logado.group.access_user:
            usuario_no_banco = User.query.all()
        else:
            mensagem_bloqueio = 'Acesso Restrito: Você não tem permissão para visualizar a lista de usuários.'

        if not pode_gerenciar_permissoes:
            mensagem_bloqueio_permissoes = (
                'Apenas o usuário administrador pode controlar as permissões dos outros usuários.'
            )
        else:
            grupos_permissao = ControlePermissoesUsuarios.listar_grupos_permissao()
            usuarios_gerenciaveis = ControlePermissoesUsuarios.listar_usuarios_gerenciaveis(usuario_logado)

        if pode_cadastrar_receita:
            usuarios_receita = User.query.filter_by(is_active=True).order_by(User.username.asc()).all()

        return render_template(
            'dashboard.html',
            usuarios=usuario_no_banco,
            receitas=receitas_do_usuario,
            mensagem_bloqueio=mensagem_bloqueio,
            pode_gerenciar_permissoes=pode_gerenciar_permissoes,
            mensagem_bloqueio_permissoes=mensagem_bloqueio_permissoes,
            grupos_permissao=grupos_permissao,
            usuarios_gerenciaveis=usuarios_gerenciaveis,
            pode_cadastrar_receita=pode_cadastrar_receita,
            usuarios_receita=usuarios_receita,
        )

    @staticmethod
    def alternar_status(id_alvo):
        if 'user_id' not in session:
            return redirect('/')

        usuario_logado = User.query.get(session['user_id'])
        if usuario_logado is None:
            session.clear()
            return redirect('/')

        try:
            ControlePermissoesUsuarios.alternar_status_usuario(usuario_logado, id_alvo)
            flash('Status do usuário atualizado com sucesso.', 'success')
        except PermissionError as erro:
            flash(str(erro), 'erro')
        except LookupError as erro:
            flash(str(erro), 'erro')

        return redirect('/dashboard')

    @staticmethod
    def listar_permissoes():
        return None

    @staticmethod
    def atualizar_permissao_usuario(id_alvo):
        usuario_logado = DashboardController._obter_usuario_logado()
        if usuario_logado is None:
            return redirect('/')

        novo_grupo = request.form.get('role_id', type=int)
        if novo_grupo is None:
            flash('Selecione um grupo de permiss\u00e3o v\u00e1lido.', 'erro')
            return redirect('/dashboard?aba=permissao')

        try:
            ControlePermissoesUsuarios.atualizar_grupo_usuario(usuario_logado, id_alvo, novo_grupo)
            flash('Permiss\u00e3o do usu\u00e1rio atualizada com sucesso.', 'success')
        except PermissionError as erro:
            flash(str(erro), 'erro')
        except LookupError as erro:
            flash(str(erro), 'erro')

        return redirect('/dashboard?aba=permissao')

    @staticmethod
    def cadastrar_receita():
        usuario_logado = DashboardController._obter_usuario_logado()
        if usuario_logado is None:
            return redirect('/')

        if not ControlePermissoesUsuarios.usuario_pode_lancar_receita(usuario_logado):
            flash('Apenas administrador ou gerente podem cadastrar receitas para usuarios.', 'erro')
            return redirect('/dashboard?aba=receita')

        usuario_id = request.form.get('usuario_id', type=int)
        descricao = (request.form.get('descricao') or '').strip()
        valor_bruto = (request.form.get('valor') or '').strip().replace(',', '.')
        data_recebimento_bruta = (request.form.get('data_recebimento') or '').strip()
        forma_recebimento = (request.form.get('forma_recebimento') or '').strip()
        status = (request.form.get('status') or '').strip().lower()
        observacoes = (request.form.get('observacoes') or '').strip()
        recorrente = request.form.get('recorrente') == 'on'
        data_fim_recorrencia_bruta = (request.form.get('data_fim_recorrencia') or '').strip()

        if not all([usuario_id, descricao, valor_bruto, data_recebimento_bruta, forma_recebimento, status]):
            flash('Preencha todos os campos obrigatorios da receita.', 'erro')
            return redirect('/dashboard?aba=receita')

        usuario_alvo = User.query.get(usuario_id)
        if usuario_alvo is None or not usuario_alvo.is_active:
            flash('Usuario selecionado invalido para receber a receita.', 'erro')
            return redirect('/dashboard?aba=receita')

        try:
            valor = Decimal(valor_bruto)
            if valor <= 0:
                raise InvalidOperation
        except InvalidOperation:
            flash('Informe um valor de receita valido.', 'erro')
            return redirect('/dashboard?aba=receita')

        try:
            data_recebimento = datetime.strptime(data_recebimento_bruta, '%Y-%m-%d').date()
        except ValueError:
            flash('Informe uma data de recebimento valida.', 'erro')
            return redirect('/dashboard?aba=receita')

        data_fim_recorrencia = None
        if data_fim_recorrencia_bruta:
            try:
                data_fim_recorrencia = datetime.strptime(data_fim_recorrencia_bruta, '%Y-%m-%d').date()
            except ValueError:
                flash('Informe uma data final de recorrencia valida.', 'erro')
                return redirect('/dashboard?aba=receita')

            if data_fim_recorrencia < data_recebimento:
                flash('A data final da recorrencia nao pode ser anterior ao recebimento.', 'erro')
                return redirect('/dashboard?aba=receita')

        try:
            categoria = DashboardController._obter_ou_criar_categoria_receita(usuario_alvo)

            receita = Receita(
                descricao=descricao,
                valor=valor,
                data_recebimento=data_recebimento,
                categoria_id=categoria.id,
                forma_recebimento=forma_recebimento,
                status=status,
                observacoes=observacoes or None,
                usuario_id=usuario_alvo.id,
                recorrente=recorrente,
                data_fim_recorrencia=data_fim_recorrencia,
            )

            db.session.add(receita)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('Nao foi possivel cadastrar a receita por causa de um dado relacionado invalido.', 'erro')
            return redirect('/dashboard?aba=receita')

        flash(f'Receita cadastrada com sucesso para {usuario_alvo.username}.', 'success')
        return redirect('/dashboard?aba=receita')
