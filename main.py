import streamlit as st
from module.data_loader import load_data
import module.cerinta_1_pondere as c1 
import module.cerinta_2_risc as c2 # Le vei decomenta când le creezi
# import module.cerinta_3_trend as c3
import module.cerinta_4_dobanzi as c4

# 1. Configurare pagină (trebuie să fie prima comandă, setează lățimea pe tot ecranul)
st.set_page_config(page_title="Sistem Asistare Decizii Credite", layout="wide")

# 2. Încărcarea datelor (se va rula rapid din cache-ul setat anterior)
df = load_data()

# 3. Meniul principal de navigare în bara laterală
st.sidebar.title("Navigare SAD")
optiune = st.sidebar.radio(
    "Alege secțiunea:",
    ["Baza de Date (Grid)", 
     "1. Ponderea Creditelor", 
     "2. Analiză Rău-Platnici", 
     "3. Evoluție Volum", 
     "4. Impact Dobânzi"]
)

# 4. Logica de afișare pentru prima pagină
if optiune == "Baza de Date (Grid)":
    st.title("Explorarea Bazei de Date")
    st.write("Folosește filtrele pentru a restrânge setul de date. **Click pe numele coloanelor pentru a sorta tabelul.**")
    
    # --- FILTRE INTERACTIVE ---
    st.sidebar.header("Filtrează Datele")
    
    # Filtru Multiselect (Combo Box)
    scopuri = df['loan_intent'].unique()
    scop_ales = st.sidebar.multiselect("Scopul Creditului:", options=scopuri, default=scopuri)
    
    # Filtru Slider (Interval valori)
    varsta_min, varsta_max = int(df['person_age'].min()), int(df['person_age'].max())
    varsta_interval = st.sidebar.slider("Interval Vârstă:", varsta_min, varsta_max, (20, 50))
    
    # Filtru Selectbox (O singură opțiune)
    proprietate = df['person_home_ownership'].unique().tolist()
    proprietate.insert(0, "Toate") # Adăugăm opțiunea de a nu filtra
    proprietate_aleasa = st.sidebar.selectbox("Statut Locuință:", options=proprietate)
    
    # --- APLICAREA FILTRELOR PE PANDAS ---
    # Creăm o mască de filtrare
    df_filtrat = df[
        (df['loan_intent'].isin(scop_ales)) &
        (df['person_age'] >= varsta_interval[0]) &
        (df['person_age'] <= varsta_interval[1])
    ]
    
    if proprietate_aleasa != "Toate":
        df_filtrat = df_filtrat[df_filtrat['person_home_ownership'] == proprietate_aleasa]
        
    # --- AFIȘAREA GRID-ULUI ---
    # use_container_width întinde grid-ul pe tot ecranul, hide_index ascunde numerele de rând inutile
    st.dataframe(df_filtrat, use_container_width=True, hide_index=True)
    
    # Sumarizare simplă la baza tabelului
    st.caption(f"Afișăm {len(df_filtrat)} din totalul de {len(df)} credite pe baza filtrelor aplicate.")

# Logica de direcționare către modulele voastre viitoare
elif optiune == "1. Ponderea Creditelor":
    c1.render_page(df)
    
elif optiune == "2. Analiză Rău-Platnici":
    c2.render_page(df)

elif optiune == "4. Impact Dobânzi":
    c4.render_page(df)
    
# ... restul opțiunilor ...