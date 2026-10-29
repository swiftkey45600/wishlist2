"""Optional event reminders for users who explicitly enabled them."""
import logging
import os
from datetime import date, datetime, timedelta
from threading import Event as ThreadEvent, Thread

from app.config import SMTPConfigurationError, get_smtp_settings
from app.database import get_connection
from app.services.email_service import EmailDeliveryError, EmailService

logger = logging.getLogger(__name__)


def send_due_reminders(today: date | None = None, mail: EmailService | None = None) -> int:
    """Send one reminder per person and event date, the day before the event."""
    tomorrow = (today or datetime.now().astimezone().date()) + timedelta(days=1)
    day = tomorrow.isoformat()
    with get_connection() as connection:
        rows = connection.execute('''
            SELECT DISTINCT e.id AS event_id, e.title, e.event_date, e.place,
                   u.id AS user_id, u.email, u.name
            FROM events e
            JOIN users u ON u.id = e.owner_id OR EXISTS (
                SELECT 1 FROM gifts g JOIN reservations r ON r.gift_id = g.id
                WHERE g.event_id = e.id AND r.reserver_id = u.id
            )
            WHERE e.status = 'active' AND substr(e.event_date, 1, 10) = ?
              AND u.email IS NOT NULL AND u.email_verified = 1 AND u.event_reminders = 1
        ''', (day,)).fetchall()

    sender = mail or EmailService()
    sent = 0
    for row in rows:
        with get_connection() as connection:
            claimed = connection.execute('''
                INSERT OR IGNORE INTO event_reminder_deliveries (event_id, user_id, event_date)
                SELECT ?, ?, ? WHERE EXISTS (
                    SELECT 1 FROM users WHERE id = ? AND email = ? AND email_verified = 1 AND event_reminders = 1
                ) AND EXISTS (
                    SELECT 1 FROM events WHERE id = ? AND status = 'active' AND substr(event_date, 1, 10) = ?
                )
            ''', (row['event_id'], row['user_id'], day, row['user_id'], row['email'], row['event_id'], day)).rowcount
        if not claimed:
            continue
        # The unique claim is stored before contacting SMTP to prevent duplicate emails
        # across workers. An interrupted send is intentionally not retried automatically.
        event_date = tomorrow.strftime('%d.%m.%Y')
        body = (f"Здравствуйте, {row['name']}!\n\n"
                f"Напоминаем: завтра, {event_date}, состоится событие «{row['title']}».\n")
        if row['place']:
            body += f"Место: {row['place']}\n"
        body += ("\nНадеемся, подготовка идёт хорошо и впереди приятный день.\n\n"
                 "Если не хотите получать такие письма, выключите напоминания в профиле Wishlist.\n"
                 "Команда Wishlist")
        try:
            sender.send(row['email'], 'Wishlist: завтра событие', body)
        except (EmailDeliveryError, SMTPConfigurationError, ValueError):
            with get_connection() as connection:
                connection.execute('DELETE FROM event_reminder_deliveries WHERE event_id = ? AND user_id = ? AND event_date = ?',
                                   (row['event_id'], row['user_id'], day))
            logger.warning('Event reminder could not be sent')
        else:
            sent += 1
    return sent


_stop = ThreadEvent()
_thread = None


def start_reminder_worker() -> None:
    global _thread
    if os.getenv('EVENT_REMINDERS_ENABLED', '').strip().lower() not in {'1', 'true'}:
        return
    if _thread and _thread.is_alive():
        return
    _stop.clear()

    def run():
        while not _stop.is_set():
            try:
                get_smtp_settings()
                send_due_reminders()
            except SMTPConfigurationError:
                logger.warning('Event reminders are enabled but SMTP is not configured')
            except Exception:
                logger.exception('Event reminder worker failed')
            _stop.wait(3600)

    _thread = Thread(target=run, name='event-reminders', daemon=True)
    _thread.start()


def stop_reminder_worker() -> None:
    _stop.set()
