from datetime import datetime
from decimal import Decimal, InvalidOperation

from flask import render_template, session, redirect, flash, request
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from models.categoria import Categoria
from models.database import db
from models.controle_permissoes import ControlePermissoesUsuarios
from models.despesa import Despesa
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
    def _obter_ou_criar_categoria_despesa(usuario_alvo):
        categoria = Categoria.query.filter(
            Categoria.tipo == 'despesa',
            Categoria.ativo.is_(True),
            (Categoria.user_id == usuario_alvo.id) | (Categoria.user_id.is_(None)),
        ).order_by(Categoria.user_id.desc(), Categoria.id.asc()).first()

        if categoria is not None:
            return categoria

        categoria = Categoria(
            nome='Despesas Gerais',
            tipo='despesa',
            user_id=usuario_alvo.id,
            ativo=True,
        )
        db.session.add(categoria)
        db.session.flush()
        return categoria

    @staticmethod
    def _obter_valor_decimal(valor_bruto, mensagem_erro, aba_destino):
        try:
            valor = Decimal(valor_bruto)
            if valor <= 0:
                raise InvalidOperation
            return valor, None
        except InvalidOperation:
            flash(mensagem_erro, 'erro')
            return None, redirect(f'/dashboard?aba={aba_destino}')

    @staticmethod
    def _obter_data(data_bruta, mensagem_erro, aba_destino, obrigatoria=True):
        if not data_bruta and not obrigatoria:
            return None, None

        try:
            return datetime.strptime(data_bruta, '%Y-%m-%d').date(), None
        except ValueError:
            flash(mensagem_erro, 'erro')
            return None, redirect(f'/dashboard?aba={aba_destino}')

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
        despesas_do_usuario = Despesa.query.filter_by(usuario_id=usuario_logado.id).order_by(
            Despesa.data_vencimento.desc(),
            Despesa.id.desc(),
        ).all()
        movimentacoes = []
        for receita in receitas_do_usuario:
            movimentacoes.append({
                'data': receita.data_recebimento,
                'descricao': receita.descricao,
                'valor': receita.valor,
                'tipo': 'receita',
            })

        for despesa in despesas_do_usuario:
            movimentacoes.append({
                'data': despesa.data_vencimento,
                'descricao': despesa.descricao,
                'valor': despesa.valor,
                'tipo': 'despesa',
            })

        ultimas_movimentacoes = sorted(
            movimentacoes,
            key=lambda movimentacao: movimentacao['data'],
            reverse=True,
        )[:5]
        total_receitas = db.session.query(func.coalesce(func.sum(Receita.valor), 0)).filter(
            Receita.usuario_id == usuario_logado.id,
        ).scalar()
        total_despesas = db.session.query(func.coalesce(func.sum(Despesa.valor), 0)).filter(
            Despesa.usuario_id == usuario_logado.id,
        ).scalar()
        saldo_atual = total_receitas - total_despesas
        mensagem_bloqueio = None
        pode_gerenciar_permissoes = ControlePermissoesUsuarios.usuario_eh_administrador(usuario_logado)
        mensagem_bloqueio_permissoes = None
        grupos_permissao = []
        usuarios_gerenciaveis = []
        pode_cadastrar_receita = ControlePermissoesUsuarios.usuario_pode_lancar_receita(usuario_logado)
        usuarios_receita = []
        pode_cadastrar_despesa = ControlePermissoesUsuarios.usuario_pode_lancar_despesa(usuario_logado)
        usuarios_despesa = []
        pode_lancar_para_terceiros = ControlePermissoesUsuarios.usuario_pode_lancar_para_terceiros(usuario_logado)

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

        if pode_lancar_para_terceiros:
            usuarios_receita = User.query.filter_by(is_active=True).order_by(User.username.asc()).all()

        if pode_lancar_para_terceiros:
            usuarios_despesa = User.query.filter_by(is_active=True).order_by(User.username.asc()).all()

        return render_template(
            'dashboard.html',
            usuario_logado=usuario_logado,
            role_usuario=usuario_logado.group.name.upper() if usuario_logado.group and usuario_logado.group.name else None,
            usuarios=usuario_no_banco,
            receitas=receitas_do_usuario,
            despesas=despesas_do_usuario,
            ultimas_movimentacoes=ultimas_movimentacoes,
            total_receitas=total_receitas,
            total_despesas=total_despesas,
            saldo_atual=saldo_atual,
            mensagem_bloqueio=mensagem_bloqueio,
            pode_gerenciar_permissoes=pode_gerenciar_permissoes,
            mensagem_bloqueio_permissoes=mensagem_bloqueio_permissoes,
            grupos_permissao=grupos_permissao,
            usuarios_gerenciaveis=usuarios_gerenciaveis,
            pode_cadastrar_receita=pode_cadastrar_receita,
            usuarios_receita=usuarios_receita,
            pode_cadastrar_despesa=pode_cadastrar_despesa,
            usuarios_despesa=usuarios_despesa,
            pode_lancar_para_terceiros=pode_lancar_para_terceiros,
        )

    @staticmethod
    def listar_despesas():
        usuario_logado = DashboardController._obter_usuario_logado()
        if usuario_logado is None:
            return redirect('/')

        return redirect('/dashboard?aba=despesas')

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
            flash('Voce nao tem permissao para cadastrar receitas.', 'erro')
            return redirect('/dashboard?aba=receita')

        if ControlePermissoesUsuarios.usuario_pode_lancar_para_terceiros(usuario_logado):
            usuario_id = request.form.get('usuario_id', type=int)
        else:
            usuario_id = usuario_logado.id

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

    @staticmethod
    def cadastrar_despesa():
        usuario_logado = DashboardController._obter_usuario_logado()
        if usuario_logado is None:
            return redirect('/')

        if not ControlePermissoesUsuarios.usuario_pode_lancar_despesa(usuario_logado):
            flash('Voce nao tem permissao para cadastrar despesas.', 'erro')
            return redirect('/dashboard?aba=despesas')

        if ControlePermissoesUsuarios.usuario_pode_lancar_para_terceiros(usuario_logado):
            usuario_id = request.form.get('usuario_id', type=int)
        else:
            usuario_id = usuario_logado.id

        descricao = (request.form.get('descricao') or '').strip()
        valor_bruto = (request.form.get('valor') or '').strip().replace(',', '.')
        data_vencimento_bruta = (request.form.get('data_vencimento') or '').strip()
        data_pagamento_bruta = (request.form.get('data_pagamento') or '').strip()
        forma_pagamento = (request.form.get('forma_pagamento') or '').strip()
        status = (request.form.get('status') or '').strip().lower()
        observacoes = (request.form.get('observacoes') or '').strip()
        recorrente = request.form.get('recorrente') == 'on'
        data_fim_recorrencia_bruta = (request.form.get('data_fim_recorrencia') or '').strip()

        if not all([usuario_id, descricao, valor_bruto, data_vencimento_bruta, forma_pagamento, status]):
            flash('Preencha todos os campos obrigatorios da despesa.', 'erro')
            return redirect('/dashboard?aba=despesas')

        usuario_alvo = User.query.get(usuario_id)
        if usuario_alvo is None or not usuario_alvo.is_active:
            flash('Usuario selecionado invalido para receber a despesa.', 'erro')
            return redirect('/dashboard?aba=despesas')

        valor, erro = DashboardController._obter_valor_decimal(
            valor_bruto,
            'Informe um valor de despesa valido.',
            'despesas',
        )
        if erro:
            return erro

        data_vencimento, erro = DashboardController._obter_data(
            data_vencimento_bruta,
            'Informe uma data de vencimento valida.',
            'despesas',
        )
        if erro:
            return erro

        data_pagamento, erro = DashboardController._obter_data(
            data_pagamento_bruta,
            'Informe uma data de pagamento valida.',
            'despesas',
            obrigatoria=False,
        )
        if erro:
            return erro

        data_fim_recorrencia, erro = DashboardController._obter_data(
            data_fim_recorrencia_bruta,
            'Informe uma data final de recorrencia valida.',
            'despesas',
            obrigatoria=False,
        )
        if erro:
            return erro

        if data_fim_recorrencia and data_fim_recorrencia < data_vencimento:
            flash('A data final da recorrencia nao pode ser anterior ao vencimento.', 'erro')
            return redirect('/dashboard?aba=despesas')

        try:
            categoria = DashboardController._obter_ou_criar_categoria_despesa(usuario_alvo)

            despesa = Despesa(
                descricao=descricao,
                valor=valor,
                data_vencimento=data_vencimento,
                data_pagamento=data_pagamento,
                categoria_id=categoria.id,
                forma_pagamento=forma_pagamento,
                status=status,
                observacoes=observacoes or None,
                usuario_id=usuario_alvo.id,
                recorrente=recorrente,
                data_fim_recorrencia=data_fim_recorrencia,
            )

            db.session.add(despesa)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('Nao foi possivel cadastrar a despesa por causa de um dado relacionado invalido.', 'erro')
            return redirect('/dashboard?aba=despesas')

        flash(f'Despesa cadastrada com sucesso para {usuario_alvo.username}.', 'success')
        return redirect('/dashboard?aba=despesas')

    @staticmethod
    def atualizar_despesa(id_despesa):
        usuario_logado = DashboardController._obter_usuario_logado()
        if usuario_logado is None:
            return redirect('/')

        if not ControlePermissoesUsuarios.usuario_pode_lancar_despesa(usuario_logado):
            flash('Voce nao tem permissao para atualizar despesas.', 'erro')
            return redirect('/dashboard?aba=despesas')

        despesa = Despesa.query.get(id_despesa)
        if despesa is None:
            flash('Despesa nao encontrada.', 'erro')
            return redirect('/dashboard?aba=despesas')

        if (
            not ControlePermissoesUsuarios.usuario_pode_lancar_para_terceiros(usuario_logado)
            and despesa.usuario_id != usuario_logado.id
        ):
            flash('Voce nao tem permissao para atualizar esta despesa.', 'erro')
            return redirect('/dashboard?aba=despesas')

        descricao = (request.form.get('descricao') or '').strip()
        valor_bruto = (request.form.get('valor') or '').strip().replace(',', '.')
        data_vencimento_bruta = (request.form.get('data_vencimento') or '').strip()
        data_pagamento_bruta = (request.form.get('data_pagamento') or '').strip()
        forma_pagamento = (request.form.get('forma_pagamento') or '').strip()
        status = (request.form.get('status') or '').strip().lower()
        observacoes = (request.form.get('observacoes') or '').strip()
        recorrente = request.form.get('recorrente') == 'on'
        data_fim_recorrencia_bruta = (request.form.get('data_fim_recorrencia') or '').strip()

        if not all([descricao, valor_bruto, data_vencimento_bruta, forma_pagamento, status]):
            flash('Preencha todos os campos obrigatorios da despesa.', 'erro')
            return redirect('/dashboard?aba=despesas')

        valor, erro = DashboardController._obter_valor_decimal(
            valor_bruto,
            'Informe um valor de despesa valido.',
            'despesas',
        )
        if erro:
            return erro

        data_vencimento, erro = DashboardController._obter_data(
            data_vencimento_bruta,
            'Informe uma data de vencimento valida.',
            'despesas',
        )
        if erro:
            return erro

        data_pagamento, erro = DashboardController._obter_data(
            data_pagamento_bruta,
            'Informe uma data de pagamento valida.',
            'despesas',
            obrigatoria=False,
        )
        if erro:
            return erro

        data_fim_recorrencia, erro = DashboardController._obter_data(
            data_fim_recorrencia_bruta,
            'Informe uma data final de recorrencia valida.',
            'despesas',
            obrigatoria=False,
        )
        if erro:
            return erro

        if data_fim_recorrencia and data_fim_recorrencia < data_vencimento:
            flash('A data final da recorrencia nao pode ser anterior ao vencimento.', 'erro')
            return redirect('/dashboard?aba=despesas')

        despesa.descricao = descricao
        despesa.valor = valor
        despesa.data_vencimento = data_vencimento
        despesa.data_pagamento = data_pagamento
        despesa.forma_pagamento = forma_pagamento
        despesa.status = status
        despesa.observacoes = observacoes or None
        despesa.recorrente = recorrente
        despesa.data_fim_recorrencia = data_fim_recorrencia

        db.session.commit()
        flash('Despesa atualizada com sucesso.', 'success')
        return redirect('/dashboard?aba=despesas')

    @staticmethod
    def deletar_despesa(id_despesa):
        usuario_logado = DashboardController._obter_usuario_logado()
        if usuario_logado is None:
            return redirect('/')

        if not ControlePermissoesUsuarios.usuario_pode_lancar_despesa(usuario_logado):
            flash('Voce nao tem permissao para deletar despesas.', 'erro')
            return redirect('/dashboard?aba=despesas')

        despesa = Despesa.query.get(id_despesa)
        if despesa is None:
            flash('Despesa nao encontrada.', 'erro')
            return redirect('/dashboard?aba=despesas')

        if (
            not ControlePermissoesUsuarios.usuario_pode_lancar_para_terceiros(usuario_logado)
            and despesa.usuario_id != usuario_logado.id
        ):
            flash('Voce nao tem permissao para deletar esta despesa.', 'erro')
            return redirect('/dashboard?aba=despesas')

        db.session.delete(despesa)
        db.session.commit()
        flash('Despesa deletada com sucesso.', 'success')
        return redirect('/dashboard?aba=despesas')
