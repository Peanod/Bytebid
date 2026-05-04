"""
ByteBid - Application Factory
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_mail import Mail
from flask_bcrypt import Bcrypt

from config import config_map

# ── Extensions (dideklarasikan di luar factory agar bisa di-import modul lain) ─
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')
bcrypt = Bcrypt()
mail = Mail()


def create_app(config_name='default'):
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')
    app.config.from_object(config_map[config_name])

    # Pastikan folder upload ada
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # ── Inisialisasi extensions ────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    socketio.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ── Register blueprints ────────────────────────────────────────────────
    from app.routes.auth import auth_bp
    from app.routes.items import items_bp
    from app.routes.bids import bids_bp
    from app.routes.notifications import notif_bp
    from app.routes.admin import admin_bp
    from app.routes.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp,  url_prefix='/api/auth')
    app.register_blueprint(items_bp, url_prefix='/api/items')
    app.register_blueprint(bids_bp,  url_prefix='/api/bids')
    app.register_blueprint(notif_bp, url_prefix='/api/notifications')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    # ── Register socket events ─────────────────────────────────────────────
    from app.sockets import auction_events  # noqa: F401

    # ── Background scheduler untuk cek lelang berakhir ─────────────────────
    from app.services.scheduler import start_scheduler
    if not app.config.get('TESTING'):
        start_scheduler(app)

    # ── Error handlers ─────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return {'success': False, 'message': 'Resource tidak ditemukan'}, 404

    @app.errorhandler(500)
    def server_error(e):
        return {'success': False, 'message': 'Terjadi kesalahan server'}, 500

    return app
