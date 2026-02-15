import requests
from data_manager import actualizar_datos

# --- TUS CREDENCIALES ---
TELEGRAM_TOKEN = "7987107497:AAFPYOZU9fmCILjDX-wls6gtC2hMDcI5NAo"
CHAT_ID = "7427129383"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID, 
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("✅ Notificación enviada.")
        else:
            print(f"⚠️ Error Telegram: {response.text}")
    except Exception as e:
        print(f"❌ Error conexión: {e}")

if __name__ == "__main__":
    print("🔄 Corriendo robot multilotería...")
    
    # Busca actualizaciones
    nuevos_datos = actualizar_datos()
    
    if nuevos_datos:
        # Construimos un mensaje bonito con todos los resultados
        fecha_reporte = nuevos_datos[0]['Fecha']
        mensaje = f"🚨 *RESULTADOS DEL {fecha_reporte}* 🚨\n\n"
        
        for sorteo in nuevos_datos:
            mensaje += (
                f"🎲 *{sorteo['Loteria']}*\n"
                f"└ {sorteo['1er']} - {sorteo['2do']} - {sorteo['3er']}\n\n"
            )
        
        mensaje += "📊 [Ver Gráficos](https://share.streamlit.io)"
        enviar_telegram(mensaje)
    else:
        print("💤 Sin novedades.")