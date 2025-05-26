import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

st.title("Análisis de Retención de Usuarios por Cohortes")

st.markdown("""
Subí un archivo Excel que contenga las siguientes columnas mínimas:
- **Usuario**: Identificador único del usuario.
- **Fecha registro**: Fecha en que el usuario se registró.
- Columnas de actividad mensual: una columna por cada mes con valores numéricos positivos si hubo actividad, 0 o vacío si no.
  
El análisis calculará la matriz de retención por cohortes mensuales.
""")

archivo = st.file_uploader("Subí tu archivo Excel", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo)

    # Revisar que estén las columnas mínimas
    columnas_minimas = ['Usuario', 'Fecha registro']
    if not all(col in df.columns for col in columnas_minimas):
        st.error(f"El archivo debe contener las columnas: {', '.join(columnas_minimas)}")
    else:
        # Convertir 'Fecha registro' a datetime
        df['Fecha registro'] = pd.to_datetime(df['Fecha registro'], errors='coerce')
        df = df.dropna(subset=['Fecha registro'])

        # Extraer Mes de Cohorte (primer día del mes de registro)
        df['Mes cohorte'] = df['Fecha registro'].dt.to_period('M').dt.to_timestamp()

        # Detectar columnas de actividad mensual (todas excepto 'Usuario', 'Fecha registro', 'Mes cohorte')
        actividad_cols = [col for col in df.columns if col not in ['Usuario', 'Fecha registro', 'Mes cohorte']]

        if not actividad_cols:
            st.error("No se detectaron columnas de actividad mensual.")
        else:
            # Ordenar columnas de actividad por nombre (opcional, según formato de tu archivo)
            actividad_cols_sorted = sorted(actividad_cols)

            # Para debug
            st.write("Columnas de actividad detectadas:", actividad_cols_sorted)

            cohort_data = {}
            for cohorte, grupo in df.groupby('Mes cohorte'):
                total_usuarios = grupo['Usuario'].nunique()
                cohort_data[cohorte] = [total_usuarios]

                for col in actividad_cols_sorted:
                    # Convertir valores a numéricos y filtrar positivos (>0)
                    activos = grupo[grupo[col].apply(lambda x: pd.to_numeric(x, errors='coerce')).fillna(0) > 0]['Usuario'].nunique()
                    pct_retencion = activos / total_usuarios if total_usuarios > 0 else 0
                    cohort_data[cohorte].append(pct_retencion)

            # Crear DataFrame de retención
            columnas_retorno = ['Total usuarios'] + [f'Mes {i}' for i in range(len(actividad_cols_sorted))]
            retencion_df = pd.DataFrame.from_dict(cohort_data, orient='index', columns=columnas_retorno)

            # Formatear porcentajes para mostrar
            retencion_pct_df = retencion_df.copy()
            retencion_pct_df.iloc[:, 1:] = retencion_pct_df.iloc[:, 1:].applymap(lambda x: f"{x:.1%}")

            st.subheader("Matriz de Retención (porcentaje de usuarios activos)")
            st.dataframe(retencion_pct_df)

            # Mostrar heatmap con valores numéricos (0 a 1)
            st.subheader("Heatmap de Retención")
            plt.figure(figsize=(12, 6))
            sns.heatmap(retencion_df.iloc[:, 1:], annot=True, fmt=".1%", cmap="YlGnBu", cbar=True)
            plt.xlabel("Mes desde la cohorte")
            plt.ylabel("Mes de cohorte")
            plt.yticks(rotation=0)
            st.pyplot(plt.gcf())
