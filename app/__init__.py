from flask import Flask
from .routes import bp
from .store import init_db

def create_app(test_config=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.update(MAX_CONTENT_LENGTH=8 * 1024 * 1024, JSON_AS_ASCII=False)
    if test_config:
        app.config.update(test_config)
    init_db()
    app.register_blueprint(bp)
    return app
