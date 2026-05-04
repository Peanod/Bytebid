"""
Auction Service — implementasi SKPL-BB-09 (penentuan pemenang otomatis)
dan SKPL-BB-10 (notifikasi hasil lelang).
"""
from datetime import datetime
from flask import current_app

from app import db, socketio
from app.models import (Item, AuctionStatus, Bid,
                        Notification, NotificationType)


def end_auction(item: Item) -> None:
    """
    Tutup lelang & tentukan pemenang berdasarkan harga tertinggi.
    Kirim notifikasi menang/kalah ke semua peserta.
    """
    if item.status != AuctionStatus.ACTIVE:
        return

    item.status = AuctionStatus.ENDED

    winning_bid = item.bids.first()   # bids di-order desc by created_at
    winner_id = None

    if winning_bid:
        winner_id = winning_bid.user_id
        item.winner_id = winner_id
        winning_bid.is_winning = True

        # Notifikasi menang
        win_notif = Notification(
            user_id=winner_id,
            item_id=item.id,
            type=NotificationType.WIN,
            title='Selamat! Anda Memenangkan Lelang',
            message=(f'Anda memenangkan lelang "{item.name}" dengan '
                     f'harga Rp {winning_bid.amount:,.0f}. '
                     'Tim ByteBid akan menghubungi Anda dalam 24 jam.'),
        )
        db.session.add(win_notif)

        # Push notif ke pemenang
        socketio.emit('notification', {
            'type': 'win',
            'item_id': item.id,
            'title': 'Selamat! Anda Menang',
            'message': f'Anda memenangkan "{item.name}".',
        }, room=f'user_{winner_id}')

        # Notifikasi kalah ke peserta lain (unique)
        loser_ids = {
            b.user_id for b in item.bids.all() if b.user_id != winner_id
        }
        for uid in loser_ids:
            db.session.add(Notification(
                user_id=uid,
                item_id=item.id,
                type=NotificationType.LOSE,
                title='Lelang Berakhir',
                message=(f'Lelang "{item.name}" telah berakhir. '
                         f'Pemenang dengan penawaran Rp {winning_bid.amount:,.0f}. '
                         'Coba lelang lainnya!'),
            ))
            socketio.emit('notification', {
                'type': 'lose',
                'item_id': item.id,
                'title': 'Lelang Berakhir',
                'message': f'Lelang "{item.name}" telah berakhir.',
            }, room=f'user_{uid}')

        # Email ke pemenang
        try:
            from app.services.email_service import send_winner_email
            send_winner_email(winning_bid.user, item, float(winning_bid.amount))
        except Exception as e:
            current_app.logger.error(f'Gagal kirim email pemenang: {e}')

    # Broadcast ke ruang item
    socketio.emit('auction_ended', {
        'item_id': item.id,
        'winner_id': winner_id,
        'final_price': float(item.current_bid),
        'has_winner': winner_id is not None,
    }, room=f'item_{item.id}')


def check_expired_auctions() -> int:
    """Dipanggil periodik oleh scheduler."""
    expired = (Item.query.filter_by(status=AuctionStatus.ACTIVE)
               .filter(Item.end_time <= datetime.utcnow()).all())
    for item in expired:
        end_auction(item)
    if expired:
        db.session.commit()
    return len(expired)
