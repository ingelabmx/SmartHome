import yfinance as yf
import logging
from datetime import datetime
from utilities.sender import send_discord_message, DISCORD_WEBHOOK_URL_INVESTING

# Configuración
INDEX_TICKER = "SPY"  # Ticker para el S&P 500 en Yahoo Finance
ATH_VALUE = None  # si es None, se calculará automáticamente del histórico
DEFAULT_THRESHOLD = 2.0  # porcentaje de caída (por ejemplo, 2.0 significa caída ≥ 2.0%)

def fetch_current_price() -> float:
    """
    Obtiene el precio de cierre más reciente del índice S&P 500.
    """
    try:
        ticker = yf.Ticker(INDEX_TICKER)
        # Usamos history con period corto para obtener el precio más reciente
        hist = ticker.history(period="5d", interval="1d", auto_adjust=True)
        if hist.empty:
            raise ValueError("No se pudo obtener histórico")
        # Tomamos el último precio de cierre ajustado
        price = hist["Close"].iloc[-1]
        return float(price)
    except Exception as e:
        logging.error(f"Error al obtener precio actual: {e}")
        raise

def compute_ath(threshold_days: int = 3650) -> float:
    """
    Calcula el ATH (máximo histórico) usando un histórico amplio.
    threshold_days indica cuántos días hacia atrás mirar (por ejemplo, 10 años ≈ 3650 días).
    """
    ticker = yf.Ticker(INDEX_TICKER)
    hist = ticker.history(period=f"{threshold_days}d", interval="1d", auto_adjust=True)
    if hist.empty:
        raise ValueError("Histórico vacío para ATH")
    ath = float(hist["Close"].max())
    return ath

def main(threshold: float = DEFAULT_THRESHOLD) -> bool:
    """
    Función principal que será llamada por el scheduler en main.py.

    threshold: porcentaje mínimo de caída desde el ATH para activar cooldown.

    Retorna True si la caída ≥ threshold, o False si no.
    """
    try:
        now = datetime.now()
        current = fetch_current_price()
        #print(f"Precio actual: {current}")                  

        global ATH_VALUE
        if ATH_VALUE is None:
            # calcular ATH dinámico la primera vez
            ath = compute_ath()
            ATH_VALUE = ath
            #print(f"ATH: {ATH_VALUE}")
        else:
            ath = ATH_VALUE
            #print(f"Usando ATH fijo: {ath}")

        # Calcular caída porcentual
        # caída = (ATH - current) / ATH * 100
        drop_pct = (ath - current) / ath * 100
        #print(f"Caída desde ATH: {drop_pct:.4f}%")

        if drop_pct >= threshold:
            message = (
                f"⚠️ **Alerta SP500** ⚠️\n"
                f"El S&P500 ha caído **{drop_pct:.2f}%** desde su maximo historico de **{ATH_VALUE:.2f}**\n"
                f"Precio actual: **{current:.2f}**\n"
                f"Umbral configurado: {threshold}%\n"
                f"Hora: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"✅ Es buen momento para invertir!"
            )
            send_discord_message(DISCORD_WEBHOOK_URL_INVESTING, message)
            return True
        else:
            #print(f"Caída < {threshold}%, nada que hacer.")
            return False

    except Exception as e:
        logging.error(f"Error en sp500.main: {e}")
        send_discord_message(DISCORD_WEBHOOK_URL_INVESTING, f"❌ Error en sp500.py: {e}")
        return False
