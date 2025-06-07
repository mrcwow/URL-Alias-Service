import os
import sys
from flask import Flask
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config

db = SQLAlchemy()
migrate = Migrate()
api = Api(
    title="URL Alias Service",
    description="Service for converting long URLs into short unique URLs",
    doc="/docs",
    authorizations={
        "basicAuth": {
            "type": "basic",
            "in": "header",
            "name": "Authorization"
        }
    }
)

SERVICE_URL = f"http://localhost:{os.getenv('SERVER_PORT')}/service/"

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    try:
        db.init_app(app)
    except Exception as e:
        print(f"Database init error: {e}")
        sys.exit(1)
    migrate.init_app(app, db)
    api.init_app(app)
    
    from .routes import api as url_api
    api.add_namespace(url_api)
    
    return app