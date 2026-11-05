import streamlit as st

st.set_page_config(page_title="Sistem Asistare Decizii Credite", layout="wide")

# Titlu deasupra navigării din bara laterală
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"]::before {
            content: "Sistem Asistare Decizii Credite - Navigare";
            display: block;
            margin: 1rem 1rem 0.5rem 1rem;
            font-size: 1.4rem;
            font-weight: 700;
            line-height: 1.3;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

pagina = st.navigation([
    st.Page("pages/0_Baza_de_Date.py", title="Baza de Date", default=True),
    st.Page("pages/1_Ponderea_Creditelor.py", title="1. Ponderea Creditelor"),
    st.Page("pages/2_Analiza_Rau_Platnici.py", title="2. Analiză Rău-Platnici"),
    st.Page("pages/3_Evolutie_Volum.py", title="3. Evoluție Volum"),
    st.Page("pages/4_Impact_Dobanzi.py", title="4. Impact Dobânzi"),
])
pagina.run()