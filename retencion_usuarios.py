import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import unicodedata

st.title("🔍 Análisis de Retención de Usuarios por Cohortes")

st.markdown("""
Subí un archivo Excel que contenga:
- Una columna `Usuario` con identificadores únicos
- Una columna `Fecha registro` con la fecha de registro
- Varias columnas con nombres de meses (ej. junio, julio...) indicando si el usuario tuvo actividad ese mes (valores positivos).
""")

# Subida del archivo
archivo = st.file_uploader("📤 Subí tu archivo Excel", type=["xlsx"])

if archivo is not None:
    df = pd.read_excel(archivo)

    # Normalizar nombres de columnas (sin acentos, minúsculas)
    def normalizar_columna(col):
        col = col.lower()
        col = unicodedata.normalize('NFKD', col).encode('ascii', errors='ignore').decode()
        return col.strip()

    df.columns = [normalizar_columna(c) for c in df.columns]

    # Asegurar existencia de columnas mínimas
    if 'usuario' not in df.columns or 'fecha registro' not in df.columns:
        st.error("El archivo debe tener al menos las columnas 'Usuario' y 'Fecha registro'.")
    else:
        # Convertir la fecha de registro
        df['fecha registro'] = pd.to_datetime(df['fecha registro'], errors='coerce')
        df['cohorte'] = df['fecha registro'].dt.to_period('M').astype(str) + "-01"

        # Detectar columnas de meses (excluyendo las primeras conocidas)
        columnas_mes = [col for col in df.columns if col not in ['usuario', 'fecha registro', 'cohorte', 'mes registro', 'anio', 'año']]

        # Convertir columnas de meses a numérico (para detectar valores positivos)
        for col in columnas_mes:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Calcular matriz de retención
        retencion = {}

        for cohorte, grupo in df.groupby('cohorte'):
            base = len(grupo)
            actividad = []

            for i, col in enumerate(columnas_mes):
                activos = grupo[grupo[col] > 0]
                porcentaje = len(activos) / base if base > 0 else 0
                actividad.append(round(porcentaje * 100, 1))

            retencion[cohorte] = actividad

        # Crear DataFrame de retención
        retencion_df = pd.DataFrame.from_dict(retencion, orient='index', columns=[f"Mes {i}" for i in range(len(columnas_mes))])
        retencion_df.index.name = "Mes de Cohorte"

        # Mostrar tabla
        st.subheader("📋 Tabla de Retención")
        st.dataframe(retencion_df.style.format("{:.1f}%"))

        # Mostrar heatmap
        st.subheader("🔥 Heatmap de Retención")
        plt.figure(figsize=(12, len(retencion_df) * 0.5 + 3))
        sns.heatmap(retencion_df, annot=True, fmt=".1f", cmap="YlGnBu", cbar_kws={'label': '% Retención'})
        plt.xlabel("Mes desde registro")
        plt.ylabel("Mes de Cohorte")
        st.pyplot(plt)
