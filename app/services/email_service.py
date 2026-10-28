"""SMTP transport for future verification/reset emails; no public send endpoint."""
import smtplib
import socket
import ssl
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

from email_validator import EmailNotValidError, validate_email

from app.config import SMTPSettings, get_smtp_settings


class EmailDeliveryError(RuntimeError):
    """SMTP did not successfully accept the message."""


class EmailService:
    def send(self, recipient: str, subject: str, body: str) -> None:
        """Send plain text over verified TLS; success means accepted by SMTP.

        This is blocking I/O: use a sync route/worker or a thread when calling
        from an async route. It does not confirm delivery to the inbox.
        """
        settings = get_smtp_settings()
        try:
            address = validate_email(recipient, check_deliverability=False, allow_smtputf8=False).ascii_email
        except EmailNotValidError:
            raise ValueError("Recipient must be a valid email address") from None
        if not subject.strip() or "\r" in subject or "\n" in subject:
            raise ValueError("Subject must be non-empty and contain no line breaks")

        message = EmailMessage()
        message["From"] = settings.sender
        message["To"] = address
        message["Subject"] = subject
        message["Date"] = formatdate(usegmt=True)
        message["Message-ID"] = make_msgid(domain=settings.sender.rsplit("@", 1)[1])
        message.set_content(body)
        context = ssl.create_default_context()

        try:
            if settings.use_ssl:
                with smtplib.SMTP_SSL(settings.host, settings.port, timeout=settings.timeout, context=context) as client:
                    self._send(client, settings, message, address)
            else:
                # false means STARTTLS, never plaintext authentication.
                with smtplib.SMTP(settings.host, settings.port, timeout=settings.timeout) as client:
                    client.ehlo()
                    client.starttls(context=context)
                    client.ehlo()
                    self._send(client, settings, message, address)
        except ssl.SSLCertVerificationError:
            raise EmailDeliveryError(
                "SMTP TLS certificate verification failed: check Python's trusted CA certificates"
            ) from None
        except ssl.SSLError:
            raise EmailDeliveryError("SMTP TLS connection failed: check SMTP_PORT and SMTP_USE_SSL") from None
        except smtplib.SMTPAuthenticationError as error:
            raise EmailDeliveryError(
                f"SMTP authentication failed (code {error.smtp_code}): check SMTP_USERNAME, "
                "the mail app password and mail-client access settings"
            ) from None
        except smtplib.SMTPSenderRefused as error:
            raise EmailDeliveryError(
                f"SMTP sender rejected (code {error.smtp_code}): check SMTP_FROM matches the authorized mailbox"
            ) from None
        except smtplib.SMTPRecipientsRefused:
            raise EmailDeliveryError("SMTP recipient rejected: check the recipient address") from None
        except smtplib.SMTPNotSupportedError:
            raise EmailDeliveryError("SMTP server does not support the required TLS or authentication method") from None
        except smtplib.SMTPResponseException as error:
            raise EmailDeliveryError(f"SMTP server rejected the operation (code {error.smtp_code})") from None
        except socket.gaierror:
            raise EmailDeliveryError("SMTP hostname could not be resolved: check SMTP_HOST, DNS and network") from None
        except TimeoutError:
            raise EmailDeliveryError("SMTP connection timed out: check network access to the SMTP port") from None
        except ConnectionRefusedError:
            raise EmailDeliveryError("SMTP connection refused: check SMTP_HOST and SMTP_PORT") from None
        except smtplib.SMTPServerDisconnected:
            raise EmailDeliveryError("SMTP server disconnected before the operation completed") from None
        except (smtplib.SMTPException, OSError):
            # Keep provider text out: it can contain addresses or credentials.
            raise EmailDeliveryError("SMTP communication failed: check the connection and mail server settings") from None

    @staticmethod
    def _send(client, settings: SMTPSettings, message: EmailMessage, recipient: str) -> None:
        client.login(settings.username, settings.password)
        refused = client.send_message(message, from_addr=settings.sender, to_addrs=[recipient])
        if refused:
            raise EmailDeliveryError("Email recipient was rejected by the SMTP server")
