import streamlit as st
import plotly.express as px
import pandas as pd

def render_page(df):
    st.title("1. Ponderea tipurilor de credit")
    st.markdown("Analiza distribuției portofoliului de credite acordate persoanelor fizice, cu opțiuni de filtrare și vizualizare dinamică.")
    
    # --- FILTRE INTERACTIVE ÎN BARA LATERALĂ (SPECIFICE ACESTEI PAGINI) ---
    st.sidebar.header("Filtre - Ponderea Creditelor")
    
    # 1. Slider pentru vârstă
    min_v, max_v = int(df['person_age'].min()), int(df['person_age'].max())
    interval_varsta = st.sidebar.slider("Selectează intervalul de vârstă", min_v, max_v, (min_v, max_v), key="c1_age")
    
    # 2. Selectbox pentru statutul locuinței
    locuinte = ["Toate"] + list(df['person_home_ownership'].unique())
    locuinta_aleasa = st.sidebar.selectbox("Statut locuință", locuinte, key="c1_home")
    
    # --- APLICAREA FILTRELOR PE DATAFRAME ---
    df_f = df[
        (df['person_age'] >= interval_varsta[0]) & 
        (df['person_age'] <= interval_varsta[1])
    ]
    if locuinta_aleasa != "Toate":
        df_f = df_f[df_f['person_home_ownership'] == locuinta_aleasa]
        
    # Verificăm dacă au rămas date după filtrare
    if df_f.empty:
        st.warning("Nu există înregistrări care să corespundă filtrelor selectate.")
        return

    # --- AGREGAREA DATELOR ---
    pondere_df = df_f['loan_intent'].value_counts().reset_index()
    pondere_df.columns = ['Destinație Credit', 'Număr Credite']
    
    total_credite = pondere_df['Număr Credite'].sum()
    pondere_df['Procent (%)'] = (pondere_df['Număr Credite'] / total_credite * 100).round(2)
    
    # --- INTERFAȚĂ: SELECTOR DE TIP DE CHART ---
    st.subheader("Configurare Vizualizare")
    tip_chart = st.selectbox(
        "Alege tipul de reprezentare grafică:",
        ["Grafic Circular (Donut)", "Grafic cu Bare (Bar Chart)", "Hartă Proporțională (Treemap)"]
    )
    
    # --- LAYOUT PRINCIPAL: TABEL + GRAFIC ---
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.subheader("Date Tabelare Agregate")
        st.dataframe(pondere_df, use_container_width=True, hide_index=True)
        st.metric("Total Credite (filtrate)", f"{total_credite:,}")
        
    with col2:
        st.subheader("Reprezentare Vizuală")
        
        # Generarea dinamică a graficului în funcție de selecția utilizatorului
        if tip_chart == "Grafic Circular (Donut)":
            fig = px.pie(
                pondere_df, 
                values='Număr Credite', 
                names='Destinație Credit',
                hole=0.4,
                title="Ponderea creditelor pe destinații"
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            
        elif tip_chart == "Grafic cu Bare (Bar Chart)":
            fig = px.bar(
                pondere_df, 
                x='Destinație Credit', 
                y='Număr Credite',
                text='Procent (%)',
                color='Destinație Credit',
                title="Numărul de credite pe categorii"
            )
            fig.update_traces(texttemplate='%{text}%', textposition='outside')
            
        else: # Treemap
            fig = px.treemap(
                pondere_df,
                path=['Destinație Credit'],
                values='Număr Credite',
                title="Ponderea ierarhică a creditelor"
            )
            
        st.plotly_chart(fig, use_container_width=True)