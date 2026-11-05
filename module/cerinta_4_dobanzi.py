import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# Etichete în română pentru tipurile de credit (loan_intent)
TIPURI_CREDIT = {
    "EDUCATION": "Educație",
    "MEDICAL": "Medical",
    "VENTURE": "Antreprenoriat",
    "PERSONAL": "Personal",
    "DEBTCONSOLIDATION": "Consolidare datorii",
    "HOMEIMPROVEMENT": "Renovare locuință",
}

# Intervale de venit anual (min inclusiv, max exclusiv) - le poți ajusta
INTERVALE_VENIT = {
    "Sub 30.000 $": (0, 30_000),
    "30.000 - 50.000 $": (30_000, 50_000),
    "50.000 - 75.000 $": (50_000, 75_000),
    "75.000 - 100.000 $": (75_000, 100_000),
    "Peste 100.000 $": (100_000, float("inf")),
}

# Intervale de vârstă (min inclusiv, max exclusiv) - le poți ajusta
INTERVALE_VARSTA = {
    "Sub 25 ani": (0, 25),
    "25 - 29 ani": (25, 30),
    "30 - 34 ani": (30, 35),
    "35 - 44 ani": (35, 45),
    "45+ ani": (45, float("inf")),
}

# Criteriile după care se poate grupa graficul cu bare
CRITERII_GRUPARE = ["Tipul creditului", "Interval de vârstă", "Interval de venit"]


def _limite(intervale):
    """Transformă un dicționar de intervale în lista de limite pentru pd.cut."""
    return [0] + [maxim for _, maxim in intervale.values()]


