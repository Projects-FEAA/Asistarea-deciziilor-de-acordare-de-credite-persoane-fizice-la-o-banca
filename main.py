import streamlit as st
import pandas as pd
from module.data_loader import load_data
import module.cerinta_1_pondere as c1 
import module.cerinta_2_risc as c2 # Le vei decomenta când le creezi
import module.cerinta_3_trend as c3
import module.cerinta_4_dobanzi as c4

# 1. Configurare pagină (trebuie să fie prima comandă, setează lățimea pe tot ecranul)
st.set_page_config(page_title="Sistem Asistare Decizii Credite", layout="wide")

# 2. Încărcarea datelor (se va rula rapid din cache-ul setat anterior)
df = load_data()

# 3. Meniul principal de navigare în bara laterală
st.sidebar.title("Navigare SAD")
optiune = st.sidebar.radio(
    "Alege secțiunea:",
    ["Baza de Date", 
     "1. Ponderea Creditelor", 
     "2. Analiză Rău-Platnici", 
     "3. Evoluție Volum", 
     "4. Impact Dobânzi"]
)

# 4. Logica de afișare pentru prima pagină
if optiune == "Baza de Date":
    st.title("Baza de Date")

    # --- FILTRE (în chenar, 2 rânduri a câte 2) ---
    with st.container(border=True):
        st.markdown("**Filtre**")

        r1c1, r1c2 = st.columns(2)
        with r1c1:
            varsta_min, varsta_max = int(df['person_age'].min()), int(df['person_age'].max())
            varsta_interval = st.slider(
                "Vârstă", varsta_min, varsta_max, (varsta_min, varsta_max), key="db_age"
            )
        with r1c2:
            proprietati = ["Toate"] + sorted(df['person_home_ownership'].unique())
            proprietate_aleasa = st.selectbox("Statutul locuinței", proprietati, key="db_home")

        r2c1, r2c2 = st.columns(2)
        with r2c1:
            # gol = toate intervalele
            venituri_alese = st.multiselect(
                "Venit anual", list(c1.INTERVALE_VENIT.keys()), key="db_income", placeholder="Toate"
            )
        with r2c2:
            # gol = toate scopurile
            scopuri_alese = st.multiselect(
                "Tipul creditului", sorted(df['loan_intent'].unique()), key="db_intent", placeholder="Toate"
            )

    # --- APLICAREA FILTRELOR PE PANDAS ---
    df_filtrat = df[df['person_age'].between(varsta_interval[0], varsta_interval[1])]

    if proprietate_aleasa != "Toate":
        df_filtrat = df_filtrat[df_filtrat['person_home_ownership'] == proprietate_aleasa]

    if scopuri_alese:
        df_filtrat = df_filtrat[df_filtrat['loan_intent'].isin(scopuri_alese)]

    if venituri_alese:
        masca_venit = pd.Series(False, index=df_filtrat.index)
        for eticheta in venituri_alese:
            v_min, v_max = c1.INTERVALE_VENIT[eticheta]
            masca_venit |= (
                (df_filtrat['person_income'] >= v_min) &
                (df_filtrat['person_income'] < v_max)
            )
        df_filtrat = df_filtrat[masca_venit]

    # --- AFIȘAREA GRID-ULUI ---
    st.dataframe(df_filtrat, use_container_width=True, hide_index=True)

    st.caption(f"Afișăm {len(df_filtrat):,} din totalul de {len(df):,} credite pe baza filtrelor aplicate.")

# Logica de direcționare către modulele voastre viitoare
elif optiune == "1. Ponderea Creditelor":
    c1.render_page(df)
    
elif optiune == "2. Analiză Rău-Platnici":
    c2.render_page(df)

elif optiune == "3. Evoluție Volum":
    c3.render_page(df)

elif optiune == "4. Impact Dobânzi":
    c4.render_page(df)