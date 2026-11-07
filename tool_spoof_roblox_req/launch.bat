@echo off
call :setup
python gui.py
goto :end
:setup
if not exist "ms-playwright" (
    echo Installing Playwright browsers...
    python -m playwright install chromium
    echo Done. You can delete this .bat file now.
)
:end