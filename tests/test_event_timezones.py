import unittest
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from app.utils.event_dates import end_date_for_duration, validate_future_instant

class EventTimezoneTests(unittest.TestCase):
    def test_end_date_preserves_creator_offset(self):
        self.assertEqual(end_date_for_duration('2099-11-01T15:00+03:00', 2), '2099-11-02T23:59:59+03:00')
        self.assertEqual(end_date_for_duration('2099-11-01T15:00', 2), '2099-11-02T23:59:59')

    def test_aware_timestamps_are_compared_as_instants(self):
        now = datetime.now(timezone.utc)
        with self.assertRaises(HTTPException):
            validate_future_instant((now - timedelta(minutes=2)).astimezone(timezone(timedelta(hours=3))).isoformat())
        validate_future_instant((now + timedelta(minutes=2)).astimezone(timezone(timedelta(hours=-5))).isoformat())
        validate_future_instant('2020-01-01T12:00')  # Legacy records have no timezone.
