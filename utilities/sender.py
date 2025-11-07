# File: utilities/sender.py
import requests

# === Webhooks por categoría ===
DISCORD_WEBHOOK_URL_INVESTING = "https://discord.com/api/webhooks/1428423347296796688/a6rfCu8z_tFrAYvpR-KfBfQ1BXbE7OEWIsYCNUSZNN4cGplTRE7XKvShwedk9ib3O-gJ"
DISCORD_WEBHOOK_URL_HOME = "https://discord.com/api/webhooks/1428426560188186664/fXHKNfrK1Ph6d4uknPPWSZ5T9tMho6h_03AEjU7TG6PaAEUxwt2qmLi5WTTHFgA06WtP"
DISCORD_WEBHOOK_URL_WEATHER = "https://discord.com/api/webhooks/1435323456223707240/hxxtD_jszwO_4Nyy5_SC-nZapRQ0Z76yVnGOpuxLNuSceGgmsJfz_hJRUOsDq-Kxxbg0"
DISCORD_WEBHOOK_URL_REMINDER = "https://discord.com/api/webhooks/1435347160471437544/WoOZhQtj1JkBk5KzjIBQpk16ZHv_ucFGGnwWd8mDQfdyVwN_Kgbxq6jSi4Yvys73uWd0"
DISCORD_WEBHOOK_URL_DANGERSTACK = "https://discord.com/api/webhooks/1436135019793088602/m0mEP164svaye87He-XTJbFR1w4BNC3kaW6UgIzYoHCCsz4RE8Jud3DoOzFemfsiT4lI"

def send_discord_message(webhook_url: str, content: str, send: bool = True):
    data = {"content": content}

    try:
        response = requests.post(webhook_url, json=data)
        """
        if response.status_code not in (200, 204):
            print(f"❌ Error al enviar mensaje ({response.status_code}): {response.text}")
        else:
            print("✅ Mensaje enviado a Discord correctamente.")
        """    
    except Exception as e:
        print(f"❌ Excepción al enviar mensaje: {e}")
