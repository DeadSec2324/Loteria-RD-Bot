import pandas as pd
import random
from datetime import datetime, timedelta
import os
import requests
from bs4 import BeautifulSoup
import re

FILE_NAME = 'historial_loterias.csv'

# LISTA DE LOTERÍAS A BUSCAR
LOTERIAS_OBJETIVO = [
    "Nacional", "Leidsa", "Real", "Loteka", 
    "New York", "Florida", "La Primera", "La Suerte"
]

def generar_datos_prueba(dias=90):
    """Genera un archivo base si no existe."""
    data = []
    hoy = datetime.now()
    
    # CORRECCIÓN CLAVE: Empezamos desde 2 para dejar AYER (día 1) vacío.
    # Así el robot puede guardar los datos reales de ayer sin chocar con los falsos.
    for i in range(2, dias):
        fecha = hoy - timedelta(days=i)
        for loteria in LOTERIAS_OBJETIVO:
            data.append({
                "Fecha": fecha.strftime("%Y-%m-%d"),
                "Loteria": loteria,
                "1er": random.randint(0, 99),
                "2do": random.randint(0, 99),
                "3er": random.randint(0, 99)
            })
    return pd.DataFrame(data)

def scrapear_conectate():
    url = "https://www.conectate.com.do/loterias/"
    print(f"🌍 Conectando a {url}...")
    
    resultados_encontrados = []
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        if response.status_code != 200: return []

        soup = BeautifulSoup(response.text, 'html.parser')
        bloques = soup.find_all('div', class_=re.compile(r'game-block|content-game'))
        print(f"🔎 Analizando {len(bloques)} bloques de lotería encontrados...")

        # --- LÓGICA DE FECHA ---
        hora_actual = datetime.now().hour
        if hora_actual < 12:
            fecha_logica = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            print(f"🌙 Es madrugada ({hora_actual}:00). Asignando fecha de AYER: {fecha_logica}")
        else:
            fecha_logica = datetime.now().strftime("%Y-%m-%d")
            print(f"☀️ Es día ({hora_actual}:00). Asignando fecha de HOY: {fecha_logica}")

        for nombre_loteria in LOTERIAS_OBJETIVO:
            for bloque in bloques:
                texto_bloque = bloque.get_text(" ", strip=True)
                
                if nombre_loteria.lower() in texto_bloque.lower():
                    # Extraer números
                    numeros = re.findall(r'\b\d{2}\b', texto_bloque)
                    premios = [int(n) for n in numeros if 0 <= int(n) <= 99]
                    
                    if len(premios) >= 3:
                        # CORRECCIÓN PRECISIÓN:
                        # Tomamos los ÚLTIMOS 3 números encontrados (premios[-3:])
                        # Antes tomábamos los primeros y a veces agarraba la fecha (14, 02...)
                        n1, n2, n3 = premios[-3:]
                        
                        resultados_encontrados.append({
                            "Fecha": fecha_logica,
                            "Loteria": nombre_loteria,
                            "1er": n1,
                            "2do": n2,
                            "3er": n3
                        })
                        print(f"   ✅ {nombre_loteria}: {n1} - {n2} - {n3}")
                    break 
                    
        return resultados_encontrados

    except Exception as e:
        print(f"❌ Error scraping: {e}")
        return []

def cargar_datos():
    if os.path.exists(FILE_NAME):
        return pd.read_csv(FILE_NAME)
    else:
        print("📂 Creando archivo de historial nuevo (dejando hueco para datos reales)...")
        df = generar_datos_prueba(90)
        df.to_csv(FILE_NAME, index=False)
        return df

def actualizar_datos():
    df = cargar_datos()
    nuevos_resultados = scrapear_conectate()
    nuevos_para_guardar = []
    
    if nuevos_resultados:
        for dato in nuevos_resultados:
            # Verifica si ya existe (Fecha + Loteria)
            existe = df[
                (df['Fecha'] == dato['Fecha']) & 
                (df['Loteria'] == dato['Loteria'])
            ]
            
            if existe.empty:
                nuevos_para_guardar.append(dato)

        if nuevos_para_guardar:
            print(f"💾 Guardando {len(nuevos_para_guardar)} sorteos nuevos...")
            df_nuevos = pd.DataFrame(nuevos_para_guardar)
            df = pd.concat([df_nuevos, df], ignore_index=True)
            df.to_csv(FILE_NAME, index=False)
            return nuevos_para_guardar 
        else:
            print("💤 Los datos encontrados YA existen en el historial.")
            
    return []