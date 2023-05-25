import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from config import Config, DevelopmentConfig, ProductionConfig

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
login = LoginManager()
login.login_view = "auth.login"
login.login_message = "Please login to access this page"


def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.config.update(
        dict(
            DEBUG=os.environ.get("DEBUG"),
            MAIL_SERVER=os.environ.get("MAIL_SERVER"),
            MAIL_PORT=587,
            MAIL_USE_TLS=True,
            MAIL_USE_SSL=False,
            MAIL_USERNAME=os.environ.get("MAIL_USERNAME"),
            MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD"),
        )
    )

    @app.before_first_request
    def create_tables():
        db.create_all()

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    app.debug = 1
    mail.init_app(app)

    from webapp.user.routes import bp as user_bp
    from webapp.auth.routes import bp as auth_bp
    from webapp.project.routes import bp as project_bp

    app.register_blueprint(user_bp, url_prefix="/")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(project_bp, url_prefix="/project")

    return app
