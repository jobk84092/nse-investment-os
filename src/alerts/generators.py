from datetime import datetime
from src.utils.io import write_text
from src.utils.paths import ALERTS_DIR, settings

def generate_desktop_alert(text: str) -> None:
    write_text(text, ALERTS_DIR / "desktop_alert.txt")

def generate_email_summary(text: str) -> None:
    recipient = settings().get("alerts", {}).get("recipient_email", "").strip()
    if recipient:
        prefixed = f"To: {recipient}\n\n{text}"
    else:
        prefixed = text
    write_text(prefixed, ALERTS_DIR / "email_summary.md")

def generate_calendar_ics() -> None:
    recipient = settings().get("alerts", {}).get("recipient_email", "").strip()
    recipient_line = f"Target recipient: {recipient}. " if recipient else ""
    today = datetime.utcnow().strftime("%Y%m01T070000Z")
    ics = (
        "BEGIN:VCALENDAR\n"
        "VERSION:2.0\n"
        "PRODID:-//OpenAI//NSE Investment OS//EN\n"
        "BEGIN:VEVENT\n"
        f"DTSTART:{today}\n"
        "RRULE:FREQ=MONTHLY;BYMONTHDAY=1\n"
        "SUMMARY:Review monthly stock purchase plan\n"
        f"DESCRIPTION:{recipient_line}Run NSE Investment OS, read memo, review alerts, decide one or two buys.\n"
        "END:VEVENT\n"
        "END:VCALENDAR\n"
    )
    write_text(ics, ALERTS_DIR / "monthly_stock_review.ics")
