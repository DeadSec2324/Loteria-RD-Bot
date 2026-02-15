import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import os
import sys
from datetime import datetime

# --- CONFIGURACIÓN ---
# Si sabes usar GitHub Secrets, usa os.environ.get. Si no, pon tus claves aquí directo.
TOKEN = os.environ.get("TELEGRAM_TOKEN", "7987107497:AAFPYOZU9fmCILjDX-wls6gtC2hMDcI5NAo") 
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7427129383")
FILE_NAME = 'historial_loterias.csv'

# Mapeo de nombres
MAPA_CONECTATE = {
    "Anguila 10:00 AM": "Anguila Mañana", "Anguila 1:00 PM": "Anguila Medio Dia",
    "Anguila 6:00 PM": "Anguila Tarde", "Anguila 9:00 PM": "Anguila Noche",
    "Gana Más": "Nacional Gana Mas", "Lotería Nacional": "Nacional Noche",
    "Juega + Pega +": "Nacional Juega+Pega+", "Quiniela Leidsa": "Leidsa Quiniela",
    "Pega 3 Más": "Leidsa Pega 3 Mas", "Loto Pool": "Leidsa Loto Pool",
    "Quiniela Real": "Real Quiniela", "Loto Real": "Real Loto",
    "Quiniela Loteka": "Loteka Quiniela", "Mega Chances": "Loteka Mega Chances",
    "New York Tarde": "NY Tarde", "New York Noche": "NY Noche",
    "Florida Día": "Florida Dia", "Florida Noche": "Florida Noche",
    "La Primera Día": "La Primera Dia", "La Primera Noche": "La Primera Noche",
    "La Suerte 12:30": "La Suerte 12:30", "La Suerte 6:00": "La Suerte 18:00",
    "Quiniela LoteDom": "LoteDom Quiniela", "King Lottery 12:30": "King Lottery 12:30",
    "King Lottery 7:30": "King Lottery 7:30"
}

URLS = [
    "https://www.conectate.com.do/loterias/anguila/", "https://www.conectate.com.do/loterias/nacional/",
    "https://www.conectate.com.do/loterias/leidsa/", "https://www.conectate.com.do/loterias/real/",
    "https://www.conectate.com.do/loterias/loteka/", "https://www.conectate.com.do/loterias/new-york/",
    "https://www.conectate.com.do/loterias/florida/", "https://www.conectate.com.do/loterias/la-primera/",
    "https://www.conectate.com.do/loterias/la-suerte-dominicana/", "https://www.conectate.com.do/loterias/lote-dom/",
    "https://www.conectate.com.do/loterias/king-lottery/"
]

def enviar_telegram(mensaje):
    if "TU_TOKEN" in TOKEN: return # Evitar error si no hay token
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"})

def main():
    print("🚀 Ejecutando revisión automática en la nube...")
    
    # 1. Cargar datos existentes
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
    else:
        df = pd.DataFrame(columns=['Fecha', 'Loteria', '1er', '2do', '3er'])

    nuevos_registros = []
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    headers = {'User-Agent': 'Mozilla/5.0'}

    # 2. Escanear Web
    for url in URLS:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code != 200: continue
            soup = BeautifulSoup(r.text, 'html.parser')
            bloques = soup.find_all('div', class_='content-game')
            if not bloques: bloques = soup.find_all('div', class_='game-block')

            for bloque in bloques:
                texto = bloque.get_text(" ", strip=True)
                
                # Identificar Lotería
                nombre_app = None
                for web, app in MAPA_CONECTATE.items():
                    if web.lower() in texto.lower():
                        nombre_app = app
                        break
                if not nombre_app: continue

                # Extraer números
                nums = re.findall(r'\b\d{2}\b', texto)
                if len(nums) < 3: continue
                n1, n2, n3 = int(nums[-3]), int(nums[-2]), int(nums[-1])

                # Verificar si ya existe en el CSV
                existe = not df[
                    (df['Fecha'] == fecha_hoy) & (df['Loteria'] == nombre_app)
                ].empty

                if not existe:
                    item = {"Fecha": fecha_hoy, "Loteria": nombre_app, "1er": n1, "2do": n2, "3er": n3}
                    nuevos_registros.append(item)
                    print(f"✨ Nuevo detectado: {nombre_app}")

        except Exception as e:
            print(f"Error en {url}: {e}")

    # 3. Guardar y Avisar
    if nuevos_registros:
        df_new = pd.DataFrame(nuevos_registros)
        df_final = pd.concat([df_new, df], ignore_index=True)
        df_final.drop_duplicates(subset=['Fecha', 'Loteria'], keep='first', inplace=True)
        df_final.sort_values(by='Fecha', ascending=False, inplace=True)
        df_final.to_csv(FILE_NAME, index=False)
        
        # Mensaje Telegram
        msg = f"📢 *RESULTADOS AUTO-DETECTADOS* ☁️\n📅 {fecha_hoy}\n\n"
        for i in nuevos_registros:
            msg += f"🎱 *{i['Loteria']}*\n`{i['1er']:02d} - {i['2do']:02d} - {i['3er']:02d}`\n\n"
        
        # Calcular calientes rápido
        top3 = df_final[['1er','2do','3er']].stack().value_counts().head(3)
        msg += "🔥 *Calientes Globales:*\n"
        for n, c in top3.items(): msg += f"🎯 {n:02d} ({c})\n"
        
        enviar_telegram(msg)
        print("✅ Datos actualizados y notificados.")
    else:
        print("💤 No hay novedades.")

if __name__ == "__main__":
    main()