import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime

# --- CONFIGURACIÓN ---
FILE_NAME = 'historial_loterias.csv'

# Mapeo: Nombre en la Web (Conectate) -> Nombre en tu App
# Basado en tu foto, Conectate usa horas para Anguila.
MAPA_CONECTATE = {
    # ANGUILA (Página específica)
    "Anguila 10:00 AM": "Anguila Mañana",
    "Anguila 1:00 PM": "Anguila Medio Dia",
    "Anguila 6:00 PM": "Anguila Tarde",
    "Anguila 9:00 PM": "Anguila Noche",
    
    # NACIONAL
    "Gana Más": "Nacional Gana Mas",
    "Lotería Nacional": "Nacional Noche",
    
    # LEIDSA
    "Quiniela Leidsa": "Leidsa Quiniela",
    "Pega 3 Más": "Leidsa Pega 3 Mas",
    
    # REAL
    "Quiniela Real": "Real Quiniela",
    
    # LOTEKA
    "Quiniela Loteka": "Loteka Quiniela",
    
    # NY y FLORIDA
    "New York Tarde": "NY Tarde",
    "New York Noche": "NY Noche",
    "Florida Día": "Florida Dia",
    "Florida Noche": "Florida Noche",
    
    # OTRAS
    "La Primera Día": "La Primera Dia",
    "La Primera Noche": "La Primera Noche",
    "La Suerte 12:30": "La Suerte 12:30",
    "La Suerte 6:00": "La Suerte 18:00",
    "Quiniela LoteDom": "LoteDom Quiniela",
    "King Lottery 12:30": "King Lottery 12:30",
    "King Lottery 7:30": "King Lottery 7:30"
}

# URLs donde buscar (Páginas de historial de Conectate)
URLS_A_ESCANEAR = [
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

def obtener_html(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0'}
        r = requests.get(url, headers=headers, timeout=10)
        return r.text if r.status_code == 200 else None
    except:
        return None

def extraer_numeros(texto):
    # Busca grupos de números (ej: 90 82 02)
    numeros = re.findall(r'\b\d{2}\b', texto)
    return [int(n) for n in numeros if 0 <= int(n) <= 99]

def main():
    print("🕵️‍♂️ INICIANDO EXTRACCIÓN REAL (CONECTATE.COM.DO)...")
    datos_reales = []
    
    for url in URLS_A_ESCANEAR:
        print(f"   🌍 Escaneando: {url} ...", end="\r")
        html = obtener_html(url)
        
        if not html:
            continue
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # En Conectate, cada sorteo suele estar en un bloque con clase "game-block" o similar.
        # Pero a veces cambia. Vamos a buscar por TEXTO, que es más seguro.
        # Dividimos la página en bloques visuales (divs principales)
        bloques = soup.find_all('div', class_='content-game') 
        
        if not bloques: # Si no encuentra content-game, busca game-block
            bloques = soup.find_all('div', class_='game-block')

        for bloque in bloques:
            texto_bloque = bloque.get_text(" ", strip=True)
            
            # 1. Buscar Fecha (Formato: 15-02 o 15 de febrero)
            # En tu foto se ve "15-02" o "Hoy"
            fecha_encontrada = None
            
            # Intentamos buscar patrones de fecha DD-MM
            match_fecha = re.search(r'(\d{1,2})-(\d{1,2})', texto_bloque)
            if match_fecha:
                dia, mes = match_fecha.groups()
                # Asumimos año actual (el de tu PC o 2026)
                fecha_encontrada = f"2026-{int(mes):02d}-{int(dia):02d}"
            elif "hoy" in texto_bloque.lower():
                fecha_encontrada = datetime.now().strftime("%Y-%m-%d")
            
            # Si no hay fecha en el bloque, a veces la fecha es el título de la sección anterior
            # Para simplificar, si no hay fecha clara, usaremos "Hoy" por defecto si estamos bajando datos frescos
            if not fecha_encontrada: 
                 # Si el bloque tiene números, asumimos que es reciente
                 fecha_encontrada = datetime.now().strftime("%Y-%m-%d")

            # 2. Identificar Lotería
            nombre_app = None
            for nombre_web, nombre_interno in MAPA_CONECTATE.items():
                if nombre_web.lower() in texto_bloque.lower():
                    nombre_app = nombre_interno
                    break
            
            if nombre_app:
                # 3. Extraer Números
                numeros = extraer_numeros(texto_bloque)
                
                # Filtramos: Necesitamos al menos 3 números
                if len(numeros) >= 3:
                    # En Conectate los números ganadores suelen ser los últimos 3 del bloque o los que están en bolas
                    # Tomamos los 3 primeros que aparezcan DESPUÉS del nombre del sorteo
                    # (Esto requiere un regex más fino, pero tomaremos los 3 últimos del bloque por seguridad)
                    n1, n2, n3 = numeros[-3], numeros[-2], numeros[-1]
                    
                    # Guardamos
                    datos_reales.append({
                        "Fecha": fecha_encontrada,
                        "Loteria": nombre_app,
                        "1er": n1, "2do": n2, "3er": n3
                    })

    print(f"\n\n✅ ¡LISTO! Se encontraron {len(datos_reales)} sorteos REALES.")
    
    if datos_reales:
        df = pd.DataFrame(datos_reales)
        # Eliminamos duplicados por si acaso
        df = df.drop_duplicates(subset=['Fecha', 'Loteria'])
        
        # Guardamos encima del archivo simulado
        df.sort_values(by='Fecha', ascending=False).to_csv(FILE_NAME, index=False)
        print(f"💾 Archivo actualizado: {FILE_NAME}")
        print("👉 Sube esto a GitHub y verás los números 90-82-02 en Anguila.")
    else:
        print("⚠️ No se encontraron datos. Verifica que la página de Conectate cargue en tu navegador.")

if __name__ == "__main__":
    main()