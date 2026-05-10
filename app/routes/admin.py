"""
Admin API — SKPL-BB-11 (kelola data barang) & SKPL-BB-12 (pantau lelang).

Endpoint:
  POST   /api/admin/items                tambah barang (+ optional upload gambar)
  PUT    /api/admin/items/<id>           edit barang
  DELETE /api/admin/items/<id>           hapus barang
  POST   /api/admin/items/<id>/cancel    batalkan lelang
  POST   /api/admin/items/<id>/end       tutup lelang manual
  GET    /api/admin/dashboard            statistik
  POST   /api/admin/promote/<user_id>    jadikan user admin
"""
import os
import uuid
from decimal import Decimal
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models import User, Item, AuctionStatus, Bid
from app.services.auction_service import end_auction

admin_bp = Blueprint('admin', __name__)


def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = User.query.get(int(get_jwt_identity()))
        if not user or not user.is_admin:
            return jsonify({'success': False,
                            'message': 'Akses ditolak. Hanya admin.'}), 403
        return fn(*args, **kwargs)
    return wrapper


def _allowed(filename):
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower()
            in current_app.config['ALLOWED_EXTENSIONS'])


def _save_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    if not _allowed(file_storage.filename):
        return None
    ext = file_storage.filename.rsplit('.', 1)[1].lower()
    fname = f"{uuid.uuid4().hex}.{ext}"
    fpath = os.path.join(current_app.config['UPLOAD_FOLDER'], fname)
    file_storage.save(fpath)
    return f'/uploads/{fname}'


@admin_bp.route('/items', methods=['POST'])
@admin_required
def create_item():
    user_id = int(get_jwt_identity())

    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form
        image_file = request.files.get('image')
    else:
        data = request.get_json() or {}
        image_file = None

    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': 'Nama barang wajib diisi.'}), 400

    try:
        start_price = Decimal(str(data.get('start_price', 0)))
    except Exception:
        return jsonify({'success': False, 'message': 'Harga awal tidak valid.'}), 400

    if start_price <= 0:
        return jsonify({'success': False, 'message': 'Harga awal harus lebih dari 0.'}), 400

    duration = int(data.get('duration_minutes',
                            current_app.config['DEFAULT_AUCTION_DURATION_MINUTES']))

    image_path = data.get('image_url')
    if image_file:
        saved = _save_image(image_file)
        if saved:
            image_path = saved

    item = Item(
        name=name,
        description=data.get('description', ''),
        condition=data.get('condition', ''),
        category=data.get('category', 'Lainnya'),
        image=image_path,
        start_price=start_price,
        current_bid=start_price,
        status=AuctionStatus.ACTIVE,
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(minutes=duration),
        created_by=user_id,
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'success': True, 'item': item.to_dict()}), 201


@admin_bp.route('/items/<int:item_id>', methods=['PUT', 'PATCH'])
@admin_required
def update_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'success': False, 'message': 'Barang tidak ditemukan'}), 404

    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form
        image_file = request.files.get('image')
    else:
        data = request.get_json() or {}
        image_file = None

    for f in ('name', 'description', 'condition', 'category'):
        if f in data:
            setattr(item, f, data.get(f))

    if image_file:
        saved = _save_image(image_file)
        if saved:
            item.image = saved
    elif data.get('image_url'):
        item.image = data.get('image_url')

    if 'duration_minutes' in data:
        try:
            mins = int(data.get('duration_minutes'))
            item.end_time = datetime.utcnow() + timedelta(minutes=mins)
        except ValueError:
            pass

    db.session.commit()
    return jsonify({'success': True, 'item': item.to_dict()})


@admin_bp.route('/items/<int:item_id>', methods=['DELETE'])
@admin_required
def delete_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'success': False, 'message': 'Barang tidak ditemukan'}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Barang dihapus.'})


@admin_bp.route('/items/<int:item_id>/cancel', methods=['POST'])
@admin_required
def cancel_auction(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'success': False, 'message': 'Barang tidak ditemukan'}), 404
    item.status = AuctionStatus.CANCELLED
    db.session.commit()
    return jsonify({'success': True, 'item': item.to_dict()})


@admin_bp.route('/items/<int:item_id>/end', methods=['POST'])
@admin_required
def end_auction_manual(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'success': False, 'message': 'Barang tidak ditemukan'}), 404
    end_auction(item)
    db.session.commit()
    return jsonify({'success': True, 'item': item.to_dict()})


@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def dashboard():
    stats = {
        'total_items': Item.query.count(),
        'active_items': Item.query.filter_by(status=AuctionStatus.ACTIVE).count(),
        'ended_items': Item.query.filter_by(status=AuctionStatus.ENDED).count(),
        'total_users': User.query.count(),
        'total_bids': Bid.query.count(),
    }
    recent_items = Item.query.order_by(Item.created_at.desc()).limit(5).all()
    return jsonify({
        'success': True,
        'stats': stats,
        'recent_items': [i.to_dict() for i in recent_items],
    })


@admin_bp.route('/promote/<int:user_id>', methods=['POST'])
@admin_required
def promote_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User tidak ditemukan'}), 404
    user.is_admin = True
    db.session.commit()
    return jsonify({'success': True, 'user': user.to_dict()})
