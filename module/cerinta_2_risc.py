import streamlit as st
import plotly.express as px
import pandas as pd
from module.cerinta_1_pondere import INTERVALE_VENIT


def render_page(df):
    st.title("2. Evidențierea clienților rău/platnici")
    st.markdown("Ce tipuri de clienți au cea mai mare probabilitate să nu își plătească creditul.")

    # --- FILTRE (2 rânduri a câte 2) ---
    with st.container(border=True):
        st.markdown("**Filtre**")

        r1c1, r1c2 = st.columns(2)
        with r1c1:
            # 1. Slider pentru vârstă
            min_v, max_v = int(df['person_age'].min()), int(df['person_age'].max())
            interval_varsta = st.slider("Vârstă", min_v, max_v, (min_v, max_v), key="c2_age")
        with r1c2:
            # 2. Selectbox pentru statutul locuinței
            locuinte = ["Toate"] + sorted(df['person_home_ownership'].unique())
            locuinta_aleasa = st.selectbox("Statutul locuinței", locuinte, key="c2_home")

        r2c1, r2c2 = st.columns(2)
        with r2c1:
            # 3. Multiselect pentru intervalul de venit (gol = toate)
            venituri_alese = st.multiselect(
                "Venit anual", list(INTERVALE_VENIT.keys()), key="c2_income", placeholder="Toate"
            )
        with r2c2:
            # 4. Multiselect pentru tipul creditului (gol = toate)
            scopuri_alese = st.multiselect(
                "Tipul creditului", sorted(df['loan_intent'].unique()), key="c2_intent", placeholder="Toate"
            )

    # --- APLICAREA FILTRELOR ---
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

    if df_f.empty:
        st.warning("Nu există clienți care să corespundă filtrelor selectate.")
        return

    # --- CIFRELE PRINCIPALE ---
    rata_generala = df['loan_status'].mean() * 100
    rata_neplata = df_f['loan_status'].mean() * 100
    diferenta = rata_neplata - rata_generala

    if abs(diferenta) >= 0.05:
        text_diferenta = f"{diferenta:+.1f} pp față de medie"
    else:
        text_diferenta = None

    col1, col2, col3 = st.columns(3)
    col1.metric("Clienți", f"{len(df_f):,}")
    col2.metric("Rău platnici", f"{int(df_f['loan_status'].sum()):,}")
    col3.metric("Rata de neplată", f"{rata_neplata:.1f}%", text_diferenta, delta_color="inverse")

    # --- ANALIZA PE CATEGORII ---
    st.divider()

    criterii = {
        "Grad de risc": "loan_grade",
        "Tipul creditului": "loan_intent",
        "Statutul locuinței": "person_home_ownership",
        "Istoric de neplată": "cb_person_default_on_file",
    }

    s1, s2 = st.columns(2)
    with s1:
        criteriu_ales = st.selectbox("Împarte clienții după:", list(criterii.keys()), key="c2_criteriu")
    with s2:
        tip_chart = st.selectbox(
            "Tipul de grafic:",
            ["Grafic cu Bare (Bar Chart)", "Bare 100% (Bun vs. Rău platnic)", "Hartă Proporțională (Treemap)"],
            key="c2_chart",
        )
    coloana = criterii[criteriu_ales]

    analiza = df_f.groupby(coloana).agg(
        numar_clienti=('loan_status', 'count'),
        rau_platnici=('loan_status', 'sum'),
        rata_neplata=('loan_status', 'mean'),
    ).reset_index()
    analiza['rata_neplata'] = (analiza['rata_neplata'] * 100).round(1)
    analiza = analiza.sort_values('rata_neplata', ascending=False)
    analiza.columns = [criteriu_ales, 'Clienți', 'Rău platnici', 'Rata de neplată (%)']

    # Ordinea categoriilor pe grafic: cea mai riscantă sus
    ordine_categorii = list(analiza[criteriu_ales])[::-1]

    # --- GRAFICUL: toate variantele arată riscul fiecărei categorii ---
    if tip_chart == "Grafic cu Bare (Bar Chart)":
        st.caption("Ce procent din clienții fiecărei categorii nu și-au plătit creditul. Linia punctată = media generală.")
        fig = px.bar(
            analiza,
            x='Rata de neplată (%)',
            y=criteriu_ales,
            orientation='h',
            color='Rata de neplată (%)',
            color_continuous_scale='Reds',
            custom_data=['Rău platnici', 'Clienți'],
        )
        fig.update_traces(
            texttemplate='%{x:.1f}%',
            textposition='outside',
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Rata de neplată: %{x:.1f}%<br>"
                "%{customdata[0]:,} rău platnici din %{customdata[1]:,} clienți"
                "<extra></extra>"
            ),
        )
        limita_axa = max(analiza['Rata de neplată (%)'].max(), rata_generala) * 1.15
        fig.update_xaxes(range=[0, limita_axa])
        fig.add_vline(
            x=rata_generala,
            line_dash='dash',
            annotation_text=f"Media: {rata_generala:.1f}%",
            annotation_position='top',
        )

    elif tip_chart == "Bare 100% (Bun vs. Rău platnic)":
        st.caption("Fiecare bară reprezintă toți clienții categoriei (100%). Partea roșie = rău platnici.")
        # Pentru fiecare categorie facem două rânduri: unul pentru rău platnici, unul pentru bun platnici
        rau = analiza[[criteriu_ales]].copy()
        rau['Status'] = 'Rău platnici'
        rau['Procent'] = analiza['Rata de neplată (%)']
        rau['Număr'] = analiza['Rău platnici']

        bun = analiza[[criteriu_ales]].copy()
        bun['Status'] = 'Bun platnici'
        bun['Procent'] = (100 - analiza['Rata de neplată (%)']).round(1)
        bun['Număr'] = analiza['Clienți'] - analiza['Rău platnici']

        date_bare = pd.concat([rau, bun])

        fig = px.bar(
            date_bare,
            x='Procent',
            y=criteriu_ales,
            color='Status',
            orientation='h',
            color_discrete_map={'Rău platnici': '#c0392b', 'Bun platnici': '#d5d8dc'},
            custom_data=['Status', 'Număr'],
        )
        fig.update_traces(
            texttemplate='%{x:.1f}%',
            textposition='inside',
            hovertemplate=(
                "<b>%{y}</b><br>"
                "%{customdata[0]}: %{x:.1f}%<br>"
                "(%{customdata[1]:,} clienți)"
                "<extra></extra>"
            ),
        )
        fig.update_xaxes(range=[0, 100], title='Procent din clienții categoriei (%)')
        fig.update_layout(legend=dict(title=None, orientation='h', y=1.08))

    else:  # Treemap
        st.caption("Mărimea dreptunghiului = numărul de clienți. Culoarea și eticheta = rata de neplată.")
        fig = px.treemap(
            analiza,
            path=[criteriu_ales],
            values='Clienți',
            color='Rata de neplată (%)',
            color_continuous_scale='Reds',
            custom_data=['Rata de neplată (%)', 'Rău platnici'],
        )
        fig.update_traces(
            texttemplate="<b>%{label}</b><br>Risc: %{customdata[0]:.1f}%",
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Rata de neplată: %{customdata[0]:.1f}%<br>"
                "%{customdata[1]:,} rău platnici din %{value:,} clienți"
                "<extra></extra>"
            ),
        )

    # Setări comune pentru toate graficele
    if tip_chart != "Hartă Proporțională (Treemap)":
        fig.update_yaxes(categoryorder='array', categoryarray=ordine_categorii, title=None)
    fig.update_layout(
        coloraxis_showscale=False,
        height=400,
        margin=dict(l=0, r=0, t=30, b=0),
        hoverlabel=dict(font_size=14),
    )
    st.plotly_chart(fig)

    with st.expander("Vezi cifrele detaliate"):
        st.dataframe(analiza, hide_index=True)
    # --- LISTA CLIENȚILOR ---
    st.divider()
    st.subheader("Lista clienților")

    coloane_sortare = [
        "Suma creditului ($)", "Venit anual ($)", "Vârstă", "Dobândă (%)",
        "Rata din venit (%)", "Grad de risc", "ID client",
    ]

    with st.container(border=True):
        l1, l2 = st.columns(2)
        with l1:
            afisare = st.radio(
                "Arată:",
                ["Rău platnici", "Bun platnici", "Toți clienții"],
                horizontal=True,
                key="c2_lista",
            )
        with l2:
            grade_alese = st.multiselect(
                "Grad de risc", sorted(df['loan_grade'].unique()), key="c2_lista_grad", placeholder="Toate"
            )

        l3, l4 = st.columns(2)
        with l3:
            sortare = st.selectbox("Sortează după:", coloane_sortare, key="c2_sortare")
        with l4:
            ordine = st.radio(
                "Ordine:", ["Descrescător", "Crescător"], horizontal=True, key="c2_ordine"
            )

    if afisare == "Rău platnici":
        lista = df_f[df_f['loan_status'] == 1]
    elif afisare == "Bun platnici":
        lista = df_f[df_f['loan_status'] == 0]
    else:
        lista = df_f

    if grade_alese:
        lista = lista[lista['loan_grade'].isin(grade_alese)]

    if lista.empty:
        st.info("Nu există astfel de clienți în segmentul selectat.")
        return

    # Tabel nou, cu denumiri în română, un cod unic pentru fiecare client și un status ușor de recunoscut
    tabel_clienti = pd.DataFrame({
        'ID client': [f"CL-{i + 1:05d}" for i in lista.index],
        'Status': lista['loan_status'].map({1: '🔴 Rău platnic', 0: '🟢 Bun platnic'}),
        'Vârstă': lista['person_age'],
        'Venit anual ($)': lista['person_income'],
        'Locuință': lista['person_home_ownership'],
        'Tipul creditului': lista['loan_intent'],
        'Grad de risc': lista['loan_grade'],
        'Suma creditului ($)': lista['loan_amnt'],
        'Dobândă (%)': lista['loan_int_rate'],
        'Rata din venit (%)': lista['loan_percent_income'] * 100,
        'Istoric de neplată': lista['cb_person_default_on_file'],
    })

    # Sortarea aleasă de utilizator (valorile lipsă ajung la final)
    tabel_clienti = tabel_clienti.sort_values(
        sortare, ascending=(ordine == "Crescător"), na_position='last'
    )

    st.caption(
        f"{len(tabel_clienti):,} clienți, sortați după „{sortare}” ({ordine.lower()}). "
        "Poți sorta și cu click pe numele unei coloane."
    )
    st.dataframe(
        tabel_clienti,
        hide_index=True,
        height=400,
        column_config={
            'Venit anual ($)': st.column_config.NumberColumn(format="localized"),
            'Suma creditului ($)': st.column_config.NumberColumn(format="localized"),
            'Dobândă (%)': st.column_config.NumberColumn(format="%.2f%%"),
            'Rata din venit (%)': st.column_config.NumberColumn(format="%.0f%%"),
        },
    )

    st.download_button(
        "Descarcă lista (CSV)",
        data=tabel_clienti.to_csv(index=False).encode('utf-8-sig'),
        file_name="clienti_segment.csv",
        mime="text/csv",
    )