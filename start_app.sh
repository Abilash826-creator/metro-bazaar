#!/bin/bash

echo ""
echo "=================================================="
echo "  New Metro Big Bazaar - Billing & Inventory"
echo "=================================================="
echo ""

# Move to script directory
cd "$(dirname "$0")"

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "  [ERROR] Python 3 is not installed."
    echo "  Install it from https://www.python.org/downloads/"
    exit 1
fi

# Check Flask
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "  Flask not found. Installing..."
    pip3 install Flask Werkzeug --quiet
fi

echo "  Starting application..."
echo "  Browser will open automatically."
echo "  Login: admin / admin123"
echo ""
echo "  Press Ctrl+C to stop the app."
echo "--------------------------------------------------"
echo ""

python3 launcher.py
