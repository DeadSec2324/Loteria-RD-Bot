import streamlit as st
import pandas as pd
from data_manager import cargar_datos, LOTERIAS_OBJETIVO

st.set_page_config(page_title="Analizador de Loterías", layout="wide", page_icon="🎱")

st.title("🎱 Centro de Estadísticas de Lotería")
st.markdown("Análisis de tendencias, números calientes y fríos.")

# Cargar datos
df = cargar_datos()

# Sidebar (Menú lateral)
st.sidebar.header("Filtros")
loteria_selec = st.sidebar.selectbox("Selecciona la Lotería:", LOTERIAS_OBJETIVO)

# Filtrar por la lotería seleccionada
df_loto = df[df['Loteria'] == loteria_selec]

if not df_loto.empty:
    # --- LOGICA DE CALIENTES Y FRIOS ---
    # Unimos las 3 columnas de premios en una sola lista para contar
    todos_numeros = pd.concat([df_loto['1er'], df_loto['2do'], df_loto['3er']])
    conteo = todos_numeros.value_counts().sort_values(ascending=False)
    
    # KPIs Principales
    ultimo_sorteo = df_loto.iloc[0]
    st.info(f"📅 **Último Sorteo ({ultimo_sorteo['Fecha']}):** {ultimo_sorteo['1er']} - {ultimo_sorteo['2do']} - {ultimo_sorteo['3er']}")

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔥 Los Más Calientes (Top 5)")
        st.write("Estos números son los que más han salido en los últimos 3 meses.")
        # Mostramos los 5 primeros del conteo
        top_hot = conteo.head(5)
        st.bar_chart(top_hot, color="#FF4B4B") # Rojo
        
    with col2:
        st.subheader("🧊 Los Más Fríos (Top 5)")
        st.write("Estos números casi no salen. ¿Toca que salgan pronto?")
        # Mostramos los 5 últimos del conteo (que tengan al menos 1 salida, o los menos frecuentes)
        top_cold = conteo.tail(5).sort_values()
        st.bar_chart(top_cold, color="#1E90FF") # Azul

    st.divider()
    
    # Análisis Detallado
    st.subheader(f"📜 Historial Reciente: {loteria_selec}")
    st.dataframe(df_loto[['Fecha', '1er', '2do', '3er']].head(10), use_container_width=True)

else:
    st.warning(f"Todavía no hay suficientes datos registrados para {loteria_selec}.")