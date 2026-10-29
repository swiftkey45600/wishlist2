from datetime import date
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app.database import get_connection, init_db
from app.services.email_service import EmailDeliveryError
from app.services.event_reminders import send_due_reminders


class MailStub:
    def __init__(self):
        self.messages = []

    def send(self, address, subject, body):
        self.messages.append((address, subject, body))


class ReminderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        database = patch('app.database.DATABASE_PATH', Path(self.temp.name) / 'test.db')
        database.start()
        self.addCleanup(database.stop)
        init_db()
        with get_connection() as db:
            db.execute("UPDATE users SET name='Анна', email='owner@example.com', email_verified=1, event_reminders=1 WHERE id=1")
            db.execute("INSERT INTO users (id,name,login,password_hash,email,email_verified,event_reminders) VALUES (2,'Игорь','guest','x','guest@example.com',1,1)")
            db.execute("INSERT INTO users (id,name,login,password_hash,email,email_verified,event_reminders) VALUES (3,'Друг','other','x','other@example.com',1,0)")
            db.execute("INSERT INTO events (id,owner_id,title,event_date,place) VALUES (1,1,'День рождения','2026-11-02T15:00','Дома')")
            db.execute("INSERT INTO gifts (id,event_id,title) VALUES (1,1,'Подарок'),(2,1,'Другой подарок'),(3,1,'Ещё подарок')")
            db.execute("INSERT INTO reservations (gift_id,reserver_id) VALUES (1,2),(2,2),(3,3)")

    def test_opted_in_owner_and_guest_receive_once_without_spoilers(self):
        mail = MailStub()
        self.assertEqual(send_due_reminders(date(2026, 11, 1), mail), 2)
        self.assertEqual(send_due_reminders(date(2026, 11, 1), mail), 0)
        self.assertEqual({message[0] for message in mail.messages}, {'owner@example.com', 'guest@example.com'})
        for _, subject, body in mail.messages:
            self.assertIn('День рождения', body)
            self.assertIn('02.11.2026', body)
            self.assertIn('Дома', body)
            self.assertNotIn('Подарок', body)
            self.assertIn('завтра', subject)

    def test_no_mail_for_unverified_archived_or_wrong_date(self):
        with get_connection() as db:
            db.execute('UPDATE users SET email_verified=0 WHERE id=2')
        mail = MailStub()
        self.assertEqual(send_due_reminders(date(2026, 10, 31), mail), 0)
        self.assertEqual(send_due_reminders(date(2026, 11, 1), mail), 1)
        with get_connection() as db:
            db.execute("UPDATE events SET status='archived'")
            db.execute('UPDATE users SET email_verified=1 WHERE id=2')
        self.assertEqual(send_due_reminders(date(2026, 11, 1), mail), 0)

    def test_smtp_failure_allows_retry(self):
        class FailedMail:
            def send(self, *args):
                raise EmailDeliveryError('failed')
        self.assertEqual(send_due_reminders(date(2026, 11, 1), FailedMail()), 0)
        self.assertEqual(send_due_reminders(date(2026, 11, 1), MailStub()), 2)


if __name__ == '__main__':
    unittest.main()
