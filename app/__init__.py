from flask import Flask
from flask_socketio import SocketIO
from config import config
import os

socketio = SocketIO(async_mode='eventlet')

def create_app():
    app = Flask(__name__,
                template_folder=os.path.join(config.BASE_DIR, 'templates'),
                static_folder=os.path.join(config.BASE_DIR, 'static'))
    app.config.from_object(config)

    from .api.routes import api as api_blueprint
    app.register_blueprint(api_blueprint)

    socketio.init_app(app)
    return app
