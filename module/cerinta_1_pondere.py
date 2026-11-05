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
    with st.container(border=True):
        st.markdown("**Filtre**")

        r1c1, r1c2 = st.columns(2)
        with r1c1:
            min_v, max_v = int(df['person_age'].min()), int(df['person_age'].max())
            interval_varsta = st.slider("Vârstă", min_v, max_v, (min_v, max_v), key="c1_age")
        with r1c2:
            locuinte = ["Toate"] + sorted(df['person_home_ownership'].unique())
            locuinta_aleasa = st.selectbox("Statutul locuinței", locuinte, key="c1_home")

        r2c1, r2c2 = st.columns(2)
        with r2c1:
            # gol = toate intervalele
            venituri_alese = st.multiselect(
                "Venit anual", list(INTERVALE_VENIT.keys()), key="c1_income", placeholder="Toate"
            )
        with r2c2:
            # gol = toate scopurile
            scopuri_alese = st.multiselect(
                "Tipul creditului", sorted(df['loan_intent'].dropna().unique()), key="c1_intent", placeholder="Toate"
            )

    # --- APLICAREA FILTRELOR PE DATAFRAME ---
    df_f = df[df['person_age'].between(interval_varsta[0], interval_varsta[1])]

    if locuinta_aleasa != "Toate":
        df_f = df_f[df_f['person_home_ownership'] == locuinta_aleasa]

    if scopuri_alese:
        df_f = df_f[df_f['loan_intent'].isin(scopuri_alese)]

    if venituri_alese:
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

    # --- CIFRA PRINCIPALĂ ---
    st.metric("Total credite (filtrate)", f"{total_credite:,}")

    # --- GRAFICUL ---
    st.divider()

    tip_chart = st.selectbox(
        "Tipul de grafic:",
        ["Grafic Circular (Donut)", "Grafic cu Bare (Bar Chart)", "Hartă Proporțională (Treemap)"],
        key="c1_chart",
    )

    if tip_chart == "Grafic Circular (Donut)":
        st.caption("Ce pondere are fiecare destinație în totalul creditelor.")
        fig = px.pie(
            pondere_df,
            values='Număr Credite',
            names='Destinație Credit',
            hole=0.4,
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')

    elif tip_chart == "Grafic cu Bare (Bar Chart)":
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