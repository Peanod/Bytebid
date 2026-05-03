from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.secret_key = 'bytebid_secret_2026'

# ── Mock Data ──────────────────────────────────────────────────────────────────
items = [
    {
        'id': 1, 'name': 'MG 1/100 Barbatos Lupus Rex Bandai', 'category': 'Seni',
        'condition': 'Kondisi Baru/New - Garansi Aktif',
        'image': 'https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhM6dxBSs0TsE7ZC-SeLnD35H5cpB8GHXPjKkUHzrj2Otm18Oz5AEn52ikaear5mG8L2uU6AUZtTJkP-jg4LCfYtRdhjySARqInB0uCJbJMBEgrZEGXPuSGP0pekxikfKQZeEFPEOK11emiIGT2b5Lqrf-AdEai05hQmquulxns7VtI2OP9myapAn5psA/s16000-rw/mg%20barbatos%20lupus%20rex%20box%20art.jpg',
        'current_bid': 16500000, 'start_price': 12000000,
        'bids': [
            {'user': 'Anda', 'amount': 19000000, 'time': '13.00', 'initial': 'AF'},
            {'user': 'A***r', 'amount': 18400000, 'time': '12.08', 'initial': 'AR'},
            {'user': 'R***j', 'amount': 17800000, 'time': '11.25', 'initial': 'Ri'},
            {'user': 'L***o', 'amount': 17000000, 'time': '10.59', 'initial': 'LO'},
        ],
        'timer': '02:19:50', 'badge': 'Segera Berakhir', 'active': True
    },
    {
        'id': 2, 'name': 'iPhone 15 Pro Max', 'category': 'Elektronik',
        'condition': 'Kondisi 98% - Box Lengkap',
        'image': 'https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-15-pro-finish-select-202309-6-7inch-naturaltitanium?wid=5120&hei=2880&fmt=p-jpg&qlt=80&.v=1692846352658',
        'current_bid': 14200000, 'start_price': 10000000,
        'bids': [], 'timer': '05:37:44', 'badge': 'Baru Ditambahkan', 'active': True
    },
    {
        'id': 3, 'name': 'Honda Brio 2012', 'category': 'Kendaraan',
        'condition': 'Plat B Genap - 12.000 KM',
        'image': 'https://imgcdn.oto.com/medium/gallery/exterior/46/1085/honda-brio-front-angle-low-view-633474.jpg',
        'current_bid': 95500000, 'start_price': 80000000,
        'bids': [], 'timer': '04:45:57', 'badge': 'Baru Ditambahkan', 'active': True
    },
    {
        'id': 4, 'name': 'Adiputro Jetbus 3+ SHD 2017', 'category': 'Kendaraan',
        'condition': 'Mercy OH 1836 - 50 Seat',
        'image': 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/Mercedes-Benz_O_500_RS_Adiputro_Jetbus_3%2B_SHD_%28Rosalia_Indah%2C_B_7552_UZ%29_@_Boyolali.jpg/1280px-Mercedes-Benz_O_500_RS_Adiputro_Jetbus_3%2B_SHD_%28Rosalia_Indah%2C_B_7552_UZ%29_@_Boyolali.jpg',
        'current_bid': 730500000, 'start_price': 600000000,
        'bids': [], 'timer': '06:55:80', 'badge': 'Baru Ditambahkan', 'active': True
    },
    {
        'id': 5, 'name': 'Toyota Calya 1.2 E M/T', 'category': 'Kendaraan',
        'condition': 'Clean & Clear - 24.000 KM',
        'image': 'https://imgcdn.oto.com/medium/gallery/exterior/38/1316/toyota-calya-front-angle-low-view-636041.jpg',
        'current_bid': 145000000, 'start_price': 120000000,
        'bids': [], 'timer': '01:00:56', 'badge': 'Segera Berakhir', 'active': True
    },
    {
        'id': 6, 'name': 'Photocard Mark NCT + Album', 'category': 'Seni',
        'condition': 'Mulus no minus - Freebies',
        'image': 'https://images.unsplash.com/photo-1618160702438-9b02ab6515c9?w=400',
        'current_bid': 875000, 'start_price': 500000,
        'bids': [], 'timer': '02:04:08', 'badge': 'Segera Berakhir', 'active': True
    },
    {
        'id': 7, 'name': 'Sony A7 IV Mirrorless', 'category': 'Elektronik',
        'condition': 'Kondisi 90% - Lensa Kit',
        'image': 'https://www.bhphotovideo.com/images/images2500x2500/sony_ilce_7m4k_b_alpha_a7_iv_mirrorless_1668428.jpg',
        'current_bid': 22000000, 'start_price': 18000000,
        'bids': [], 'timer': '05:11:22', 'badge': 'Segera Berakhir', 'active': True
    },
    {
        'id': 8, 'name': 'Jersey Barcelona Messi', 'category': 'Seni',
        'condition': '2014/2015 - Autentik',
        'image': 'https://images.unsplash.com/photo-1579952363873-27f3bade9f55?w=400',
        'current_bid': 50500000, 'start_price': 40000000,
        'bids': [], 'timer': '09:42:37', 'badge': 'Baru Ditambahkan', 'active': True
    },
    {
        'id': 9, 'name': 'Lukisan Kuda Api Pak SBY', 'category': 'Seni',
        'condition': 'Kondisi 100% - Historical',
        'image': 'https://images.unsplash.com/photo-1547036967-23d11aacaee0?w=400',
        'current_bid': 1200550000, 'start_price': 1000000000,
        'bids': [], 'timer': '09:58:45', 'badge': 'Segera Berakhir', 'active': True
    },
]

