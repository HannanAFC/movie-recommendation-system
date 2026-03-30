from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
mail = Mail()
jwt_manager = JWTManager()
mail = Mail()
jwt_manager = JWTManager()
socketio = SocketIO()