"""
User model — sesuai SKPL-BB-01, SKPL-BB-02, SKPL-BB-03
Login menggunakan username ATAU email (sesuai laporan Modul 3 UI-300)
"""
from datetime import datetime
from app import db, bcrypt


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    avatar = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)

    # Relationships
    bids = db.relationship('Bid', backref='user', lazy='dynamic',
                           cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic',
                                    cascade='all, delete-orphan')
    items_created = db.relationship('Item', backref='creator', lazy='dynamic',
                                    foreign_keys='Item.created_by')
    items_won = db.relationship('Item', backref='winner', lazy='dynamic',
                                foreign_keys='Item.winner_id')

    # ── Password helpers (enkripsi - SKPL-BB-N3 Security) ──────────────────
    def set_password(self, plain_password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(plain_password).decode('utf-8')

    def check_password(self, plain_password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, plain_password)

    def to_dict(self, include_email: bool = False) -> dict:
        data = {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'avatar': self.avatar,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_email:
            data['email'] = self.email
        return data

    def __repr__(self):
        return f'<User {self.username}>'
