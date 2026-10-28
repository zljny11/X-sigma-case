# X-Sigma Case — Wagtopia Booking Demo

A mobile-friendly dog grooming booking app built with Python, SQLite, and plain HTML/CSS/JavaScript. Includes parent booking, groomer schedules, and overlap prevention. No login required.

## Quick start

Requires **Python 3.10+**. No third-party dependencies are needed.

```bash
git clone https://github.com/zljny11/X-sigma-case.git
cd X-sigma-case
python app.py
```

Open **http://127.0.0.1:8000**. The same server serves both the frontend and API. SQLite tables and sample data are created automatically; bookings persist across restarts.

On Windows, use `py app.py` if `python` is unavailable, or run `./start-demo.ps1` in PowerShell.

## Try it

1. Select a parent, their dog, a service, a groomer, and a start time.
2. Submit the booking, then open the groomer schedule to see it.
3. Try an overlapping appointment for the same groomer: it is rejected. Adjacent appointments are allowed. Each appointment lasts exactly 60 minutes.

## Run tests

```bash
python -m unittest -v test_app.py
```

Tests use temporary databases and cover validation, persistence, overlapping and adjacent bookings, midnight boundaries, and concurrent requests.

## Project files

- `app.py` — backend API and static server
- `schema.sql` / `seed.sql` — database schema and sample data
- `static/` — responsive frontend
- `screenshots/` — booking and schedule screenshots
- [Detailed demo guide (Chinese)](DEMO_GUIDE.zh-CN.md)

For local demos only. Appointment times use the shop's local time.
