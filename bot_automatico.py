import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import os
from datetime import datetime

# --- 🔑 TUS CREDENCIALES TELEGRAM ---
TOKEN = "7987107497:AAFPYOZU9fmCILjDX-wls6gtC2hMDcI5NAo"       # <--- ¡PON TU TOKEN!
CHAT_ID = "7427129383"   # <--- ¡PON TU CHAT ID!

# --- CONFIGURACIÓN ---
FILE_NAME = 'historial_loterias.csv'
TIEMPO_ESPERA = 3600  # Revisar cada 1 hora (3600 segundos). Puedes bajarlo a 600 (10 min).

# Mapa de nombres (Web -> App)
MAPA_CONECTATE = {
    "Anguila 10:00 AM": "Anguila Mañana",
    "Anguila 1:00 PM": "Anguila Medio Dia",
    "Anguila 6:00 PM": "Anguila Tarde",
    "Anguila 9:00 PM": "Anguila Noche",
    "Gana Más": "Nacional Gana Mas",
    "Lotería Nacional": "Nacional Noche",
    "Juega + Pega +": "Nacional Juega+Pega+",
    "Quiniela Leidsa": "Leidsa Quiniela",
    "Pega 3 Más": "Leidsa Pega 3 Mas",
    "Loto Pool": "Leidsa Loto Pool",
    "Quiniela Real": "Real Quiniela",
    "Loto Real": "Real Loto",
    "Quiniela Loteka": "Loteka Quiniela",
    "Mega Chances": "Loteka Mega Chances",
    "New York Tarde": "NY Tarde",
    "New York Noche": "NY Noche",
    "Florida Día": "Florida Dia",
    "Florida Noche": "Florida Noche",
    "La Primera Día": "La Primera Dia",
    "La Primera Noche": "La Primera Noche",
    "La Suerte 12:30": "La Suerte 12:30",
    "La Suerte 6:00": "La Suerte 18:00",
    "Quiniela LoteDom": "LoteDom Quiniela",
    "King Lottery 12:30": "King Lottery 12:30",
    "King Lottery 7:30": "King Lottery 7:30"
}

URLS_A_VIGILAR = [
    "https://www.conectate.com.do/loterias/anguila/",
    "https://www.conectate.com.do/loterias/nacional/",
    "https://www.conectate.com.do/loterias/leidsa/",
    "https://www.conectate.com.do/loterias/real/",
    "https://www.conectate.com.do/loterias/loteka/",
    "https://www.conectate.com.do/loterias/new-york/",
    "https://www.conectate.com.do/loterias/florida/",
    "https://www.conectate.com.do/loterias/la-primera/",
    "https://www.conectate.com.do/loterias/la-suerte-dominicana/",
    "https://www.conectate.com.do/loterias/lote-dom/",
    "https://www.conectate.com.do/loterias/king-lottery/"
]

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except:
        pass

def calcular_calientes():
    """Analiza el CSV y saca los 3 números que más salen globalmente."""
    if not os.path.exists(FILE_NAME): return "Sin datos"
    
    try:
        df = pd.read_csv(FILE_NAME)
        # Juntar todos los premios
        todos = pd.concat([df['1er'], df['2do'], df['3er']])
        conteo = todos.value_counts().head(3)
        
        texto = "🔥 *NÚMEROS CALIENTES (Global)*:\n"
        for num, freq in conteo.items():
            texto += f"🎯 *{num:02d}* (Salió {freq} veces)\n"
        return texto
    except:
        return "Calculando..."

