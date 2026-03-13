import streamlit as st
import pandas as pd
import plotly.express as px

# Seite konfigurieren
st.set_page_config(page_title="Coupon Dashboard", layout="wide")

st.title("🚀 Coupon-Aktionsdashboard (Lokal & Kostenlos)")

# UPLOAD FUNKTION
uploaded_file = st.file_uploader("CSV Datei hochladen (Hello again Export)", type="csv")

if uploaded_file is not None:
    # Daten einlesen (skiprows=3 überspringt die Header-Info deiner Datei)
    df = pd.read_csv(uploaded_file, sep=";", skiprows=3, decimal=",")
    
    # Bereinigung: Leere Spalten entfernen und Namen säubern
    df = df.dropna(axis=1, how='all')
    df.columns = [c.strip() for c in df.columns]
    
    # Zahlenformate korrigieren (Punkte entfernen, Komma zu Punkt für Berechnungen)
    for col in ['Aktivierungen', 'Einlösungen', 'Umsatz']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace('€', '', regex=False).str.replace(',', '.', regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # --- ZUSÄTZLICHE INSIGHTS (Die Kennzahlen-Erweiterung) ---
    df['Conversion_Rate_%'] = (df['Einlösungen'] / df['Aktivierungen'] * 100).round(2)
    df['Umsatz_pro_Einloesung'] = (df['Umsatz'] / df['Einlösungen']).round(2)

    # --- FILTER ---
    st.sidebar.header("Filter-Optionen")
    # Filter für die letzten 10 Tage
    show_active_only = st.sidebar.checkbox("Nur Aktionen aktiv in den letzten 10 Tagen", value=False)
    
    if show_active_only:
        filtered_df = df[df['Aktiv (letzte 10 Tage)'] == 'JA']
    else:
        filtered_df = df

    # --- DASHBOARD LAYOUT ---
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Gesamtumsatz", f"{filtered_df['Umsatz'].sum():,.2f} €")
    kpi2.metric("Ø Conversion Rate", f"{filtered_df['Conversion_Rate_%'].mean():.1f} %")
    kpi3.metric("Aktivierungen gesamt", f"{int(filtered_df['Aktivierungen'].sum()):,}")

    # Grafik 1: Top Aktionen nach Umsatz
    st.subheader("Umsatzstärkste Aktionen")
    fig = px.bar(filtered_df.nlargest(10, 'Umsatz'), x='Umsatz', y='bounty_name', 
                 orientation='h', color='Conversion_Rate_%', 
                 labels={'bounty_name': 'Aktion', 'Conversion_Rate_%': 'Conversion %'})
    st.plotly_chart(fig, use_container_width=True)

    # Grafik 2: Effizienz-Check (Zusatz-Insight)
    st.subheader("Insight: Welche Aktionen lohnen sich? (Umsatz vs. Conversion)")
    fig2 = px.scatter(filtered_df, x='Conversion_Rate_%', y='Umsatz_pro_Einloesung', 
                      size='Einlösungen', hover_name='bounty_name', color='Aktiv (letzte 10 Tage)')
    st.plotly_chart(fig2, use_container_width=True)

    # Tabelle
    st.subheader("Rohdaten Übersicht")
    st.dataframe(filtered_df)

else:
    st.info("Bitte lade die Datei 'Hello again Couponauswertung.csv' oben hoch.")