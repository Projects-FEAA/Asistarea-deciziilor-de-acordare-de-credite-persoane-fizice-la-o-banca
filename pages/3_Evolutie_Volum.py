import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from module.data_loader import load_data
from module.filters import filtre_standard, aplica_filtre, opreste_daca_gol

# Ce putem estima: "nume afișat": (coloana din tabel, formatul numărului, ce scriem după număr)
INDICATORI = {
    "Număr de credite": ("numar", ",.0f", ""),
    "Valoare totală ($)": ("suma", ",.0f", " $"),
}

# Cum grupăm datele: "nume afișat": (codul pandas, cum îi spunem la plural)
GRANULARITATE = {
    "Lună": ("M", "luni"),
    "Trimestru": ("Q", "trimestre"),
}

df = load_data()

st.title("3. Estimarea volumului de credite pentru perioada următoare")
st.markdown("Estimarea volumului de credite ce se vor acorda in perioada urmatoare, in functie de creditele deja acordate si de trendul estimat")

# Luna fiecărui credit, sub formă de text: "2021-01", "2021-02" ...
luna_credit = df['loan_date'].dt.to_period('M').astype(str)
luni = sorted(luna_credit.unique())

# --- FILTRE (primul filtru este perioada, în locul vârstei) ---
alegeri = filtre_standard(
    df, "c3",
    filtru_stanga_sus=lambda: st.select_slider(
        "Istoricul folosit", options=luni, value=(luni[0], luni[-1]), key="c3_period"
    ),
)
perioada = alegeri["extra"]

# --- SETĂRILE PROGNOZEI (2 rânduri a câte 2) ---
with st.container(border=True):
    st.markdown("**Setări prognoză**")

    p1, p2 = st.columns(2)
    with p1:
        indicator = st.selectbox("Ce estimăm:", list(INDICATORI.keys()), key="c3_indicator")
    with p2:
        granularitate = st.selectbox("Grupează pe:", list(GRANULARITATE.keys()), key="c3_gran")

    p3, p4 = st.columns(2)
    with p3:
        orizont = st.slider("Câte perioade estimăm:", 1, 12, 6, key="c3_orizont")
    with p4:
        tip_chart = st.selectbox(
            "Tipul de grafic:",
            ["Line Chart", "Bar Chart"],
            key="c3_chart",
        )

coloana, format_nr, sufix = INDICATORI[indicator]
cod_perioada, plural = GRANULARITATE[granularitate]

# --- APLICAREA FILTRELOR ---
df_f = aplica_filtre(df[luna_credit.between(perioada[0], perioada[1])], alegeri)
opreste_daca_gol(df_f, "Nu există credite care să corespundă filtrelor selectate.")

# --- ISTORICUL: totalul pe fiecare perioadă ---
istoric = df_f.groupby(df_f['loan_date'].dt.to_period(cod_perioada)).agg(
    numar=('loan_amnt', 'count'),
    suma=('loan_amnt', 'sum'),
)

# Ne asigurăm că apar toate perioadele, inclusiv cele fără credite (cu 0)
prima = pd.Period(perioada[0], 'M').asfreq(cod_perioada)
ultima = pd.Period(perioada[1], 'M').asfreq(cod_perioada)
toate_perioadele = pd.period_range(prima, ultima, freq=cod_perioada)
istoric = istoric.reindex(toate_perioadele, fill_value=0)
istoric = istoric.rename_axis('Perioada').reset_index()

if len(istoric) < 3:
    st.warning(f"Pentru a estima trendul sunt necesare cel puțin 3 {plural} de istoric. Mărește perioada.")
    st.stop()

# --- TRENDUL: cea mai potrivită linie dreaptă prin punctele din trecut ---
x = np.arange(len(istoric))              # 0, 1, 2, ... (numărul perioadei)
y = istoric[coloana]                     # valorile reale
panta, start = np.polyfit(x, y, 1)       # linia: valoare = start + panta * x
istoric['Trend'] = start + panta * x

# Cât de mult se abat valorile reale de la linie, în medie
abatere = (y - istoric['Trend']).std()

# --- PROGNOZA: prelungim linia în viitor ---
x_viitor = np.arange(len(istoric), len(istoric) + orizont)
ultima_perioada = istoric['Perioada'].iloc[-1]

prognoza = pd.DataFrame({
    'Perioada': [ultima_perioada + i for i in range(1, orizont + 1)],
    'Estimare': start + panta * x_viitor,
})
prognoza['Estimare'] = prognoza['Estimare'].clip(lower=0)
prognoza['Minim'] = (prognoza['Estimare'] - 2 * abatere).clip(lower=0)
prognoza['Maxim'] = prognoza['Estimare'] + 2 * abatere

