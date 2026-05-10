"""
Background scheduler — cek lelang yang sudah expired tiap 15 detik
agar pemenang ditentukan otomatis (SKPL-BB-09).
"""
from apscheduler.schedulers.background import BackgroundScheduler

_scheduler = None


def start_scheduler(app):
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    sched = BackgroundScheduler(daemon=True)

    def _tick():
        with app.app_context():
            try:
                from app.services.auction_service import check_expired_auctions
                check_expired_auctions()
            except Exception as e:
                app.logger.warning(f'[scheduler] check_expired_auctions error: {e}')

    sched.add_job(_tick, 'interval', seconds=15, id='check_expired',
                  replace_existing=True)
    sched.start()
    _scheduler = sched
    app.logger.info('[scheduler] started, interval=15s')
    return sched
