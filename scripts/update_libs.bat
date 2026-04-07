@echo off
echo ==========================================
echo STOPPING PYTHON SERVERS (Uvicorn)...
echo ==========================================
taskkill /F /IM python.exe /T

echo.
echo ==========================================
echo UPDATING LIBRARIES...
echo ==========================================
pip install --upgrade langchain-google-genai google-generativeai==0.5.2

echo.
echo ==========================================
echo DONE!
echo You can now restart the backend with:
echo uvicorn app.main:app --reload --app-dir backend
echo ==========================================
pause
