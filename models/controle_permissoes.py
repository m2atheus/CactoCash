from models.database import db
from models.permissoes import Permissoes
from models.usuario import User


class ControlePermissoesUsuarios:
    @staticmethod
    def usuario_eh_administrador(usuario):
        return bool(usuario and usuario.group and usuario.group.access_permissions)

    @staticmethod
    def usuario_pode_lancar_receita(usuario):
        return bool(
            usuario
            and usuario.group
            and usuario.group.name in {'ADMIN', 'GERENTE'}
        )

    @classmethod
    def pode_controlar_permissoes(cls, usuario_executor, usuario_alvo=None):
        if not cls.usuario_eh_administrador(usuario_executor):
            return False

        if usuario_alvo is None:
            return True

        return usuario_executor.id != usuario_alvo.id

    @classmethod
    def alternar_status_usuario(cls, usuario_executor, id_usuario_alvo):
        usuario_alvo = User.query.get(id_usuario_alvo)

        if usuario_alvo is None:
            raise LookupError('Usuario nao encontrado.')

        if not cls.pode_controlar_permissoes(usuario_executor, usuario_alvo):
            raise PermissionError('Apenas o administrador pode gerenciar as permissoes dos outros usuarios.')

        usuario_alvo.is_active = not usuario_alvo.is_active
        db.session.commit()

        return usuario_alvo

    @staticmethod
    def listar_grupos_permissao():
        return Permissoes.query.order_by(Permissoes.id.asc()).all()

    @classmethod
    def listar_usuarios_gerenciaveis(cls, usuario_executor):
        if not cls.usuario_eh_administrador(usuario_executor):
            return []
        return User.query.order_by(User.username.asc()).all()

    @classmethod
    def atualizar_grupo_usuario(cls, usuario_executor, id_usuario_alvo, id_novo_grupo):
        usuario_alvo = User.query.get(id_usuario_alvo)

        if usuario_alvo is None:
            raise LookupError('Usuário não encontrado.')

        if not cls.pode_controlar_permissoes(usuario_executor, usuario_alvo):
            raise PermissionError('Apenas o administrador pode gerenciar as permissões dos outros usuários.')

        grupo = Permissoes.query.get(id_novo_grupo)
        if grupo is None:
            raise LookupError('Grupo de permissão nao encontrado.')

        usuario_alvo.role_id = grupo.id
        db.session.commit()

        return usuario_alvo
