import streamlit as st
import pandas as pd
import plotly.express as px
import re

# Seite breit einstellen
st.set_page_config(page_title="Mücke Performance Dashboard", layout="wide")

# Styling für eine moderne Optik
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Mücke Aktionsdashboard")
st.markdown("---")

# Sidebar für Upload und Filter
st.sidebar.header("Navigation & Daten")
uploaded_file = st.sidebar.file_uploader("Hello again CSV hochladen", type="csv")

def clean_value_to_float(val):
    if pd.isna(val) or val == "": return 0.0
    cleaned = re.sub(r'[^\d,]', '', str(val))
    if ',' in cleaned:
        cleaned = cleaned.replace(',', '.')
    try:
        return float(cleaned)
    except:
        return 0.0

if uploaded_file is not None:
    # Daten laden
    try:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, sep=";", skiprows=3, encoding='iso-8859-1')
    except:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, sep=";", skiprows=3, encoding='utf-8')

    # Spalten säubern
    df.columns = [c.strip() for c in df.columns]
    
    # Konvertierung
    for col in ['Umsatz', 'Einlösungen', 'Aktivierungen', 'Dauer in Tagen']:
        if col in df.columns:
            df[col] = df[col].apply(clean_value_to_float)

    # Zusätzliche Berechnungen für die Diagramme
    df['Conversion_Rate_%'] = (df['Einlösungen'] / df['Aktivierungen'] * 100).fillna(0).round(2)
    df['Umsatz_pro_Einloesung'] = (df['Umsatz'] / df['Einlösungen']).fillna(0).round(2)
    df['Umsatz_pro_Tag'] = (df['Umsatz'] / df['Dauer in Tagen']).fillna(0).round(2)

    # Filter
    status_list = df['Aktiv (letzte 10 Tage)'].unique().tolist()
    selected_status = st.sidebar.multiselect("Filter: Status Aktiv", status_list, default=status_list)
    df_filtered = df[df['Aktiv (letzte 10 Tage)'].isin(selected_status)]

    # --- KPI SEKTION ---
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Gesamtumsatz", f"{df_filtered['Umsatz'].sum():,.2f} €".replace(',', 'X').replace('.', ',').replace('X', '.'))
    with kpi2:
        st.metric("Gesamt-Einlösungen", f"{int(df_filtered['Einlösungen'].sum()):,}".replace(',', '.'))
    with kpi3:
        st.metric("Ø Conversion Rate", f"{df_filtered['Conversion_Rate_%'].mean():.1f} %")
    with kpi4:
        st.metric("Ø Warenkorb (Coupon)", f"{df_filtered['Umsatz_pro_Einloesung'].mean():.2f} €".replace('.', ','))

    st.markdown("---")

    # --- DIAGRAMM SEKTION ---
    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        st.subheader("🏆 Top 10 Umsatztreiber")
        # Balkendiagramm für Umsatz
        fig1 = px.bar(df_filtered.nlargest(10, 'Umsatz'), 
                     x='Umsatz', y='bounty_name', 
                     orientation='h', color='Umsatz',
                     color_continuous_scale='Viridis',
                     labels={'bounty_name': 'Aktion'})
        fig1.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig1, use_container_width=True)

    with row1_col2:
        st.subheader("⚡ Effizienz: Umsatz vs. Conversion")
        # Scatter Plot zur Identifikation von "Star"-Aktionen
        fig2 = px.scatter(df_filtered, 
                         x='Conversion_Rate_%', y='Umsatz_pro_Einloesung',
                         size='Umsatz', hover_name='bounty_name',
                         color='Aktiv (letzte 10 Tage)',
                         labels={'Conversion_Rate_%': 'Conversion Rate (%)', 'Umsatz_pro_Einloesung': 'Umsatz pro Einlösung (€)'})
        st.plotly_chart(fig2, use_container_width=True)

    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.subheader("📅 Umsatz-Power (Umsatz pro Tag)")
        # Zeigt, welche Aktionen in kurzer Zeit am meisten "Druck" machen
        fig3 = px.treemap(df_filtered[df_filtered['Umsatz_pro_Tag'] > 0].nlargest(15, 'Umsatz_pro_Tag'), 
                         path=['bounty_name'], values='Umsatz_pro_Tag',
                         color='Umsatz_pro_Tag', color_continuous_scale='RdYlGn')
        st.plotly_chart(fig3, use_container_width=True)

    with row2_col2:
        st.subheader("📊 Einlösungen nach Status")
        # Anteil aktiver vs. inaktiver Aktionen
        fig4 = px.pie(df_filtered, values='Einlösungen', names='Aktiv (letzte 10 Tage)', 
                     hole=0.4, title="Verteilung der Einlösungen",
                     color_discrete_sequence=px.colors.sequential.RdBu)
    
        st.plotly_chart(fig4, use_container_width=True)

    # Tabelle am Ende
    st.subheader("Detaillierte Auswertung")
    st.dataframe(df_filtered[['bounty_name', 'Aktiv (letzte 10 Tage)', 'Umsatz', 'Einlösungen', 'Conversion_Rate_%', 'Umsatz_pro_Tag']], use_container_width=True)

else:
    st.info("Bitte lade die CSV-Datei hoch, um die Analyse zu starten.")
