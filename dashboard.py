import streamlit as st
import pandas as pd
import time
import os

# Configuration de la page
st.set_page_config(
    page_title="Supervision IoT - Temps Réel",
    page_icon="✅",
    layout="wide"
)

st.title("🏭 Tableau de Bord de Supervision IoT")

# Emplacements pour les éléments dynamiques
kpi1_col, kpi2_col, kpi3_col = st.columns(3)
kpi1 = kpi1_col.empty()
kpi2 = kpi2_col.empty()
kpi3 = kpi3_col.empty()
alert_placeholder = st.empty()
chart_placeholder = st.empty()
table_placeholder = st.empty()

DATA_FILE = "historique_iot.csv"

def load_data():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame()
    # On charge le CSV
    df = pd.read_csv(DATA_FILE)
    # On s'assure que le timestamp est bien compris comme une date
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

# Boucle d'auto-actualisation (Simule le temps réel)
while True:
    df = load_data()
    
    if not df.empty:
        # On prend la dernière mesure reçue
        last_row = df.iloc[-1]
        
        # --- 1. AFFICHAGE DES KPIs (Indicateurs) ---
        kpi1.metric(
            label="🌡️ Température",
            value=f"{last_row['temperature']} °C",
            delta=f"{last_row['temperature'] - 25:.1f} °C vs ref"
        )
        
        kpi2.metric(
            label="💧 Humidité",
            value=f"{last_row['humidity']} %"
        )
        
        # --- 2. GESTION DES ALERTES [Critère examen] ---
        # Si le score d'anomalie est -1 (calculé par ton IA)
        if 'anomaly_score' in last_row and last_row['anomaly_score'] == -1:
            alert_placeholder.error(f"🚨 ALERTE CRITIQUE : Anomalie détectée sur le capteur {last_row['sensor_id']} !")
            status = "ANOMALIE"
        else:
            alert_placeholder.success("✅ Système stable. Aucune anomalie détectée.")
            status = "NORMAL"
            
        kpi3.metric(label="Statut Système", value=status)

        # --- 3. GRAPHIQUES [Critère examen] ---
        # On affiche les 50 derniers points pour que le graphique reste lisible
        chart_data = df.tail(50).set_index("timestamp")
        chart_placeholder.line_chart(chart_data[['temperature', 'humidity']])

        # --- 4. TABLEAU DE DONNÉES [Critère examen] ---
        # On affiche les 10 dernières lignes, triées par date (plus récent en haut)
        latest_data = df.tail(10)[['timestamp', 'sensor_id', 'temperature', 'humidity', 'anomaly_score']]
        # On ajoute une colonne lisible pour l'humain
        latest_data['Statut'] = latest_data['anomaly_score'].apply(lambda x: '🔴 ANOMALIE' if x == -1 else '🟢 OK')
        
        table_placeholder.dataframe(latest_data.style.map(
            lambda v: 'color: red; font-weight: bold;' if v == '🔴 ANOMALIE' else '', 
            subset=['Statut']
        ), width='stretch')

    else:
        alert_placeholder.warning("⏳ En attente de données du Backend IA...")

    # Pause de 2 secondes avant de recharger le fichier (Actualisation auto)
    time.sleep(2)