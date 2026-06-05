$env:PYTHONPATH = "C:\Users\RICARDO\Documents\TigerOne"
.\venv\Scripts\pip install -r requirements.txt
.\venv\Scripts\playwright install chromium
.\venv\Scripts\uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
