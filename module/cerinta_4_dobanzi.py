import streamlit as st
import plotly.express as px
import pandas as pd

def render_page(df):
    st.title("4. Estimarea cererii în funcție de dobândă")
    st.markdown("Impactul variației ratei dobânzii asupra volumului total de credite solicitate.")
    
    # Eliminăm rândurile fără dobândă setată pentru acuratețea analizei matematice
    df_valid = df.dropna(subset=['loan_int_rate']).copy()
    
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
        # Grafic cu bare pentru a arăta clar scăderea/creșterea cererii
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
        st.subheader("Elasticitatea Cererii (Scatter)")
        # Folosim un eșantion pentru performanță vizuală bună în browser
        df_sample = df_valid.sample(n=min(2000, len(df_valid)), random_state=42)
        
        fig_scatter = px.scatter(
            df_sample, 
            x="loan_int_rate", 
            y="loan_amnt", 
            trendline="ols", # Adaugă o linie de trend automat
            title="Relația Dobândă vs. Sumă Solicitată (Eșantion)",
            labels={"loan_int_rate": "Rata Dobânzii (%)", "loan_amnt": "Suma Solicitată ($)"},
            opacity=0.5
        )
        st.plotly_chart(fig_scatter, use_container_width=True)