"""
Auth API JSON — SKPL-BB-01, SKPL-BB-02, SKPL-BB-03.

Endpoint:
  POST /api/auth/register   sign up
  POST /api/auth/login      sign in (username ATAU email)
  POST /api/auth/forgot     minta reset password
  POST /api/auth/reset      submit password baru
  GET  /api/auth/me         profile user yang sedang login (JWT)
"""
import re
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from app import db
from app.models import User, PasswordResetToken

auth_bp = Blueprint('auth', __name__)

USERNAME_RE = re.compile(r'^[a-zA-Z0-9_]{3,30}$')
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _err(msg, field=None, status=400):
    payload = {'success': False, 'message': msg}
    if field:
        payload['field'] = field
    return jsonify(payload), status


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip().lower()
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not username:
        username = re.sub(r'[^a-zA-Z0-9_]', '', email.split('@')[0])
    if not USERNAME_RE.match(username):
        return _err('Username harus 3-30 karakter (huruf, angka, underscore).', 'username')
    if not name or len(name) < 2:
        return _err('Nama lengkap minimal 2 karakter.', 'name')
    if not EMAIL_RE.match(email):
        return _err('Format email tidak valid.', 'email')
    if len(password) < 8:
        return _err('Password minimal 8 karakter.', 'password')

    if User.query.filter_by(username=username).first():
        return _err('Username sudah digunakan.', 'username')
    if User.query.filter_by(email=email).first():
        return _err('Email sudah terdaftar.', 'email')

    user = User(username=username, name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({
        'success': True,
        'message': 'Registrasi berhasil. Selamat datang di ByteBid!',
        'token': token,
        'user': user.to_dict(include_email=True),
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    identifier = (data.get('identifier') or data.get('username')
                  or data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not identifier or not password:
        return _err('Username/email dan password wajib diisi.')

    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier)
    ).first()

    if not user or not user.check_password(password):
        return _err('Username/email atau password salah.', status=401)

    token = create_access_token(identity=str(user.id))
    return jsonify({
        'success': True,
        'message': f'Selamat datang kembali, {user.name}!',
        'token': token,
        'user': user.to_dict(include_email=True),
    })


@auth_bp.route('/forgot', methods=['POST'])
def forgot_password():
    data = request.get_json() or {}
    identifier = (data.get('identifier') or data.get('email')
                  or data.get('username') or '').strip().lower()

    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier)
    ).first()

    if user:
        tok = PasswordResetToken.create_for(user)
        db.session.add(tok)
        db.session.commit()
        try:
            from app.services.email_service import send_password_reset_email
            send_password_reset_email(user, tok.token)
        except Exception as e:
            current_app.logger.warning(f'Email reset gagal terkirim: {e}')

    return jsonify({
        'success': True,
        'message': 'Jika akun terdaftar, instruksi reset password telah dikirim ke email.',
    })


@auth_bp.route('/reset', methods=['POST'])
def reset_password():
    data = request.get_json() or {}
    token_str = data.get('token') or ''
    new_password = data.get('password') or ''

    if len(new_password) < 8:
        return _err('Password minimal 8 karakter.')

    tok = PasswordResetToken.query.filter_by(token=token_str).first()
    if not tok or not tok.is_valid:
        return _err('Token reset tidak valid atau sudah kadaluarsa.')

    tok.user.set_password(new_password)
    tok.used = True
    db.session.commit()

    return jsonify({'success': True,
                    'message': 'Password berhasil direset. Silakan login kembali.'})


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return _err('User tidak ditemukan', status=404)
    return jsonify({'success': True, 'user': user.to_dict(include_email=True)})
