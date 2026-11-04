import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Etichete în română pentru tipurile de credit (loan_intent)
TIPURI_CREDIT = {
    "EDUCATION": "Educație",
    "MEDICAL": "Medical",
    "VENTURE": "Antreprenoriat",
    "PERSONAL": "Personal",
    "DEBTCONSOLIDATION": "Consolidare datorii",
    "HOMEIMPROVEMENT": "Renovare locuință",
}


def render_page(df):
    st.title("4. Estimarea cererii în funcție de dobândă")
    st.markdown("Impactul variației ratei dobânzii asupra volumului total de credite solicitate.")

    # ------------------------------------------------------------------
    # FILTRE: tipul creditului + vârsta
    # ------------------------------------------------------------------
    f1, f2 = st.columns(2)

    with f1:
        tipuri_disponibile = sorted(
            df['loan_intent'].dropna().unique(),
            key=lambda x: TIPURI_CREDIT.get(x, x)
        )
        tipuri_alese = st.multiselect(
            "Tipul creditului",
            options=tipuri_disponibile,
            default=tipuri_disponibile,
            format_func=lambda x: TIPURI_CREDIT.get(x, x),
            placeholder="Alege unul sau mai multe tipuri"
        )

    with f2:
        # Limităm la 80 de ani: în date există vârste nerealiste (ex. 144)
        varsta_min, varsta_max = st.slider(
            "Vârsta solicitantului",
            min_value=int(df['person_age'].min()), max_value=80,
            value=(int(df['person_age'].min()), 80)
        )

    # Eliminăm rândurile fără dobândă setată pentru acuratețea analizei matematice
    df_valid = df.dropna(subset=['loan_int_rate']).copy()

    # Aplicăm filtrele
    df_valid = df_valid[df_valid['person_age'].between(varsta_min, varsta_max)]
    df_valid = df_valid[df_valid['loan_intent'].isin(tipuri_alese)]

    if df_valid.empty:
        st.warning("Nu există credite pentru filtrele selectate.")
        return

    st.caption(f"{len(df_valid):,} credite după filtrare.")

    # Creăm intervale de dobândă (ex: 5-8%, 8-11% etc.)
    bins = [0, 8, 11, 14, 17, 25]
    labels = ['Sub 8%', '8% - 11%', '11% - 14%', '14% - 17%', 'Peste 17%']
    df_valid['Interval_Dobanda'] = pd.cut(df_valid['loan_int_rate'], bins=bins, labels=labels)

    # Agregăm cererea totală (suma cerută) pe fiecare interval de dobândă
    cerere_df = df_valid.groupby('Interval_Dobanda', observed=False)['loan_amnt'].sum().reset_index()
    cerere_df.columns = ['Interval Dobândă', 'Cerere Totală (Volum $)']

    # UI Layout
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Volumul Cererii pe Intervale")
        fig_bar = px.bar(
            cerere_df,
            x='Interval Dobândă',
            y='Cerere Totală (Volum $)',
            title="Volumul total de credite pe tranșe de dobândă",
            text_auto='.2s',
            color='Cerere Totală (Volum $)',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        st.subheader("Relația dobândă – sumă (Scatter)")
        # Folosim un eșantion pentru performanță vizuală bună în browser
        df_sample = df_valid.sample(n=min(2000, len(df_valid)), random_state=42)

        fig_scatter = px.scatter(
            df_sample,
            x="loan_int_rate",
            y="loan_amnt",
            title="Relația Dobândă vs. Sumă Solicitată (Eșantion)",
            labels={"loan_int_rate": "Rata Dobânzii (%)", "loan_amnt": "Suma Solicitată ($)"},
            opacity=0.5
        )

        # Linie de trend OLS calculată cu numpy
        if len(df_sample) >= 2 and df_sample["loan_int_rate"].nunique() > 1:
            panta, interceptor = np.polyfit(df_sample["loan_int_rate"], df_sample["loan_amnt"], 1)
            x_line = np.linspace(
                df_sample["loan_int_rate"].min(),
                df_sample["loan_int_rate"].max(),
                100
            )
            fig_scatter.add_scatter(
                x=x_line, y=panta * x_line + interceptor,
                mode="lines", name="Trend (OLS)", line=dict(color="red"),
                hovertemplate="Trend <br> Dobândă: %{x:.2f}%<br>Trend: %{y:,.0f} $<extra></extra>"
            )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # ------------------------------------------------------------------
    # PROGNOZĂ: cererea la reducerea / creșterea dobânzii (elasticitate)
    # ------------------------------------------------------------------
    st.divider()
    st.header("Prognoză: cererea la reducerea / creșterea dobânzii")
    st.markdown(
        "Model cu elasticitate constantă: "
        "`Volum nou = Volum actual × (Rata nouă / Rata medie) ^ ε`"
    )

    rata_medie = df_valid['loan_int_rate'].mean()
    volum_baza = df_valid['loan_amnt'].sum()
    nr_baza = len(df_valid)

    c1, c2 = st.columns(2)
    with c1:
        delta = st.slider(
            "Modificarea dobânzii (puncte procentuale)",
            min_value=-5.0, max_value=5.0, value=1.0, step=0.5
        )
    with c2:
        elast = st.slider(
            "Elasticitatea cererii (ipoteză)",
            min_value=-3.0, max_value=-0.1, value=-1.0, step=0.1,
        )

    def prognoza(delta_pp, e):
        rata_noua = rata_medie + delta_pp
        return volum_baza * (rata_noua / rata_medie) ** e

    volum_nou = prognoza(delta, elast)
    diferenta = volum_nou - volum_baza

    m1, m2, m3 = st.columns(3)
    m1.metric("Rata medie actuală", f"{rata_medie:.2f}%")
    m2.metric("Rata medie nouă", f"{rata_medie + delta:.2f}%", f"{delta:+.1f} pp")
    m3.metric("Cerere estimată (volum $)", f"{volum_nou:,.0f}",
              f"{diferenta / volum_baza:+.1%}")

    st.caption(
        f"Bază: {nr_baza:,} credite, volum {volum_baza:,.0f} $. "
        f"Cu o modificare de {delta:+.1f} pp și elasticitate {elast}, "
        f"cererea totală ar ajunge la ~{volum_nou:,.0f} $ ({diferenta / volum_baza:+.1%})."
    )

    # ------------------------------------------------------------------
    # GRAFIC: trend observat (linie plină) + prognoză (linie punctată)
    # ------------------------------------------------------------------
    # Trend observat: volumul cerut pe fiecare punct procentual de dobândă
    df_valid['rata_rotunjita'] = df_valid['loan_int_rate'].round()
    istoric = (
        df_valid.groupby('rata_rotunjita')['loan_amnt']
        .sum()
        .reset_index()
        .rename(columns={'rata_rotunjita': 'Rata dobânzii (%)',
                         'loan_amnt': 'Cerere (volum $)'})
        .sort_values('Rata dobânzii (%)')
    )
    istoric = istoric[istoric['Rata dobânzii (%)'] > 0]

    # Prognoza: aplicăm modelul de elasticitate pe fiecare punct al curbei
    prognoza_df = istoric.copy()
    prognoza_df['Rata nouă (%)'] = prognoza_df['Rata dobânzii (%)'] + delta
    # Evităm ratele noi <= 0 (ar da împărțiri / puteri nedefinite)
    prognoza_df = prognoza_df[prognoza_df['Rata nouă (%)'] > 0]
    prognoza_df['Cerere estimată ($)'] = (
        prognoza_df['Cerere (volum $)']
        * (prognoza_df['Rata nouă (%)'] / prognoza_df['Rata dobânzii (%)']) ** elast
    )

    fig_prog = go.Figure()

    # Linia plină = datele reale
    fig_prog.add_trace(go.Scatter(
        x=istoric['Rata dobânzii (%)'],
        y=istoric['Cerere (volum $)'],
        mode='lines+markers',
        name='Cerere observată',
        line=dict(color='#1f77b4', width=3),
    ))

    # Linia punctată = prognoza (aceeași curbă, după modificarea dobânzii)
    fig_prog.add_trace(go.Scatter(
        x=prognoza_df['Rata nouă (%)'],
        y=prognoza_df['Cerere estimată ($)'],
        mode='lines+markers',
        name=f'Prognoză (Δ={delta:+.1f} pp, ε={elast})',
        line=dict(color='red', width=3, dash='dot'),
    ))

    fig_prog.update_layout(
        title="Cererea observată și prognoza (linie punctată)",
        xaxis_title="Rata dobânzii (%)",
        yaxis_title="Cerere (volum $)",
    )
    st.plotly_chart(fig_prog, use_container_width=True)


# Rulare directă (opțional): streamlit run cerere_dobanda.py
if __name__ == "__main__":
    st.set_page_config(page_title="Cerere vs. dobândă", layout="wide")
    _df = pd.read_csv("credit_risk_dataset_final_proiect.csv")
    render_page(_df)