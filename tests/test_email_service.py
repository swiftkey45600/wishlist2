"""SMTP transport tests: all network access is replaced by mocks."""
import os
import smtplib
import socket
import ssl
import unittest
from unittest.mock import call, patch

from app.config import get_smtp_settings, SMTPConfigurationError
from app.services.email_service import EmailDeliveryError, EmailService


SMTP_ENV = {
    "SMTP_HOST": "smtp.example.com",
    "SMTP_PORT": "465",
    "SMTP_USE_SSL": "true",
    "SMTP_USERNAME": "wishlist@example.com",
    "SMTP_PASSWORD": "smtp-test-secret",
    "SMTP_FROM": "wishlist@example.com",
    "SMTP_TIMEOUT": "10",
}


class SMTPConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(os.environ, SMTP_ENV, clear=True))

    def test_load_settings_and_hide_password_from_repr(self):
        settings = get_smtp_settings()
        self.assertEqual(settings.host, "smtp.example.com")
        self.assertEqual(settings.port, 465)
        self.assertTrue(settings.use_ssl)
        self.assertEqual(settings.timeout, 10)
        self.assertNotIn("smtp-test-secret", repr(settings))

    def test_required_settings_fail_explicitly_without_secrets(self):
        for key in ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM"):
            with self.subTest(key=key), patch.dict(os.environ, {key: ""}):
                with self.assertRaises(SMTPConfigurationError) as error:
                    get_smtp_settings()
                self.assertIn(key, str(error.exception))
                self.assertNotIn("smtp-test-secret", str(error.exception))

    def test_invalid_ports_timeout_boolean_and_sender(self):
        for key, value in (
            ("SMTP_PORT", "0"), ("SMTP_PORT", "65536"), ("SMTP_PORT", "not-a-port"),
            ("SMTP_TIMEOUT", "0"), ("SMTP_TIMEOUT", "61"), ("SMTP_TIMEOUT", "nan"),
            ("SMTP_USE_SSL", "yes-please"), ("SMTP_FROM", "invalid"),
            ("SMTP_HOST", "smtp.example.com\r\nwrong"),
        ):
            with self.subTest(key=key, value=value), patch.dict(os.environ, {key: value}):
                with self.assertRaises(SMTPConfigurationError):
                    get_smtp_settings()

    def test_defaults_and_starttls_mode(self):
        for key in ("SMTP_PORT", "SMTP_TIMEOUT", "SMTP_USE_SSL"):
            del os.environ[key]
        settings = get_smtp_settings()
        self.assertEqual((settings.port, settings.timeout, settings.use_ssl), (465, 10, True))
        os.environ.update(SMTP_PORT="587", SMTP_USE_SSL="false")
        self.assertFalse(get_smtp_settings().use_ssl)


class EmailServiceTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(os.environ, SMTP_ENV, clear=True))
        self.ssl_factory = self.enterContext(patch("app.services.email_service.smtplib.SMTP_SSL"))
        self.starttls_factory = self.enterContext(patch("app.services.email_service.smtplib.SMTP"))
        self.client = self.ssl_factory.return_value.__enter__.return_value
        self.client.send_message.return_value = {}
        self.service = EmailService()

    def test_ssl_send_unicode_body_and_explicit_envelope(self):
        self.service.send("guest@example.com", "Письмо от Wishlist", "Привет! Это проверка отправки.")
        self.assertEqual(self.ssl_factory.call_count, 1)
        args, kwargs = self.ssl_factory.call_args
        self.assertEqual(args, ("smtp.example.com", 465))
        self.assertEqual(kwargs["timeout"], 10)
        self.assertTrue(kwargs["context"].check_hostname)
        self.assertEqual(kwargs["context"].verify_mode, ssl.CERT_REQUIRED)
        self.client.login.assert_called_once_with("wishlist@example.com", "smtp-test-secret")
        message = self.client.send_message.call_args.args[0]
        self.assertEqual(str(message["From"]), "wishlist@example.com")
        self.assertEqual(str(message["To"]), "guest@example.com")
        self.assertEqual(str(message["Subject"]), "Письмо от Wishlist")
        self.assertIn("Привет!", message.get_content())
        self.assertEqual(self.client.send_message.call_args.kwargs, {
            "from_addr": "wishlist@example.com", "to_addrs": ["guest@example.com"],
        })
        self.starttls_factory.assert_not_called()

    def test_starttls_is_required_before_authentication(self):
        os.environ.update(SMTP_USE_SSL="false", SMTP_PORT="587")
        client = self.starttls_factory.return_value.__enter__.return_value
        client.send_message.return_value = {}
        self.service.send("guest@example.com", "Subject", "Text")
        self.ssl_factory.assert_not_called()
        self.starttls_factory.assert_called_once_with("smtp.example.com", 587, timeout=10)
        calls = client.mock_calls
        tls = next(i for i, item in enumerate(calls) if item[0] == "starttls")
        login = calls.index(call.login("wishlist@example.com", "smtp-test-secret"))
        self.assertLess(tls, login)
        self.assertEqual(client.ehlo.call_count, 2)
        self.assertTrue(client.starttls.call_args.kwargs["context"].check_hostname)

    def test_tls_failure_never_authenticates(self):
        os.environ.update(SMTP_USE_SSL="false", SMTP_PORT="587")
        client = self.starttls_factory.return_value.__enter__.return_value
        client.starttls.side_effect = smtplib.SMTPNotSupportedError("STARTTLS unsupported")
        with self.assertRaises(EmailDeliveryError):
            self.service.send("guest@example.com", "Subject", "Text")
        client.login.assert_not_called()
        client.send_message.assert_not_called()

    def test_missing_configuration_does_not_open_connection(self):
        os.environ["SMTP_PASSWORD"] = ""
        with self.assertRaises(SMTPConfigurationError):
            self.service.send("guest@example.com", "Subject", "Text")
        self.ssl_factory.assert_not_called()
        self.starttls_factory.assert_not_called()

    def test_invalid_recipient_and_subject_do_not_open_connection(self):
        for recipient, subject in (
            ("invalid", "Subject"), ("a@example.com\r\nBcc:b@example.com", "Subject"),
            ("guest@example.com", "Subject\nBcc: other@example.com"),
            ("guest@example.com", " "),
        ):
            with self.subTest(recipient=recipient, subject=subject), self.assertRaises(ValueError):
                self.service.send(recipient, subject, "Text")
        self.ssl_factory.assert_not_called()

    def test_auth_failure_is_sanitized_and_no_message_is_sent(self):
        self.client.login.side_effect = smtplib.SMTPAuthenticationError(535, b"smtp-test-secret bad credentials")
        with self.assertRaises(EmailDeliveryError) as error:
            self.service.send("guest@example.com", "Subject", "Text")
        self.assertNotIn("smtp-test-secret", str(error.exception))
        self.assertIn("authentication failed (code 535)", str(error.exception))
        self.client.send_message.assert_not_called()

    def test_connection_errors_have_specific_diagnostics_without_provider_text(self):
        for error, expected in (
            (ssl.SSLCertVerificationError("smtp-test-secret"), "certificate verification failed"),
            (ssl.SSLError("smtp-test-secret"), "TLS connection failed"),
            (socket.gaierror("smtp-test-secret"), "hostname could not be resolved"),
            (TimeoutError("smtp-test-secret"), "timed out"),
            (ConnectionRefusedError("smtp-test-secret"), "connection refused"),
            (smtplib.SMTPServerDisconnected("smtp-test-secret"), "server disconnected"),
            (smtplib.SMTPNotSupportedError("smtp-test-secret"), "does not support"),
            (smtplib.SMTPSenderRefused(553, b"smtp-test-secret", "sender@example.com"), "sender rejected (code 553)"),
            (smtplib.SMTPRecipientsRefused({"guest@example.com": (550, b"smtp-test-secret")}), "recipient rejected"),
            (smtplib.SMTPDataError(554, b"smtp-test-secret"), "operation (code 554)"),
        ):
            with self.subTest(expected=expected):
                self.ssl_factory.side_effect = error
                with self.assertRaises(EmailDeliveryError) as caught:
                    self.service.send("guest@example.com", "Subject", "Text")
                self.assertIn(expected, str(caught.exception))
                self.assertNotIn("smtp-test-secret", str(caught.exception))
        self.client.send_message.assert_not_called()

    def test_connection_timeout_is_a_delivery_error(self):
        self.ssl_factory.side_effect = TimeoutError("timeout")
        with self.assertRaises(EmailDeliveryError):
            self.service.send("guest@example.com", "Subject", "Text")

    def test_rejected_recipient_and_smtp_data_error_are_not_success(self):
        self.client.send_message.return_value = {"guest@example.com": (550, b"rejected")}
        with self.assertRaises(EmailDeliveryError):
            self.service.send("guest@example.com", "Subject", "Text")
        self.client.send_message.side_effect = smtplib.SMTPDataError(554, b"rejected")
        with self.assertRaises(EmailDeliveryError):
            self.service.send("guest@example.com", "Subject", "Text")


if __name__ == "__main__":
    unittest.main()
