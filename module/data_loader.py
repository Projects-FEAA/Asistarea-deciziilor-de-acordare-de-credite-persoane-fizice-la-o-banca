import os

import pandas as pd
import streamlit as st

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


def limite_intervale(intervale):
    """Transformă un dicționar de intervale în lista de limite pentru pd.cut."""
    return [0] + [maxim for _, maxim in intervale.values()]


@st.cache_data
def load_data():
    # Construim calea relativă către fișier pentru a rula corect pe orice mașină
    file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'credit_risk_dataset_final_proiect.csv')
    
    # Citim dataset-ul
    df = pd.read_csv(file_path)
    
    # Transformăm coloana sintetică în format datetime pentru a facilita 
    # graficele de trend și filtrările pe ani/luni din celelalte module
    df['loan_date'] = pd.to_datetime(df['loan_date'])
    
    # Opțional: putem redenumi valorile din loan_status pentru a arăta mai bine în grid și grafice
    df['loan_status_label'] = df['loan_status'].map({0: 'Bun Platnic', 1: 'Rău Platnic'})
    
    return df
