# 📤 Panduan Push & Pull Request ke GitHub

Karena saya tidak punya akses langsung ke akun GitHub kamu, ikuti langkah-langkah berikut untuk push backend ini sebagai Pull Request ke repo ByteBid.

## Skenario 1 — Repo ByteBid Sudah Ada di GitHub

### Langkah 1: Clone repo & buat branch baru

```bash
# Clone repo kelompok 08 (ganti URL sesuai repo asli)
git clone https://github.com/<org-atau-username>/bytebid.git
cd bytebid

# Buat branch baru untuk fitur backend
git checkout -b feat/backend-flask-mysql
```

### Langkah 2: Copy file backend ke repo

Copy seluruh isi folder `bytebid-backend/` (yang baru dibuat) ke dalam repo. Ada beberapa pilihan struktur:

**Opsi A — Backend di subfolder `backend/`** (rekomendasi kalau frontend Flask lama mau dipertahankan):
```bash
mkdir -p backend
cp -r /path/ke/bytebid-backend/* /path/ke/bytebid-backend/.* backend/
```

**Opsi B — Backend di root** (replace app.py lama):
```bash
# Backup dulu app.py lama
mv app.py app.py.legacy
# Copy file baru
cp -r /path/ke/bytebid-backend/* /path/ke/bytebid-backend/.* .
```

### Langkah 3: Commit & push

```bash
git add .
git status   # cek file apa saja yang akan di-commit

git commit -m "feat(backend): implementasi backend Flask + MySQL sesuai SKPL

- Implementasi 12 kebutuhan fungsional (SKPL-BB-01 s/d SKPL-BB-12)
- MySQL/XAMPP via SQLAlchemy + bcrypt password hashing
- JWT auth (login pakai username/email)
- Real-time bidding via Socket.IO
- Auto-end auction via APScheduler
- Email notifikasi pemenang
- Admin panel CRUD barang + upload gambar
- Reset password via token"

git push origin feat/backend-flask-mysql
```

### Langkah 4: Buka Pull Request

1. Buka GitHub di browser, pergi ke repo ByteBid
2. Akan muncul banner kuning: **"feat/backend-flask-mysql had recent pushes"** → klik **"Compare & pull request"**
3. Isi PR dengan template di bawah ini.

---

## Skenario 2 — Belum Ada Repo di GitHub

### Langkah 1: Buat repo baru di GitHub

1. Buka https://github.com/new
2. Repository name: `bytebid` atau `bytebid-rpl-kel08`
3. Description: `ByteBid - Sistem Lelang Berbasis Web | RPL Kelompok 08 UNDIP 2026`
4. **JANGAN** centang "Initialize with README" (karena local sudah ada)
5. Klik **Create repository**

### Langkah 2: Init git lokal & push

```bash
cd /path/ke/bytebid-backend

git init
git branch -M main
git add .
git commit -m "feat: initial backend implementation untuk ByteBid"

# Tambah remote (ganti dengan URL repo kamu)
git remote add origin https://github.com/<username>/bytebid.git
git push -u origin main

# Buat branch development & PR-able branch
git checkout -b feat/backend-flask-mysql
git push -u origin feat/backend-flask-mysql
```

### Langkah 3: Invite teman kelompok

GitHub repo → **Settings → Collaborators → Add people** untuk Anindya, Gotara, Finodi.

---

## 📝 Template Deskripsi Pull Request

Copy paste teks berikut ke deskripsi PR di GitHub:

```markdown
## Ringkasan
Implementasi backend Flask + MySQL untuk ByteBid berdasarkan dokumen SKPL (Modul 2) dan DPP (Modul 3) yang telah disusun Kelompok 08.

## Pemetaan Kebutuhan SKPL
| Kode | Deskripsi | Status |
|------|-----------|--------|
| SKPL-BB-01 | Registrasi sign up | ✅ `POST /api/auth/register` |
| SKPL-BB-02 | Autentikasi sign in | ✅ `POST /api/auth/login` (username/email) |
| SKPL-BB-03 | Reset forgot password | ✅ `POST /api/auth/forgot` & `/reset` |
| SKPL-BB-04 | Daftar barang lelang | ✅ `GET /api/items` |
| SKPL-BB-05 | Proses bidding | ✅ `POST /api/bids/<id>` |
| SKPL-BB-06 | Timer durasi lelang | ✅ APScheduler interval 10 detik |
| SKPL-BB-07 | Update real-time | ✅ Socket.IO `bid_update` |
| SKPL-BB-08 | Riwayat penawaran | ✅ Tabel `bids` |
| SKPL-BB-09 | Pemenang otomatis | ✅ `auction_service.end_auction()` |
| SKPL-BB-10 | Notifikasi hasil | ✅ Email + tabel `notifications` |
| SKPL-BB-11 | Kelola data barang | ✅ Admin CRUD + upload gambar |
| SKPL-BB-12 | Pantau lelang (admin) | ✅ `GET /api/admin/dashboard` |

## Stack
- **Flask 3** + Flask-SocketIO + Flask-JWT-Extended
- **MySQL** via XAMPP (SQLAlchemy + PyMySQL)
- **bcrypt** untuk hashing password (SKPL-BB-N3 Security)
- **APScheduler** untuk auto-end lelang
- **Flask-Mail** untuk notifikasi pemenang

## Cara Menjalankan
1. `pip install -r requirements.txt`
2. Buat database `bytebid` di phpMyAdmin
3. Copy `.env.example` → `.env`, sesuaikan kredensial DB
4. `python seed.py` (populate 9 barang & 3 user)
5. `python run.py` → server di `http://localhost:5000`

## Akun Default
- `admin / admin123` (admin)
- `demo / demo123`
- `lionel / lionel123`

## Test
Sudah diuji manual via Flask test client:
- Auth flow (register → login dengan username & email)
- Bidding (valid, lower, increment under 100k)
- Outbid notification ke peserta sebelumnya
- Admin endpoint (403 untuk non-admin, dashboard, CRUD)
- End auction → tentukan winner + push notif WIN/LOSE
- Forgot password (token-based reset)

## Catatan Reviewer
- Modul 4 (Implementasi & Pengujian) bisa dilanjutkan dengan integrasi backend ini
- ERD sudah dipetakan ke 5 tabel: `users`, `items`, `bids`, `notifications`, `password_reset_tokens`
- Email notifikasi otomatis fallback ke log console kalau `MAIL_USERNAME` kosong (dev-friendly)
```

---

## ✅ Checklist Sebelum PR

- [ ] `.env` **TIDAK** ikut di-commit (sudah ada di `.gitignore`)
- [ ] `app/static/uploads/` kosong (cuma `.gitkeep`)
- [ ] `requirements.txt` ter-update
- [ ] README ter-update dengan instruksi setup
- [ ] Sudah test `python seed.py` & `python run.py` di local
- [ ] Tag teman kelompok sebagai reviewer di PR

## 💡 Tips Tambahan

- Setelah PR di-merge, jangan lupa update branch lokal: `git pull origin main`
- Kalau ada konflik dengan `app.py` lama (frontend), diskusikan dulu dengan tim — apakah Flask lama jadi frontend templating atau backend full-API & frontend pisah React/Vue
- Untuk demo presentasi, kamu bisa pakai Postman/Thunder Client untuk test endpoint
