import streamlit as st
import plotly.express as px

from module.data_loader import load_data
from module.filters import filtre_standard, aplica_filtre, opreste_daca_gol

df = load_data()

st.title("1. Ponderea tipurilor de credit")
st.markdown("Evidentierea ponderii fiecarui tip de credit (consum, auto, nevoi personale etc.) in total credite acordate persoanelor fizice")

# --- FILTRE ---
alegeri = filtre_standard(df, "c1")

# --- APLICAREA FILTRELOR ---
df_f = aplica_filtre(df, alegeri)
opreste_daca_gol(df_f, "Nu există înregistrări care să corespundă filtrelor selectate.")

# --- AGREGAREA DATELOR ---
pondere_df = df_f['loan_intent'].value_counts().reset_index()
pondere_df.columns = ['Destinație Credit', 'Număr Credite']

total_credite = pondere_df['Număr Credite'].sum()
pondere_df['Procent (%)'] = (pondere_df['Număr Credite'] / total_credite * 100).round(2)

# --- CIFRA PRINCIPALĂ ---
st.metric("Total credite (filtrate)", f"{total_credite:,}")

# --- GRAFICUL ---
st.divider()

tip_chart = st.selectbox(
    "Tipul de grafic:",
    ["Pie Chart", "Bar Chart", "Treemap"],
    key="c1_chart",
)

if tip_chart == "Pie Chart":
    st.caption("Ce pondere are fiecare destinație în totalul creditelor.")
    fig = px.pie(
        pondere_df,
        values='Număr Credite',
        names='Destinație Credit',
        hole=0.4,
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')

elif tip_chart == "Bar Chart":
    st.caption("Numărul de credite pe fiecare destinație.")
    fig = px.bar(
        pondere_df,
        x='Destinație Credit',
        y='Număr Credite',
        text='Procent (%)',
        color='Destinație Credit',
    )
    fig.update_traces(texttemplate='%{text}%', textposition='outside')

else:  # Treemap
    st.caption("Mărimea dreptunghiului = numărul de credite.")
    fig = px.treemap(
        pondere_df,
        path=['Destinație Credit'],
        values='Număr Credite',
    )

fig.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig, use_container_width=True)

with st.expander("Vezi cifrele detaliate"):
    st.dataframe(pondere_df, use_container_width=True, hide_index=True)
