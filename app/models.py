"""
ByteBid Models — semua database models terpusat di sini.
Mengacu pada DPP Modul 4 (tabel user, barang, sesi_lelang, penawaran, notifikasi, admin).
"""
import enum
import secrets
from datetime import datetime, timedelta
from app import db, bcrypt


# ── Enums ──────────────────────────────────────────────────────────────────────

class AuctionStatus(enum.Enum):
    SCHEDULED = 'scheduled'
    ACTIVE = 'active'
    ENDED = 'ended'
    CANCELLED = 'cancelled'


class NotificationType(enum.Enum):
    OUTBID = 'outbid'                     # Penawaran user dilampaui
    WIN = 'win'                           # User memenangkan lelang
    LOSE = 'lose'                         # User kalah lelang
    AUCTION_ENDED = 'auction_ended'       # Lelang ditutup tanpa pemenang
    AUCTION_CANCELLED = 'auction_cancelled'
    ITEM_CREATED = 'item_created'


# ── User Model (tabel `users`) ─────────────────────────────────────────────────

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    avatar = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)

    bids = db.relationship('Bid', backref='user', lazy='dynamic',
                           cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic',
                                    cascade='all, delete-orphan')
    items_created = db.relationship('Item', backref='creator', lazy='dynamic',
                                    foreign_keys='Item.created_by')
    items_won = db.relationship('Item', backref='winner', lazy='dynamic',
                                foreign_keys='Item.winner_id')
    reset_tokens = db.relationship('PasswordResetToken', backref='user',
                                   cascade='all, delete-orphan')

    def set_password(self, plain_password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(plain_password).decode('utf-8')

    def check_password(self, plain_password: str) -> bool:
        try:
            return bcrypt.check_password_hash(self.password_hash, plain_password)
        except Exception:
            return False

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


# ── Item / Barang Model (tabel `items`) ───────────────────────────────────────

class Item(db.Model):
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    condition = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(50), nullable=False, index=True, default='Lainnya')
    image = db.Column(db.String(500), nullable=True)

    start_price = db.Column(db.Numeric(15, 2), nullable=False)
    current_bid = db.Column(db.Numeric(15, 2), nullable=False)
    status = db.Column(db.Enum(AuctionStatus),
                       default=AuctionStatus.ACTIVE, nullable=False)

    start_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)

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
        if self.status not in (AuctionStatus.ACTIVE, AuctionStatus.SCHEDULED):
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
    def unique_bidders(self) -> int:
        return db.session.query(Bid.user_id).filter_by(item_id=self.id).distinct().count()

    @property
    def badge(self) -> str:
        if self.status == AuctionStatus.ENDED:
            return 'Selesai'
        if self.status == AuctionStatus.CANCELLED:
            return 'Dibatalkan'
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
            'unique_bidders': self.unique_bidders,
            'winner_id': self.winner_id,
            'winner': self.winner.to_dict() if self.winner else None,
        }
        if with_bids:
            data['bids'] = [b.to_dict() for b in self.bids.limit(20).all()]
        return data

    def __repr__(self):
        return f'<Item {self.id} {self.name}>'


# ── Bid / Penawaran Model (tabel `bids`) ──────────────────────────────────────

class Bid(db.Model):
    __tablename__ = 'bids'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    is_winning = db.Column(db.Boolean, default=False, nullable=False, index=True)

    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'amount': float(self.amount),
            'is_winning': self.is_winning,
            'user': self.user.to_dict() if self.user else None,
            'item_id': self.item_id,
            'created_at': self.created_at.isoformat(),
        }

    def __repr__(self):
        return f'<Bid {self.id} item={self.item_id} user={self.user_id} amount={self.amount}>'


# ── Notification Model (tabel `notifications`) ───────────────────────────────

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(NotificationType), nullable=False)
    title = db.Column(db.String(200), nullable=False, default='')
    message = db.Column(db.String(500), nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'type': self.type.value,
            'title': self.title,
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
    used = db.Column(db.Boolean, default=False, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    @classmethod
    def create_for(cls, user, expires_in_hours: int = 24):
        token = cls(
            token=secrets.token_urlsafe(32),
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours),
        )
        return token

    @property
    def is_valid(self) -> bool:
        return (not self.used) and datetime.utcnow() < self.expires_at

    def __repr__(self):
        return f'<PasswordResetToken user_id={self.user_id} valid={self.is_valid}>'