def buscar_nuevos_resultados():
    print(f"[{datetime.now().strftime('%H:%M')}] 🔎 Escaneando web...")
    nuevos_hallazgos = []
    
    # Cargar base de datos actual para saber qué ya tenemos
    if os.path.exists(FILE_NAME):
        df_actual = pd.read_csv(FILE_NAME)
    else:
        df_actual = pd.DataFrame(columns=['Fecha', 'Loteria', '1er', '2do', '3er'])

    headers = {'User-Agent': 'Mozilla/5.0'}
    fecha_hoy = datetime.now().strftime("%Y-%m-%d") # Ej: 2026-02-15

    for url in URLS_A_VIGILAR:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code != 200: continue
            
            soup = BeautifulSoup(r.text, 'html.parser')
            bloques = soup.find_all('div', class_='content-game')
            if not bloques: bloques = soup.find_all('div', class_='game-block')
            
            for bloque in bloques:
                texto = bloque.get_text(" ", strip=True)
                texto_lower = texto.lower()
                
                # Identificar Lotería
                nombre_app = None
                for nombre_web, nombre_interno in MAPA_CONECTATE.items():
                    if nombre_web.lower() in texto_lower:
                        nombre_app = nombre_interno
                        break
                
                if not nombre_app: continue

                # EXTRAER NÚMEROS (Últimos 3)
                numeros = re.findall(r'\b\d{2}\b', texto)
                if len(numeros) < 3: continue
                premios = [int(n) for n in numeros]
                n1, n2, n3 = premios[-3], premios[-2], premios[-1]

                # --- VERIFICACIÓN DE NOVEDAD ---
                # ¿Ya tenemos este sorteo guardado con la fecha de HOY?
                ya_existe = not df_actual[
                    (df_actual['Fecha'] == fecha_hoy) & 
                    (df_actual['Loteria'] == nombre_app)
                ].empty

                # Si NO existe en el Excel, ¡ES NUEVO!
                if not ya_existe:
                    # Lo agregamos a la lista de hallazgos
                    nuevos_hallazgos.append({
                        "Fecha": fecha_hoy,
                        "Loteria": nombre_app,
                        "1er": n1, "2do": n2, "3er": n3
                    })
                    print(f"   ✨ ¡NUEVO! {nombre_app}: {n1}-{n2}-{n3}")

        except Exception as e:
            print(f"Error técnico en {url}: {e}")

    return nuevos_hallazgos

def main():
    print("🤖 ROBOT VIGILANTE INICIADO")
    print("⏳ Revisaré la página cada 1 hora. No cierres esta ventana.")
    
    primer_inicio = True
    
    while True:
        # 1. Buscar
        nuevos = buscar_nuevos_resultados()
        
        # 2. Si hay nuevos, guardar y avisar
        if nuevos:
            df_nuevos = pd.DataFrame(nuevos)
            
            # Cargar archivo existente o crear nuevo
            if os.path.exists(FILE_NAME):
                df_viejo = pd.read_csv(FILE_NAME)
                df_final = pd.concat([df_nuevos, df_viejo], ignore_index=True)
            else:
                df_final = df_nuevos
            
            # Guardar en CSV (Así la App se actualiza sola si subes a GitHub)
            df_final.drop_duplicates(subset=['Fecha', 'Loteria'], keep='first', inplace=True)
            df_final.sort_values(by='Fecha', ascending=False, inplace=True)
            df_final.to_csv(FILE_NAME, index=False)
            print("💾 Base de datos actualizada en PC.")
            
            # --- ENVIAR TELEGRAM ---
            calientes = calcular_calientes()
            mensaje = f"📢 *NUEVOS RESULTADOS DETECTADOS* 🇩🇴\n📅 {datetime.now().strftime('%d/%m/%Y')}\n\n"
            
            for item in nuevos:
                mensaje += f"🎱 *{item['Loteria']}*\n`{item['1er']:02d} - {item['2do']:02d} - {item['3er']:02d}`\n\n"
            
            mensaje += "-------------------\n"
            mensaje += calientes
            mensaje += "\n🤖 _Bot Automático_"
            
            enviar_telegram(mensaje)
            print("✅ Notificación enviada a Telegram.")
        
        else:
            print("💤 Nada nuevo por ahora.")
            # Si es la primera vez que corre, mandamos los calientes para confirmar que funciona
            if primer_inicio:
                enviar_telegram(f"🤖 *BOT INICIADO*\nEstoy vigilando...\n\n{calcular_calientes()}")
                primer_inicio = False

        # 3. Esperar para la siguiente ronda
        time.sleep(TIEMPO_ESPERA)

if __name__ == "__main__":
    main()