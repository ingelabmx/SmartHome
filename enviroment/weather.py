# temp_now.py
import requests, sys, logging
from datetime import datetime
from utilities.sender import send_discord_message, DISCORD_WEBHOOK_URL_WEATHER

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:
    ZoneInfo = None

# ==================== Configuración ====================
LAT = 32.5149                 # Tijuana
LON = -117.0382
TZ  = "America/Tijuana"

NOTIFY_AT = "05:30"           # Hora local a la que debe avisar (formato 24h HH:MM)
WINDOW_MIN = 5                # Ventana (±) para tolerar ejecuciones alrededor de la hora (en minutos)

COLD_THRESHOLD_C = 15.0       # Umbral de frío (°C) para disparar el aviso
USE_APPARENT = False          # True = usar sensación térmica; False = usar temperatura ambiente
# =======================================================

def _now_local():
    if ZoneInfo:
        return datetime.now(ZoneInfo(TZ))
    return datetime.now()

def _within_window(now, hhmm: str, window_min: int) -> bool:

    h, m = [int(x) for x in hhmm.split(":")]
    target = now.replace(hour=h, minute=m, second=0, microsecond=0)
    delta_min = abs((now - target).total_seconds()) / 60.0
    return delta_min <= (window_min / 2.0)

def _fetch_current(lat: float, lon: float, tz: str):

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,apparent_temperature",
        "timezone": tz,
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    cur = data.get("current", {})
    temp = cur.get("temperature_2m")
    app  = cur.get("apparent_temperature")
    ts   = cur.get("time")
    return float(temp) if temp is not None else None, float(app) if app is not None else None, ts

def main(threshold_c: float = COLD_THRESHOLD_C) -> bool:
    now = _now_local()

    # 1) Solo ejecutar la lógica exactamente a la hora deseada (con ventana)
    if not _within_window(now, NOTIFY_AT, WINDOW_MIN):
        return False

    try:
        temp_c, apparent_c, ts = _fetch_current(LAT, LON, TZ)
        value = apparent_c if USE_APPARENT else temp_c
        metric = "sensación térmica" if USE_APPARENT else "temperatura"

        if value is None:
            raise ValueError("No se recibió dato de temperatura actual.")

        if value < threshold_c:
            message = (
                f"🌡️ **Alerta de clima** 🌡️\n"
                f"La {metric} de hoy es **{value:.1f} °C** \n"
                f"Ubicación: **Tijuana**\n"
                f"**Tip:** Hoy vale la pena abrigarse. 🧥"
            )
            send_discord_message(DISCORD_WEBHOOK_URL_WEATHER, message)
            return True  # -> permite a tu scheduler aplicar cooldown
        else:
            return False

    except Exception as e:
        logging.error(f"Error en temp_now.py: {e}")
        # Reporta el error en el mismo canal para visibilidad
        try:
            send_discord_message(DISCORD_WEBHOOK_URL_WEATHER, f"❌ Error en temp_now.py: {e}")
        except Exception:
            pass
        return False

if __name__ == "__main__":
    # Si lo corres manualmente, solo hará la comprobación y (si corresponde) enviará.
    # Imprime el resultado para debug rápido.
    result = main()
