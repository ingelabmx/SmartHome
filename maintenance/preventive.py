#https://docs.google.com/spreadsheets/d/e/2PACX-1vSTpapmVlF-Y6AhJu0k-sKCkO0w4RkMo01rajGq5IcicbL0p-Ih0B99Iu4Wr6biX5YEngI6v2sqYKqp/pub?gid=0&single=true&output=csv
# home/reminders.py
from __future__ import annotations
import csv, io, json, logging, calendar
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests

try:
    from zoneinfo import ZoneInfo  # Py 3.9+
except Exception:
    ZoneInfo = None

from utilities.sender import send_discord_message, DISCORD_WEBHOOK_URL_REMINDER

# =============== CONFIG ===============
TIMEZONE = "America/Tijuana"
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSTpapmVlF-Y6AhJu0k-sKCkO0w4RkMo01rajGq5IcicbL0p-Ih0B99Iu4Wr6biX5YEngI6v2sqYKqp/pub?gid=0&single=true&output=csv"  # pega aquí tu enlace .../pub?output=csv
LOCAL_CSV_PATH = "" # opcional, CSV local
WINDOW_MIN = 20      # ventana ±10 min alrededor de la hora objetivo
STATE_FILE = Path(__file__).with_name(".reminders_state.json")
# Catch-up de vencidos (para MONTH con FECHA como fecha completa)
CATCH_UP_OVERDUE = True      # True: avisa inmediato si detecta atraso
CATCH_UP_MAX_DAYS = None     # None = sin límite; o pon un entero (p. ej. 30) para avisar si el atraso ≤ 30 días


# Fallback de ejemplo (borra si ya tienes CSV)
FALLBACK_ROWS = [
    {"ACTIVIDAD":"Pagar Tarjeta Costco","FRECUENCIA":"1","UNIDAD":"MONTH","FECHA":"5","HORA":"1300"},
    {"ACTIVIDAD":"Pagar Tarjeta Invex","FRECUENCIA":"1","UNIDAD":"MONTH","FECHA":"15","HORA":"900"},
    {"ACTIVIDAD":"Pagar Internet","FRECUENCIA":"1","UNIDAD":"MONTH","FECHA":"1","HORA":"900"},
    {"ACTIVIDAD":"Verificar presion llantas","FRECUENCIA":"1","UNIDAD":"WEEK","FECHA":"5","HORA":"1500"},  # 1=Lun..7=Dom
    {"ACTIVIDAD":"Cambiar llantas","FRECUENCIA":"6","UNIDAD":"MONTH","FECHA":"4/11/2025","HORA":"1150"},
]
# ======================================

def _now_local() -> datetime:
    return datetime.now(ZoneInfo(TIMEZONE)) if ZoneInfo else datetime.now()

def _load_rows() -> List[Dict[str,str]]:
    if SHEET_CSV_URL:
        try:
            r = requests.get(SHEET_CSV_URL, timeout=10)
            r.raise_for_status()
            return list(csv.DictReader(io.StringIO(r.text)))
        except Exception as e:
            logging.error(f"Google CSV error: {e}")
    if LOCAL_CSV_PATH:
        try:
            with open(LOCAL_CSV_PATH, "r", encoding="utf-8", newline="") as f:
                return list(csv.DictReader(f))
        except Exception as e:
            logging.error(f"CSV local error: {e}")
    return FALLBACK_ROWS

def _parse_int(s: str) -> Optional[int]:
    try: return int(str(s).strip())
    except Exception: return None

def _parse_hhmm(h: str) -> Optional[tuple[int,int]]:
    s = (h or "").strip()
    if ":" in s:
        try:
            hh, mm = s.split(":"); return int(hh), int(mm)
        except Exception: return None
    n = _parse_int(s); 
    if n is None: return None
    return divmod(n, 100)  # 1150 -> (11,50)

def _parse_date_any(s: str) -> Optional[datetime]:
    s = (s or "").strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.replace(tzinfo=ZoneInfo(TIMEZONE)) if ZoneInfo else dt
        except Exception:
            continue
    return None

def _within_window(now: datetime, hh: int, mm: int) -> bool:
    tgt = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    return abs((now - tgt).total_seconds())/60.0 <= (WINDOW_MIN/2)

def _last_dom(y:int, m:int) -> int:
    return calendar.monthrange(y, m)[1]

def _add_months_keep_dom(dt: datetime, months: int) -> datetime:
    """Suma 'months' manteniendo el día (capado al último del mes)."""
    y = dt.year + (dt.month - 1 + months) // 12
    m = (dt.month - 1 + months) % 12 + 1
    d = min(dt.day, _last_dom(y, m))
    # preserva tzinfo si existe
    return dt.replace(year=y, month=m, day=d)

