# Luxe Mobile Detailing – Booking Website

A full-stack booking website I built for **Luxe Mobile Detailing**, a mobile car detailing business in Calgary. The site was used in production by the business to take real customer bookings in 2025. The business has since stopped operating, so this repo is now kept as a portfolio project.

**Live demo:** [add Render link here] *(demo mode: bookings are not sent anywhere)*

## What it did

Customers picked a detailing package, chose an open time slot, and booked in a couple of minutes. The owner no longer had to coordinate every booking by text or phone.

- **Live availability.** The booking page pulled the owner's Google Calendar and only showed time slots that were actually open. Slot length depended on the package (90 min standard, 3 hr premium, 8 hr elite), with a 35-minute travel buffer between jobs and business hours of 8 AM to 3 PM.
- **Automatic scheduling.** A confirmed booking was written straight into the owner's Google Calendar with the vehicle, address, phone number and add-ons in the event details.
- **Email confirmations.** Customers got a confirmation email with their booking details as soon as they submitted.
- **Input validation.** The server checked email format, Calgary phone numbers (403/587/825/368), Calgary postal codes (T2/T3) and that the address was in Calgary, since the business only served the city.
- **Marketing site.** Homepage with service packages, a photo gallery and social links.

## My role

I was the only developer. I worked directly with the owner to gather requirements, built the front end and back end, deployed it, and kept fixing issues and updating features after launch as the business's needs changed (for example, tightening the calendar booking window and moving credentials out of the code).

## Tech stack

| Area | Tools |
|---|---|
| Back end | Python, Flask, Gunicorn |
| Integrations | Google Calendar API (service account), Gmail SMTP |
| Front end | HTML, CSS, JavaScript, Jinja templates |
| Hosting | Render |

## How it works

```
Customer → booking.html
             │  picks date + package
             ▼
        GET /available-times ──► Google Calendar (existing events)
             │  returns open slots
             ▼
        POST /book ──► validate input
                    ├─► create Google Calendar event
                    └─► send confirmation email
             ▼
        successful.html
```

## Demo mode

This copy runs in **demo mode** by default, because the business is closed and its Google account is no longer in use. Demo mode keeps the real booking flow: the availability algorithm, package durations, travel buffer and all input validation run exactly as they did in production. The only differences are that existing bookings are simulated, and confirmed bookings are not saved to a calendar or emailed.

## Running it locally

```bash
pip install -r requirements.txt
python backend.py        # starts in demo mode
```

To run the original production behaviour, set `DEMO_MODE=false` and provide your own credentials:

```bash
export DEMO_MODE=false
export GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
export SENDER_EMAIL=you@gmail.com
export APP_PASSWORD=your-gmail-app-password
```

## Deploying

`render.yaml` deploys the demo to Render: build with `pip install -r requirements.txt`, start with `gunicorn backend:app`.
