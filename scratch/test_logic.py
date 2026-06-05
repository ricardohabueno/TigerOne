import sys
import os

# Adiciona o diretório raiz ao path para podermos importar o backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.engine.normalizer import Normalizer
import urllib.parse
from datetime import datetime, timedelta

def test_time_normalization():
    test_cases = [
        ("10", "10:00"),
        ("1030", "10:30"),
        ("10:30", "10:30"),
        ("10h", "10:00"),
        ("10h:00", "10:00"),
        ("9", "09:00"),
        ("930", "09:30"),
        ("14h30", "14:30"),
        ("", "18:00"),
    ]
    
    for val, expected in test_cases:
        res = Normalizer.normalize_time_str(val)
        print(f"normalize_time_str({val!r}) -> {res!r} | Expected: {expected!r} | {'OK' if res == expected else 'FAIL'}")
        assert res == expected, f"Failed for {val}: got {res}, expected {expected}"

def test_date_normalization():
    test_cases = [
        ("28/05/2026", "28/05/2026"),
        ("28-05-2026", "28/05/2026"),
        ("28052026", "28/05/2026"),
        ("280526", "28/05/2026"),
        ("", datetime.now().strftime("%d/%m/%Y")),
    ]
    
    for val, expected in test_cases:
        res = Normalizer.normalize_date_str(val)
        print(f"normalize_date_str({val!r}) -> {res!r} | Expected: {expected!r} | {'OK' if res == expected else 'FAIL'}")
        assert res == expected, f"Failed for {val}: got {res}, expected {expected}"

def test_google_calendar_link():
    data_reserva = "28/05/2026"
    hora_reserva = "10:30"
    
    dt = datetime.strptime(f"{data_reserva} {hora_reserva}", "%d/%m/%Y %H:%M")
    dt_end = dt + timedelta(hours=1)
    
    fmt_start = dt.strftime("%Y%m%dT%H%M00")
    fmt_end = dt_end.strftime("%Y%m%dT%H%M00")
    
    assert fmt_start == "20260528T103000"
    assert fmt_end == "20260528T113000"
    
    title = "Lembrete: seu horário na Barbearia Tarantino."
    details = ""
    location = "Barbearia Tarantino"
    
    params = {
        "action": "TEMPLATE",
        "text": title,
        "dates": f"{fmt_start}/{fmt_end}",
        "details": details,
        "location": location
    }
    qs = urllib.parse.urlencode(params)
    link = f"https://calendar.google.com/calendar/render?{qs}"
    
    print("Generated Google Calendar link:")
    print(link)
    
    parsed = urllib.parse.urlparse(link)
    query_params = urllib.parse.parse_qs(parsed.query)
    
    assert query_params["text"][0] == title
    assert query_params["location"][0] == location
    assert query_params["dates"][0] == f"{fmt_start}/{fmt_end}"
    print("Google Calendar URL structure matches expectations! OK")

if __name__ == "__main__":
    print("Running tests...")
    test_time_normalization()
    test_date_normalization()
    test_google_calendar_link()
    print("All tests passed successfully! 🎉")
