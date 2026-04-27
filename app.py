import os
from flask import Flask
from controllers.app_controller import AppController
from config import Config
from models.database import db
from controllers.dashboard_controller import DashboardController

app = Flask(__name__, template_folder=os.path.join('views', 'templates'),static_folder=os.path.join('views', 'static'))

app.config.from_object(Config)

db.init_app(app)

app.add_url_rule('/','index',AppController.index,methods=['POST','GET'])
app.add_url_rule('/autenticar','autenticar',AppController.autenticar,methods=['POST','GET'])
app.add_url_rule('/dashboard', 'dashboard', view_func=DashboardController.listar_usuarios, methods=['POST', 'GET'])
app.add_url_rule('/usuario/status/<int:id_alvo>', 'alternar_status', view_func=DashboardController.alternar_status, methods=['GET'])
app.add_url_rule(
    '/usuario/permissao/<int:id_alvo>',
    'atualizar_permissao_usuario',
    view_func=DashboardController.atualizar_permissao_usuario,
    methods=['POST'],
)
app.add_url_rule(
    '/receita/cadastrar',
    'cadastrar_receita',
    view_func=DashboardController.cadastrar_receita,
    methods=['POST'],
)
app.add_url_rule('/logout', 'logout', view_func=AppController.logout, methods=['POST', 'GET'])
app.add_url_rule('/cadastrar','cadastrar',AppController.cadastrar,methods=['POST','GET'])

if __name__ == '__main__':
    app.run(debug=True)
