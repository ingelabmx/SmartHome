# File: investment/sp500.py
import random

def main():
    """
    Simula una revisión del SP500.
    Devuelve True si hay caída > 2% (para activar cooldown).
    """
    print("📊 Revisando SP500...")
    simulated_change = random.uniform(-3, 3)
    print(f"Variación simulada: {simulated_change:.2f}%")

    if simulated_change <= -2:
        print("⚠️  Caída detectada > 2%. Enviando alerta y activando cooldown.")
        return True  # activa cooldown 24h
    return False  # no activa cooldown
