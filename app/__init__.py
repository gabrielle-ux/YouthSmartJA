from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from .models import db  # Import the db you just defined

from config import Config
from .models import db, TokenBlocklist # Import your Postgres models
from .views import main_bp

migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize Extensions
    CORS(app, origins=["http://127.0.0.1:5000", "http://localhost:5000"])
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # JWT Token Revocation Logic
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        token = TokenBlocklist.query.filter_by(jti=jti).first()
        return token is not None
    
    # Register Blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.searchjobs import jobs_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(main_bp)

    return app
