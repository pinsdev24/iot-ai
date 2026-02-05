import streamlit as st
import pandas as pd
import time
import os
from pymongo import MongoClient
import certifi

# Configuration de la page
st.set_page_config(
    page_title="Supervision IoT - Temps Réel",
    page_icon="✅",
    layout="wide"
)

st.title("🏭 Tableau de Bord de Supervision IoT")

# --- CONFIGURATION MONGODB ---
MONGO_URI = st.secrets["MONGO_URI"]
DB_NAME = "iot_db"
COLLECTION_NAME = "measures"
COLLECTION_ANOMALIES = "anomalies"

@st.cache_resource
def get_mongo_client():
    return MongoClient(MONGO_URI, tlsCAFile=certifi.where())

def load_data(limit=100):
    try:
        client = get_mongo_client()
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        # Optimisation : On ne récupère que les N derniers documents
        cursor = collection.find().sort("timestamp", -1).limit(limit)
        data = list(cursor)
        
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data)
        if '_id' in df.columns: del df['_id']
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df.sort_values(by="timestamp")
    except Exception as e:
        return pd.DataFrame()

def load_anomalies(limit=10):
    try:
        client = get_mongo_client()
        db = client[DB_NAME]
        collection = db[COLLECTION_ANOMALIES]
        data = list(collection.find().sort("timestamp", -1).limit(limit))
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data)
        if '_id' in df.columns: del df['_id']
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except:
        return pd.DataFrame()

# Sidebar pour les filtres
st.sidebar.header("⚙️ Configuration")
sensor_filter = st.sidebar.selectbox("Sélectionner un Capteur", ["Tous", "C001", "C002", "C003"])
refresh_rate = st.sidebar.slider("Taux de rafraîchissement (s)", 1, 10, 2)

# Onglets pour organiser l'affichage
tab1, tab2 = st.tabs(["📈 Monitoring Temps Réel", "🚨 Historique Anomalies"])

with tab1:
    # On crée les placeholders une seule fois ici
    top_row = st.container()
    kpi1_col, kpi2_col, kpi3_col = top_row.columns(3)
    kpi1 = kpi1_col.empty()
    kpi2 = kpi2_col.empty()
    kpi3 = kpi3_col.empty()
    
    alert_placeholder = st.empty()
    chart_placeholder = st.empty()
    
    st.subheader("Dernières Mesures")
    table_placeholder = st.empty()

with tab2:
    st.subheader("Journal des Anomalies Détectées")
    anomalies_placeholder = st.empty()

# Boucle principale
while True:
    # 1. Chargement des données (Optimisé: Fetch last 200)
    df = load_data(limit=200)
    
    if not df.empty:
        # Filtre Capteur
        if sensor_filter != "Tous":
            df_display = df[df['sensor_id'] == sensor_filter]
        else:
            df_display = df

        if not df_display.empty:
            last_row = df_display.iloc[-1]
            
            # KPIs
            kpi1.metric("🌡️ Température", f"{last_row['temperature']} °C", f"{last_row['temperature'] - 25:.1f} °C vs ref")
            kpi2.metric("💧 Humidité", f"{last_row['humidity']} %")
            
            # Statut
            is_anomaly = last_row.get('anomaly_score', 1) == -1
            status = "⚠️ ANOMALIE" if is_anomaly else "🟢 NORMAL"
            kpi3.metric("Statut Système", status)

            # Alerte Banner
            if is_anomaly:
                alert_placeholder.error(f"🚨 ANOMALIE DÉTECTÉE sur {last_row['sensor_id']} à {last_row['timestamp'].strftime('%H:%M:%S')}")
            else:
                alert_placeholder.info("Système nominal")

            # Graphique (Derniers 50 points du filtre)
            chart_data = df_display.tail(50).set_index("timestamp")
            chart_placeholder.line_chart(chart_data[['temperature', 'humidity']])
            
            # Tableau Monitoring
            latest = df_display.tail(5)[['timestamp', 'sensor_id', 'temperature', 'humidity', 'anomaly_score']]
            latest['Statut'] = latest['anomaly_score'].apply(lambda x: '🔴' if x == -1 else '🟢')
            table_placeholder.dataframe(latest, width='stretch')
    
    # 2. Chargement Anomalies (Tab 2)
    df_anomalies = load_anomalies(limit=20)
    if not df_anomalies.empty:
        anomalies_placeholder.dataframe(
            df_anomalies[['timestamp', 'sensor_id', 'temperature', 'humidity']].style.format({"temperature": "{:.1f}", "humidity": "{:.1f}%"}),
            width='stretch'
        )
    else:
        anomalies_placeholder.info("Aucune anomalie récente.")

    time.sleep(refresh_rate)