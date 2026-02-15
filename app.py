import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from data_manager import cargar_datos, LOTERIA_OBJETIVO

st.set_page_config(page_title=f"Lotería: {LOTERIA_OBJETIVO}", layout="wide")

st.title(f"🎱 Análisis {LOTERIA_OBJETIVO}")
st.markdown("Estadísticas actualizadas diariamente desde **conectate.com.do**")

df = cargar_datos()

# Métricas rápidas
st.info(f"Último sorteo registrado: {df.iloc[0]['Fecha']} -> {df.iloc[0]['1er']} - {df.iloc[0]['2do']} - {df.iloc[0]['3er']}")

# Lógica de Calientes y Fríos
def obtener_frecuencia(df):
    todos = pd.concat([df['1er'], df['2do'], df['3er']])
    return todos.value_counts().sort_values(ascending=False)

conteo = obtener_frecuencia(df)

col1, col2 = st.columns(2)
with col1:
    st.header("🔥 Calientes (Más salen)")
    st.bar_chart(conteo.head(10), color="#FF4B4B")
with col2:
    st.header("🧊 Fríos (Menos salen)")
    st.bar_chart(conteo.tail(10), color="#1E90FF")

st.divider()
st.header("🏆 Análisis por Posición")
c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("1er Lugar")
    top1 = df['1er'].value_counts().head(5)
    st.table(top1)
with c2:
    st.subheader("2do Lugar")
    top2 = df['2do'].value_counts().head(5)
    st.table(top2)
with c3:
    st.subheader("3er Lugar")
    top3 = df['3er'].value_counts().head(5)
    st.table(top3)