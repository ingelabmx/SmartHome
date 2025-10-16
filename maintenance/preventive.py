# File: maintenance/preventive.py
import random

def main():
    """
    Simula una verificación de mantenimiento preventivo.
    """
    print("🛠️  Revisando tareas preventivas...")
    event = random.choice([True, False, True, False])  # 25% chance de activar cooldown

    if event:
        print("🔔 Se detectó una tarea pendiente. Enviando recordatorio.")
        return True  # activa cooldown (3h)
    return False
