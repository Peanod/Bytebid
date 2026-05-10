"""
ByteBid Models — semua database models terpusat di sini
"""
import enum
import secrets
from datetime import datetime, timedelta
from decimal import Decimal
from app import db, bcrypt


# ── Enums ──────────────────────────────────────────────────────────────────────

class AuctionStatus(enum.Enum):
    SCHEDULED = 'scheduled'
    ACTIVE = 'active'
    ENDED = 'ended'
    CANCELLED = 'cancelled'


class NotificationType(enum.Enum):
    OUTBID = 'outbid'
    AUCTION_ENDED = 'auction_ended'
    AUCTION_CANCELLED = 'auction_cancelled'
    ITEM_CREATED = 'item_created'


# ── User Model ─────────────────────────────────────────────────────────────────

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
    password_reset_tokens = db.relationship('PasswordResetToken', backref='user',
                                           cascade='all, delete-orphan')

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


# ── Item Model ─────────────────────────────────────────────────────────────────

class Item(db.Model):
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    condition = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(50), nullable=False, index=True)
    image = db.Column(db.String(500), nullable=True)

    # Lelang
    start_price = db.Column(db.Numeric(15, 2), nullable=False)
    current_bid = db.Column(db.Numeric(15, 2), nullable=False)
    status = db.Column(db.Enum(AuctionStatus),
                       default=AuctionStatus.ACTIVE, nullable=False)

    # Waktu
    start_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)

    # FK
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    winner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)

    bids = db.relationship('Bid', backref='item', lazy='dynamic',
                           cascade='all, delete-orphan',
                           order_by='Bid.created_at.desc()')

    @property
    def time_remaining_seconds(self) -> int:
        if self.status != AuctionStatus.ACTIVE:
            return 0
        delta = self.end_time - datetime.utcnow()
        return max(0, int(delta.total_seconds()))

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() >= self.end_time

    @property
    def total_bids(self) -> int:
        return self.bids.count()

    @property
    def badge(self) -> str:
        if self.time_remaining_seconds <= 3 * 3600:
            return 'Segera Berakhir'
        return 'Baru Ditambahkan'

    @property
    def timer_display(self) -> str:
        secs = self.time_remaining_seconds
        h, rem = divmod(secs, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def to_dict(self, with_bids: bool = False) -> dict:
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'condition': self.condition,
            'category': self.category,
            'image': self.image,
            'start_price': float(self.start_price),
            'current_bid': float(self.current_bid),
            'status': self.status.value,
            'badge': self.badge,
            'timer': self.timer_display,
            'time_remaining': self.time_remaining_seconds,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'total_bids': self.total_bids,
            'winner_id': self.winner_id,
            'winner': self.winner.to_dict() if self.winner else None,
        }
        if with_bids:
            data['bids'] = [b.to_dict() for b in self.bids.limit(20).all()]
        return data

    def __repr__(self):
        return f'<Item {self.id} {self.name}>'


# ── Bid Model ──────────────────────────────────────────────────────────────────

class Bid(db.Model):
    __tablename__ = 'bids'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(15, 2), nullable=False)

    # FK
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'amount': float(self.amount),
            'user': self.user.to_dict(),
            'created_at': self.created_at.isoformat(),
        }

    def __repr__(self):
        return f'<Bid {self.id} item={self.item_id} user={self.user_id} amount={self.amount}>'


# ── Notification Model ─────────────────────────────────────────────────────────

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(NotificationType), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    # FK
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'type': self.type.value,
            'message': self.message,
            'is_read': self.is_read,
            'item_id': self.item_id,
            'created_at': self.created_at.isoformat(),
        }

    def __repr__(self):
        return f'<Notification {self.id} type={self.type.value}>'


# ── PasswordResetToken Model ───────────────────────────────────────────────────

class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)

    # FK
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    @classmethod
    def create_token(cls, user_id: int, expires_in_hours: int = 24) -> str:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        reset_token = cls(token=token, user_id=user_id, expires_at=expires_at)
        db.session.add(reset_token)
        db.session.commit()
        return token

    @classmethod
    def verify_token(cls, token: str):
        reset_token = cls.query.filter_by(token=token).first()
        if not reset_token:
            return None
        if datetime.utcnow() > reset_token.expires_at:
            db.session.delete(reset_token)
            db.session.commit()
            return None
        return reset_token

    def __repr__(self):
        return f'<PasswordResetToken user_id={self.user_id}>'
