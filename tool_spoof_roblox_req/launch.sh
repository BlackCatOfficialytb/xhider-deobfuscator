#!/bin/bash
if [ ! -d "ms-playwright" ]; then
    echo "Installing Playwright browsers..."
    python -m playwright install chromium
    echo "Done. You can delete this script now."
fi
python gui.py