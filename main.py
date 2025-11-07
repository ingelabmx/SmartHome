# File: main.py
import importlib
import asyncio
import time
from datetime import datetime, timedelta
from utilities.sender import send_discord_message, DISCORD_WEBHOOK_URL_DANGERSTACK

# === CONFIGURACIÓN DE SCRIPTS ===
SCRIPTS = {
    "investment.sp500": {"interval": 3600, "cooldown": 86400},   # cada 1h, cooldown 24h si activa
    "enviroment.weather": {"interval": 60, "cooldown": 86000},
    "maintenance.preventive": {"interval": 60, "cooldown": 60},  # cada 60 s, cooldown 60 s
    "investment.stocks": {"interval": 900, "cooldown": 600} # cada 15 min, cooldown 10 min
}

# === CONTROL DE TIEMPOS ===
next_run = {}
cooldowns = {}

async def run_script(name):
    """Ejecuta un script dinámicamente y maneja su cooldown."""
    try:
        module = importlib.import_module(name)
        #print(f"[{datetime.now().strftime('%H:%M:%S')}] Ejecutando {name}...")

        # Ejecuta la función principal del módulo
        result = await asyncio.to_thread(module.main)

        # Si el script devuelve True, aplica cooldown
        if result:
            cooldowns[name] = datetime.now() + timedelta(seconds=SCRIPTS[name]["cooldown"])
            print(f"⚠️  {name} activó señal, cooldown hasta {cooldowns[name]}")

    except Exception as e:
        print(f"❌ Error ejecutando {name}: {e}")

async def scheduler():
    """Loop infinito que ejecuta scripts según sus intervalos y cooldowns."""
    for name in SCRIPTS:
        next_run[name] = datetime.now()

    while True:
        now = datetime.now()

        for name, config in SCRIPTS.items():
            # Revisar si está en cooldown
            if name in cooldowns and cooldowns[name] > now:
                continue

            # Revisar si ya toca ejecutar
            if now >= next_run[name]:
                await run_script(name)
                next_run[name] = now + timedelta(seconds=config["interval"])

        await asyncio.sleep(10)  # espera pequeña entre iteraciones

if __name__ == "__main__":
    from datetime import datetime
    print("🚀 Iniciando SmartHome Scheduler...")

    # ✅ Notificación de arranque (siempre que se ejecute main.py)
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        scripts_list = ", ".join(SCRIPTS.keys())
        msg = (
            f"🟢 **SmartHome Scheduler iniciado**\n"
            f"Inicio: **{now}**\n"
            f"Scripts cargados: `{scripts_list}`"
        )
        send_discord_message(DISCORD_WEBHOOK_URL_DANGERSTACK, msg)
    except Exception as e:
        print(f"⚠️  No se pudo notificar arranque: {e}")

    asyncio.run(scheduler())