"""
Items API — SKPL-BB-04 (daftar barang) & SKPL-BB-06 (timer per barang).

Endpoint:
  GET /api/items                  list (filter: ?category=, ?q=, ?status=, ?limit=)
  GET /api/items/<id>             detail + bid history
  GET /api/items/categories       daftar kategori unik
"""
from flask import Blueprint, request, jsonify

from app.models import Item, AuctionStatus, Bid

items_bp = Blueprint('items', __name__)


@items_bp.route('', methods=['GET'])
@items_bp.route('/', methods=['GET'])
def list_items():
    cat = (request.args.get('category') or '').strip()
    q = (request.args.get('q') or '').strip()
    status_str = (request.args.get('status') or 'active').lower()
    limit = min(int(request.args.get('limit', 50)), 200)

    query = Item.query
    if status_str and status_str != 'all':
        try:
            st = AuctionStatus(status_str)
            query = query.filter(Item.status == st)
        except ValueError:
            pass
    if cat and cat.lower() != 'semua':
        query = query.filter(Item.category == cat)
    if q:
        like = f'%{q}%'
        query = query.filter(Item.name.ilike(like))

    items = query.order_by(Item.end_time.asc()).limit(limit).all()
    return jsonify({
        'success': True,
        'count': len(items),
        'items': [i.to_dict() for i in items],
    })


@items_bp.route('/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'success': False, 'message': 'Barang tidak ditemukan'}), 404
    return jsonify({'success': True, 'item': item.to_dict(with_bids=True)})


@items_bp.route('/categories', methods=['GET'])
def categories():
    cats = [c[0] for c in
            Item.query.with_entities(Item.category).distinct().all()
            if c[0]]
    return jsonify({'success': True, 'categories': sorted(cats)})
