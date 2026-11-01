import pandas as pd
import streamlit as st
import os

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