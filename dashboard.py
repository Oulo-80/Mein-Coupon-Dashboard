import streamlit as st
import pandas as pd
import plotly.express as px

# Seite konfigurieren
st.set_page_config(page_title="Mücke Coupon Dashboard", layout="wide")

st.title("📊 Aktionsdashboard: Couponauswertung")
st.markdown("---")

# UPLOAD FUNKTION
uploaded_file = st.sidebar.file_uploader("Hello again CSV hochladen", type="csv")

def load_and_clean_data(file):
    # Fehlerbehebung für den UnicodeDecodeError: Wir versuchen erst UTF-8, dann ISO-8859-1
    try:
        df = pd.read_csv(file, sep=";", skiprows=3, decimal=",", encoding='utf-8')
    except:
        df = pd.read_csv(file, sep=";", skiprows=3, decimal=",", encoding='iso-8859-1')
    
    # Leere Spalten entfernen
    df = df.dropna(axis=1, how='all')
    df.columns = [c.strip() for c in df.columns]
    
    # Zahlenformate bereinigen (Tausenderpunkte und €-Zeichen entfernen)
    cols_to_fix = ['Aktivierungen', 'Einlösungen', 'Umsatz']
    for col in cols_to_fix:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('.', '', regex=False)
            df[col] = df[col].str.replace('€', '', regex=False)
            df[col] = df[col].str.replace(',', '.', regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # --- ZUSÄTZLICHE KENNZAHLEN (Insights) ---
    # Conversion Rate: Wie effizient ist der Coupon?
    df['Conversion_Rate_%'] = (df['Einlösungen'] / df['Aktivierungen'] * 100).round(2)
    # Ø Umsatz: Wie viel gibt ein Kunde pro Einlösung aus?
    df['Umsatz_pro_Einloesung'] = (df['Umsatz'] / df['Einlösungen']).round(2)
    
    return df

if uploaded_file is not None:
    data = load_and_clean_data(uploaded_file)

    # --- FILTER ---
    st.sidebar.header("Filter")
    only_active = st.sidebar.checkbox("Nur aktiv (letzte 10 Tage)", value=False)
    
    # Filter-Logik basierend auf deiner Spalte [cite: 1, 3]
    if only_active:
        filtered_df = data[data['Aktiv (letzte 10 Tage)'] == 'JA']
    else:
        filtered_df = data

    # --- KPI DASHBOARD ---
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Gesamtumsatz", f"{filtered_df['Umsatz'].sum():,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
    with c2:
        st.metric("Einlösungen", f"{int(filtered_df['Einlösungen'].sum()):,}".replace(",", "."))
    with c3:
        st.metric("Ø Conversion", f"{filtered_df['Conversion_Rate_%'].mean():.1f} %")
    with c4:
        # Errechnet die profitabelste aktive Aktion [cite: 2, 4]
        top_akt = filtered_df.nlargest(1, 'Umsatz')['bounty_name'].values[0] if not filtered_df.empty else "-"
        st.metric("Top Aktion", top_akt)

    st.markdown("---")

    # --- VISUALS ---
    col_l, col_r = st.columns(2)
    
    with col_l:
        st.subheader("Top 10 Umsatzbringer")
        fig_rev = px.bar(filtered_df.nlargest(10, 'Umsatz'), x='Umsatz', y='bounty_name', 
                         orientation='h', color='Umsatz', color_continuous_scale='Viridis')
        st.plotly_chart(fig_rev, use_container_width=True)

    with col_r:
        st.subheader("Effizienz-Analyse")
        # Scatter Plot zeigt das Verhältnis von Conversion zu Warenkorbgröße
        fig_scat = px.scatter(filtered_df, x='Conversion_Rate_%', y='Umsatz_pro_Einloesung', 
                             size='Einlösungen', hover_name='bounty_name', color='Aktiv (letzte 10 Tage)')
        st.plotly_chart(fig_scat, use_container_width=True)

    # --- TABELLE ---
    st.subheader("Detailübersicht")
    st.dataframe(filtered_df, use_container_width=True)

else:
    st.info("Bitte lade die Datei hoch, um das Dashboard zu aktivieren.")
