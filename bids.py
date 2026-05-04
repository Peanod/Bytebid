"""
Bids routes — implementasi core SKPL-BB-05, SKPL-BB-07, SKPL-BB-08
- POST /api/bids/<item_id>        : ajukan penawaran
- GET  /api/bids/item/<item_id>   : daftar bid untuk satu item (riwayat)
- GET  /api/bids/me               : daftar bid milik user saat ini
"""
from decimal import Decimal, InvalidOperation
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db, socketio
from app.models import (Item, AuctionStatus, Bid, User,
                        Notification, NotificationType)

bids_bp = Blueprint('bids', __name__)


# ── POST BID (SKPL-BB-05 - Use Case Bidding di Modul 3 Tabel 3.6) ──────────────
@bids_bp.route('/<int:item_id>', methods=['POST'])
@jwt_required()
def place_bid(item_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    item = Item.query.get(item_id)

    if not item:
        return jsonify({'success': False, 'message': 'Barang tidak ditemukan.'}), 404

    # Precondition Use Case: lelang harus aktif
    if item.status != AuctionStatus.ACTIVE:
        return jsonify({'success': False,
                        'message': 'Lelang sudah berakhir atau tidak aktif.'}), 400

    if item.is_expired:
        return jsonify({'success': False,
                        'message': 'Waktu lelang sudah habis.'}), 400

    # Parse amount
    try:
        amount = Decimal(str(request.get_json().get('amount', 0)))
    except (InvalidOperation, AttributeError):
        return jsonify({'success': False,
                        'message': 'Nilai penawaran tidak valid.'}), 400

    # Business rule (Tabel 3.6 Modul 3): bid harus > harga tertinggi saat ini
    min_increment = Decimal(current_app.config.get('MIN_BID_INCREMENT', 100_000))
    min_required = item.current_bid + min_increment

    if amount < min_required:
        return jsonify({
            'success': False,
            'message': f'Penawaran minimal Rp {min_required:,.0f}.',
            'min_required': float(min_required),
        }), 400

    # Tandai bid sebelumnya bukan winning + cari user yang outbid
    previous_winner_id = None
    last_bid = item.bids.first()
    if last_bid:
        previous_winner_id = last_bid.user_id
        # Reset semua flag is_winning
        Bid.query.filter_by(item_id=item.id, is_winning=True).update(
            {'is_winning': False})

    # Simpan bid baru
    new_bid = Bid(item_id=item.id, user_id=user_id,
                  amount=amount, is_winning=True)
    item.current_bid = amount
    item.updated_at = datetime.utcnow()
    db.session.add(new_bid)

    # Notifikasi outbid ke user sebelumnya
    if previous_winner_id and previous_winner_id != user_id:
        notif = Notification(
            user_id=previous_winner_id,
            item_id=item.id,
            type=NotificationType.OUTBID,
            title='Penawaranmu dilampaui',
            message=(f'Penawaran Anda untuk "{item.name}" telah dilampaui. '
                     f'Harga sekarang Rp {amount:,.0f}.'),
        )
        db.session.add(notif)

    db.session.commit()

    # ── Broadcast real-time (SKPL-BB-07) via Socket.IO ─────────────────────
    socketio.emit('bid_update', {
        'item_id': item.id,
        'current_bid': float(item.current_bid),
        'bid': new_bid.to_dict(),
        'total_bids': item.total_bids,
    }, room=f'item_{item.id}')

    # Notif outbid juga di-push real-time
    if previous_winner_id and previous_winner_id != user_id:
        socketio.emit('notification', {
            'type': 'outbid',
            'item_id': item.id,
            'message': f'Penawaranmu untuk "{item.name}" dilampaui!',
        }, room=f'user_{previous_winner_id}')

    return jsonify({
        'success': True,
        'message': 'Penawaran berhasil diajukan!',
        'bid': new_bid.to_dict(),
        'item': item.to_dict(),
    }), 201


# ── RIWAYAT BID PER ITEM ───────────────────────────────────────────────────────
@bids_bp.route('/item/<int:item_id>', methods=['GET'])
def item_bids(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'success': False, 'message': 'Barang tidak ditemukan'}), 404

    limit = min(int(request.args.get('limit', 20)), 100)
    bids = item.bids.limit(limit).all()
    return jsonify({
        'success': True,
        'item_id': item.id,
        'bids': [b.to_dict() for b in bids],
    })


# ── BID MILIK USER ─────────────────────────────────────────────────────────────
@bids_bp.route('/me', methods=['GET'])
@jwt_required()
def my_bids():
    user_id = int(get_jwt_identity())
    bids = (Bid.query.filter_by(user_id=user_id)
            .order_by(Bid.created_at.desc()).limit(50).all())
    return jsonify({
        'success': True,
        'bids': [{
            **b.to_dict(),
            'item': b.item.to_dict() if b.item else None,
        } for b in bids],
    })
