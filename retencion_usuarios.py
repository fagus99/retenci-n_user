import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Análisis de Retención por Cohortes")

st.title("Análisis de Retención de Usuarios por Cohortes")
st.markdown("""
Subí un archivo Excel que contenga las columnas clave:
- **Usuario:** identificador único del usuario.
- **Fecha registro:** fecha en que el usuario fue creado/registrado.
- **Columnas de actividad mensual:** columnas nombradas con los meses (Ej: Ene, Feb, Mar, etc.) con valor "SÍ" si el usuario estuvo activo ese mes, o vacío/cero si no.
""")

# Subida de archivo Excel
archivo = st.file_uploader("Subí tu archivo Excel", type=["xlsx", "xls"])
if archivo is not None:
    # Leer Excel
    df = pd.read_excel(archivo)

    # Mostrar primeras filas
    st.write("Primeras filas del archivo:")
    st.dataframe(df.head())

    # Verificar columnas clave
    required_cols = ['Usuario', 'Fecha registro']
    if not all(col in df.columns for col in required_cols):
        st.error(f"Faltan columnas obligatorias: {', '.join(required_cols)}")
        st.stop()

    # Convertir Fecha registro a datetime y extraer mes cohorte (primer día del mes)
    df['Fecha registro'] = pd.to_datetime(df['Fecha registro'], errors='coerce')
    if df['Fecha registro'].isnull().any():
        st.warning("Hay fechas inválidas en 'Fecha registro' que se ignorarán.")
    df = df.dropna(subset=['Fecha registro'])
    df['Mes cohorte'] = df['Fecha registro'].dt.to_period('M').dt.to_timestamp()

    # Detectar columnas de actividad mensual (todas menos Usuario, Fecha registro, Mes cohorte)
    actividad_cols = [c for c in df.columns if c not in ['Usuario', 'Fecha registro', 'Mes cohorte']]
    if len(actividad_cols) == 0:
        st.error("No se detectaron columnas de actividad mensual.")
        st.stop()

    # Ordenar columnas actividad por orden mensual, si posible
    # (Por ejemplo, si son abreviaturas de meses en español: Ene, Feb, Mar, ...)
    meses_orden = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    # Ordenar solo las que existan
    actividad_cols_sorted = [m for m in meses_orden if m in actividad_cols]
    # Agregar otras columnas que no estén en la lista meses_orden (en orden original)
    actividad_cols_otros = [c for c in actividad_cols if c not in meses_orden]
    actividad_cols_sorted.extend(actividad_cols_otros)

    # Construir matriz de retención
    cohort_data = {}

    for cohorte, grupo in df.groupby('Mes cohorte'):
        total_usuarios = grupo['Usuario'].nunique()
        cohort_data[cohorte] = [total_usuarios]
        # Para cada mes desde creación:
        for i, col in enumerate(actividad_cols_sorted):
             # Detectar si valor es positivo numérico (>0)
        activos = grupo[grupo[col].apply(lambda x: pd.to_numeric(x, errors='coerce')).fillna(0) > 0]['Usuario'].nunique()
        pct_retencion = activos / total_usuarios if total_usuarios > 0 else 0
        cohort_data[cohorte].append(pct_retencion)

    # Crear DataFrame
    columnas = ['Total usuarios'] + [f'Mes {i}' for i in range(len(actividad_cols_sorted))]
    retencion_df = pd.DataFrame.from_dict(cohort_data, orient='index', columns=columnas)

    # Mostrar tabla de retención (porcentajes en formato %)
    retencion_mostrar = retencion_df.style.format("{:.1%}")
    st.subheader("Matriz de Retención por Cohortes")
    st.dataframe(retencion_mostrar, use_container_width=True)

    # Mostrar heatmap
    st.subheader("Mapa de calor (heatmap) de la retención")
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(retencion_df.iloc[:,1:], annot=True, fmt=".0%", cmap="YlGnBu", cbar=True, ax=ax)
    ax.set_ylabel("Mes de Cohorte")
    ax.set_xlabel("Mes desde registro")
    st.pyplot(fig)
