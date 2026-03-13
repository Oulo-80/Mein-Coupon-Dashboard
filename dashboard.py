import streamlit as st
import pandas as pd
import plotly.express as px

# Grundkonfiguration der Seite
st.set_page_config(page_title="Mücke Coupon Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- STYLING ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_import_headers=True)

st.title("📊 Mücke Aktionsdashboard")
st.subheader("Couponauswertung ab Q3 2024")
st.markdown("---")

# --- UPLOAD FUNKTION (Sidebar) ---
st.sidebar.header("Daten-Upload")
uploaded_file = st.sidebar.file_uploader("Hello again CSV Datei hochladen", type="csv")

def load_and_clean_data(file):
    # Fehlerbehebung für UnicodeDecodeError & EmptyDataError
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
            df[col] = df[col].astype(str).str.replace('.', '', regex=False)
            df[col] = df[col].str.replace('€', '', regex=False)
            df[col] = df[col].str.replace(',', '.', regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # --- ZUSÄTZLICHE KENNZAHLEN (Insights) ---
    # Wie viele Aktivierer lösen wirklich ein?
    df['Conversion_Rate_%'] = (df['Einlösungen'] / df['Aktivierungen'] * 100).round(2)
    # Welchen Wert hat ein eingelöster Coupon im Schnitt?
    df['Umsatz_pro_Einloesung'] = (df['Umsatz'] / df['Einlösungen']).round(2)
    # Wie viel Umsatz generiert die Aktion pro Tag Laufzeit?
    df['Umsatz_pro_Tag'] = (df['Umsatz'] / df['Dauer in Tagen']).round(2)
    
    return df

if uploaded_file is not None:
    data = load_and_clean_data(uploaded_file)

    # --- FILTER (Sidebar) ---
    st.sidebar.markdown("---")
    st.sidebar.header("Filter & Ansicht")
    
    # Filter: Aktiv in den letzten 10 Tagen
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
    m1.metric("Gesamtumsatz", f"{total_rev:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
    m2.metric("Einlösungen", f"{int(total_red):,}".replace(",", "."))
    m3.metric("Ø Conversion Rate", f"{avg_conv:.1f} %")
    m4.metric("Aktive Aktionen", len(filtered_df[filtered_df['Aktiv (letzte 10 Tage)'] == 'JA']))

    st.markdown("---")

    # --- VISUALISIERUNGEN ---
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Top 10 Umsatz-Aktionen")
        # Horizontaler Balkenchart für die umsatzstärksten Aktionen
        fig_rev = px.bar(filtered_df.nlargest(10, 'Umsatz'), 
                         x='Umsatz', y='bounty_name', 
                         orientation='h', 
                         color='Umsatz', 
                         color_continuous_scale='GnBu',
                         text_auto='.2s')
        fig_rev.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
        st.plotly_chart(fig_rev, use_container_width=True)

    with col_r:
        st.subheader("Effizienz: Conversion vs. Warenkorb")
        # Scatter Plot zur Analyse der Qualität
        fig_scat = px.scatter(filtered_df, 
                             x='Conversion_Rate_%', 
                             y='Umsatz_pro_Einloesung', 
                             size='Einlösungen', 
                             hover_name='bounty_name', 
                             color='Aktiv (letzte 10 Tage)',
                             labels={'Conversion_Rate_%': 'Einlöse-Quote (%)', 'Umsatz_pro_Einloesung': 'Ø Umsatz pro Kunde'})
        st.plotly_chart(fig_scat, use_container_width=True)

    # --- ZUSATZ-INSIGHT: BESTE REICHWEITE VS. BESTER UMSATZ ---
    st.markdown("### 💡 Strategische Insights")
    i1, i2 = st.columns(2)
    with i1:
        best_conv = filtered_df.nlargest(1, 'Conversion_Rate_%')
        st.info(f"**Höchste Relevanz:** Die Aktion '{best_conv['bounty_name'].values[0]}' hat eine Conversion von {best_conv['Conversion_Rate_%'].values[0]}%.")
    with i2:
        best_val = filtered_df.nlargest(1, 'Umsatz_pro_Einloesung')
        st.success(f"**Höchster Warenkorb:** Bei '{best_val['bounty_name'].values[0]}' geben Kunden im Schnitt {best_val['Umsatz_pro_Einloesung'].values[0]} € aus.")

    # --- TABELLE ---
    st.subheader("Vollständige Aktionsdaten")
    st.dataframe(filtered_df.sort_values(by='Umsatz', ascending=False), use_container_width=True)

else:
    # Willkommens-Bildschirm
    st.info("👋 Willkommen! Bitte lade die 'Hello again Couponauswertung.csv' in der linken Sidebar hoch.")
    st.image("https://img.icons8.com/clouds/500/000000/data-configuration.png", width=200)
    st.markdown("""
    **Anleitung:**
    1. Exportiere deine Daten aus dem Hello again Portal.
    2. Klicke links auf 'Browse files'.
    3. Analysiere deine Kampagnen-Performance live.
    """)
