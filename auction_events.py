"""
Socket.IO Events — implementasi SKPL-BB-07 (update real-time)
dan SKPL-BB-N1 (delay maksimal 1 detik).

Client events:
- join_item   {item_id}    : masuk ke ruang lelang barang tertentu
- leave_item  {item_id}    : keluar dari ruang
- join_user   {user_id, token} : masuk ke ruang pribadi (untuk notifikasi)

Server emits:
- bid_update      : ada bid baru pada item (broadcast ke item_<id>)
- auction_ended   : lelang berakhir
- notification    : notif personal (ke user_<id>)
"""
from flask import current_app
from flask_socketio import emit, join_room, leave_room

from app import socketio


@socketio.on('connect')
def on_connect():
    current_app.logger.info('[SocketIO] Client connected')
    emit('connected', {'message': 'Terhubung ke ByteBid real-time server'})


@socketio.on('disconnect')
def on_disconnect():
    current_app.logger.info('[SocketIO] Client disconnected')


@socketio.on('join_item')
def on_join_item(data):
    item_id = data.get('item_id')
    if not item_id:
        return
    room = f'item_{item_id}'
    join_room(room)
    emit('joined', {'room': room})


@socketio.on('leave_item')
def on_leave_item(data):
    item_id = data.get('item_id')
    if not item_id:
        return
    leave_room(f'item_{item_id}')


@socketio.on('join_user')
def on_join_user(data):
    """User join ke ruangan pribadi untuk menerima notifikasi."""
    user_id = data.get('user_id')
    if not user_id:
        return
    join_room(f'user_{user_id}')
    emit('joined', {'room': f'user_{user_id}'})
