import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

st.title("Análisis de Retención de Usuarios por Cohortes")

st.markdown("""
Subí un archivo Excel que contenga las siguientes columnas mínimas:
- **Usuario**: Identificador único del usuario.
- **Fecha registro**: Fecha en que el usuario se registró.
- Columnas de actividad mensual: una columna por cada mes con valores numéricos positivos si hubo actividad, 0 o vacío si no.

El análisis calculará la matriz de retención por cohortes mensuales, considerando solo actividad hasta el mes actual.
""")

archivo = st.file_uploader("Subí tu archivo Excel", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo)

    columnas_minimas = ['Usuario', 'Fecha registro']
    if not all(col in df.columns for col in columnas_minimas):
        st.error(f"El archivo debe contener las columnas: {', '.join(columnas_minimas)}")
    else:
        # Convertir 'Fecha registro' a datetime, sin hora
        df['Fecha registro'] = pd.to_datetime(df['Fecha registro'], errors='coerce').dt.normalize()
        df = df.dropna(subset=['Fecha registro'])

        # Formatear la fecha para mostrarla después (en la tabla o como info)
        df['Fecha registro formateada'] = df['Fecha registro'].dt.strftime('%Y-%m-%d')

        # Extraer Mes de Cohorte (primer día del mes)
        df['Mes cohorte'] = df['Fecha registro'].dt.to_period('M').dt.to_timestamp()

        # Columnas de actividad mensual (asumiendo que son todas menos las básicas)
        actividad_cols = [col for col in df.columns if col not in ['Usuario', 'Fecha registro', 'Fecha registro formateada', 'Mes cohorte']]

        if not actividad_cols:
            st.error("No se detectaron columnas de actividad mensual.")
        else:
            actividad_cols_sorted = sorted(actividad_cols)

            st.write("Columnas de actividad detectadas:", actividad_cols_sorted)

            cohort_data = {}
            fecha_actual = pd.Timestamp(datetime.now().date())

            # Calculamos el máximo número de meses que puede haber (para mostrar toda la matriz)
            max_meses = len(actividad_cols_sorted) - 1

            for cohorte, grupo in df.groupby('Mes cohorte'):
                total_usuarios = grupo['Usuario'].nunique()

                # Cuántos meses pasaron desde la cohorte hasta hoy
                meses_hasta_hoy = (fecha_actual.year - cohorte.year) * 12 + (fecha_actual.month - cohorte.month)

                lista_retencion = [total_usuarios]

                for i, col in enumerate(actividad_cols_sorted):
                    # Para meses futuros respecto a hoy, poner NaN (sin calcular retención)
                    if i > meses_hasta_hoy:
                        lista_retencion.append(np.nan)
                        continue

                    # Revisar actividad positiva
                    activos = grupo[grupo[col].apply(lambda x: pd.to_numeric(x, errors='coerce')).fillna(0) > 0]['Usuario'].nunique()
                    pct_retencion = activos / total_usuarios if total_usuarios > 0 else 0
                    lista_retencion.append(pct_retencion)

                cohort_data[cohorte] = lista_retencion

            columnas_retorno = ['Total usuarios'] + [f'Mes {i}' for i in range(len(actividad_cols_sorted))]

            retencion_df = pd.DataFrame.from_dict(cohort_data, orient='index', columns=columnas_retorno)

            # Formatear para mostrar porcentaje y total usuarios
            retencion_pct_df = retencion_df.copy()
            retencion_pct_df.iloc[:, 1:] = retencion_pct_df.iloc[:, 1:].applymap(lambda x: f"{x:.1%}" if pd.notnull(x) else "")

            st.subheader("Matriz de Retención (porcentaje de usuarios activos)")
            st.dataframe(retencion_pct_df)

            st.subheader("Heatmap de Retención")
            plt.figure(figsize=(12, 6))
            sns.heatmap(retencion_df.iloc[:, 1:], annot=True, fmt=".1%", cmap="YlGnBu", cbar=True, linewidths=.5, linecolor='gray')
            plt.xlabel("Mes desde la cohorte")
            plt.ylabel("Mes de cohorte")
            plt.yticks(rotation=0)
            st.pyplot(plt.gcf())