def render_page(df):
    st.title("4. Estimarea cererii în funcție de dobândă")
    st.markdown("Estimarea cererii de credite în cazul reducerii/creșterii dobânzii")

    # --- FILTRE (în chenar, 2 rânduri a câte 2) ---
    with st.container(border=True):
        st.markdown("**Filtre**")

        r1c1, r1c2 = st.columns(2)
        with r1c1:
            min_v, max_v = int(df['person_age'].min()), int(df['person_age'].max())
            interval_varsta = st.slider("Vârstă", min_v, max_v, (min_v, max_v), key="c4_age")
        with r1c2:
            tipuri_disponibile = sorted(
                df['loan_intent'].dropna().unique(),
                key=lambda x: TIPURI_CREDIT.get(x, x),
            )
            tipuri_alese = st.multiselect(
                "Tipul creditului",
                tipuri_disponibile,
                format_func=lambda x: TIPURI_CREDIT.get(x, x),
                key="c4_intent",
                placeholder="Toate",
            )

        r2c1, r2c2 = st.columns(2)
        with r2c1:
            # gol = toate intervalele
            venituri_alese = st.multiselect(
                "Venit anual", list(INTERVALE_VENIT.keys()), key="c4_income", placeholder="Toate"
            )
        with r2c2:
            locuinte = ["Toate"] + sorted(df['person_home_ownership'].unique())
            locuinta_aleasa = st.selectbox("Statutul locuinței", locuinte, key="c4_home")

    # --- SETĂRILE PROGNOZEI (în chenar) ---
    with st.container(border=True):
        st.markdown("**Setări prognoză**")
        st.caption("Model cu elasticitate constantă: `Volum nou = Volum actual × (Rata nouă / Rata medie) ^ ε`")

        p1, p2 = st.columns(2)
        with p1:
            delta = st.slider(
                "Modificarea dobânzii (puncte procentuale)",
                min_value=-5.0, max_value=5.0, value=1.0, step=0.5, key="c4_delta",
            )
        with p2:
            elast = st.slider(
                "Elasticitatea cererii (ipoteză)",
                min_value=-3.0, max_value=-0.1, value=-1.0, step=0.1, key="c4_elast",
            )

        p3, p4 = st.columns(2)
        with p3:
            criteriu = st.selectbox("Grupează graficul cu bare după:", CRITERII_GRUPARE, key="c4_group")

    # --- APLICAREA FILTRELOR ---
    # Eliminăm rândurile fără dobândă setată pentru acuratețea analizei matematice
    df_valid = df.dropna(subset=['loan_int_rate'])
    df_valid = df_valid[df_valid['person_age'].between(interval_varsta[0], interval_varsta[1])]

    if locuinta_aleasa != "Toate":
        df_valid = df_valid[df_valid['person_home_ownership'] == locuinta_aleasa]

    if tipuri_alese:
        df_valid = df_valid[df_valid['loan_intent'].isin(tipuri_alese)]

    if venituri_alese:
        masca_venit = pd.Series(False, index=df_valid.index)
        for eticheta in venituri_alese:
            v_min, v_max = INTERVALE_VENIT[eticheta]
            masca_venit |= (df_valid['person_income'] >= v_min) & (df_valid['person_income'] < v_max)
        df_valid = df_valid[masca_venit]

    df_valid = df_valid.copy()

    if df_valid.empty:
        st.warning("Nu există credite pentru filtrele selectate.")
        return

    # --- CIFRELE PRINCIPALE ---
    rata_medie = df_valid['loan_int_rate'].mean()
    volum_baza = df_valid['loan_amnt'].sum()
    nr_baza = len(df_valid)

    volum_nou = volum_baza * ((rata_medie + delta) / rata_medie) ** elast
    diferenta = volum_nou - volum_baza

    m1, m2, m3 = st.columns(3)
    m1.metric("Rata medie actuală", f"{rata_medie:.2f}%")
    m2.metric("Rata medie nouă", f"{rata_medie + delta:.2f}%", f"{delta:+.1f} pp")
    m3.metric("Cerere estimată (volum $)", f"{volum_nou:,.0f}", f"{diferenta / volum_baza:+.1%}")

    # Semnul dolarului se scapă (\\$), altfel Streamlit îl interpretează ca formulă matematică
    st.caption(
        f"Bază: {nr_baza:,} credite, volum {volum_baza:,.0f} \\$. "
        f"Cu o modificare de {delta:+.1f} pp și elasticitate {elast}, "
        f"cererea totală ar ajunge la ~{volum_nou:,.0f} \\$ ({diferenta / volum_baza:+.1%})."
    )

    # --- DATE: prognoza pe grupuri (pentru graficul cu bare) ---
    if criteriu == "Tipul creditului":
        df_valid['grup'] = df_valid['loan_intent'].map(lambda x: TIPURI_CREDIT.get(x, x))
    elif criteriu == "Interval de vârstă":
        df_valid['grup'] = pd.cut(
            df_valid['person_age'],
            bins=_limite(INTERVALE_VARSTA),
            labels=list(INTERVALE_VARSTA.keys()),
            right=False,
        )
    else:  # Interval de venit
        df_valid['grup'] = pd.cut(
            df_valid['person_income'],
            bins=_limite(INTERVALE_VENIT),
            labels=list(INTERVALE_VENIT.keys()),
            right=False,
        )

    # observed=True: intervalele goale nu apar; rândurile fără grup (ex. venit lipsă) sunt ignorate
    pe_grup = (
        df_valid.groupby('grup', observed=True)
        .agg(volum=('loan_amnt', 'sum'), rata=('loan_int_rate', 'mean'))
        .reset_index()
    )
    pe_grup['grup'] = pe_grup['grup'].astype(str)
    pe_grup['rata_noua'] = pe_grup['rata'] + delta
    pe_grup = pe_grup[pe_grup['rata_noua'] > 0]  # evităm rate noi <= 0
    pe_grup['volum_estimat'] = pe_grup['volum'] * (pe_grup['rata_noua'] / pe_grup['rata']) ** elast
    pe_grup['variatie'] = pe_grup['volum_estimat'] / pe_grup['volum'] - 1

    # Tipurile de credit se sortează după volum; intervalele rămân în ordinea lor naturală
    if criteriu == "Tipul creditului":
        pe_grup = pe_grup.sort_values('volum', ascending=False)

    # --- DATE: trend observat (pe fiecare punct procentual de dobândă) + prognoză ---
    df_valid['rata_rotunjita'] = df_valid['loan_int_rate'].round()
    istoric = (
        df_valid.groupby('rata_rotunjita')['loan_amnt']
        .sum()
        .reset_index()
        .rename(columns={'rata_rotunjita': 'Rata dobânzii (%)', 'loan_amnt': 'Cerere (volum $)'})
        .sort_values('Rata dobânzii (%)')
    )
    istoric = istoric[istoric['Rata dobânzii (%)'] > 0]

    prognoza_df = istoric.copy()
    prognoza_df['Rata nouă (%)'] = prognoza_df['Rata dobânzii (%)'] + delta
    prognoza_df = prognoza_df[prognoza_df['Rata nouă (%)'] > 0]
    prognoza_df['Cerere estimată ($)'] = (
        prognoza_df['Cerere (volum $)']
        * (prognoza_df['Rata nouă (%)'] / prognoza_df['Rata dobânzii (%)']) ** elast
    )

    # --- GRAFICE una lângă alta ---
    st.divider()
    col_bare, col_linie = st.columns(2)

    # Bare: volum curent vs. volum estimat, pe grupul ales
    with col_bare:
        st.subheader("Volumul de credite: curent vs. estimat")
        fig_bare = go.Figure()
        fig_bare.add_trace(go.Bar(
            x=pe_grup['grup'],
            y=pe_grup['volum'],
            name='Volum curent',
            marker_color='#1f77b4',
            hovertemplate="%{x}<br>Volum curent: %{y:,.0f} $<extra></extra>",
        ))
        fig_bare.add_trace(go.Bar(
            x=pe_grup['grup'],
            y=pe_grup['volum_estimat'],
            name=f'Volum estimat (Δ={delta:+.1f} pp, ε={elast})',
            marker_color='rgba(255, 0, 0, 0.55)',
            customdata=pe_grup['variatie'],
            hovertemplate=(
                "%{x}<br>Volum estimat: %{y:,.0f} $"
                "<br>Variație: %{customdata:+.1%}<extra></extra>"
            ),
        ))
        fig_bare.update_layout(
            barmode='overlay',
            height=420,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis_title=criteriu,
            yaxis_title="Volum ($)",
            legend=dict(orientation='h', y=-0.3),
        )
        st.plotly_chart(fig_bare, use_container_width=True)

    # Linii: cerere observată (plină) + prognoză (punctată)
    with col_linie:
        st.subheader("Cererea observată și prognoza (linie punctată)")
        fig_prog = go.Figure()
        fig_prog.add_trace(go.Scatter(
            x=istoric['Rata dobânzii (%)'],
            y=istoric['Cerere (volum $)'],
            mode='lines+markers',
            name='Cerere observată',
            line=dict(color='#1f77b4', width=3),
            hovertemplate="Dobândă: %{x}%<br>Cerere actuală: %{y:,.0f} $<extra></extra>",
        ))
        fig_prog.add_trace(go.Scatter(
            x=prognoza_df['Rata dobânzii (%)'],
            y=prognoza_df['Cerere estimată ($)'],
            mode='lines+markers',
            name=f'Prognoză (Δ={delta:+.1f} pp, ε={elast})',
            line=dict(color='red', width=3, dash='dot'),
            customdata=prognoza_df['Rata nouă (%)'],
            hovertemplate=(
                "Dobândă actuală: %{x}%<br>"
                "Rata nouă: %{customdata}%<br>"
                "Cerere estimată: %{y:,.0f} $<extra></extra>"
            ),
        ))
        fig_prog.update_layout(
            height=420,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis_title="Rata dobânzii actuale (%)",
            yaxis_title="Cerere (volum $)",
            legend=dict(orientation='h', y=-0.3),
        )
        st.plotly_chart(fig_prog, use_container_width=True)

    # --- TABELUL CU ESTIMĂRI ---
    with st.expander("Vezi valorile estimate"):
        tabel = pe_grup[['grup', 'volum', 'rata', 'rata_noua', 'volum_estimat', 'variatie']].copy()
        tabel['variatie'] = tabel['variatie'] * 100
        tabel.columns = [
            criteriu, 'Volum curent ($)', 'Rata medie (%)',
            'Rata nouă (%)', 'Volum estimat ($)', 'Variație (%)',
        ]
        st.dataframe(
            tabel,
            hide_index=True,
            use_container_width=True,
            column_config={
                'Volum curent ($)': st.column_config.NumberColumn(format="localized"),
                'Volum estimat ($)': st.column_config.NumberColumn(format="localized"),
                'Rata medie (%)': st.column_config.NumberColumn(format="%.2f%%"),
                'Rata nouă (%)': st.column_config.NumberColumn(format="%.2f%%"),
                'Variație (%)': st.column_config.NumberColumn(format="%+.1f%%"),
            },
        )