def _dt_with_time(d: datetime, hh: int, mm: int) -> datetime:
    """Devuelve 'd' con la hora hh:mm, conservando tzinfo."""
    return d.replace(hour=hh, minute=mm, second=0, microsecond=0)

def _load_state() -> Dict[str,str]:
    try: return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception: return {}

def _save_state(st: Dict[str,str]) -> None:
    if len(st) > 1000:
        keys = list(st.keys())[-500:]
        st = {k: st[k] for k in keys}
    try: STATE_FILE.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    except Exception: pass

def _sent_key(activity:str, date_key:str, hh:int, mm:int) -> str:
    return f"{activity}|{date_key}|{hh:02d}:{mm:02d}"

def _today_key(now: datetime) -> str:
    return now.strftime("%Y-%m-%d")

# -------- Reglas --------
def _is_day_due(row, now, hh, mm) -> bool:
    freq = max(1, _parse_int(row.get("FRECUENCIA","1")) or 1)
    if freq == 1:
        return _within_window(now, hh, mm)
    base = _parse_date_any(row.get("FECHA",""))
    if not base: return False
    days = (now.date() - base.date()).days
    return days >= 0 and (days % freq == 0) and _within_window(now, hh, mm)

def _is_week_due(row, now, hh, mm) -> bool:
    # FECHA = 1..7 (1=Lun .. 7=Dom)
    dow = _parse_int(row.get("FECHA",""))
    if dow is None or not (1 <= dow <= 7): return False
    mon1 = now.weekday() + 1
    if mon1 != dow or not _within_window(now, hh, mm): return False
    freq = max(1, _parse_int(row.get("FRECUENCIA","1")) or 1)
    if freq == 1: return True
    base = _parse_date_any(row.get("FECHA_BASE","")) or _parse_date_any(row.get("START",""))
    if base:
        weeks = (now.date() - base.date()).days // 7
        return weeks >= 0 and (weeks % freq == 0)
    return True  # sin base, acepta el match de día/hora

