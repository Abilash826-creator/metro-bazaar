# New Metro Big Bazaar — Billing System

Flask + PostgreSQL billing & inventory app. Deploy-ready for Render.

## Deploy to Render (Step by Step)

### Step 1 — Push to GitHub
1. Create a new repo at github.com
2. Upload all project files (drag & drop or git push)

### Step 2 — Create PostgreSQL DB on Render
1. Go to render.com → New + → PostgreSQL
2. Name: metro-bazaar-db | Plan: Free | Click Create
3. Copy the "Internal Database URL" — you'll need it next

### Step 3 — Deploy Web Service
1. render.com → New + → Web Service
2. Connect your GitHub repo
3. Settings:
   - Name: metro-bazaar
   - Runtime: Python 3
   - Build Command: pip install -r requirements.txt
   - Start Command: gunicorn app:app --preload
   - Plan: Free
4. Add Environment Variables:
   - DATABASE_URL = (paste Internal DB URL from Step 2)
   - SECRET_KEY = (any random string)
5. Click Create Web Service

### Step 4 — Initialize Database
The app auto-creates tables and seeds data on first request.
Just visit your app URL and it's ready!

## Login
- Username: admin
- Password: admin123

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variable
export DATABASE_URL=postgresql://user:pass@localhost:5432/metro_bazaar

# Run
python app.py
```

## Features
- Billing / POS with product search
- Auto stock deduction on billing
- Delete bill with automatic stock restore
- Sales history with date filters
- Inventory management with restock
- Low stock alerts on dashboard
- Printable receipts
