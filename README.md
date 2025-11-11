# 🧠 SmartHome Raspberry Pi System

Sistema automatizado ejecutado en una **Raspberry Pi**, encargado de:
- Enviar recordatorios desde Google Sheets.  
- Avisar clima y temperatura.  
- Monitorear acciones y enviar alertas bursátiles (caídas bajo EMA 200).  
- Centralizar todos los mensajes en **Discord** mediante webhooks.

---

## ⚙️ Estructura del proyecto

```
/home/pi/smarthome/
│
├── main.py                       # Scheduler principal
├── utilities/
│   └── sender.py                 # Funciones de envío a Discord (webhooks)
│
├── home/
│   ├── reminders.py              # Recordatorios automáticos
│   ├── temp_now.py               # Clima puntual
│   └── weather.py                # Clima programado
│
├── investing/
│   └── stocks_ema200_alerts.py   # Alertas por caída bajo EMA 200
│
├── .venv/                        # Entorno virtual de Python
└── requirements.txt              # Dependencias de Python
```

---

## 🚀 Inicio automático (systemd)

El servicio se inicia al encender la Raspberry Pi mediante **systemd**.

### Archivo del servicio
`/etc/systemd/system/smarthome.service`

```ini
[Unit]
Description=SmartHome main scheduler
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/smarthome
ExecStart=/home/pi/smarthome/.venv/bin/python /home/pi/smarthome/main.py
Restart=always
RestartSec=5
Environment="TZ=America/Tijuana"

[Install]
WantedBy=multi-user.target
```

### Comandos útiles
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now smarthome.service
sudo systemctl status smarthome.service
journalctl -u smarthome.service -f
sudo systemctl restart smarthome.service
```

---

## 🧩 Entorno virtual

Para aislar tus dependencias:

```bash
cd ~/smarthome
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Salir del entorno:
```bash
deactivate
```

Actualizar dependencias:
```bash
pip install --upgrade -r requirements.txt
```

---

## 🌐 Webhooks configurados (`utilities/sender.py`)

```python
DISCORD_WEBHOOK_URL_DANGERSTACK = "..."   # Notificación de arranque
DISCORD_WEBHOOK_URL_REMINDER = "..."      # Recordatorios
DISCORD_WEBHOOK_URL_INVESTING = "..."     # Stocks / Finanzas
DISCORD_WEBHOOK_URL_WEATHER = "..."       # Clima
```

Cada módulo usa su webhook correspondiente.

---

## 📦 Módulos principales

### 🔔 `home/reminders.py`
- Lee una hoja de Google Sheets publicada como CSV.  
- Columnas: `ACTIVIDAD, FRECUENCIA, UNIDAD, FECHA, HORA`  
- Unidades soportadas: `DAY`, `WEEK`, `MONTH`, `YEAR`.  
- Guarda estado en `.reminders_state.json` para evitar duplicados.

### 🌡️ `home/temp_now.py` / `home/weather.py`
- Consulta [Open-Meteo](https://open-meteo.com/).  
- Envía alerta si la temperatura (o sensación térmica) baja del umbral configurado.

### 📉 `investing/stocks_ema200_alerts.py`
- Monitorea tickers definidos en `TICKERS`.  
- Envía alerta si el precio < EMA 200 × (1 − umbral).  
- Cooldown **individual por acción** (controlado con `.stocks_ema200_state.json`).

---

## 📊 Ejemplo de umbrales de caída por símbolo

| Símbolo | Umbral (%) | Descripción |
|----------|-------------|--------------|
| TSLA | 25 % | Alta volatilidad |
| AAPL | 12 % | Movimientos suaves |
| COIN | 35 % | Extremadamente volátil |
| NVDA | 20 % | Correcciones típicas |
| OSCR | 30 % | Mid/small cap volátil |
| AMZN | 15 % | Movimientos moderados |
| GOOGL | 15 % | Estable |
| MSFT | 12 % | Baja volatilidad |
| META | 18 % | Media-alta volatilidad |
| CRCL | 40 % | Cripto / riesgo alto |
| MSTR | 35 % | Proxy de Bitcoin |

---

## 🧭 Comandos básicos de Raspberry Pi

| Acción | Comando |
|--------|----------|
| Ver IP de la Pi | `hostname -I` |
| Ver procesos SmartHome | `ps aux | grep main.py` |
| Reiniciar Raspberry | `sudo reboot` |
| Apagar Raspberry | `sudo shutdown now` |
| Actualizar sistema | `sudo apt update && sudo apt upgrade -y` |
| Copiar archivo desde Windows | `scp archivo.zip pi@192.168.x.x:/home/pi/` |
| Extraer ZIP | `unzip archivo.zip -d /home/pi/carpeta` |
| Borrar carpeta | `rm -rf carpeta` |

---

## 🔧 Solución de problemas

| Problema | Solución |
|-----------|-----------|
| `externally-managed-environment` | Usa venv: `python3 -m venv .venv && source .venv/bin/activate` |
| `No module named yfinance` | Instala dentro del venv: `pip install yfinance` |
| `Error importing numpy` | Elimina cualquier carpeta local `numpy` y reinstala `pip install --no-cache-dir numpy` |
| Servicio no inicia | `journalctl -u smarthome.service -f` para ver logs |
| No envía mensajes | Revisa los webhooks y la conexión a internet (`ping discord.com`) |

---

## 🗓️ Respaldo rápido

```bash
cd /home/pi
zip -r smarthome_backup_$(date +%F).zip smarthome
```

Copiar al PC:
```bash
scp pi@192.168.x.x:/home/pi/smarthome_backup_2025-11-06.zip C:\Users\TuUsuario\Desktop\
```

---

## 🔒 Consejos finales

- Mantén actualizado el entorno:
  ```bash
  pip list --outdated
  ```
- Guarda copia del `requirements.txt` y de `sender.py` (tienen tus webhooks).  
- Evita usar `pip install --break-system-packages`.  
- Siempre activa el venv antes de ejecutar o actualizar.  
- Si modificas módulos o thresholds, reinicia el servicio con:
  ```bash
  sudo systemctl restart smarthome.service
  ```

---

### ✅ En cada arranque
Cuando la Raspberry Pi inicia, `main.py` envía un mensaje a `DISCORD_WEBHOOK_URL_DANGERSTACK` indicando que el **SmartHome Scheduler** se puso en marcha.

---

**Autor:** Sistema configurado en Raspberry Pi  
**Ubicación del proyecto:** `/home/pi/smarthome`  
**Última actualización:** 2025-11-06
