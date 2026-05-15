# 🚀 ByteBid - Run Backend + Frontend Bersama

Setelah backend & frontend terintegrasi, ini cara menjalankannya bersama.

## Struktur Akhir Project

```
bytebid/
├── bytebid-backend/     ← Flask API + MySQL + Socket.IO (port 5000)
│   ├── app/
│   ├── config.py
│   ├── run.py
│   ├── seed.py
│   └── requirements.txt
└── bytebid-frontend/    ← Flask templates + JS (port 8000)
    ├── app.py            ← Sudah TIPIS, hanya render template
    ├── static/bytebid.js ← API client + auth helpers
    ├── templates/        ← 12 halaman, semua fetch ke backend
    └── requirements.txt
```

## Cara Menjalankan (2 Terminal)

### Terminal 1 — Backend

```bash
cd bytebid-backend
python -m venv venv
source venv/bin/activate     # Linux/Mac
# venv\Scripts\activate      # Windows
pip install -r requirements.txt
cp .env.example .env

# Pastikan XAMPP MySQL aktif & buat database
# Di phpMyAdmin: CREATE DATABASE bytebid;

python seed.py               # populate 9 barang & 3 user
python run.py                # → http://localhost:5000
```

### Terminal 2 — Frontend

```bash
cd bytebid-frontend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

python app.py                # → http://localhost:8000
```

### Akses

Buka browser → `http://localhost:8000`

## Akun Demo

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | Admin (bisa akses /admin) |
| `demo` | `demo123` | User biasa |
| `lionel` | `lionel123` | User biasa |

Login bisa pakai username **atau** email.

## Cara Tes Real-Time Bidding

1. Buka 2 browser/incognito tab
2. Tab A: login sebagai `demo`, buka `/pantau/1`
3. Tab B: login sebagai `lionel`, buka `/ajukan/1`
4. Di Tab B: ajukan bid — lihat Tab A update real-time tanpa refresh

## Yang Sudah Terintegrasi

✅ **Auth** — register/login/forgot dengan JWT, login pakai username atau email  
✅ **Bidding** — submit via API, validasi increment Rp 100k server-side  
✅ **Real-time** — Socket.IO push `bid_update`, `auction_ended`, `notification`  
✅ **Notifikasi** — outbid otomatis ke user yang dilampaui  
✅ **Admin Panel** — CRUD barang + upload gambar + dashboard statistik  
✅ **Auto-end** — APScheduler tutup lelang otomatis sesuai timer  
✅ **Email pemenang** — kirim email saat lelang berakhir (atau log console kalau MAIL belum dikonfigurasi)  

## Push ke GitHub

Lihat `bytebid-backend/GITHUB_PR_GUIDE.md` untuk panduan langkah-langkah git push & buat PR. Strategi yang direkomendasikan:

```bash
# Di root project (parent folder bytebid-backend & bytebid-frontend)
git init
git add .
git commit -m "feat: backend Flask + MySQL + frontend terintegrasi via API

Backend:
- 12 SKPL functional requirements terimplementasi
- MySQL via SQLAlchemy + JWT auth + bcrypt
- Socket.IO real-time bidding
- APScheduler auto-end auction
- Admin CRUD barang + upload gambar

Frontend:
- app.py thin (hanya render template)
- bytebid.js: API client + auth state management
- 12 halaman terhubung backend via fetch + Socket.IO
- Halaman baru: /forgot-password, /notifications, /admin"

git remote add origin https://github.com/<username>/bytebid.git
git branch -M main
git push -u origin main
```

## Production Notes

- Ganti `SECRET_KEY` & `JWT_SECRET_KEY` di `.env` backend
- Pakai WSGI server (gunicorn + eventlet) untuk Socket.IO production
- Setup MySQL password & user khusus aplikasi (jangan pakai `root`)
- Konfigurasi Gmail App Password untuk email pemenang
- HTTPS di reverse proxy (nginx)
- Update `API_BASE_URL` di frontend ke domain production