users = [
    {'id': 1, 'name': 'Demo User', 'email': 'demo@bytebid.id', 'password': 'demo123'}
]

def format_rupiah(amount):
    return f"Rp{amount:,.0f}".replace(',', '.')

app.jinja_env.filters['rupiah'] = format_rupiah


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html', items=items[:3])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        for u in users:
            if u['email'] == email:
                return render_template('register.html', error='Email sudah terdaftar.')
        new_user = {'id': len(users)+1, 'name': name, 'email': email, 'password': password}
        users.append(new_user)
        session['user_id'] = new_user['id']
        session['user_name'] = name
        return redirect(url_for('lelang'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        for u in users:
            if u['email'] == email and u['password'] == password:
                session['user_id'] = u['id']
                session['user_name'] = u['name']
                return redirect(url_for('lelang'))
        return render_template('login.html', error='Email atau password salah.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/lelang')
def lelang():
    cat = request.args.get('cat', 'Semua')
    q = request.args.get('q', '')
    filtered = items
    if cat != 'Semua':
        filtered = [i for i in filtered if i['category'] == cat]
    if q:
        filtered = [i for i in filtered if q.lower() in i['name'].lower()]
    return render_template('lelang.html', items=filtered, active_cat=cat, query=q)

@app.route('/cara-kerja')
def cara_kerja():
    faqs = [
        {'q': 'Apakah penawaran bisa dibatalkan?', 'a': 'Penawaran yang sudah diajukan bersifat final dan tidak bisa dibatalkan. Pastikan kamu sudah yakin sebelum mengkonfirmasi penawaran.'},
        {'q': 'Bagaimana jika ada dua penawar dengan harga sama?', 'a': 'Penawar yang terlebih dahulu mengajukan harga tersebut yang dinyatakan sebagai pemenang. Sistem mencatat timestamp setiap penawaran secara real-time.'},
        {'q': 'Bagaimana proses pengiriman barang?', 'a': 'Setelah memenangkan lelang, penjual akan menghubungi dalam 24 jam untuk mengatur pengiriman. ByteBid menggunakan layanan ekspedisi terpercaya.'},
        {'q': 'Apakah ada biaya tambahan?', 'a': 'Pendaftaran dan melihat lelang gratis. ByteBid mengambil komisi 2% dari nilai transaksi yang berhasil sebagai biaya layanan platform.'},
        {'q': 'Berapa kenaikan minimum penawaran?', 'a': 'Setiap penawaran baru harus minimal Rp 100.000 lebih tinggi dari penawaran tertinggi yang sedang berlaku.'},
        {'q': 'Apa yang terjadi jika saya tidak melanjutkan setelah menang?', 'a': 'Sistem akan mencatat meyamai kemenangan kamu. Penyelesaian transaksi boleh langsung bersama penjual dan penjual secara langsung.'},
        {'q': 'Apakah saya harus bayar untuk mulai menawar?', 'a': 'Tidak. Pendaftaran dan menawar di ByteBid sepenuhnya gratis. Proses pembayaran hanya dilakukan di luar sistem setelah pemenang ditentukan.'},
        {'q': 'Bisakah saya membatalkan penawaran yang sudah masuk?', 'a': 'Tidak. Penawaran yang sudah diajukan bersifat final dan tidak dapat dibatalkan setelah dikonfirmasi oleh sistem.'},
    ]
    return render_template('cara_kerja.html', faqs=faqs)

@app.route('/tentang')
def tentang():
    team = [
        {'initial': 'AZ', 'name': 'ANINDYA FAIRUZ AZ ZAHRA', 'role': 'UI/UX', 'nim': 'NIM 21120124120018', 'color': '#e74c3c'},
        {'initial': 'FN', 'name': 'FINODI', 'role': 'Programmer', 'nim': 'NIM 21120124140138', 'color': '#3498db'},
        {'initial': 'GT', 'name': 'GOTARA PARASDYA ABIMANYU', 'role': 'Project Manager', 'nim': 'NIM 21120124140157', 'color': '#2ecc71'},
        {'initial': 'LJ', 'name': 'LIONEL JEREMI PINONDANG S.', 'role': 'Programmer', 'nim': 'NIM 21120124130067', 'color': '#9b59b6'},
    ]
    return render_template('tentang.html', team=team)

@app.route('/ajukan/<int:item_id>', methods=['GET', 'POST'])
def ajukan(item_id):
    item = next((i for i in items if i['id'] == item_id), None)
    if not item:
        return redirect(url_for('lelang'))
    if not session.get('user_id'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        amount = int(request.form.get('amount', 0))
        if amount > item['current_bid']:
            item['current_bid'] = amount
            item['bids'].insert(0, {
                'user': 'Anda', 'amount': amount,
                'time': datetime.now().strftime('%H.%M'), 'initial': 'AF'
            })
            return redirect(url_for('konfirmasi', item_id=item_id, amount=amount))
        return render_template('ajukan.html', item=item, error='Penawaran harus lebih tinggi dari harga saat ini.')
    return render_template('ajukan.html', item=item)

@app.route('/konfirmasi/<int:item_id>')
def konfirmasi(item_id):
    item = next((i for i in items if i['id'] == item_id), None)
    amount = request.args.get('amount', 0)
    return render_template('konfirmasi.html', item=item, amount=int(amount))

@app.route('/pantau/<int:item_id>')
def pantau(item_id):
    item = next((i for i in items if i['id'] == item_id), None)
    if not item:
        return redirect(url_for('lelang'))
    return render_template('pantau.html', item=item)

@app.route('/api/bid/<int:item_id>', methods=['POST'])
def api_bid(item_id):
    item = next((i for i in items if i['id'] == item_id), None)
    if not item:
        return jsonify({'success': False, 'message': 'Item not found'}), 404
    data = request.get_json()
    amount = data.get('amount', 0)
    if amount > item['current_bid']:
        item['current_bid'] = amount
        return jsonify({'success': True, 'new_price': amount})
    return jsonify({'success': False, 'message': 'Penawaran terlalu rendah'})

if __name__ == '__main__':
    app.run(debug=True)