def _is_month_due(row, now: datetime, hh: int, mm: int):
    """
    MONTH:
      - FECHA con barra/guión => tratar como FECHA BASE completa (d/m/Y, d/m/y, Y-m-d).
        Dispara en base + k*FRECUENCIA meses. Si CATCH_UP_OVERDUE=True y ya pasó, envía una vez
        por la última vencida (luego se reengancha al próximo múltiplo).
      - FECHA numérica (1..31) y FRECUENCIA=1 => mensual simple en ese día exacto.
    Retorna (due: bool, due_dt: datetime|None, base_str: str|None, freq: int|None)
    """
    freq = max(1, _parse_int(row.get("FRECUENCIA", "1")) or 1)
    fecha_raw = (row.get("FECHA") or "").strip()

    # ¿Fecha base completa?
    is_full_date = ("/" in fecha_raw) or ("-" in fecha_raw)
    base = _parse_date_any(fecha_raw) if is_full_date else None

    if base:
        # ---- Caso FECHA BASE ----
        first_due = _add_months_keep_dom(base, freq)
        first_due_dt = _dt_with_time(first_due, hh, mm)
        if now < first_due_dt:
            return (False, None, None, None)

        months_since = (now.year - base.year) * 12 + (now.month - base.month)
        k = max(1, months_since // freq)

        last_due = _add_months_keep_dom(base, k * freq)
        last_due_dt = _dt_with_time(last_due, hh, mm)

        # Si quedó “por delante”, retrocede un múltiplo
        if last_due_dt > now and k >= 1:
            k -= 1
            last_due = _add_months_keep_dom(base, k * freq)
            last_due_dt = _dt_with_time(last_due, hh, mm)

        # a) On-time: hoy es la fecha/hora exacta
        if _within_window(now, hh, mm) and now.date() == last_due_dt.date():
            return (True, last_due_dt, fecha_raw, freq)

        # b) Catch-up: la última vencida es <= now (enviar una vez)
        if CATCH_UP_OVERDUE and last_due_dt <= now:
            if CATCH_UP_MAX_DAYS is None:
                return (True, last_due_dt, fecha_raw, freq)
            overdue_days = (now - last_due_dt).total_seconds() / 86400.0
            if overdue_days <= float(CATCH_UP_MAX_DAYS):
                return (True, last_due_dt, fecha_raw, freq)

        return (False, None, None, None)

    # ---- Caso día del mes (mensual simple) ----
    day_cfg = _parse_int(fecha_raw)
    if day_cfg is None:
        return (False, None, None, None)
    if freq != 1:
        # Para día del mes sin base solo permitimos mensual simple (freq=1)
        return (False, None, None, None)

    last_dom = _last_dom(now.year, now.month)
    target_day = min(max(1, day_cfg), last_dom)
    if now.day != target_day:
        return (False, None, None, None)
    if not _within_window(now, hh, mm):
        return (False, None, None, None)
    return (True, _dt_with_time(now, hh, mm), None, None)


def _is_year_due(row, now, hh, mm) -> bool:
    base = _parse_date_any(row.get("FECHA",""))
    if not base: return False
    if (now.month, now.day) != (base.month, base.day): return False
    freq = max(1, _parse_int(row.get("FRECUENCIA","1")) or 1)
    if now.year < base.year + freq: return False
    return _within_window(now, hh, mm)

def _normalize_unit(s: str) -> str:
    s = (s or "").strip().upper()
    return s

def _due_for_row(row: Dict[str, str], now: datetime) -> Optional[Dict[str, str]]:
    actividad = (row.get("ACTIVIDAD") or "").strip()
    unidad = (row.get("UNIDAD") or "").strip().upper()
    hhmm = _parse_hhmm(row.get("HORA", ""))
    if not actividad or not unidad or not hhmm:
        return None
    hh, mm = hhmm

    if unidad == "DAY" and _is_day_due(row, now, hh, mm):
        return {"actividad": actividad, "hh": hh, "mm": mm, "unidad": "DAY", "date_key": now.strftime("%Y-%m-%d")}

    if unidad == "WEEK" and _is_week_due(row, now, hh, mm):
        return {"actividad": actividad, "hh": hh, "mm": mm, "unidad": "WEEK", "date_key": now.strftime("%Y-%m-%d")}

    if unidad == "MONTH":
        due, due_dt, base_str, freq = _is_month_due(row, now, hh, mm)
        if due:
            return {
                "actividad": actividad,
                "hh": hh, "mm": mm, "unidad": "MONTH",
                # usamos la fecha real de vencimiento (on-time o catch-up) para el control de reenvío
                "date_key": (due_dt.strftime("%Y-%m-%d") if due_dt else now.strftime("%Y-%m-%d")),
                # extras para el mensaje (solo si hay base)
                "base_str": base_str,
                "freq": freq,
            }
        return None

    if unidad == "YEAR" and _is_year_due(row, now, hh, mm):
        return {"actividad": actividad, "hh": hh, "mm": mm, "unidad": "YEAR", "date_key": now.strftime("%Y-%m-%d")}

    return None

def _send(activity: str, now: datetime, hh: int, mm: int, *, base_str: str | None = None, unit: str | None = None, freq: int | None = None) -> None:
    hora_txt = f"{hh:02d}:{mm:02d}"
    fecha_txt = now.strftime("%Y-%m-%d")
    msg = [
        f"🔔 **{activity}**",
        f"Hoy **{fecha_txt}** a las **{hora_txt}** toca realizarlo. ✅",
    ]
    if base_str and unit and freq:
        unit_txt = {"DAY":"días","WEEK":"semanas","MONTH":"meses","YEAR":"años"}.get(unit.upper(), unit.lower())
        msg.append(f"🗓️ Fecha original: **{base_str}**  |  Frecuencia: **{freq} {unit_txt}**")

    send_discord_message(DISCORD_WEBHOOK_URL_REMINDER, "\n".join(msg))



def main() -> bool:
    now = _now_local()
    rows = _load_rows()
    state = _load_state()
    sent = False

    for row in rows:
        due = _due_for_row(row, now)
        if not due:
            continue

        date_key = due.get("date_key") or now.strftime("%Y-%m-%d")
        key = _sent_key(due["actividad"], date_key, due["hh"], due["mm"])
        if key in state:
            continue

        try:
            _send(
                due["actividad"], now, due["hh"], due["mm"],
                base_str=due.get("base_str"),
                unit=due.get("unidad"),
                freq=due.get("freq"),
            )
            state[key] = now.isoformat(timespec="seconds")
            sent = True
            # time.sleep(0.4)  # opcional: anti 429 si hay muchas
        except Exception as e:
            logging.error(f"Error enviando '{due['actividad']}': {e}")

    if sent:
        _save_state(state)
    return sent



if __name__ == "__main__":
    print("Notificado" if main() else "Sin acción")
