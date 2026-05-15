"""
ByteBid - Entry Point
Jalankan: python run.py
"""
import os
import sys
from app import create_app, socketio

# Force UTF-8 stdout di Windows agar print karakter non-ASCII tidak crash
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(config_name)


if __name__ == '__main__':
    print('=' * 60)
    print(' ByteBid Backend Server')
    print(' Kelompok 08 - RPL Teknik Komputer UNDIP 2026')
    print('=' * 60)
    print(' Web:    http://localhost:5000/')
    print(' API:    http://localhost:5000/api')
    print(' Health: http://localhost:5000/health')
    print(' Socket: ws://localhost:5000')
    print('=' * 60)

    socketio.run(app, host='0.0.0.0', port=5000,
                 debug=app.config['DEBUG'],
                 allow_unsafe_werkzeug=True)
