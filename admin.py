import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Cardinal - Admin", page_icon="⚙️", layout="wide")
st.title("⚙️ Vista Administrador - Carga de Planillas por Categoría")
st.markdown("---")

# Definimos las categorías disponibles (y se pueden sumar más en el futuro)
categorias = ["Retenciones", "Ventas", "NPS"]
categoria_seleccionada = st.selectbox("Seleccione la categoría de la planilla:", categorias)

archivo_subido = st.file_uploader(f"Cargar archivo para {categoria_seleccionada}", type=["csv", "xlsx"])

if archivo_subido is not None:
    if archivo_subido.name.endswith('.csv'):
        df = pd.read_csv(archivo_subido)
    else:
        df = pd.read_excel(archivo_subido)
    
    # Guardamos en un archivo independiente para esta categoría
    ruta_archivo = f"datos_{categoria_seleccionada.lower()}.pkl"
    df.to_pickle(ruta_archivo)
    
    st.success(f"¡Planilla de **{categoria_seleccionada}** actualizada con éxito!")
    st.write(f"Vista previa de {categoria_seleccionada}:", df.head())

st.markdown("---")
st.subheader("Estado actual de las categorías guardadas:")
for cat in categorias:
    ruta = f"datos_{cat.lower()}.pkl"
    if os.path.exists(ruta):
        st.success(f"📂 {cat}: Archivo activo y sincronizado.")
    else:
        st.info(f"⚪ {cat}: Sin datos cargados aún.")