import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# Configuración de la página
st.set_page_config(page_title="Lotería Dominicana", page_icon="🎱")

# Título
st.title("🎱 Centro de Estadísticas de Lotería")

# 1. CARGAR DATOS CON SEGURIDAD
archivo = 'historial_loterias.csv'

if not os.path.exists(archivo):
    st.error(f"⚠️ No se encuentra el archivo '{archivo}'. Asegúrate de subirlo a GitHub.")
    st.stop()

try:
    df = pd.read_csv(archivo)
except Exception as e:
    st.error(f"❌ Error leyendo el archivo: {e}")
    st.stop()

if df.empty:
    st.warning("⚠️ El archivo de datos está vacío. Ejecuta el generador primero.")
    st.stop()

# 2. MENÚ INTELIGENTE (La clave del arreglo)
# Buscamos los nombres ÚNICOS que realmente existen en el archivo.
# Así no hay error de "nombre incorrecto".
lista_loterias = sorted(df['Loteria'].unique())

loteria_seleccionada = st.selectbox("Selecciona tu Sorteo:", lista_loterias)

# 3. FILTRAR DATOS
# Buscamos en el Excel solo los datos de la lotería que elegiste
datos_loteria = df[df['Loteria'] == loteria_seleccionada].copy()

# Ordenar por fecha (lo más nuevo arriba)
datos_loteria['Fecha'] = pd.to_datetime(datos_loteria['Fecha'])
datos_loteria = datos_loteria.sort_values(by='Fecha', ascending=False)

# 4. MOSTRAR RESULTADOS
if len(datos_loteria) < 1:
    st.warning(f"No hay datos para {loteria_seleccionada}.")
else:
    # Último resultado
    ultimo = datos_loteria.iloc[0]
    st.success(f"📅 **Último Sorteo ({ultimo['Fecha'].strftime('%d-%m-%Y')}):**")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("1er Premio", ultimo['1er'])
    col2.metric("2do Premio", ultimo['2do'])
    col3.metric("3er Premio", ultimo['3er'])

    st.markdown("---")

    # --- ANÁLISIS DE CALIENTES ---
    st.subheader("🔥 Números Calientes (Más frecuentes)")
    
    if len(datos_loteria) > 5:
        # Juntamos todos los premios en una sola lista
        todos_numeros = pd.concat([datos_loteria['1er'], datos_loteria['2do'], datos_loteria['3er']])
        conteo = todos_numeros.value_counts().head(10)

        # Gráfico de Barras
        fig, ax = plt.subplots(figsize=(10, 5))
        conteo.plot(kind='bar', color='#ff4b4b', ax=ax)
        ax.set_title(f"Números que más salen en {loteria_seleccionada}")
        ax.set_xlabel("Número")
        ax.set_ylabel("Veces que ha salido")
        st.pyplot(fig)
    else:
        st.info("Necesitamos más historial para mostrar la gráfica de calientes.")

    # Tabla de Historial Reciente
    st.markdown("---")
    st.subheader("📜 Historial Reciente")
    # Formatear la fecha para que se vea bonita en la tabla
    tabla_mostrar = datos_loteria.copy()
    tabla_mostrar['Fecha'] = tabla_mostrar['Fecha'].dt.strftime('%d-%m-%Y')
    st.dataframe(tabla_mostrar.head(10))
