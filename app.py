"""
ByteBid Frontend (Flask templates) — terhubung ke backend API
Kelompok 08 - RPL Teknik Komputer UNDIP 2026

Server ini hanya melayani halaman HTML.
Semua data dimuat via fetch() ke backend API (default http://localhost:5000).
"""
import os
from flask import Flask, render_template
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'bytebid-frontend-2026')

# URL backend API — frontend & backend bisa beda host/port
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')


@app.context_processor
def inject_globals():
    """Variabel yang tersedia di semua template."""
    return {'API_BASE_URL': API_BASE_URL}


# ── Halaman ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/lelang')
def lelang():
    return render_template('lelang.html')


@app.route('/cara-kerja')
def cara_kerja():
    return render_template('cara_kerja.html')


@app.route('/tentang')
def tentang():
    return render_template('tentang.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot.html')


@app.route('/ajukan/<int:item_id>')
def ajukan(item_id):
    return render_template('ajukan.html', item_id=item_id)


@app.route('/konfirmasi/<int:item_id>')
def konfirmasi(item_id):
    return render_template('konfirmasi.html', item_id=item_id)


@app.route('/pantau/<int:item_id>')
def pantau(item_id):
    return render_template('pantau.html', item_id=item_id)


@app.route('/notifications')
def notifications():
    return render_template('notifications.html')


@app.route('/admin')
def admin_dashboard():
    return render_template('admin.html')


if __name__ == '__main__':
    print(f"\n🌐 ByteBid Frontend → http://localhost:8000")
    print(f"🔗 API Backend       → {API_BASE_URL}\n")
    app.run(host='0.0.0.0', port=8000, debug=True)
