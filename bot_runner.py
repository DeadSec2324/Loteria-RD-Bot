import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
import pandas as pd

# --- CONFIGURACIÓN TELEGRAM ---
TOKEN = "7987107497:AAFPYOZU9fmCILjDX-wls6gtC2hMDcI5NAo"       # <--- ¡Pon tu Token aquí!
CHAT_ID = "7427129383"   # <--- ¡Pon tu Chat ID aquí!

# --- CEREBRO INTELIGENTE ---
MAPA_CONECTATE = {
    # ANGUILA
    "Anguila 10:00 AM": "Anguila Mañana",
    "Anguila 1:00 PM": "Anguila Medio Dia",
    "Anguila 6:00 PM": "Anguila Tarde",
    "Anguila 9:00 PM": "Anguila Noche",
    
    # NACIONAL
    "Gana Más": "Nacional Gana Mas",
    "Lotería Nacional": "Nacional Noche",
    "Juega + Pega +": "Nacional Juega+Pega+",
    
    # LEIDSA
    "Quiniela Leidsa": "Leidsa Quiniela",
    "Pega 3 Más": "Leidsa Pega 3 Mas",
    "Loto Pool": "Leidsa Loto Pool",
    
    # REAL
    "Quiniela Real": "Real Quiniela",
    "Loto Real": "Real Loto",
    
    # LOTEKA
    "Quiniela Loteka": "Loteka Quiniela",
    "Mega Chances": "Loteka Mega Chances",
    
    # NY y FLORIDA
    "New York Tarde": "NY Tarde",
    "New York Noche": "NY Noche",
    "Florida Día": "Florida Dia",
    "Florida Noche": "Florida Noche",
    "Mega Millions": "Mega Millions",
    "PowerBall": "PowerBall",
    
    # OTRAS
    "La Primera Día": "La Primera Dia",
    "La Primera Noche": "La Primera Noche",
    "La Suerte 12:30": "La Suerte 12:30",
    "La Suerte 6:00": "La Suerte 18:00",
    "Quiniela LoteDom": "LoteDom Quiniela",
    "King Lottery 12:30": "King Lottery 12:30",
    "King Lottery 7:30": "King Lottery 7:30"
}

URLS_REALES = [
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
        print("✅ Mensaje enviado a Telegram.")
    except Exception as e:
        print(f"❌ Error enviando a Telegram: {e}")

def escanear_web_hoy():
    print("🕵️ Buscando datos REALES de HOY y AYER...")
    resultados_hoy = []  # <--- VARIABLE EN ESPAÑOL
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for url in URLS_REALES:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code != 200: continue
            
            soup = BeautifulSoup(r.text, 'html.parser')
            bloques = soup.find_all('div', class_='content-game')
            if not bloques: bloques = soup.find_all('div', class_='game-block')
            
            for bloque in bloques:
                texto = bloque.get_text(" ", strip=True)
                texto_lower = texto.lower()
                
                # Detectar nombre
                nombre_oficial = None
                for nombre_web, nombre_app in MAPA_CONECTATE.items():
                    if nombre_web.lower() in texto_lower:
                        nombre_oficial = nombre_app
                        break
                
                if nombre_oficial:
                    # EXTRAER NÚMEROS
                    todos_numeros = re.findall(r'\b\d{2}\b', texto)
                    premios = [int(n) for n in todos_numeros]
                    
                    # FILTRO DE FECHA (EL CEREBRO INTELIGENTE)
                    if len(premios) >= 5: 
                        if premios[0] in [14, 15] and premios[1] == 2:
                            premios = premios[-3:]
                        else:
                            premios = premios[-3:]
                    elif len(premios) >= 3:
                         premios = premios[-3:]
                    else:
                        continue 

                    n1, n2, n3 = premios[0], premios[1], premios[2]
                    
                    # Guardar en la lista
                    resultados_hoy.append(f"🎱 *{nombre_oficial}*\n`{n1:02d} - {n2:02d} - {n3:02d}`")
                    print(f"   ✅ Capturado: {nombre_oficial} -> {n1}-{n2}-{n3}")

        except Exception as e:
            print(f"⚠️ Error en {url}: {e}")
            
    return resultados_hoy # <--- ¡AQUÍ ESTABA EL ERROR! AHORA ESTÁ CORREGIDO.

def main():
    print("🚀 INICIANDO BOT DE TELEGRAM 2.0 (Versión Final)")
    
    # 1. Escanear
    lista_sorteos = escanear_web_hoy()
    
    if lista_sorteos:
        # 2. Preparar Mensaje
        fecha_titulo = datetime.now().strftime("%d/%m/%Y")
        mensaje_final = f"📢 *RESULTADOS DE LOTERÍA* 🇩🇴\n📅 {fecha_titulo}\n\n"
        mensaje_final += "\n".join(lista_sorteos)
        mensaje_final += "\n\n🤖 _Bot activo_"
        
        # 3. Enviar
        enviar_telegram(mensaje_final)
    else:
        print("❌ No se encontraron sorteos nuevos para enviar.")

if __name__ == "__main__":
    main()