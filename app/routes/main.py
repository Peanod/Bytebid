"""
Main web routes — melayani halaman HTML dengan Jinja templates.
Menggunakan Flask session untuk autentikasi user (sederhana, sesuai SKPL-BB-N3).
"""
import os
import re
import uuid
from decimal import Decimal, InvalidOperation
from datetime import datetime
from functools import wraps

from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, flash, jsonify, current_app, send_from_directory)

from app import db, socketio
from app.models import (User, Item, AuctionStatus, Bid,
                        Notification, NotificationType, PasswordResetToken)
from app.services.auction_service import (place_bid_for_user,
                                          BidError)

main_bp = Blueprint('main', __name__)

USERNAME_RE = re.compile(r'^[a-zA-Z0-9_]{3,30}$')
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


# ── Helpers ────────────────────────────────────────────────────────────────────

def _current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    return User.query.get(uid)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            flash('Silakan masuk terlebih dahulu.', 'error')
            return redirect(url_for('main.login', next=request.path))
        return view(*args, **kwargs)
    return wrapped


@main_bp.app_context_processor
def inject_globals():
    user = _current_user()
    unread_count = 0
    if user:
        unread_count = Notification.query.filter_by(
            user_id=user.id, is_read=False).count()
    return {
        'current_user': user,
        'now': datetime.utcnow(),
        'unread_notif_count': unread_count,
    }


# ── Public pages ───────────────────────────────────────────────────────────────

@main_bp.route('/')
def index():
    items = (Item.query
             .filter(Item.status == AuctionStatus.ACTIVE,
                     Item.deleted_at.is_(None))
             .order_by(Item.created_at.desc())
             .limit(6).all())
    return render_template('index.html', items=items)


@main_bp.route('/lelang')
def lelang():
    cat = request.args.get('cat', 'Semua')
    q = (request.args.get('q') or '').strip()

    query = Item.query.filter(Item.status == AuctionStatus.ACTIVE,
                              Item.deleted_at.is_(None))
    if cat and cat != 'Semua':
        query = query.filter(Item.category == cat)
    if q:
        like = f'%{q}%'
        query = query.filter(Item.name.ilike(like))
    items = query.order_by(Item.end_time.asc()).all()

    return render_template('lelang.html',
                           items=items, active_cat=cat, query=q)


@main_bp.route('/cara-kerja')
def cara_kerja():
    return render_template('cara_kerja.html')


@main_bp.route('/tentang')
def tentang():
    return render_template('tentang.html')


