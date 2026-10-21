from flask import Flask, render_template, jsonify, request, redirect, url_for
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pytz
import random
import re
import time as time_module
from collections import defaultdict, deque

app = Flask(__name__)

# === Google Calendar Setup ===
CALENDAR_ID = os.environ.get("CALENDAR_ID")
SERVICE_ACCOUNT_FILE = os.environ.get(
    "GOOGLE_APPLICATION_CREDENTIALS",
    os.path.join(os.path.dirname(__file__), 'templates', 'credentials.json')  # fallback: templates/
)

SCOPES = ['https://www.googleapis.com/auth/calendar']

# === Feature switches ===
# Each integration turns on only when its settings exist, so the site runs
# anywhere: with no settings it simulates availability and skips side effects.
CALENDAR_ENABLED = bool(CALENDAR_ID) and os.path.exists(SERVICE_ACCOUNT_FILE)

credentials = None
if CALENDAR_ENABLED:
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )

# === Booking rate limit (public demo protection) ===
MAX_BOOKINGS_PER_HOUR = int(os.environ.get("MAX_BOOKINGS_PER_HOUR", "3"))
_recent_bookings = defaultdict(deque)

def client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    return forwarded.split(",")[0].strip() if forwarded else request.remote_addr

def rate_limited(ip):
    now = time_module.time()
    history = _recent_bookings[ip]
    while history and now - history[0] > 3600:
        history.popleft()
    if len(history) >= MAX_BOOKINGS_PER_HOUR:
        return True
    history.append(now)
    return False


def demo_busy_events(date_base, tz):
    """Fake existing bookings for a date, so the demo shows a realistic,
    partly-booked day. Seeded by the date, so the same day always looks the same."""
    rng = random.Random(date_base.strftime("%Y-%m-%d"))
    events = []
    for _ in range(rng.randint(0, 2)):
        start_hour = rng.randint(8, 13)
        start = tz.localize(date_base.replace(hour=start_hour, minute=rng.choice([0, 30])))
        end = start + datetime.timedelta(minutes=rng.choice([90, 180]))
        events.append((start, end))
    return events

# === Booking duration by package ===
PACKAGE_LENGTHS = {
    "standard": 90,
    "premium": 180,
    "elite": 480
}

# === Email Sender Info (Set these!) ===

SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")
EMAIL_ENABLED = bool(SENDER_EMAIL and APP_PASSWORD)

print(f"Calendar: {'on' if CALENDAR_ENABLED else 'simulated'} | Email: {'on' if EMAIL_ENABLED else 'off'}")

def send_confirmation_email(to_email, package, date, time, vehicle, address, postal_code, phone):
    subject = "Luxe Mobile Detailing Booking Confirmation (Demo)"
    body = f"""
Hi,

Your Luxe Mobile Detailing booking is confirmed!

Details:
- Package: {package.title()}
- Date: {date}
- Time: {time}
- Vehicle: {vehicle}
- Address: {address}
- Postal Code: {postal_code}
- Phone: {phone}

We'll see you soon!
If you need to change or cancel, reply to this email.

Thank you!

---
Note: Luxe Mobile Detailing is a portfolio demo built by Abel Lema.
No real appointment has been scheduled.
"""
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
    except Exception as e:
        print("Failed to send confirmation email:", e)

def is_valid_email(email):
    # Basic RFC-compliant email regex
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

@app.route('/')
def home():
    return render_template('car_detailing.html')

@app.route('/booking.html')
def booking_page():
    return render_template('booking.html')

@app.route('/successful.html')
def successful():
    return render_template('successful.html')

