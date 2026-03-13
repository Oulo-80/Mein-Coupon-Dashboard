import streamlit as st
import pandas as pd
import plotly.express as px

# Grundkonfiguration der Seite
st.set_page_config(page_title="Mücke Coupon Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #1f77b4; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Mücke Aktionsdashboard")
st.subheader("Couponauswertung ab Q3 2024")
st.markdown("---")

# --- UPLOAD FUNKTION ---
st.sidebar.header("Daten-Upload")
uploaded_file = st.sidebar.file_uploader("Hello again CSV Datei hochladen", type="csv")

def load_and_clean_data(file):
    try:
        file.seek(0)
        df = pd.read_csv(file, sep=";", skiprows=3, decimal=",", encoding='utf-8')
    except Exception:
        file.seek(0)
        df = pd.read_csv(file, sep=";", skiprows=3, decimal=",", encoding='iso-8859-1')
    
    df = df.dropna(axis=1, how='all')
    df.columns = [c.strip() for c in df.columns]
    
    # --- SPEZIELLE REINIGUNG FÜR DEN UMSATZ ---
    def clean_currency(value):
        if pd.isna(value) or value == "" or "DIV/0" in str(value):
            return 0.0
        s = str(value).replace('€', '').strip()
        # Wichtig: Wenn ein Punkt für Tausender UND ein Komma für Cent da ist:
        if '.' in s and ',' in s:
            s = s.replace('.', '') # Tausenderpunkt weg
            s = s.replace(',', '.') # Dezimalkomma zu Punkt
        # Wenn nur ein Punkt da ist (z.B. 8.150.458)
        elif '.' in s and ',' not in s:
            s = s.replace('.', '')
        # Wenn nur ein Komma da ist
        elif ',' in s:
            s = s.replace(',', '.')
        return pd.to_numeric(s, errors='coerce')

    # Spalten bereinigen
    if 'Umsatz' in df.columns:
        df['Umsatz'] = df['Umsatz'].apply(clean_currency)
    
    for col in ['Aktivierungen', 'Einlösungen']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Kennzahlen
    df['Conversion_Rate_%'] = (df['Einlösungen'] / df['Aktivierungen'] * 100).fillna(0).round(2)
    df['Umsatz_pro_Einloesung'] = (df['Umsatz'] / df['Einlösungen']).fillna(0).round(2)
    
    return df

if uploaded_file is not None:
    data = load_and_clean_data(uploaded_file)
    
    # Filter
    status_options = data['Aktiv (letzte 10 Tage)'].unique().tolist()
    selected_status = st.sidebar.multiselect("Status 'Aktiv':", options=status_options, default=status_options)
    filtered_df = data[data['Aktiv (letzte 10 Tage)'].isin(selected_status)]

    # KPIs
    total_rev = filtered_df['Umsatz'].sum()
    total_red = filtered_df['Einlösungen'].sum()
    
    m1, m2, m3 = st.columns(3)
    # Anzeige mit Tausendertrennung für Deutschland
    m1.metric("Gesamtumsatz", f"{total_rev:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
    m2.metric("Einlösungen", f"{int(total_red):,}".replace(",", "."))
    m3.metric("Ø Conversion", f"{filtered_df['Conversion_Rate_%'].mean():.1f} %")

    # Visualisierung
    st.subheader("Top 10 Aktionen nach Umsatz")
    # Wir filtern 0-Werte aus, damit der Chart sauber ist
    chart_data = filtered_df[filtered_df['Umsatz'] > 0].nlargest(10, 'Umsatz')
    if not chart_data.empty:
        fig = px.bar(chart_data, x='Umsatz', y='bounty_name', orientation='h', 
                     color='Umsatz', color_continuous_scale='Greens', text_auto='.3s')
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Daten-Check")
    st.dataframe(filtered_df[['bounty_name', 'Umsatz', 'Einlösungen', 'Conversion_Rate_%']])
else:
    st.info("Bitte lade die Datei hoch.")
