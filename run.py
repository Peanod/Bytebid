"""
ByteBid - Entry Point
Jalankan: python run.py
"""
import os
from app import create_app, socketio

config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(config_name)


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print(" 🚀 ByteBid Backend Server")
    print(" Kelompok 08 - RPL Teknik Komputer UNDIP 2026")
    print("=" * 60)
    print(" Server: http://localhost:5000")
    print(" API:    http://localhost:5000/api")
    print(" Health: http://localhost:5000/health")
    print(" Socket: ws://localhost:5000")
    print("=" * 60 + "\n")

    socketio.run(app, host='0.0.0.0', port=5000,
                 debug=app.config['DEBUG'],
                 allow_unsafe_werkzeug=True)
