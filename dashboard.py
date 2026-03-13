import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Mücke Coupon Dashboard", layout="wide")

st.title("📊 Mücke Aktionsdashboard")

# Dateiupload
uploaded_file = st.sidebar.file_uploader("CSV Datei hochladen", type="csv")

def clean_value_to_float(val):
    """Reinigt Strings wie '8.150.458 €' zu einer Zahl."""
    if pd.isna(val) or val == "": return 0.0
    # Alles entfernen außer Ziffern und das Komma für die Nachkommastellen
    cleaned = re.sub(r'[^\d,]', '', str(val))
    if ',' in cleaned:
        cleaned = cleaned.replace(',', '.')
    try:
        return float(cleaned)
    except:
        return 0.0

if uploaded_file is not None:
    # 1. Datei einlesen (ISO-8859-1 ist bei Excel-CSVs am sichersten)
    try:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, sep=";", skiprows=3, encoding='iso-8859-1')
    except:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, sep=";", skiprows=3, encoding='utf-8')

    # Spalten säubern
    df.columns = [c.strip() for c in df.columns]
    
    # 2. Daten umwandeln
    if 'Umsatz' in df.columns:
        # Wir speichern den Originalwert für das Debugging
        df['Umsatz_Original'] = df['Umsatz'] 
        df['Umsatz'] = df['Umsatz'].apply(clean_value_to_float)
    
    if 'Einlösungen' in df.columns:
        df['Einlösungen'] = df['Einlösungen'].apply(clean_value_to_float)
    
    if 'Aktivierungen' in df.columns:
        df['Aktivierungen'] = df['Aktivierungen'].apply(clean_value_to_float)

    # 3. Filter
    if 'Aktiv (letzte 10 Tage)' in df.columns:
        status_filter = st.sidebar.multiselect("Status:", df['Aktiv (letzte 10 Tage)'].unique(), default=df['Aktiv (letzte 10 Tage)'].unique())
        df = df[df['Aktiv (letzte 10 Tage)'].isin(status_filter)]

    # 4. KPIs anzeigen
    total_umsatz = df['Umsatz'].sum()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Gesamtumsatz (berechnet)", f"{total_umsatz:,.2f} €".replace(',', 'X').replace('.', ',').replace('X', '.'))
    with col2:
        st.metric("Anzahl Zeilen", len(df))

    # 5. DEBUG-BEREICH (Nur sichtbar, wenn Umsatz 0 ist)
    if total_umsatz == 0:
        st.error("⚠️ Der Umsatz wird mit 0 berechnet. Prüfe hier die Rohdaten:")
        st.write(df[['bounty_name', 'Umsatz_Original', 'Umsatz']].head(10))
    else:
        st.success("✅ Daten erfolgreich geladen!")
        # Einfache Tabelle der Top-Aktionen
        st.subheader("Top 10 Aktionen nach Umsatz")
        st.dataframe(df.nlargest(10, 'Umsatz')[['bounty_name', 'Umsatz', 'Einlösungen']])

else:
    st.info("Bitte lade die Datei hoch.")
