import streamlit as st
import pandas as pd
import plotly.express as px

# Grundkonfiguration der Seite
st.set_page_config(page_title="Mücke Coupon Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- STYLING (Korrigiert) ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Mücke Aktionsdashboard")
st.subheader("Couponauswertung ab Q3 2024")
st.markdown("---")

# --- UPLOAD FUNKTION (Sidebar) ---
st.sidebar.header("Daten-Upload")
uploaded_file = st.sidebar.file_uploader("Hello again CSV Datei hochladen", type="csv")

def load_and_clean_data(file):
    # Fehlerbehebung für Encoding & Dateizugriff
    try:
        file.seek(0)
        df = pd.read_csv(file, sep=";", skiprows=3, decimal=",", encoding='utf-8')
    except Exception:
        file.seek(0)
        df = pd.read_csv(file, sep=";", skiprows=3, decimal=",", encoding='iso-8859-1')
    
    # Bereinigung der Struktur
    df = df.dropna(axis=1, how='all')
    df.columns = [c.strip() for c in df.columns]
    
    # Zahlenformate bereinigen (Punkte entfernen, Euro-Zeichen weg)
    cols_to_fix = ['Aktivierungen', 'Einlösungen', 'Umsatz']
    for col in cols_to_fix:
        if col in df.columns:
            # Konvertierung zu String, um sicher zu gehen, dann Säuberung
            df[col] = df[col].astype(str).str.replace('.', '', regex=False)
            df[col] = df[col].str.replace('€', '', regex=False)
            df[col] = df[col].str.replace(',', '.', regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # --- ZUSÄTZLICHE KENNZAHLEN ---
    # Berechnung der Conversion Rate (Einlöser vs Aktivierer) [cite: 2, 3]
    df['Conversion_Rate_%'] = (df['Einlösungen'] / df['Aktivierungen'] * 100).round(2)
    # Durchschnittlicher Umsatz pro eingelöstem Coupon [cite: 2]
    df['Umsatz_pro_Einloesung'] = (df['Umsatz'] / df['Einlösungen']).round(2)
    
    return df

if uploaded_file is not None:
    data = load_and_clean_data(uploaded_file)

    # --- FILTER (Sidebar) ---
    st.sidebar.markdown("---")
    st.sidebar.header("Filter & Ansicht")
    
    # Filter für die letzten 10 Tage [cite: 1]
    status_options = data['Aktiv (letzte 10 Tage)'].unique().tolist()
    selected_status = st.sidebar.multiselect("Status 'Aktiv (letzte 10 Tage)':", 
                                            options=status_options, 
                                            default=status_options)
    
    filtered_df = data[data['Aktiv (letzte 10 Tage)'].isin(selected_status)]

    # --- KPI DASHBOARD ---
    total_rev = filtered_df['Umsatz'].sum()
    total_red = filtered_df['Einlösungen'].sum()
    avg_conv = filtered_df['Conversion_Rate_%'].mean()

    m1, m2, m3, m4 = st.columns(4)
    # Anzeige des Gesamtumsatzes (z.B. 8,15 Mio € für die Geschenkkarte) [cite: 2]
    m1.metric("Gesamtumsatz", f"{total_rev:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
    # Summe der Einlösungen (z.B. über 56.000 bei Top-Aktionen) [cite: 2]
    m2.metric("Einlösungen", f"{int(total_red):,}".replace(",", "."))
    m3.metric("Ø Conversion Rate", f"{avg_conv:.1f} %")
    m4.metric("Anzahl Aktionen", len(filtered_df))

    st.markdown("---")

    # --- VISUALISIERUNGEN ---
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Top Umsatz-Bringer")
        # Zeigt die umsatzstärksten Coupons wie z.B. 20% auf gesamten Einkauf [cite: 2]
        fig_rev = px.bar(filtered_df.nlargest(10, 'Umsatz'), 
                         x='Umsatz', y='bounty_name', 
                         orientation='h', 
                         color='Umsatz', 
                         color_continuous_scale='Blues')
        fig_rev.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_rev, use_container_width=True)

    with col_r:
        st.subheader("Einlöse-Qualität")
        # Vergleich von Conversion Rate und Durchschnittsumsatz [cite: 2, 3]
        fig_scat = px.scatter(filtered_df, 
                             x='Conversion_Rate_%', 
                             y='Umsatz_pro_Einloesung', 
                             size='Einlösungen', 
                             hover_name='bounty_name', 
                             color='Aktiv (letzte 10 Tage)')
        st.plotly_chart(fig_scat, use_container_width=True)

    # --- TABELLE ---
    st.subheader("Alle Daten im Überblick")
    st.dataframe(filtered_df.sort_values(by='Umsatz', ascending=False), use_container_width=True)

else:
    st.info("Bitte lade die Datei 'Hello again Couponauswertung.csv' links hoch.")
