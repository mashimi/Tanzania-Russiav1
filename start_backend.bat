@echo off
cd /d "%~dp0\tz-radar-saas\backend"
echo Starting TZ Radar Backend...
uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause