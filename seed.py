"""
Seed data ByteBid — populate database dengan barang & user awal.
Jalankan: python seed.py
"""
from datetime import datetime, timedelta
from decimal import Decimal

from app import create_app, db
from app.models import User, Item, AuctionStatus


def seed():
    app = create_app()
    with app.app_context():
        print('[seed] Drop & create all tables...')
        db.drop_all()
        db.create_all()

        # ── Users ──────────────────────────────────────────────────────────
        admin = User(username='admin', name='Admin ByteBid',
                     email='admin@bytebid.id', is_admin=True)
        admin.set_password('admin123')

        demo = User(username='demo', name='Demo User', email='demo@bytebid.id')
        demo.set_password('demo123')

        lionel = User(username='lionel', name='Lionel Jeremi P.',
                      email='lionel@bytebid.id')
        lionel.set_password('lionel123')

        anin = User(username='anindya', name='Anindya Fairuz',
                    email='anindya@bytebid.id')
        anin.set_password('anindya123')

        db.session.add_all([admin, demo, lionel, anin])
        db.session.commit()
        print(f'[seed] Created {User.query.count()} users')

        # ── Items ──────────────────────────────────────────────────────────
        now = datetime.utcnow()

        items_data = [
            dict(name='MG 1/100 Barbatos Lupus Rex Bandai',
                 category='Seni', condition='Kondisi Baru/New - Garansi Aktif',
                 image='https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhM6dxBSs0TsE7ZC-SeLnD35H5cpB8GHXPjKkUHzrj2Otm18Oz5AEn52ikaear5mG8L2uU6AUZtTJkP-jg4LCfYtRdhjySARqInB0uCJbJMBEgrZEGXPuSGP0pekxikfKQZeEFPEOK11emiIGT2b5Lqrf-AdEai05hQmquulxns7VtI2OP9myapAn5psA/s16000-rw/mg%20barbatos%20lupus%20rex%20box%20art.jpg',
                 start_price=12000000, current_bid=16500000, minutes=140,
                 description='Gundam Master Grade dengan kondisi mint, original Bandai.'),
            dict(name='iPhone 15 Pro Max', category='Elektronik',
                 condition='Kondisi 98% - Box Lengkap',
                 image='https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/iphone-15-pro-finish-select-202309-6-7inch-naturaltitanium?wid=5120&hei=2880&fmt=p-jpg&qlt=80&.v=1692846352658',
                 start_price=10000000, current_bid=14200000, minutes=337,
                 description='256GB Natural Titanium, garansi resmi iBox.'),
            dict(name='Honda Brio 2012', category='Kendaraan',
                 condition='Plat B Genap - 12.000 KM',
                 image='https://imgcdn.oto.com/medium/gallery/exterior/46/1085/honda-brio-front-angle-low-view-633474.jpg',
                 start_price=80000000, current_bid=95500000, minutes=285,
                 description='Pemilik tangan pertama, service record lengkap.'),
            dict(name='Adiputro Jetbus 3+ SHD 2017', category='Kendaraan',
                 condition='Mercy OH 1836 - 50 Seat',
                 image='https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/Mercedes-Benz_O_500_RS_Adiputro_Jetbus_3%2B_SHD_%28Rosalia_Indah%2C_B_7552_UZ%29_@_Boyolali.jpg/1280px-Mercedes-Benz_O_500_RS_Adiputro_Jetbus_3%2B_SHD_%28Rosalia_Indah%2C_B_7552_UZ%29_@_Boyolali.jpg',
                 start_price=600000000, current_bid=730500000, minutes=415,
                 description='Bus pariwisata eks PO Rosalia Indah, mesin sehat.'),
            dict(name='Toyota Calya 1.2 E M/T', category='Kendaraan',
                 condition='Clean & Clear - 24.000 KM',
                 image='https://imgcdn.oto.com/medium/gallery/exterior/38/1316/toyota-calya-front-angle-low-view-636041.jpg',
                 start_price=120000000, current_bid=145000000, minutes=60,
                 description='LMPV irit BBM, cocok keluarga.'),
            dict(name='Photocard Mark NCT + Album', category='Seni',
                 condition='Mulus no minus - Freebies',
                 image='https://images.unsplash.com/photo-1618160702438-9b02ab6515c9?w=400',
                 start_price=500000, current_bid=875000, minutes=124,
                 description='Photocard rare + album original.'),
            dict(name='Sony A7 IV Mirrorless', category='Elektronik',
                 condition='Kondisi 90% - Lensa Kit',
                 image='https://www.bhphotovideo.com/images/images2500x2500/sony_ilce_7m4k_b_alpha_a7_iv_mirrorless_1668428.jpg',
                 start_price=18000000, current_bid=22000000, minutes=311,
                 description='Bonus lensa kit 28-70mm, baterai 2 buah.'),
            dict(name='Jersey Barcelona Messi', category='Seni',
                 condition='2014/2015 - Autentik',
                 image='https://images.unsplash.com/photo-1579952363873-27f3bade9f55?w=400',
                 start_price=40000000, current_bid=50500000, minutes=582,
                 description='Jersey match-worn signed by Messi.'),
            dict(name='Lukisan Kuda Api Pak SBY', category='Seni',
                 condition='Kondisi 100% - Historical',
                 image='https://images.unsplash.com/photo-1547036967-23d11aacaee0?w=400',
                 start_price=1000000000, current_bid=1200550000, minutes=598,
                 description='Lukisan langka, sertifikat keaslian disertakan.'),
        ]

        for d in items_data:
            mins = d.pop('minutes')
            sp = Decimal(str(d.pop('start_price')))
            cb = Decimal(str(d.pop('current_bid')))
            it = Item(
                **d,
                start_price=sp,
                current_bid=cb,
                status=AuctionStatus.ACTIVE,
                start_time=now,
                end_time=now + timedelta(minutes=mins),
                created_by=admin.id,
            )
            db.session.add(it)

        db.session.commit()
        print(f'[seed] Created {Item.query.count()} items')
        print('\n[seed] Selesai. Akun login:')
        print('       admin   / admin123    (admin)')
        print('       demo    / demo123')
        print('       lionel  / lionel123')
        print('       anindya / anindya123')


if __name__ == '__main__':
    seed()
