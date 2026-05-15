"""
ByteBid Configuration

Default DB: SQLite (cocok untuk development & demo).
Set env DB_DRIVER=mysql untuk pakai MySQL sesuai DPP Modul 4 (lingkungan produksi).
"""
import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


def _build_database_uri() -> str:
    driver = os.getenv('DB_DRIVER', 'sqlite').lower()
    if driver == 'mysql':
        user = os.getenv('DB_USER', 'root')
        pwd = os.getenv('DB_PASSWORD', '')
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '3306')
        name = os.getenv('DB_NAME', 'bytebid')
        return f'mysql+pymysql://{user}:{pwd}@{host}:{port}/{name}'
    sqlite_path = os.getenv('SQLITE_PATH', os.path.join(basedir, 'bytebid.db'))
    return f'sqlite:///{sqlite_path}'


class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    SQLALCHEMY_DATABASE_URI = _build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)

    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    MAIL_SERVER = os.getenv('MAIL_SERVER', '')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@bytebid.id')

    # Aturan bisnis lelang
    MIN_BID_INCREMENT = int(os.getenv('MIN_BID_INCREMENT', 100_000))
    DEFAULT_AUCTION_DURATION_MINUTES = int(os.getenv('DEFAULT_AUCTION_DURATION_MINUTES', 30))

    SOCKETIO_MESSAGE_QUEUE = None
    TESTING = False


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
