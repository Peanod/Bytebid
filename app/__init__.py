"""
ByteBid - Application Factory.

Single Flask app yang melayani:
- Halaman web (Jinja templates) dengan Flask session auth.
- API JSON di /api/* dengan JWT untuk klien programmatic.
- WebSocket real-time (Socket.IO) untuk update bid & timer.
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

# ── Extensions (dideklarasikan di luar factory) ───────────────────────────────
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')
bcrypt = Bcrypt()
mail = Mail()


def _format_rupiah(value) -> str:
    """Jinja filter: 1500000 -> 'Rp 1.500.000'."""
    if value is None:
        return 'Rp 0'
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        return 'Rp 0'
    return 'Rp ' + f'{n:,}'.replace(',', '.')


def create_app(config_name='default'):
    app = Flask(__name__,
                static_folder='static',
                template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'))
    app.config.from_object(config_map[config_name])

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    socketio.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Jinja filters
    app.jinja_env.filters['rupiah'] = _format_rupiah

    # Blueprints — web (no prefix) + API JSON (/api/*)
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.items import items_bp
    from app.routes.bids import bids_bp
    from app.routes.notifications import notif_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp,  url_prefix='/api/auth')
    app.register_blueprint(items_bp, url_prefix='/api/items')
    app.register_blueprint(bids_bp,  url_prefix='/api/bids')
    app.register_blueprint(notif_bp, url_prefix='/api/notifications')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    # Socket.IO events
    from app.sockets import auction_events  # noqa: F401

    # Auto-create tables jika belum ada (dev/demo)
    with app.app_context():
        db.create_all()

    # Background scheduler (cek lelang berakhir)
    from app.services.scheduler import start_scheduler
    if not app.config.get('TESTING'):
        start_scheduler(app)

    @app.errorhandler(404)
    def not_found(e):
        from flask import request, render_template
        if request.path.startswith('/api/'):
            return {'success': False, 'message': 'Resource tidak ditemukan'}, 404
        try:
            return render_template('404.html'), 404
        except Exception:
            return '<h1>404 — Halaman tidak ditemukan</h1>', 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import request
        if request.path.startswith('/api/'):
            return {'success': False, 'message': 'Terjadi kesalahan server'}, 500
        return '<h1>500 — Terjadi kesalahan server</h1>', 500

    return app
