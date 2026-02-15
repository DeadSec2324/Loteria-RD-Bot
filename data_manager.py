import pandas as pd
import random
from datetime import datetime, timedelta
import os
import requests
from bs4 import BeautifulSoup
import re

FILE_NAME = 'historial_loterias.csv'
LOTERIA_OBJETIVO = "Lotería Nacional"  # CAMBIA ESTO por: "Gana Más", "Quiniela Leidsa", etc.

def generar_datos_prueba(dias=90):
    """Genera datos históricos simulados para que la app funcione hoy mismo."""
    data = []
    hoy = datetime.now()
    for i in range(dias):
        fecha = hoy - timedelta(days=i)
        data.append({
            "Fecha": fecha.strftime("%Y-%m-%d"),
            "1er": random.randint(0, 99),
            "2do": random.randint(0, 99),
            "3er": random.randint(0, 99)
        })
    return pd.DataFrame(data)

def scrapear_conectate():
    """Extrae los números reales de conectate.com.do"""
    url = "https://www.conectate.com.do/loterias/"
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print("Error al conectar con la web")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # BUSCADOR INTELIGENTE:
        # Busca el texto de la lotería (ej. "Lotería Nacional")
        titulo = soup.find(string=re.compile(LOTERIA_OBJETIVO))
        
        if titulo:
            # Una vez encontrado el título, buscamos el contenedor cercano que tenga los números.
            # En conectate, los números suelen estar en bloques cercanos.
            # Esta lógica busca los siguientes elementos numéricos en el contenedor padre.
            contenedor = titulo.find_parent('div') or titulo.find_parent('li') or titulo.find_parent('td')
            
            if contenedor:
                # Buscamos todos los textos dentro del contenedor que parezcan números de lotería (00-99)
                textos = contenedor.get_text(separator=" ").split()
                numeros_encontrados = []
                
                for t in textos:
                    # Limpiamos caracteres no numéricos
                    limpio = ''.join(filter(str.isdigit, t))
                    if limpio.isdigit() and len(limpio) <= 2: # Asumimos números de 2 cifras
                        numeros_encontrados.append(int(limpio))
                
                # Asumimos que los 3 primeros números después del título son los ganadores
                # (A veces el título tiene fecha, hay que filtrar)
                # Filtramos para quedarnos solo con los ultimos 3 encontrados que suelen ser los premios
                if len(numeros_encontrados) >= 3:
                    # Normalmente los premios son los últimos 3 o los que están destacados
                    # Ajuste: Tomamos los primeros 3 que aparezcan tras el título si la estructura es simple
                    # OJO: Esto puede requerir ajuste fino según cómo cambie la web hoy.
                    n1, n2, n3 = numeros_encontrados[:3]
                    
                    hoy = datetime.now().strftime("%Y-%m-%d")
                    return {"Fecha": hoy, "1er": n1, "2do": n2, "3er": n3}
        
        print(f"No se encontraron resultados para {LOTERIA_OBJETIVO}")
        return None

    except Exception as e:
        print(f"Error en el scraping: {e}")
        return None

def cargar_datos():
    if os.path.exists(FILE_NAME):
        return pd.read_csv(FILE_NAME)
    else:
        # Crea histórico simulado si no existe archivo
        df = generar_datos_prueba(90)
        df.to_csv(FILE_NAME, index=False)
        return df

def actualizar_datos():
    df = cargar_datos()
    nuevo_dato = scrapear_conectate()
    
    if nuevo_dato:
        # Verificar si la fecha ya existe para no duplicar hoy
        if nuevo_dato['Fecha'] not in df['Fecha'].values:
            nuevo_fila = pd.DataFrame([nuevo_dato])
            df = pd.concat([nuevo_fila, df], ignore_index=True)
            df.to_csv(FILE_NAME, index=False)
            return nuevo_dato
    return None