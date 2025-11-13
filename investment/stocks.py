# stocks_ema200_alerts.py
import logging
from datetime import datetime
from typing import Dict, List, Tuple

import yfinance as yf
import pandas as pd

from utilities.sender import send_discord_message, DISCORD_WEBHOOK_URL_INVESTING
from pathlib import Path
import json
from datetime import datetime, timedelta

# Cooldown por símbolo (segundos)
SYMBOL_COOLDOWN_S: dict[str, int] = {
    # si no está aquí, usará COOLDOWN_DEFAULT_S
    "TSLA": 86400,   # 1 h
    "AAPL": 86400,   # 30 min
    "COIN": 86400,
    "NVDA": 86400,
    "OSCR": 86400,
    "AMZN": 86400,
    "GOOGL": 86400,
    "MSFT": 86400,
    "META": 86400,
    "CRCL": 86400,
    "MSTR": 86400,
}
COOLDOWN_DEFAULT_S = 1800  # 30 min por defecto

STATE_FILE = Path(__file__).with_name(".stocks_ema200_state.json")

# ============== CONFIG ==============
# Lista de tickers a vigilar (puedes agregar/quitar)
TICKERS: List[str] = [
    "TSLA","AAPL","COIN","NVDA","OSCR","AMZN","GOOGL","MSFT","META","CRCL","MSTR"
]

# Umbral por símbolo: cuánto % por debajo de la EMA200 debe estar el precio para alertar.
# Si un símbolo no está en el dict, usará DEFAULT_THRESHOLD_PCT.
SYMBOL_THRESHOLDS_PCT: Dict[str, float] = {
    "TSLA": 25.0,
    "AAPL": 12.0,
    "COIN": 35.0,
    "NVDA": 20.0,
    "OSCR": 30.0,
    "AMZN": 15.0,
    "GOOGL": 15.0,
    "MSFT": 12.0,
    "META": 18.0,
    "CRCL": 40.0,
    "MSTR": 35.0,
}
DEFAULT_THRESHOLD_PCT: float = 20.0

EMA_SPAN: int = 200         # EMA de 200 días
YF_PERIOD: str = "400d"     # historial para calcular correctamente EMA200
YF_INTERVAL: str = "1d"
USE_ADJ_CLOSE: bool = True  # usar cierre ajustado
# ===================================

def _get_hist(ticker: str) -> pd.DataFrame:
    """Descarga histórico diario suficiente para EMA200."""
    tkr = yf.Ticker(ticker)
    hist = tkr.history(period=YF_PERIOD, interval=YF_INTERVAL, auto_adjust=USE_ADJ_CLOSE)
    if hist is None or hist.empty:
        raise ValueError(f"Hist vacío para {ticker}")
    return hist

def _last_price_and_ema200(hist: pd.DataFrame) -> Tuple[float, float]:
    """Devuelve (precio_ultimo_cierre, ema200_ultimo)."""
    close_col = "Close"
    if close_col not in hist.columns:
        # yfinance a veces regresa 'Adj Close' si no se autoajusta
        close_col = "Adj Close" if "Adj Close" in hist.columns else hist.columns[-1]

    ema = hist[close_col].ewm(span=EMA_SPAN, adjust=False).mean()
    price = float(hist[close_col].iloc[-1])
    ema200 = float(ema.iloc[-1])
    return price, ema200

def _threshold_for(symbol: str) -> float:
    return SYMBOL_THRESHOLDS_PCT.get(symbol.upper(), DEFAULT_THRESHOLD_PCT)

def _format_pct(x: float) -> str:
    return f"{x:.2f}%"

def _maybe_alert(symbol: str) -> bool:
    """Calcula precio y EMA200; si precio <= EMA200*(1 - thr%), envía alerta y retorna True."""
    try:
        hist = _get_hist(symbol)
        price, ema200 = _last_price_and_ema200(hist)
        thr = _threshold_for(symbol) / 100.0
        trigger_level = ema200 * (1.0 - thr)

        below_pct = (1.0 - price / ema200) * 100.0  # % por debajo de la EMA200 (si negativo, está arriba)

        if price <= trigger_level:
            now = datetime.now()
            msg = (
                f"⚠️ **Alerta {symbol}** ⚠️\n"
                f"Precio: **{price:.2f}**\n"
                f"EMA200: **{ema200:.2f}**\n"
                f"Caída vs EMA200: **{_format_pct(below_pct)}**\n"
                f"Umbral configurado: **{_format_pct(_threshold_for(symbol))}** por debajo de EMA200\n"
                f"Hora: {now.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            send_discord_message(DISCORD_WEBHOOK_URL_INVESTING, msg)
            return True
        return False

    except Exception as e:
        logging.error(f"[{symbol}] error: {e}")
        return False
        
def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _save_state(state: dict) -> None:
    try:
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

def _cooldown_for(sym: str) -> int:
    return int(SYMBOL_COOLDOWN_S.get(sym.upper(), COOLDOWN_DEFAULT_S))

def _can_send(sym: str, now: datetime, state: dict) -> bool:
    last = state.get(sym.upper())
    if not last:
        return True
    try:
        last_dt = datetime.fromisoformat(last)
    except Exception:
        return True
    return (now - last_dt).total_seconds() >= _cooldown_for(sym)

def _mark_sent(sym: str, now: datetime, state: dict) -> None:
    state[sym.upper()] = now.isoformat(timespec="seconds")

def main() -> bool:
    any_sent = False
    state = _load_state()
    now = datetime.now()

    for sym in TICKERS:
        # respeta cooldown individual
        if not _can_send(sym, now, state):
            continue
        if _maybe_alert(sym):
            _mark_sent(sym, now, state)
            any_sent = True

    if any_sent:
        _save_state(state)
    return any_sent