# Perioadele ca text, pentru grafic: "2024-01", "2024Q1" ...
istoric['Eticheta'] = istoric['Perioada'].astype(str)
prognoza['Eticheta'] = prognoza['Perioada'].astype(str)

# --- CIFRELE PRINCIPALE ---
media_istorica = y.mean()
estimare_urmatoare = prognoza['Estimare'].iloc[0]
total_estimat = prognoza['Estimare'].sum()
diferenta = (estimare_urmatoare / media_istorica - 1) * 100 if media_istorica > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric(f"Media istorică pe {granularitate.lower()}", f"{media_istorica:{format_nr}}{sufix}")
col2.metric(
    f"Estimare {prognoza['Eticheta'].iloc[0]}",
    f"{estimare_urmatoare:{format_nr}}{sufix}",
    f"{diferenta:+.1f}% față de medie",
)
col3.metric(f"Total estimat ({orizont} {plural})", f"{total_estimat:{format_nr}}{sufix}")

# Interpretarea trendului, în cuvinte
if abs(panta) < 0.005 * media_istorica:
    directie = "aproximativ **constant**"
elif panta > 0:
    directie = "**în creștere**"
else:
    directie = "**în scădere**"
st.caption(
    f"Trendul este {directie}: în medie {panta:+,.1f}{sufix} pe {granularitate.lower()}. "
    f"Zona colorată arată intervalul în care este probabil să se afle valoarea reală."
)

# --- GRAFICUL ---
fig = go.Figure()

# Zona de incertitudine (între Minim și Maxim)
fig.add_trace(go.Scatter(
    x=prognoza['Eticheta'], y=prognoza['Maxim'],
    mode='lines', line=dict(width=0), hoverinfo='skip', showlegend=False,
))
fig.add_trace(go.Scatter(
    x=prognoza['Eticheta'], y=prognoza['Minim'],
    mode='lines', line=dict(width=0), fill='tonexty',
    fillcolor='rgba(230, 126, 34, 0.15)', hoverinfo='skip', name='Interval probabil',
))

hover_istoric = "<b>%{x}</b><br>Real: %{y:" + format_nr + "}" + sufix + "<extra></extra>"
hover_prognoza = (
    "<b>%{x}</b><br>Estimare: %{y:" + format_nr + "}" + sufix
    + "<br>Interval probabil: %{customdata[0]:" + format_nr + "} – %{customdata[1]:" + format_nr + "}" + sufix
    + "<extra></extra>"
)

if tip_chart == "Line Chart":
    fig.add_trace(go.Scatter(
        x=istoric['Eticheta'], y=istoric[coloana], mode='lines+markers',
        name='Istoric (real)', line=dict(color='#1f4e79'), hovertemplate=hover_istoric,
    ))
    fig.add_trace(go.Scatter(
        x=prognoza['Eticheta'], y=prognoza['Estimare'], mode='lines+markers',
        name='Estimare', line=dict(color='#e67e22', dash='dash'),
        customdata=prognoza[['Minim', 'Maxim']].to_numpy(), hovertemplate=hover_prognoza,
    ))
else:
    fig.add_trace(go.Bar(
        x=istoric['Eticheta'], y=istoric[coloana],
        name='Istoric (real)', marker_color='#1f4e79', hovertemplate=hover_istoric,
    ))
    fig.add_trace(go.Bar(
        x=prognoza['Eticheta'], y=prognoza['Estimare'],
        name='Estimare', marker_color='#e67e22',
        customdata=prognoza[['Minim', 'Maxim']].to_numpy(), hovertemplate=hover_prognoza,
    ))

# Linia de trend peste istoric
fig.add_trace(go.Scatter(
    x=istoric['Eticheta'], y=istoric['Trend'], mode='lines',
    name='Trend', line=dict(color='gray', dash='dot'),
    hovertemplate="<b>%{x}</b><br>Trend: %{y:" + format_nr + "}" + sufix + "<extra></extra>",
))

toate_etichetele = list(istoric['Eticheta']) + list(prognoza['Eticheta'])
fig.update_xaxes(type='category', categoryorder='array', categoryarray=toate_etichetele, title=None)
fig.update_yaxes(title=indicator, rangemode='tozero')
fig.update_layout(
    height=420,
    margin=dict(l=0, r=0, t=30, b=0),
    hoverlabel=dict(font_size=14),
    legend=dict(orientation='h', y=1.1),
)
st.plotly_chart(fig)

# --- TABELUL CU ESTIMĂRI ---
with st.expander("Vezi valorile estimate"):
    tabel = prognoza[['Eticheta', 'Estimare', 'Minim', 'Maxim']].copy()
    tabel.columns = ['Perioada', f'Estimare {indicator}', 'Minim probabil', 'Maxim probabil']
    st.dataframe(tabel.round(0), hide_index=True)
