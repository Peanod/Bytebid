"""
Bids API — SKPL-BB-05 (proses bidding), SKPL-BB-07 (real-time), SKPL-BB-08 (riwayat).

Endpoint:
  POST /api/bids/<item_id>        ajukan penawaran (JWT)
  GET  /api/bids/item/<item_id>   riwayat bid untuk satu item
  GET  /api/bids/me               daftar bid milik user saat ini (JWT)
"""
from decimal import Decimal, InvalidOperation
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import Item, User, Bid
from app.services.auction_service import place_bid_for_user, BidError

bids_bp = Blueprint('bids', __name__)


@bids_bp.route('/<int:item_id>', methods=['POST'])
@jwt_required()
def place_bid(item_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    item = Item.query.get(item_id)

    if not item:
        return jsonify({'success': False, 'message': 'Barang tidak ditemukan.'}), 404

    try:
        amount = Decimal(str((request.get_json() or {}).get('amount', 0)))
    except (InvalidOperation, TypeError):
        return jsonify({'success': False,
                        'message': 'Nilai penawaran tidak valid.'}), 400

    try:
        bid = place_bid_for_user(user, item, amount)
    except BidError as e:
        return jsonify({'success': False, 'message': str(e),
                        'min_required': e.min_required}), 400

    return jsonify({
        'success': True,
        'message': 'Penawaran berhasil diajukan!',
        'bid': bid.to_dict(),
        'item': item.to_dict(),
    }), 201


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
