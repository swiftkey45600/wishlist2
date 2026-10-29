"""Optional event reminders for users who explicitly enabled them."""
import logging
import os
from datetime import date, datetime, timedelta
from threading import Event as ThreadEvent, Thread

from app.config import SMTPConfigurationError, get_smtp_settings
from app.database import get_connection
from app.services.email_service import EmailDeliveryError, EmailService

logger = logging.getLogger(__name__)


def reminder_message(row, days_before: int) -> tuple[str, str]:
    event_date = date.fromisoformat(row["event_date"][:10]).strftime("%d.%m.%Y")
    when = "завтра" if days_before == 1 else "через неделю"
    subject = f"Wishlist: событие {when}"
    role = "которое вы организуете" if row["user_id"] == row["owner_id"] else "для которого вы забронировали подарок"
    body = (f"Здравствуйте, {row['name']}!\n\n"
            f"Напоминаем: {when}, {event_date}, состоится событие «{row['title']}», {role}.\n")
    if row["place"]:
        body += f"Место: {row['place']}\n"
    if days_before == 7:
        body += "\nЕщё есть время спокойно подготовиться и проверить свои планы.\n"
    else:
        body += "\nЖелаем вам приятного дня и тёплой встречи.\n"
    body += ("\nЕсли не хотите получать напоминания, выключите их в профиле Wishlist.\n"
             "Команда Wishlist")
    return subject, body


def send_due_reminders(today: date | None = None, mail: EmailService | None = None) -> int:
    """At most one email per recipient, start date and reminder window (7 or 1 days)."""
    current_day = today or datetime.now().astimezone().date()
    days = [(current_day + timedelta(days=lead)).isoformat() for lead in (1, 7)]
    with get_connection() as connection:
        rows = connection.execute('''
            SELECT DISTINCT e.id AS event_id, e.owner_id, e.title, e.event_date, e.place,
                   u.id AS user_id, u.email, u.name
            FROM events e
            JOIN users u ON u.id = e.owner_id OR EXISTS (
                SELECT 1 FROM gifts g JOIN reservations r ON r.gift_id = g.id
                WHERE g.event_id = e.id AND r.reserver_id = u.id
            )
            WHERE e.status = 'active' AND substr(e.event_date, 1, 10) IN (?, ?)
              AND u.email IS NOT NULL AND u.email_verified = 1 AND u.event_reminders = 1
        ''', days).fetchall()

    sender = mail or EmailService()
    sent = 0
    for row in rows:
        event_day = row["event_date"][:10]
        lead = (date.fromisoformat(event_day) - current_day).days
        with get_connection() as connection:
            claimed = connection.execute('''
                INSERT OR IGNORE INTO event_reminder_deliveries (event_id, user_id, event_date, days_before)
                SELECT ?, ?, ?, ? WHERE EXISTS (
                    SELECT 1 FROM users WHERE id = ? AND email = ? AND email_verified = 1 AND event_reminders = 1
                ) AND EXISTS (
                    SELECT 1 FROM events e
                    WHERE e.id = ? AND e.status = 'active' AND substr(e.event_date, 1, 10) = ?
                      AND (e.owner_id = ? OR EXISTS (
                          SELECT 1 FROM gifts g JOIN reservations r ON r.gift_id = g.id
                          WHERE g.event_id = e.id AND r.reserver_id = ?
                      ))
                )
            ''', (row["event_id"], row["user_id"], event_day, lead,
                   row["user_id"], row["email"], row["event_id"], event_day, row["user_id"], row["user_id"])).rowcount
        if not claimed:
            continue
        # Claim before SMTP so concurrent workers do not send duplicate messages.
        subject, body = reminder_message(row, lead)
        try:
            sender.send(row["email"], subject, body)
        except (EmailDeliveryError, SMTPConfigurationError, ValueError):
            with get_connection() as connection:
                connection.execute(
                    "DELETE FROM event_reminder_deliveries WHERE event_id=? AND user_id=? AND event_date=? AND days_before=?",
                    (row["event_id"], row["user_id"], event_day, lead),
                )
            logger.warning("Event reminder could not be sent")
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
