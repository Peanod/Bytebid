"""
Item model — barang yang dilelang
Implementasi SKPL-BB-04 (daftar barang) dan SKPL-BB-11 (kelola data barang)
"""
import enum
from datetime import datetime, timedelta
from app import db


class AuctionStatus(enum.Enum):
    SCHEDULED = 'scheduled'   # belum mulai
    ACTIVE = 'active'          # sedang berlangsung
    ENDED = 'ended'            # waktu habis, pemenang ditentukan
    CANCELLED = 'cancelled'    # dibatalkan admin


class Item(db.Model):
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    condition = db.Column(db.String(255), nullable=True)   # mis. "Kondisi Baru"
    category = db.Column(db.String(50), nullable=False, index=True)
    image = db.Column(db.String(500), nullable=True)        # path/URL gambar

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

    # ── Helpers ────────────────────────────────────────────────────────────
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
        """Badge untuk UI — 'Segera Berakhir' atau 'Baru Ditambahkan'"""
        if self.time_remaining_seconds <= 3 * 3600:   # < 3 jam
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
