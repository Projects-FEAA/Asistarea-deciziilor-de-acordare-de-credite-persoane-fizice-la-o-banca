import streamlit as st
import plotly.express as px
import pandas as pd

# Intervale de venit anual (min inclusiv, max exclusiv) - le poți ajusta
INTERVALE_VENIT = {
    "Sub 30.000 $": (0, 30_000),
    "30.000 - 50.000 $": (30_000, 50_000),
    "50.000 - 75.000 $": (50_000, 75_000),
    "75.000 - 100.000 $": (75_000, 100_000),
    "Peste 100.000 $": (100_000, float("inf")),
}

def render_page(df):
    st.title("1. Ponderea tipurilor de credit")
    st.markdown("Analiza distribuției portofoliului de credite acordate persoanelor fizice, cu opțiuni de filtrare și vizualizare dinamică.")
    
    # --- FILTRE INTERACTIVE (SPECIFICE ACESTEI PAGINI) ---
    filterCol1, filterCol2, filterCol3, filterCol4 = st.columns(4)

    with filterCol1:
        # 1. Slider pentru vârstă
        min_v, max_v = int(df['person_age'].min()), int(df['person_age'].max())
        interval_varsta = st.slider("Selectează intervalul de vârstă", min_v, max_v, (min_v, max_v), key="c1_age")

    with filterCol2:
        # 2. Selectbox pentru statutul locuinței
        locuinte = ["Toate"] + list(df['person_home_ownership'].unique())
        locuinta_aleasa = st.selectbox("Statut locuință", locuinte, key="c1_home")

    with filterCol3:
        # 3. Multiselect (combo box) pentru scopul creditului - implicit sunt toate selectate
        scopuri = sorted(df['loan_intent'].dropna().unique())
        scop_ales = st.multiselect(
            "Scopul Creditului:",
            options=scopuri,
            default=scopuri,
            key="c1_intent",
            placeholder="Alege unul sau mai multe scopuri"
        )

    with filterCol4:
        # 4. Multiselect pentru intervalele de venit anual - implicit sunt toate selectate
        intervale_venit = list(INTERVALE_VENIT.keys())
        venituri_alese = st.multiselect(
            "Interval de venit anual",
            options=intervale_venit,
            default=intervale_venit,
            key="c1_income",
            placeholder="Alege unul sau mai multe intervale"
        )

    # --- APLICAREA FILTRELOR PE DATAFRAME ---
    df_f = df[
        (df['person_age'] >= interval_varsta[0]) & 
        (df['person_age'] <= interval_varsta[1])
    ]
    if locuinta_aleasa != "Toate":
        df_f = df_f[df_f['person_home_ownership'] == locuinta_aleasa]

    df_f = df_f[df_f['loan_intent'].isin(scop_ales)]

    # Dacă sunt selectate toate intervalele, nu filtrăm (rămân și rândurile fără venit)
    if len(venituri_alese) < len(intervale_venit):
        masca_venit = pd.Series(False, index=df_f.index)
        for eticheta in venituri_alese:
            v_min, v_max = INTERVALE_VENIT[eticheta]
            masca_venit |= (df_f['person_income'] >= v_min) & (df_f['person_income'] < v_max)
        df_f = df_f[masca_venit]
        
    # Verificăm dacă au rămas date după filtrare
    if df_f.empty:
        st.warning("Nu există înregistrări care să corespundă filtrelor selectate.")
        return

    # --- AGREGAREA DATELOR ---
    pondere_df = df_f['loan_intent'].value_counts().reset_index()
    pondere_df.columns = ['Destinație Credit', 'Număr Credite']
    
    total_credite = pondere_df['Număr Credite'].sum()
    pondere_df['Procent (%)'] = (pondere_df['Număr Credite'] / total_credite * 100).round(2)

    
    # --- LAYOUT PRINCIPAL: TABEL + GRAFIC ---
    
    st.subheader("Date Tabelare Agregate")
    st.dataframe(pondere_df, use_container_width=True, hide_index=True)
    st.metric("Total Credite (filtrate)", f"{total_credite:,}")
    
    st.subheader("Reprezentare Vizuală")

    tip_chart = st.selectbox(
        "Alege tipul de reprezentare grafică:",
        ["Grafic Circular (Donut)", "Grafic cu Bare (Bar Chart)", "Hartă Proporțională (Treemap)"]
    )
    
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