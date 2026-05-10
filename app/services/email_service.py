"""
Email service — kirim notifikasi via Flask-Mail jika MAIL_SERVER dikonfigurasi.
Kalau tidak, fungsi-fungsi ini diam-diam log ke console saja (cocok untuk dev).
"""
from flask import current_app, url_for
from flask_mail import Message

from app import mail


def _mail_configured() -> bool:
    return bool(current_app.config.get('MAIL_SERVER'))


def send_password_reset_email(user, reset_token: str) -> None:
    if not _mail_configured():
        # Fallback: log saja ke console — untuk dev
        try:
            link = url_for('main.reset_password', token=reset_token, _external=True)
        except Exception:
            link = f'/reset-password/{reset_token}'
        current_app.logger.info(
            f'[email/dev] Reset password untuk {user.email}: {link}')
        return

    msg = Message(
        subject='Reset Password ByteBid',
        recipients=[user.email],
        body=(f'Halo {user.name},\n\n'
              f'Klik tautan berikut untuk reset password Anda:\n'
              f'{url_for("main.reset_password", token=reset_token, _external=True)}\n\n'
              f'Tautan berlaku 24 jam.\n\nSalam,\nTim ByteBid'),
    )
    mail.send(msg)


def send_winner_email(user, item, amount: float) -> None:
    if not _mail_configured():
        current_app.logger.info(
            f'[email/dev] Pemenang {user.email} memenangkan {item.name} '
            f'dengan Rp {int(amount):,}')
        return

    msg = Message(
        subject=f'Selamat! Anda memenangkan lelang {item.name}',
        recipients=[user.email],
        body=(f'Halo {user.name},\n\n'
              f'Selamat! Anda memenangkan lelang "{item.name}" '
              f'dengan harga Rp {int(amount):,}.\n\n'
              f'Tim ByteBid akan menghubungi Anda dalam 24 jam untuk proses selanjutnya.\n\n'
              f'Salam,\nTim ByteBid'),
    )
    mail.send(msg)
