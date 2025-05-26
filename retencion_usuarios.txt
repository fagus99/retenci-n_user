
import streamlit as st
import pandas as pd

st.title("Análisis de Retención de Usuarios")

# Cargar archivo
archivo = st.file_uploader("Subí tu archivo en formato Excel", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo)
    st.write("Vista previa del archivo:")
    st.dataframe(df.head())

    # Lista de columnas de meses en orden
    meses = ['ago', 'sep', 'oct', 'nov', 'dic', 'ene', 'feb', 'mar', 'abr', 'may']
    meses_presentes = [m for m in meses if m in df.columns]

    usuarios_abandono = []
    usuarios_activos = []

    for _, row in df.iterrows():
        user = row['usuario']
        registro = row['fecha registro']
        abandono = None

        for i, mes in enumerate(meses_presentes):
            valor = row[mes]
            if pd.isna(valor) or valor == 0:
                actividad_antes = row[meses_presentes[:i]]
                if actividad_antes.notna().any() and (actividad_antes != 0).any():
                    abandono = mes
                    break

        if abandono:
            usuarios_abandono.append({'usuario': user, 'fecha registro': registro, 'mes_abandono': abandono})
        else:
            usuarios_activos.append({'usuario': user, 'fecha registro': registro})

    df_abandono = pd.DataFrame(usuarios_abandono)
    df_activos = pd.DataFrame(usuarios_activos)

    st.subheader("Usuarios activos hasta mayo")
    st.dataframe(df_activos)

    st.subheader("Usuarios que abandonaron y en qué mes")
    st.dataframe(df_abandono)

    # Botones de descarga
    st.download_button("📥 Descargar usuarios activos", data=df_activos.to_csv(index=False), file_name="usuarios_activos.csv", mime="text/csv")
    st.download_button("📥 Descargar usuarios abandonados", data=df_abandono.to_csv(index=False), file_name="usuarios_abandonados.csv", mime="text/csv")
