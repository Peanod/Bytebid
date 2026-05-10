"""
Notifications API — SKPL-BB-10 (notifikasi hasil lelang).

Endpoint:
  GET  /api/notifications                 daftar notif user (JWT)
  POST /api/notifications/<id>/read       tandai 1 notif dibaca
  POST /api/notifications/read-all        tandai semua dibaca
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models import Notification

notif_bp = Blueprint('notifications', __name__)


@notif_bp.route('', methods=['GET'])
@notif_bp.route('/', methods=['GET'])
@jwt_required()
def list_notifications():
    user_id = int(get_jwt_identity())
    notifs = (Notification.query.filter_by(user_id=user_id)
              .order_by(Notification.created_at.desc()).limit(100).all())
    unread = sum(1 for n in notifs if not n.is_read)
    return jsonify({
        'success': True,
        'unread_count': unread,
        'notifications': [n.to_dict() for n in notifs],
    })


@notif_bp.route('/<int:nid>/read', methods=['POST'])
@jwt_required()
def mark_read(nid):
    user_id = int(get_jwt_identity())
    n = Notification.query.filter_by(id=nid, user_id=user_id).first()
    if not n:
        return jsonify({'success': False, 'message': 'Notifikasi tidak ditemukan'}), 404
    n.is_read = True
    db.session.commit()
    return jsonify({'success': True, 'notification': n.to_dict()})


@notif_bp.route('/read-all', methods=['POST'])
@jwt_required()
def mark_all_read():
    user_id = int(get_jwt_identity())
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True, 'message': 'Semua notifikasi ditandai dibaca.'})
