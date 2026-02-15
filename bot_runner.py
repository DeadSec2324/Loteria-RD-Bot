import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
import pandas as pd
import os

# --- CONFIGURACIÓN ---
TOKEN = "7987107497:AAFPYOZU9fmCILjDX-wls6gtC2hMDcI5NAo"       # <--- ¡Pon tu Token aquí!
CHAT_ID = "7427129383"   # <--- ¡Pon tu Chat ID aquí!
FILE_NAME = 'historial_loterias.csv' # El archivo donde guardamos la historia

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

def guardar_en_csv(nuevos_datos):
    """Esta función es la SECRETARIA que anota todo en el Excel"""
    try:
        # 1. Cargar datos existentes si hay
        if os.path.exists(FILE_NAME):
            df_existente = pd.read_csv(FILE_NAME)
        else:
            df_existente = pd.DataFrame(columns=['Fecha', 'Loteria', '1er', '2do', '3er'])

        # 2. Convertir nuevos datos a DataFrame
        df_nuevos = pd.DataFrame(nuevos_datos)
        
        # 3. Juntar todo
        df_total = pd.concat([df_nuevos, df_existente])
        
        # 4. Eliminar duplicados (Mismo sorteo en la misma fecha)
        # Priorizamos los nuevos (keep='first')
        df_total = df_total.drop_duplicates(subset=['Fecha', 'Loteria'], keep='first')
        
        # 5. Ordenar por fecha
        df_total = df_total.sort_values(by='Fecha', ascending=False)
        
        # 6. Guardar
        df_total.to_csv(FILE_NAME, index=False)
        print(f"💾 ¡GUARDADO! Se actualizaron los datos en {FILE_NAME}")
        
    except Exception as e:
        print(f"❌ Error guardando en CSV: {e}")

def escanear_web_hoy():
    print("🕵️ Buscando datos REALES de HOY y AYER...")
    
    mensajes_telegram = []  # Para enviar al chat
    datos_para_csv = []     # Para guardar en el archivo
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # Fecha de hoy para guardar en el archivo
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")

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
                    
                    # FILTRO INTELIGENTE
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
                    
                    # 1. Preparar mensaje bonito para Telegram
                    mensajes_telegram.append(f"🎱 *{nombre_oficial}*\n`{n1:02d} - {n2:02d} - {n3:02d}`")
                    print(f"   ✅ Capturado: {nombre_oficial} -> {n1}-{n2}-{n3}")
                    
                    # 2. Preparar dato crudo para CSV (AQUÍ ESTÁ LA CLAVE)
                    # Intentamos detectar la fecha exacta del bloque, si no, usamos la de hoy
                    fecha_dato = fecha_hoy
                    if "14-02" in texto or "ayer" in texto_lower:
                        # Si detectamos que es de ayer (por si acaso), ajustamos
                        # (Opcional, pero útil para precisión)
                        pass 

                    datos_para_csv.append({
                        'Fecha': fecha_dato,
                        'Loteria': nombre_oficial,
                        '1er': n1,
                        '2do': n2,
                        '3er': n3
                    })

        except Exception as e:
            print(f"⚠️ Error en {url}: {e}")
            
    return mensajes_telegram, datos_para_csv

def main():
    print("🚀 INICIANDO BOT DE TELEGRAM + ACTUALIZADOR DE APP")
    
    # 1. Escanear
    lista_mensajes, lista_datos = escanear_web_hoy()
    
    # 2. Guardar en el Archivo (PARA QUE LA APP SE ACTUALICE)
    if lista_datos:
        guardar_en_csv(lista_datos)
    else:
        print("⚠️ No hay datos nuevos para guardar.")

    # 3. Enviar a Telegram
    if lista_mensajes:
        fecha_titulo = datetime.now().strftime("%d/%m/%Y")
        mensaje_final = f"📢 *RESULTADOS DE LOTERÍA* 🇩🇴\n📅 {fecha_titulo}\n\n"
        mensaje_final += "\n".join(lista_mensajes)
        mensaje_final += "\n\n🤖 _Bot activo_"
        
        enviar_telegram(mensaje_final)
    else:
        print("❌ No se encontraron sorteos nuevos para enviar.")
        
    print("\n👉 AHORA: Sube el archivo 'historial_loterias.csv' a GitHub para ver los cambios en la web.")

if __name__ == "__main__":
    main()
