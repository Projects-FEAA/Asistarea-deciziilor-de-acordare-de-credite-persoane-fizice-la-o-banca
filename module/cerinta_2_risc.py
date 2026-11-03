import streamlit as st
import plotly.express as px


def render_page(df):
    st.title("2. Evidențierea clienților rău platnici")
    st.markdown("Ce tipuri de clienți au cea mai mare probabilitate să nu își plătească creditul.")

    # --- CIFRELE PRINCIPALE ---
    total_clienti = len(df)
    rau_platnici = int(df['loan_status'].sum())
    rata_neplata = rau_platnici / total_clienti * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Total clienți", f"{total_clienti:,}")
    col2.metric("Rău platnici", f"{rau_platnici:,}")
    col3.metric("Rata de neplată", f"{rata_neplata:.1f}%")

    # --- ANALIZA PE CATEGORII ---
    st.divider()
    st.subheader("Rata de neplată pe categorii de clienți")

    criterii = {
        "Gradul de risc (A–G)": "loan_grade",
        "Scopul creditului": "loan_intent",
        "Statutul locuinței": "person_home_ownership",
        "Istoric de neplată (Y/N)": "cb_person_default_on_file",
    }
    criteriu_ales = st.selectbox("Analizează rata de neplată după:", list(criterii.keys()))
    coloana = criterii[criteriu_ales]

    analiza = df.groupby(coloana).agg(
        numar_clienti=('loan_status', 'count'),
        rau_platnici=('loan_status', 'sum'),
        rata_neplata=('loan_status', 'mean'),
    ).reset_index()
    analiza['rata_neplata'] = (analiza['rata_neplata'] * 100).round(1)
    analiza = analiza.sort_values('rata_neplata', ascending=False)
    analiza.columns = [criteriu_ales, 'Număr clienți', 'Rău platnici', 'Rata de neplată (%)']

    # --- GRAFICUL ---
    fig = px.bar(
        analiza,
        x='Rata de neplată (%)',
        y=criteriu_ales,
        orientation='h',
        color='Rata de neplată (%)',
        color_continuous_scale='Reds',
    )
    fig.update_traces(texttemplate='%{x:.1f}%', textposition='outside')
    fig.update_yaxes(categoryorder='total ascending', title=None)
    fig.update_xaxes(range=[0, analiza['Rata de neplată (%)'].max() * 1.15])
    fig.update_layout(coloraxis_showscale=False, height=400)
    fig.add_vline(
        x=rata_neplata,
        line_dash='dash',
        annotation_text=f"Media: {rata_neplata:.1f}%",
        annotation_position='top',
    )
    st.plotly_chart(fig)

    # --- TABELUL ---
    with st.expander("Vezi cifrele detaliate"):
        st.dataframe(analiza, hide_index=True)