@app.route('/available-times')
def available_times():
    date_str = request.args.get('date')
    package = request.args.get('package', 'standard').lower()

    if not date_str:
        return jsonify({'error': 'No date provided'}), 400

    if package not in PACKAGE_LENGTHS:
        return jsonify({'error': 'Invalid package'}), 400

    slot_length = datetime.timedelta(minutes=PACKAGE_LENGTHS[package])
    buffer = datetime.timedelta(minutes=35)
    calgary_tz = pytz.timezone('America/Edmonton')
    date_base = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    open_time = calgary_tz.localize(date_base.replace(hour=8, minute=0, second=0))
    close_time = calgary_tz.localize(date_base.replace(hour=15, minute=0, second=0))

    blocked_times = []
    if not CALENDAR_ENABLED:
        events = []
        blocked_times = [(s, e + buffer) for s, e in demo_busy_events(date_base, calgary_tz)]
    else:
        service = build('calendar', 'v3', credentials=credentials)
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=open_time.isoformat(),
            timeMax=close_time.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

    for event in events:
        if 'start' in event and 'dateTime' in event['start']:
            start = datetime.datetime.fromisoformat(event['start']['dateTime'])
            if start.tzinfo is None:
                start = calgary_tz.localize(start)
            else:
                start = start.astimezone(calgary_tz)
            end = datetime.datetime.fromisoformat(event['end']['dateTime'])
            if end.tzinfo is None:
                end = calgary_tz.localize(end)
            else:
                end = end.astimezone(calgary_tz)
            blocked_times.append((start, end + buffer))

    slots = []
    cur = open_time
    while cur < close_time:
        slot_start = cur
        slot_end = cur + slot_length
        if slot_end > close_time:
            break
        conflict = False
        for b_start, b_end in blocked_times:
            if slot_start < b_end and slot_end > b_start:
                conflict = True
                break
        if not conflict:
            slots.append(slot_start.strftime("%H:%M"))
        cur += datetime.timedelta(minutes=15)
    return jsonify({'available_slots': slots})

@app.route('/book', methods=['POST'])
def book():
    package = request.form.get('package')
    date = request.form.get('date')
    time = request.form.get('time')
    vehicle = request.form.get('vehicle')
    address = request.form.get('address')
    postal_code = request.form.get('postal_code')
    phone = request.form.get('phone')
    email = request.form.get('email')
    addons = request.form.getlist('addons')

    if rate_limited(client_ip()):
        return "Too many bookings from this device. Please try again in an hour.", 429

    # Validate all required fields
    if not (package and date and time and vehicle and address and postal_code and email and phone):
        return "Missing information", 400

    # Email validation
    if not is_valid_email(email):
        return "Invalid email address", 400

    # Calgary phone
    phone_pattern = re.compile(r'^(403|587|825|368)[-\s.]?\d{3}[-\s.]?\d{4}$')
    if not phone_pattern.match(phone):
        return "Invalid Calgary phone number", 400

    # Calgary postal code
    postal_pattern = re.compile(r'^[Tt][23][A-Za-z][ -]?\d[A-Za-z]\d$')
    if not postal_pattern.match(postal_code):
        return "Invalid Calgary postal code", 400

    # Address contains "Calgary"
    if 'calgary' not in address.lower():
        return "Address must be in Calgary", 400

    calgary_tz = pytz.timezone('America/Edmonton')
    start_naive = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    start_datetime = calgary_tz.localize(start_naive)
    duration = PACKAGE_LENGTHS.get(package, 90)
    end_datetime = start_datetime + datetime.timedelta(minutes=duration)

    start_iso = start_datetime.isoformat()
    end_iso = end_datetime.isoformat()

    description = f"Email: {email}\nVehicle: {vehicle}\nAddress: {address}\nPostal Code: {postal_code}\nPhone: {phone}\nAdd-ons: {', '.join(addons) if addons else 'None'}"

    event = {
        'summary': f"Luxe Detailing - {package.title()} Package",
        'location': address,
        'description': description,
        'start': {'dateTime': start_iso, 'timeZone': 'America/Edmonton'},
        'end': {'dateTime': end_iso, 'timeZone': 'America/Edmonton'},
    }
    if CALENDAR_ENABLED:
        try:
            service = build('calendar', 'v3', credentials=credentials)
            service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        except Exception as e:
            print("Failed to add calendar event:", e)

    if EMAIL_ENABLED:
        send_confirmation_email(email, package, date, time, vehicle, address, postal_code, phone)
    return redirect(url_for('successful'))

if __name__ == '__main__':
    app.run(debug=False)
