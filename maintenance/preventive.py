# File: maintenance/preventive.py
import random
from datetime import datetime
from utilities.sender import send_discord_message, DISCORD_WEBHOOK_URL_HOME

def main() -> bool:
    """
    Simula una revisión de mantenimiento preventivo.
    Envía mensaje a Discord si hay alerta.
    """
    now = datetime.now()
    #print(f"[{now.strftime('%H:%M:%S')}] Revisando tareas preventivas...")

    issue_found = random.choice([False])  # 0% probabilidad

    if issue_found:
        message = (
            f"🔧 **Mantenimiento Preventivo**\n"
            f"Se detectó una tarea pendiente en el sistema, han pasado 6 meses desde tu ultimo cambio de aceite.\n"
            f"Hora: {now.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        send_discord_message(DISCORD_WEBHOOK_URL_HOME, message)
        return True
    else:
        #print("Todo en orden. Sin tareas pendientes.")
        return False
