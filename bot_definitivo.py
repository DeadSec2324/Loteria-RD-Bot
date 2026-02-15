import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import os
from datetime import datetime, timedelta

# --- 🔑 TUS CREDENCIALES ---
TOKEN = "7987107497:AAFPYOZU9fmCILjDX-wls6gtC2hMDcI5NAo"       # <--- ¡Token!
CHAT_ID = "7427129383"   # <--- ¡Chat ID!

# --- CONFIGURACIÓN ---
FILE_NAME = 'historial_loterias.csv'
TIEMPO_REVISION = 3600 # Revisar cada 1 hora (3600 seg)

# Mapa de Horarios aproximados para predecir el siguiente (Hora Militar)
HORARIOS_SORTEOS = {
    "Anguila Mañana": 10, "La Suerte 12:30": 12, "Real Quiniela": 13, 
    "Anguila Medio Dia": 13, "Mega Chances": 13, "Gana Más": 15, 
    "Anguila Tarde": 18, "La Suerte 18:00": 18, "LoteDom Quiniela": 18,
    "Leidsa Quiniela": 20, "Nacional Noche": 21, "Anguila Noche": 21,
    "Florida Noche": 22, "NY Noche": 22
}

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

URLS_VIGILANCIA = [
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
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
        requests.post(url, data=data)
    except: pass

def obtener_calientes_siguiente_hora():
    """Busca qué sorteo toca pronto y da sus números calientes"""
    hora_actual = datetime.now().hour
    proximo_sorteo = None
    min_dif = 24
    
    # Buscar el sorteo más cercano en el futuro
    for nombre, hora in HORARIOS_SORTEOS.items():
        dif = hora - hora_actual
        if 0 < dif < min_dif: # Es futuro y es el más cercano
            min_dif = dif
            proximo_sorteo = nombre
            
    if not proximo_sorteo:
        return "" # No hay sorteos cercanos hoy
        
    # Calcular calientes para ese sorteo
    try:
        df = pd.read_csv(FILE_NAME)
        filtro = df[df['Loteria'] == proximo_sorteo]
        if filtro.empty: return ""
        
        todos = pd.concat([filtro['1er'], filtro['2do'], filtro['3er']])
        top3 = todos.value_counts().head(3)
        
        txt = f"🔮 *PRÓXIMO SORTEO: {proximo_sorteo}*\n🔥 Calientes: "
        numeros = [f"{n:02d}" for n in top3.index]
        txt += " - ".join(numeros)
        return txt
    except:
        return ""

def escanear_web():
    print(f"[{datetime.now().strftime('%H:%M')}] 🛰️ Escaneando satélite...")
    nuevos = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # Cargar lo que ya tenemos para no repetir
    if os.path.exists(FILE_NAME):
        df_db = pd.read_csv(FILE_NAME)
    else:
        df_db = pd.DataFrame(columns=['Fecha', 'Loteria'])

    for url in URLS_VIGILANCIA:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # Buscar bloques
            bloques = soup.find_all('div', class_='content-game')
            if not bloques: bloques = soup.find_all('div', class_='game-block')
            
            for bloque in bloques:
                texto = bloque.get_text(" ", strip=True)
                texto_lower = texto.lower()
                
                # 1. DETECTOR DE FECHA ESTRICTO
                fecha_detectada = None
                
                # Caso A: Dice explícitamente la fecha numérica (Ej: 15-02 o 14-02)
                match_fecha = re.search(r'(\d{1,2})-(\d{1,2})', texto)
                if match_fecha:
                    dia, mes = match_fecha.groups()
                    fecha_detectada = f"2026-{int(mes):02d}-{int(dia):02d}"
                
                # Caso B: Dice texto relativo
                if not fecha_detectada:
                    if "hoy" in texto_lower:
                        fecha_detectada = datetime.now().strftime("%Y-%m-%d") # HOY REAL
                    elif "ayer" in texto_lower:
                        fecha_detectada = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                
                # Si no logramos leer la fecha del bloque, LO IGNORAMOS.
                # Esto evita guardar el King Lottery del 14 como si fuera del 15.
                if not fecha_detectada:
                    continue

                # 2. IDENTIFICAR NOMBRE
                nombre_app = None
                for nombre_web, nombre_interno in MAPA_CONECTATE.items():
                    if nombre_web.lower() in texto_lower:
                        nombre_app = nombre_interno
                        break
                
                if nombre_app:
                    # 3. EXTRAER NÚMEROS (Últimos 3)
                    numeros = re.findall(r'\b\d{2}\b', texto)
                    if len(numeros) >= 3:
                        # Evitar capturar la fecha como número (filtro extra)
                        # Si los números son [14, 02, 88, 99, 11] -> Tomamos 88, 99, 11
                        premios = [int(n) for n in numeros]
                        n1, n2, n3 = premios[-3], premios[-2], premios[-1]
                        
                        # 4. ¿ES NUEVO? (Chequeamos en la Base de Datos)
                        # Buscamos si ya existe esa Lotería en esa Fecha exacta
                        existe = not df_db[
                            (df_db['Fecha'] == fecha_detectada) & 
                            (df_db['Loteria'] == nombre_app)
                        ].empty
                        
                        if not existe:
                            item = {
                                "Fecha": fecha_detectada,
                                "Loteria": nombre_app,
                                "1er": n1, "2do": n2, "3er": n3
                            }
                            nuevos.append(item)
                            print(f"   ✨ NUEVO DETECTADO: {fecha_detectada} | {nombre_app}: {n1}-{n2}-{n3}")

        except Exception as e:
            print(f"⚠️ Error en {url}: {e}")
            
    return nuevos

def main():
    print("🤖 EJECUCIÓN PROGRAMADA DE GITHUB")
    
    # 1. Escanear
    hallazgos = escanear_web()
    
    if hallazgos:
        # 2. Guardar en CSV
        df_nuevos = pd.DataFrame(hallazgos)
        if os.path.exists(FILE_NAME):
            df_old = pd.read_csv(FILE_NAME)
            df_final = pd.concat([df_nuevos, df_old])
        else:
            df_final = df_nuevos
        
        # Limpiar y Guardar
        df_final.drop_duplicates(subset=['Fecha', 'Loteria'], keep='first', inplace=True)
        df_final.sort_values(by='Fecha', ascending=False, inplace=True)
        df_final.to_csv(FILE_NAME, index=False)
        print("💾 Base de datos actualizada.")
        
        # 3. Notificar a Telegram
        msg = "📢 *NUEVOS RESULTADOS* 🇩🇴\n\n"
        fechas = sorted(list(set(h['Fecha'] for h in hallazgos)), reverse=True)
        
        for fecha in fechas:
            hoy_str = datetime.now().strftime("%Y-%m-%d")
            label_fecha = "🟢 DE HOY" if fecha == hoy_str else f"🔴 DEL {fecha}"
            msg += f"📅 *{label_fecha}*\n"
            for item in hallazgos:
                if item['Fecha'] == fecha:
                    msg += f"🎱 *{item['Loteria']}*\n`{item['1er']:02d} - {item['2do']:02d} - {item['3er']:02d}`\n"
            msg += "\n"
        
        # Predicción
        prediccion = obtener_calientes_siguiente_hora()
        if prediccion:
            msg += "-------------------\n" + prediccion
        
        enviar_telegram(msg)
    else:
        print("💤 Sin novedades en esta ejecución.")

if __name__ == "__main__":
    main()