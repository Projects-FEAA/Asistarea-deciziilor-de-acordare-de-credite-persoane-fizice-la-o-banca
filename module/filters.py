"""Filtrele comune tuturor paginilor: chenarul „Filtre”, aplicarea lor pe DataFrame
și oprirea paginii când nu rămâne nicio înregistrare."""
import pandas as pd
import streamlit as st

from module.data_loader import INTERVALE_VENIT, TIPURI_CREDIT


def filtre_standard(df, prefix, filtru_stanga_sus=None):
    """Desenează chenarul „Filtre” (2 rânduri a câte 2) și returnează alegerile.

    prefix            -> prefixul cheilor widget-urilor ("c1", "c2"...), ca paginile
                         să nu își încurce starea între ele.
    filtru_stanga_sus -> opțional: o funcție care desenează un widget propriu în locul
                         sliderului de vârstă (ex. perioada din pagina 3). Valoarea
                         returnată de ea ajunge în alegeri["extra"].
    """
    varsta = None
    extra = None

    with st.container(border=True):
        st.markdown("**Filtre**")

        r1c1, r1c2 = st.columns(2)
        with r1c1:
            if filtru_stanga_sus is None:
                min_v, max_v = int(df['person_age'].min()), int(df['person_age'].max())
                varsta = st.slider("Vârstă", min_v, max_v, (min_v, max_v), key=f"{prefix}_age")
            else:
                extra = filtru_stanga_sus()
        with r1c2:
            locuinte = ["Toate"] + sorted(df['person_home_ownership'].unique())
            locuinta = st.selectbox("Statutul locuinței", locuinte, key=f"{prefix}_home")

        r2c1, r2c2 = st.columns(2)
        with r2c1:
            # gol = toate intervalele
            venituri = st.multiselect(
                "Venit anual", list(INTERVALE_VENIT.keys()), key=f"{prefix}_income", placeholder="Toate"
            )
        with r2c2:
            # gol = toate tipurile
            scopuri = st.multiselect(
                "Tipul creditului",
                sorted(df['loan_intent'].dropna().unique(), key=lambda x: TIPURI_CREDIT.get(x, x)),
                format_func=lambda x: TIPURI_CREDIT.get(x, x),
                key=f"{prefix}_intent",
                placeholder="Toate",
            )

    return {
        "varsta": varsta,
        "locuinta": locuinta,
        "venituri": venituri,
        "scopuri": scopuri,
        "extra": extra,
    }


def aplica_filtre(df, alegeri):
    """Aplică pe DataFrame alegerile întoarse de filtre_standard()."""
    df_f = df

    if alegeri["varsta"] is not None:
        df_f = df_f[df_f['person_age'].between(alegeri["varsta"][0], alegeri["varsta"][1])]

    if alegeri["locuinta"] != "Toate":
        df_f = df_f[df_f['person_home_ownership'] == alegeri["locuinta"]]

    if alegeri["scopuri"]:
        df_f = df_f[df_f['loan_intent'].isin(alegeri["scopuri"])]

    if alegeri["venituri"]:
        masca_venit = pd.Series(False, index=df_f.index)
        for eticheta in alegeri["venituri"]:
            v_min, v_max = INTERVALE_VENIT[eticheta]
            masca_venit |= (df_f['person_income'] >= v_min) & (df_f['person_income'] < v_max)
        df_f = df_f[masca_venit]

    return df_f


def opreste_daca_gol(df_f, mesaj):
    """Dacă nu a rămas niciun rând după filtrare, arată avertismentul și oprește pagina."""
    if df_f.empty:
        st.warning(mesaj)
        st.stop()
