"""
Auction Service.

Mengimplementasikan:
- SKPL-BB-05: proses bidding (validasi & simpan)
- SKPL-BB-07: pembaruan harga real-time (broadcast Socket.IO)
- SKPL-BB-09: penentuan pemenang otomatis saat lelang berakhir
- SKPL-BB-10: notifikasi hasil lelang (menang/kalah/outbid)
"""
from datetime import datetime
from decimal import Decimal

from flask import current_app

from app import db, socketio
from app.models import (Item, AuctionStatus, Bid, User,
                        Notification, NotificationType)


class BidError(Exception):
    """Bid ditolak (validasi gagal)."""
    def __init__(self, msg, min_required=None):
        super().__init__(msg)
        self.min_required = float(min_required) if min_required is not None else None


def place_bid_for_user(user: User, item: Item, amount: Decimal) -> Bid:
    """Validasi → simpan bid → broadcast → kirim notif outbid."""
    if item.status != AuctionStatus.ACTIVE:
        raise BidError('Lelang tidak aktif.')
    if item.is_expired:
        # Auto-end kalau expired tapi belum ditutup
        end_auction(item)
        db.session.commit()
        raise BidError('Waktu lelang sudah habis.')
    if amount <= 0:
        raise BidError('Nilai penawaran harus lebih dari 0.')

    min_increment = Decimal(str(current_app.config.get('MIN_BID_INCREMENT', 100_000)))
    min_required = item.current_bid + min_increment
    if amount < min_required:
        raise BidError(
            f'Penawaran minimal Rp {int(min_required):,}.'.replace(',', '.'),
            min_required=min_required,
        )

    # Reset bid winning sebelumnya & catat user yang akan di-outbid
    previous_winner_id = None
    last_bid = item.bids.first()
    if last_bid:
        previous_winner_id = last_bid.user_id
        Bid.query.filter_by(item_id=item.id, is_winning=True).update({'is_winning': False})

    new_bid = Bid(item_id=item.id, user_id=user.id,
                  amount=amount, is_winning=True)
    item.current_bid = amount
    item.updated_at = datetime.utcnow()
    db.session.add(new_bid)

    # Notifikasi outbid
    if previous_winner_id and previous_winner_id != user.id:
        notif = Notification(
            user_id=previous_winner_id,
            item_id=item.id,
            type=NotificationType.OUTBID,
            title='Penawaranmu dilampaui',
            message=(f'Penawaran Anda untuk "{item.name}" telah dilampaui. '
                     f'Harga sekarang Rp {int(amount):,}.'.replace(',', '.')),
        )
        db.session.add(notif)

    db.session.commit()

    # Broadcast real-time
    try:
        socketio.emit('bid_update', {
            'item_id': item.id,
            'current_bid': float(item.current_bid),
            'bid': new_bid.to_dict(),
            'total_bids': item.total_bids,
        }, room=f'item_{item.id}')

        if previous_winner_id and previous_winner_id != user.id:
            socketio.emit('notification', {
                'type': 'outbid',
                'item_id': item.id,
                'title': 'Penawaranmu dilampaui',
                'message': f'Penawaranmu untuk "{item.name}" dilampaui!',
            }, room=f'user_{previous_winner_id}')
    except Exception as e:
        current_app.logger.warning(f'Socket.IO emit gagal: {e}')

    return new_bid


def end_auction(item: Item) -> None:
    """Tutup lelang & tentukan pemenang. Kirim notifikasi menang/kalah."""
    if item.status != AuctionStatus.ACTIVE:
        return

    item.status = AuctionStatus.ENDED
    winning_bid = item.bids.first()  # ordered desc by created_at
    winner_id = None

    if winning_bid:
        winner_id = winning_bid.user_id
        item.winner_id = winner_id
        winning_bid.is_winning = True

        db.session.add(Notification(
            user_id=winner_id,
            item_id=item.id,
            type=NotificationType.WIN,
            title='Selamat! Anda Memenangkan Lelang',
            message=(f'Anda memenangkan lelang "{item.name}" dengan harga '
                     f'Rp {int(winning_bid.amount):,}.'.replace(',', '.') +
                     ' Tim ByteBid akan menghubungi Anda dalam 24 jam.'),
        ))

        try:
            socketio.emit('notification', {
                'type': 'win', 'item_id': item.id,
                'title': 'Selamat! Anda Menang',
                'message': f'Anda memenangkan "{item.name}".',
            }, room=f'user_{winner_id}')
        except Exception:
            pass

        loser_ids = {b.user_id for b in item.bids.all() if b.user_id != winner_id}
        for uid in loser_ids:
            db.session.add(Notification(
                user_id=uid,
                item_id=item.id,
                type=NotificationType.LOSE,
                title='Lelang Berakhir',
                message=(f'Lelang "{item.name}" telah berakhir. Pemenang dengan '
                         f'penawaran Rp {int(winning_bid.amount):,}.'.replace(',', '.') +
                         ' Coba lelang lainnya!'),
            ))
            try:
                socketio.emit('notification', {
                    'type': 'lose', 'item_id': item.id,
                    'title': 'Lelang Berakhir',
                    'message': f'Lelang "{item.name}" telah berakhir.',
                }, room=f'user_{uid}')
            except Exception:
                pass

    try:
        socketio.emit('auction_ended', {
            'item_id': item.id,
            'winner_id': winner_id,
            'final_price': float(item.current_bid),
            'has_winner': winner_id is not None,
        }, room=f'item_{item.id}')
    except Exception:
        pass


def check_expired_auctions() -> int:
    """Dijalankan periodik oleh scheduler."""
    expired = (Item.query.filter_by(status=AuctionStatus.ACTIVE)
               .filter(Item.end_time <= datetime.utcnow()).all())
    for item in expired:
        end_auction(item)
    if expired:
        db.session.commit()
    return len(expired)
