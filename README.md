# ByteBid Backend

> **Sistem Lelang Berbasis Web** — proyek Rekayasa Perangkat Lunak
> Kelompok 08, Teknik Komputer Universitas Diponegoro 2026

Backend ini diimplementasikan berdasarkan dokumen **SKPL** (Modul 2) dan **DPP** (Modul 3) yang sudah disusun kelompok. Setiap kebutuhan fungsional (SKPL-BB-XX) dipetakan langsung ke endpoint atau service di bawah.

## Stack Teknologi

| Komponen | Teknologi |
|----------|-----------|
| Framework | Flask 3 + Flask-SocketIO |
| Database | MySQL (XAMPP) via SQLAlchemy + PyMySQL |
| Auth | JWT (Flask-JWT-Extended) + bcrypt |
| Real-time | Socket.IO (push bid update & notifikasi) |
| Migrasi | Flask-Migrate (Alembic) |
| Email | Flask-Mail (SMTP Gmail) |
| Scheduler | APScheduler (auto-end lelang) |

## Pemetaan SKPL → Implementasi

| Kode | Deskripsi (SKPL) | Lokasi |
|------|------------------|--------|
| SKPL-BB-01 | Registrasi sign up pengguna | `POST /api/auth/register` |
| SKPL-BB-02 | Autentikasi sign in pengguna | `POST /api/auth/login` |
| SKPL-BB-03 | Reset forgot password akun | `POST /api/auth/forgot` & `/reset` |
| SKPL-BB-04 | Menampilkan daftar barang lelang | `GET /api/items` |
| SKPL-BB-05 | Melakukan proses bidding barang | `POST /api/bids/<item_id>` |
| SKPL-BB-06 | Menampilkan timer durasi lelang | `Item.timer_display` + scheduler |
| SKPL-BB-07 | Update harga lelang real-time | Socket.IO event `bid_update` |
| SKPL-BB-08 | Menyimpan riwayat aktivitas penawaran | Tabel `bids` |
| SKPL-BB-09 | Menentukan pemenang lelang otomatis | `auction_service.end_auction()` |
| SKPL-BB-10 | Mengirim notifikasi hasil lelang | `email_service` + tabel `notifications` |
| SKPL-BB-11 | Mengelola data barang (admin) | `POST/PUT/DELETE /api/admin/items` |
| SKPL-BB-12 | Memantau jalannya lelang (admin) | `GET /api/admin/dashboard` |
| SKPL-BB-N1 | Performance (delay max 1 detik) | Socket.IO push langsung |
| SKPL-BB-N3 | Security (enkripsi password) | bcrypt di `User.set_password()` |

## Setup

### 1. Prasyarat

- Python 3.10+
- XAMPP berjalan dengan Apache & **MySQL** aktif
- Buat database baru via phpMyAdmin (`http://localhost/phpmyadmin`):
  ```sql
  CREATE DATABASE bytebid CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
  ```

### 2. Install dependencies

```bash
git clone <repo-url>
cd bytebid-backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Konfigurasi environment

```bash
cp .env.example .env
# edit .env, sesuaikan DB_PASSWORD jika XAMPP MySQL pakai password
```

### 4. Buat tabel & seed data awal

```bash
python seed.py
```

Output:
```
[seed] Created 3 users
[seed] Created 9 items
[seed] ✓ Selesai. Akun login:
       admin / admin123  (admin)
       demo  / demo123
       lionel / lionel123
```

### 5. Jalankan server

```bash
python run.py
```

Server berjalan di `http://localhost:5000`.

## API Endpoints

### Auth
| Method | Path | Auth | Deskripsi |
|--------|------|------|-----------|
| POST | `/api/auth/register` | – | Body: `{username, name, email, password}` |
| POST | `/api/auth/login` | – | Body: `{identifier, password}` (identifier = username/email) |
| POST | `/api/auth/forgot` | – | Body: `{identifier}` |
| POST | `/api/auth/reset` | – | Body: `{token, password}` |
| GET | `/api/auth/me` | JWT | Profile user |

### Items
| Method | Path | Deskripsi |
|--------|------|-----------|
| GET | `/api/items` | Query: `?cat=Elektronik&q=iphone&page=1` |
| GET | `/api/items/<id>` | Detail + 20 bid terakhir |
| GET | `/api/items/categories` | Daftar kategori |

### Bids
| Method | Path | Auth | Deskripsi |
|--------|------|------|-----------|
| POST | `/api/bids/<item_id>` | JWT | Body: `{amount}` |
| GET | `/api/bids/item/<item_id>` | – | Riwayat bid |
| GET | `/api/bids/me` | JWT | Bid milik user |

### Notifications
| Method | Path | Auth | Deskripsi |
|--------|------|------|-----------|
| GET | `/api/notifications` | JWT | List + unread_count |
| POST | `/api/notifications/<id>/read` | JWT | Tandai dibaca |
| POST | `/api/notifications/read-all` | JWT | Tandai semua dibaca |

### Admin (perlu `is_admin = true`)
| Method | Path | Deskripsi |
|--------|------|-----------|
| POST | `/api/admin/items` | Tambah barang. Multipart untuk upload gambar. |
| PUT | `/api/admin/items/<id>` | Edit |
| DELETE | `/api/admin/items/<id>` | Hapus |
| POST | `/api/admin/items/<id>/cancel` | Batalkan lelang |
| POST | `/api/admin/items/<id>/end` | Akhiri lelang manual |
| GET | `/api/admin/dashboard` | Statistik |

## WebSocket (Real-Time)

```js
const socket = io('http://localhost:5000');

socket.emit('join_item', { item_id: 1 });
socket.emit('join_user', { user_id: 5 });

socket.on('bid_update',    data => console.log('bid baru', data));
socket.on('auction_ended', data => console.log('lelang selesai', data));
socket.on('notification',  data => console.log('notif', data));
```

## Struktur Project

```
bytebid-backend/
├── app/
│   ├── __init__.py            # App factory
│   ├── models/                # User, Item, Bid, Notification, ResetToken
│   ├── routes/                # auth, items, bids, notifications, admin
│   ├── services/              # auction_service, email_service, scheduler
│   ├── sockets/               # Socket.IO event handlers
│   └── static/uploads/        # Gambar barang yang diupload
├── config.py
├── run.py                     # Entry point
├── seed.py                    # Populate data awal
├── requirements.txt
├── .env.example
└── .gitignore
```

## Contoh Request

### Register
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"budi","name":"Budi","email":"budi@test.com","password":"rahasia123"}'
```

### Login (pakai username atau email)
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"budi","password":"rahasia123"}'
```

### Place Bid
```bash
curl -X POST http://localhost:5000/api/bids/1 \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"amount":17000000}'
```

### Upload barang baru (admin)
```bash
curl -X POST http://localhost:5000/api/admin/items \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -F "name=PlayStation 5" \
  -F "category=Elektronik" \
  -F "start_price=8000000" \
  -F "duration_minutes=60" \
  -F "image=@/path/to/foto.jpg"
```

## Tim Kelompok 08

| Nama | NIM | Role |
|------|-----|------|
| Anindya Fairuz Az Zahra | 21120124120018 | UI/UX |
| Lionel Jeremi Pinondang S. | 21120124130067 | Programmer |
| Gotara Parasdya Abimanyu | 21120124140157 | Project Manager |
| Finodi | 21120124140138 | Programmer |

---
© 2026 ByteBid · Teknik Komputer Universitas Diponegoro · Kelompok 08
