import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def smtp_config() -> dict:
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").replace(" ", "")
    if not user or not password:
        raise ValueError("SMTP_USER and SMTP_PASSWORD must be set in .env")

    return {
        "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": user,
        "password": password,
        "test_link": os.getenv("TEST_LINK_URL", "https://example.com/assessment").strip(),
    }


def test_email_content(name: str, test_link: str) -> tuple[str, str]:
    subject = "Visl AI Labs — Technical Assessment Invitation"
    body = f"""Dear {name},

Congratulations! You have been shortlisted for the next round at Visl AI Labs.

Please complete the technical assessment using the link below:
{test_link}

The assessment covers logical aptitude and coding skills. Please complete it at your earliest convenience.

Best regards,
Visl AI Labs Recruiting Team
"""
    return subject, body


def send_test_email(to_email: str, name: str, cfg: dict) -> None:
    subject, body = test_email_content(name, cfg["test_link"])

    msg = MIMEMultipart()
    msg["From"] = cfg["user"]
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(cfg["host"], cfg["port"], timeout=30) as server:
        server.starttls()
        server.login(cfg["user"], cfg["password"])
        server.sendmail(cfg["user"], [to_email], msg.as_string())


def format_interview_slot(iso_start: str) -> tuple[str, str]:
    raw = iso_start.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    date_str = dt.strftime("%A, %d %B %Y")
    time_str = dt.strftime("%I:%M %p").lstrip("0")
    return date_str, time_str


def interview_email_content(
    name: str,
    date_str: str,
    time_str: str,
    meet_link: str,
) -> tuple[str, str]:
    subject = "Visl AI Labs — Interview Invitation"
    body = f"""Dear {name},

Congratulations! You have qualified for a technical interview at Visl AI Labs.

Interview details:
  Date: {date_str}
  Time: {time_str}
  Google Meet: {meet_link}

Please join the meeting a few minutes early. The interview will last approximately 30 minutes.

Best regards,
Visl AI Labs Recruiting Team
"""
    return subject, body


def send_interview_email(
    to_email: str,
    name: str,
    interview_start: str,
    meet_link: str,
    cfg: dict,
) -> None:
    date_str, time_str = format_interview_slot(interview_start)
    subject, body = interview_email_content(name, date_str, time_str, meet_link)

    msg = MIMEMultipart()
    msg["From"] = cfg["user"]
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(cfg["host"], cfg["port"], timeout=30) as server:
        server.starttls()
        server.login(cfg["user"], cfg["password"])
        server.sendmail(cfg["user"], [to_email], msg.as_string())
