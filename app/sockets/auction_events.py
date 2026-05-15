"""
Socket.IO events — SKPL-BB-07 (real-time update harga & timer).

Client → Server:
  connect / disconnect           : default
  join_item    {item_id}         : masuk ke ruang lelang barang
  leave_item   {item_id}         : keluar dari ruang
  join_user    {user_id}         : masuk ke ruang pribadi (notifikasi)

Server → Client:
  bid_update         : ada bid baru (broadcast ke item_<id>)
  auction_ended      : lelang berakhir (broadcast ke item_<id>)
  notification       : notif personal (ke user_<id>)
"""
from flask import current_app
from flask_socketio import emit, join_room, leave_room

from app import socketio


@socketio.on('connect')
def on_connect():
    try:
        current_app.logger.info('[SocketIO] client connected')
    except Exception:
        pass
    emit('connected', {'message': 'Terhubung ke ByteBid real-time server'})


@socketio.on('disconnect')
def on_disconnect():
    try:
        current_app.logger.info('[SocketIO] client disconnected')
    except Exception:
        pass


@socketio.on('join_item')
def on_join_item(data):
    item_id = (data or {}).get('item_id')
    if not item_id:
        return
    join_room(f'item_{item_id}')
    emit('joined', {'room': f'item_{item_id}'})


@socketio.on('leave_item')
def on_leave_item(data):
    item_id = (data or {}).get('item_id')
    if not item_id:
        return
    leave_room(f'item_{item_id}')


@socketio.on('join_user')
def on_join_user(data):
    user_id = (data or {}).get('user_id')
    if not user_id:
        return
    join_room(f'user_{user_id}')
    emit('joined', {'room': f'user_{user_id}'})
