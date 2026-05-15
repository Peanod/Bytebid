# ByteBid Setup Script untuk Windows PowerShell
# Jalankan: .\setup.ps1

Write-Host "════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " ByteBid Setup" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════" -ForegroundColor Cyan

# 1. Buat virtual environment
if (!(Test-Path "venv")) {
    Write-Host "`n[1/4] Membuat virtual environment..." -ForegroundColor Yellow
    python -m venv venv
} else {
    Write-Host "`n[1/4] Virtual environment sudah ada" -ForegroundColor Green
}

# 2. Aktivasi venv
Write-Host "[2/4] Mengaktifkan virtual environment..." -ForegroundColor Yellow
& venv\Scripts\Activate.ps1

# 3. Install dependencies
Write-Host "[3/4] Menginstall dependencies..." -ForegroundColor Yellow
pip install -q -r requirements.txt

# 4. Setup database
Write-Host "[4/4] Setup database..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    Write-Host "Membuat .env dari .env.example..."
    Copy-Item ".env.example" ".env"
    Write-Host "⚠️  Edit .env dan pastikan DB_PASSWORD sesuai dengan MySQL Anda" -ForegroundColor Yellow
}

Write-Host "`n════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " Setup selesai! Langkah selanjutnya:" -ForegroundColor Green
Write-Host "════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "`n1. Edit .env jika diperlukan"
Write-Host "2. Jalankan: python seed.py"
Write-Host "3. Terminal 1: python run.py (backend port 5000)"
Write-Host "4. Terminal 2: python frontend.py (frontend port 8000)"
Write-Host "`nAkses: http://localhost:8000"
Write-Host ""
