import streamlit as st

from module.data_loader import load_data
from module.filters import filtre_standard, aplica_filtre

df = load_data()

st.title("Asistarea deciziilor de acordare de credite persoane fizice la o banca")

# --- FILTRE ---
alegeri = filtre_standard(df, "db")

# --- APLICAREA FILTRELOR ---
df_filtrat = aplica_filtre(df, alegeri)

# --- AFIȘAREA GRID-ULUI ---
st.dataframe(df_filtrat, use_container_width=True, hide_index=True)

st.caption(f"Afișăm {len(df_filtrat):,} din totalul de {len(df):,} credite pe baza filtrelor aplicate.")
