from flask import Flask
from app.config import Config
from app.extensions import db, login_manager, mail, migrate, limiter
from flask_wtf.csrf import CSRFProtect
# from app.admin.routes import populate_curriculum_subjects


def create_app(config_class=Config):
    app = Flask(__name__)
    csrf = CSRFProtect(app)

    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = 'strong'

    # Register blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.timetable import bp as timetable_bp
    app.register_blueprint(timetable_bp, url_prefix='/timetable')

    # Create database tables
    with app.app_context():
        db.create_all()

    return app