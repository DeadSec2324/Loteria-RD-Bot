import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import data_manager

# Configuración de la página
st.set_page_config(page_title="Lotería Dominicana", page_icon="🎱")

# Título y Descripción
st.title("🎱 Centro de Estadísticas de Lotería")
st.markdown("Análisis de tendencias, números calientes y fríos.")

# 1. CARGAR DATOS
df = data_manager.cargar_datos()

# Verificación de seguridad: ¿Hay datos?
if df.empty:
    st.error("⚠️ No hay datos cargados. Por favor verifica que 'historial_loterias.csv' esté en GitHub.")
    st.stop()

# 2. MENÚ INTELIGENTE (Lee los nombres del archivo)
# En lugar de tener una lista fija, le preguntamos al archivo qué loterías tiene.
lista_loterias = sorted(df['Loteria'].unique())

if not lista_loterias:
    st.error("El archivo de datos parece estar vacío o dañado.")
    st.stop()

# Crear el menú desplegable
loteria_seleccionada = st.selectbox("Selecciona tu Sorteo:", lista_loterias)

# 3. FILTRAR DATOS
# Buscamos en el Excel solo los datos de la lotería que elegiste
datos_loteria = df[df['Loteria'] == loteria_seleccionada].copy()

# Ordenar por fecha (lo más nuevo arriba)
datos_loteria['Fecha'] = pd.to_datetime(datos_loteria['Fecha'])
datos_loteria = datos_loteria.sort_values(by='Fecha', ascending=False)

# 4. MOSTRAR RESULTADOS
if len(datos_loteria) < 5:
    st.warning(f"Todavía hay pocos datos para {loteria_seleccionada}. Esperando más sorteos...")
    st.dataframe(datos_loteria)
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
    st.subheader("🔥 Números Calientes (Últimos 3 meses)")
    
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

    # Tabla de Historial Reciente
    st.markdown("---")
    st.subheader("📜 Historial Reciente")
    st.dataframe(datos_loteria.head(10))