# ── Auth pages (web, session-based) ────────────────────────────────────────────

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = (request.form.get('username') or
                    (request.form.get('email') or '').split('@')[0]).strip().lower()
        name = (request.form.get('name') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''

        # Sanitasi auto-username dari email kalau perlu
        username = re.sub(r'[^a-zA-Z0-9_]', '', username) or username
        if not USERNAME_RE.match(username):
            username = (username + '_user')[:30]

        if not name or len(name) < 2:
            return render_template('register.html', error='Nama lengkap minimal 2 karakter.')
        if not EMAIL_RE.match(email):
            return render_template('register.html', error='Format email tidak valid.')
        if len(password) < 8:
            return render_template('register.html', error='Password minimal 8 karakter.')

        if User.query.filter_by(email=email).first():
            return render_template('register.html', error='Email sudah terdaftar.')
        # username unik — tambah suffix kalau bentrok
        base = username
        i = 1
        while User.query.filter_by(username=username).first():
            i += 1
            username = f'{base}{i}'

        user = User(username=username, name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id
        session['user_name'] = user.name
        session['is_admin'] = user.is_admin
        flash(f'Selamat datang, {user.name}! Akun berhasil dibuat.', 'success')
        return redirect(url_for('main.lelang'))

    return render_template('register.html')


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = (request.form.get('identifier') or
                      request.form.get('email') or
                      request.form.get('username') or '').strip().lower()
        password = request.form.get('password') or ''

        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()
        if not user or not user.check_password(password):
            return render_template('login.html',
                                   error='Username/email atau password salah.')

        session['user_id'] = user.id
        session['user_name'] = user.name
        session['is_admin'] = user.is_admin
        # Admin diarahkan ke dashboard admin, user biasa ke katalog lelang
        default_url = url_for('main.admin_dashboard') if user.is_admin else url_for('main.lelang')
        next_url = request.args.get('next') or default_url
        flash(f'Selamat datang kembali, {user.name}!', 'success')
        return redirect(next_url)

    return render_template('login.html')


@main_bp.route('/logout')
def logout():
    session.clear()
    flash('Anda telah keluar dari sistem.', 'info')
    return redirect(url_for('main.index'))


@main_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        identifier = (request.form.get('identifier') or
                      request.form.get('email') or '').strip().lower()
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        # Jangan bocorkan keberadaan akun
        if user:
            tok = PasswordResetToken.create_for(user)
            db.session.add(tok)
            db.session.commit()
            try:
                from app.services.email_service import send_password_reset_email
                send_password_reset_email(user, tok.token)
            except Exception as e:
                current_app.logger.warning(f'Email reset gagal terkirim: {e}')
            # Untuk demo: tampilkan link reset langsung
            reset_link = url_for('main.reset_password',
                                 token=tok.token, _external=True)
            return render_template('forgot.html',
                                   message='Tautan reset password telah dibuat.',
                                   reset_link=reset_link)

        return render_template('forgot.html',
                               message='Jika akun terdaftar, instruksi reset telah dikirim.')

    return render_template('forgot.html')


@main_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    tok = PasswordResetToken.query.filter_by(token=token).first()
    if not tok or not tok.is_valid:
        return render_template('forgot.html',
                               error='Tautan reset tidak valid atau sudah kadaluarsa.')

    if request.method == 'POST':
        new_pwd = request.form.get('password') or ''
        if len(new_pwd) < 8:
            return render_template('reset.html', token=token,
                                   error='Password minimal 8 karakter.')
        tok.user.set_password(new_pwd)
        tok.used = True
        db.session.commit()
        flash('Password berhasil direset. Silakan login.', 'success')
        return redirect(url_for('main.login'))

    return render_template('reset.html', token=token)


# ── Bidding flow (web) ─────────────────────────────────────────────────────────

@main_bp.route('/ajukan/<int:item_id>', methods=['GET', 'POST'])
@login_required
def ajukan(item_id):
    item = Item.query.get_or_404(item_id)
    user = _current_user()

    if request.method == 'POST':
        try:
            amount = Decimal(str(request.form.get('amount', '0')))
        except InvalidOperation:
            return render_template('ajukan.html', item=item,
                                   error='Nilai penawaran tidak valid.')

        try:
            bid = place_bid_for_user(user, item, amount)
        except BidError as e:
            return render_template('ajukan.html', item=item, error=str(e))

        return redirect(url_for('main.konfirmasi', item_id=item.id,
                                bid_amount=int(bid.amount)))

    return render_template('ajukan.html', item=item)


@main_bp.route('/konfirmasi/<int:item_id>')
@login_required
def konfirmasi(item_id):
    item = Item.query.get_or_404(item_id)
    bid_amount = request.args.get('bid_amount', type=int) or int(item.current_bid)
    return render_template('konfirmasi.html', item=item, bid_amount=bid_amount)


@main_bp.route('/pantau/<int:item_id>')
@login_required
def pantau(item_id):
    item = Item.query.get_or_404(item_id)
    user = _current_user()
    bids = item.bids.limit(50).all()
    my_top = (Bid.query.filter_by(item_id=item.id, user_id=user.id)
              .order_by(Bid.amount.desc()).first())
    return render_template('pantau.html', item=item, bids=bids, my_top=my_top)


# ── Notifications page ────────────────────────────────────────────────────────

@main_bp.route('/notifications')
@login_required
def notifications():
    user = _current_user()
    notifs = (Notification.query.filter_by(user_id=user.id)
              .order_by(Notification.created_at.desc()).limit(100).all())
    # Mark all as read on view
    Notification.query.filter_by(user_id=user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return render_template('notifications.html', notifs=notifs)


# ── Profil Akun ────────────────────────────────────────────────────────────────

@main_bp.route('/profil')
@login_required
def profil():
    """
    Halaman profil pribadi user:
    - Detail akun (nama, username, email, role, tanggal bergabung)
    - Statistik (total bid, lelang dimenangkan, penawaran aktif)
    - Daftar lelang yang dimenangkan + tombol Claim
    """
    user = _current_user()

    # Semua item yang dimenangkan user ini (status ENDED, winner_id = user.id)
    won_items = (Item.query
                 .filter_by(winner_id=user.id, status=AuctionStatus.ENDED)
                 .filter(Item.deleted_at.is_(None))
                 .order_by(Item.end_time.desc())
                 .all())

    # Hitung statistik
    total_bids = Bid.query.filter_by(user_id=user.id).count()
    active_bids = (Bid.query
                   .join(Item)
                   .filter(Bid.user_id == user.id,
                           Item.status == AuctionStatus.ACTIVE,
                           Item.deleted_at.is_(None))
                   .count())

    # Ambil id item yang SUDAH di-claim dari session
    claimed_ids = set(session.get('claimed_item_ids', []))
    unclaimed   = sum(1 for it in won_items if it.id not in claimed_ids)

    return render_template(
        'profil.html',
        won_items=won_items,
        total_bids=total_bids,
        active_bids=active_bids,
        claimed_ids=claimed_ids,
        unclaimed=unclaimed,
    )


# ── Claim Kemenangan ───────────────────────────────────────────────────────────

@main_bp.route('/claim', methods=['POST'])
@login_required
def claim_item():
    """
    Proses klaim hadiah lelang yang dimenangkan.
    Menerima form data: item_id, recipient_name, phone, address, city,
                        postal_code, notes (opsional).
    Menyimpan id item di session['claimed_item_ids'] sebagai tanda sudah diklaim.
    Juga membuat notifikasi konfirmasi untuk user.
    """
    user = _current_user()
    item_id = request.form.get('item_id', type=int)

    if not item_id:
        flash('Data klaim tidak valid.', 'error')
        return redirect(url_for('main.profil'))

    item = Item.query.get(item_id)
    if not item or item.winner_id != user.id:
        flash('Anda bukan pemenang lelang ini.', 'error')
        return redirect(url_for('main.profil'))

    # Tandai sebagai sudah diklaim di session
    claimed = list(session.get('claimed_item_ids', []))
    if item_id not in claimed:
        claimed.append(item_id)
    session['claimed_item_ids'] = claimed
    session.modified = True

    # Buat notifikasi konfirmasi klaim
    recipient_name = (request.form.get('recipient_name') or user.name).strip()
    city           = (request.form.get('city') or '').strip()

    notif = Notification(
        user_id = user.id,
        item_id = item.id,
        type    = NotificationType.WIN,
        title   = '🎉 Klaim Berhasil!',
        message = (
            f'Klaim untuk "{item.name}" telah kami terima. '
            f'Pengiriman ke {recipient_name}, {city}. '
            'Tim kami akan menghubungi Anda dalam 1×24 jam.'
        ),
    )
    db.session.add(notif)
    db.session.commit()

    # Kirim notifikasi real-time via Socket.IO jika tersedia
    try:
        socketio.emit('notification', {
            'title':   notif.title,
            'message': notif.message,
        }, room=f'user_{user.id}')
    except Exception:
        pass

    return redirect(url_for('main.profil', claimed=1))


# ── Admin dashboard (web) ──────────────────────────────────────────────────────

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('main.login', next=request.path))
        if not session.get('is_admin'):
            flash('Akses ditolak. Hanya admin.', 'error')
            return redirect(url_for('main.index'))
        return view(*args, **kwargs)
    return wrapped


def _save_uploaded_image(file_storage):
    """Simpan file gambar yang diupload, return path relatif atau None."""
    if not file_storage or not file_storage.filename:
        return None
    ext = file_storage.filename.rsplit('.', 1)[-1].lower()
    if ext not in current_app.config['ALLOWED_EXTENSIONS']:
        return None
    upload_dir = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)
    fname = f"{uuid.uuid4().hex}.{ext}"
    file_storage.save(os.path.join(upload_dir, fname))
    return f'/uploads/{fname}'


@main_bp.route('/admin', methods=['GET', 'POST'])
@admin_required
def admin_dashboard():
    if request.method == 'POST':
        action = request.form.get('action')

        # ── CREATE ─────────────────────────────────────────────────────────
        if action == 'create_item':
            from datetime import timedelta
            try:
                start_price = Decimal(str(request.form.get('start_price', '0')))
            except InvalidOperation:
                flash('Harga awal tidak valid.', 'error')
                return redirect(url_for('main.admin_dashboard'))
            duration = int(request.form.get('duration_minutes',
                          current_app.config['DEFAULT_AUCTION_DURATION_MINUTES']))

            # ── Handle upload gambar ────────────────────────────────────────
            image_path = ''
            image_file = request.files.get('image')
            if image_file and image_file.filename:
                saved = _save_uploaded_image(image_file)
                if saved:
                    image_path = saved
                else:
                    flash('Format gambar tidak didukung. Gunakan PNG, JPG, JPEG, GIF, atau WEBP.', 'error')
                    return redirect(url_for('main.admin_dashboard', tab='create'))

            item = Item(
                name=(request.form.get('name') or '').strip() or 'Tanpa Nama',
                description=request.form.get('description', ''),
                condition=request.form.get('condition', ''),
                category=request.form.get('category', 'Lainnya'),
                image=image_path,
                start_price=start_price,
                current_bid=start_price,
                status=AuctionStatus.ACTIVE,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(minutes=duration),
                created_by=session['user_id'],
            )
            db.session.add(item)
            db.session.commit()
            flash(f'Barang "{item.name}" berhasil dilelang.', 'success')

        # ── CANCEL (lelang dibatalkan, item tetap terlihat) ────────────────
        elif action == 'cancel_item':
            iid = int(request.form.get('item_id', 0))
            it = Item.query.get(iid)
            if it:
                it.status = AuctionStatus.CANCELLED
                db.session.commit()
                flash(f'Lelang "{it.name}" dibatalkan.', 'info')

        # ── SOFT DELETE (masuk Trash) ──────────────────────────────────────
        elif action == 'trash_item':
            iid = int(request.form.get('item_id', 0))
            it = Item.query.get(iid)
            if it:
                it.deleted_at = datetime.utcnow()
                db.session.commit()
                flash(f'Barang "{it.name}" dipindahkan ke Trash.', 'info')

        # ── RESTORE dari Trash ─────────────────────────────────────────────
        elif action == 'restore_item':
            iid = int(request.form.get('item_id', 0))
            it = Item.query.get(iid)
            if it:
                it.deleted_at = None
                db.session.commit()
                flash(f'Barang "{it.name}" berhasil dipulihkan.', 'success')

        # ── HARD DELETE (hapus permanen) ───────────────────────────────────
        elif action == 'hard_delete_item':
            iid = int(request.form.get('item_id', 0))
            it = Item.query.get(iid)
            if it:
                name = it.name
                db.session.delete(it)
                db.session.commit()
                flash(f'Barang "{name}" dihapus permanen.', 'info')

        # ── KOSONGKAN TRASH ────────────────────────────────────────────────
        elif action == 'empty_trash':
            cnt = Item.query.filter(Item.deleted_at.isnot(None)).delete(
                synchronize_session=False)
            db.session.commit()
            flash(f'Trash dikosongkan ({cnt} barang dihapus permanen).', 'info')

        return redirect(url_for('main.admin_dashboard',
                                tab=request.form.get('tab', 'items')))

    tab = request.args.get('tab', 'items')
    items = (Item.query.filter(Item.deleted_at.is_(None))
             .order_by(Item.created_at.desc()).all())
    trashed = (Item.query.filter(Item.deleted_at.isnot(None))
               .order_by(Item.deleted_at.desc()).all())
    stats = {
        'total_items': Item.query.filter(Item.deleted_at.is_(None)).count(),
        'active_items': Item.query.filter(
            Item.status == AuctionStatus.ACTIVE,
            Item.deleted_at.is_(None)).count(),
        'ended_items': Item.query.filter(
            Item.status == AuctionStatus.ENDED,
            Item.deleted_at.is_(None)).count(),
        'trashed_items': len(trashed),
        'total_users': User.query.count(),
        'total_bids': Bid.query.count(),
    }
    return render_template('admin.html',
                           items=items, trashed=trashed,
                           stats=stats, active_tab=tab)


# ── Admin: Edit item (form terpisah) ─────────────────────────────────────────
@main_bp.route('/admin/items/<int:item_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_item(item_id):
    item = Item.query.get_or_404(item_id)

    if request.method == 'POST':
        from datetime import timedelta
        try:
            start_price = Decimal(str(request.form.get('start_price', item.start_price)))
        except InvalidOperation:
            return render_template('edit_item.html', item=item,
                                   error='Harga awal tidak valid.')

        item.name = (request.form.get('name') or item.name).strip()
        item.category = request.form.get('category', item.category)
        item.condition = request.form.get('condition', item.condition or '')
        item.description = request.form.get('description', item.description or '')
        item.image = request.form.get('image_url', item.image or '')
        item.start_price = start_price
        # current_bid tidak diturunkan; hanya naik kalau start_price lebih tinggi
        if item.current_bid < start_price:
            item.current_bid = start_price

        # Perpanjang/persingkat durasi
        try:
            extra_min = int(request.form.get('extend_minutes', '0'))
            if extra_min:
                item.end_time = item.end_time + timedelta(minutes=extra_min)
        except ValueError:
            pass

        # Update status
        new_status = request.form.get('status')
        if new_status:
            try:
                item.status = AuctionStatus(new_status)
            except ValueError:
                pass

        item.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f'Barang "{item.name}" berhasil diperbarui.', 'success')
        return redirect(url_for('main.admin_dashboard'))

    return render_template('edit_item.html', item=item)


# ── Health & static helper ────────────────────────────────────────────────────

@main_bp.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'ByteBid', 'version': '1.0.0'})


@main_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)