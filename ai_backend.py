import paho.mqtt.client as mqtt
import json
import pandas as pd
from sklearn.ensemble import IsolationForest
import matplotlib.pyplot as plt
from datetime import datetime
import os

# --- CONFIGURATION ---
BROKER = "5b5ee3d0ea76408790ffb14d7edd54e0.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "hivemq.pins2026"
PASSWORD = "._js@vi8ADUSZDP"
TOPIC = "iotsystem/capteurs/temperature"

DATA_FILE = "historique_iot.csv"
IMG_FILE = "anomalies_detectees.png"

# Buffer pour stocker les données en mémoire vive avant analyse
data_buffer = []

# --- FONCTION D'ANALYSE IA ---
def analyser_donnees():
    if len(data_buffer) < 10:
        return # Pas assez de données pour analyser

    # 1. Conversion en DataFrame
    df = pd.DataFrame(data_buffer)
    
    # 2. Modèle Isolation Forest
    # Contamination = 0.05 signifie qu'on s'attend à environ 5% d'anomalies
    model = IsolationForest(contamination=0.05, random_state=42)
    
    # On entraine le modèle sur la colonne 'temperature'
    # Il faut reshape car sklearn attend un tableau 2D
    X = df[['temperature']]
    df['anomaly_score'] = model.fit_predict(X)
    
    # -1 indique une anomalie, 1 indique normal
    anomalies = df[df['anomaly_score'] == -1]
    
    if not anomalies.empty:
        print(f"⚠️ ANOMALIES DÉTECTÉES : {len(anomalies)}")
        print(anomalies[['timestamp', 'temperature']])

    # 3. Sauvegarde CSV (Mode 'w' pour écraser et garder l'exemple propre, ou 'a' pour ajouter)
    df.to_csv(DATA_FILE, index=False)
    print(f"💾 Données sauvegardées dans {DATA_FILE}")

    # 4. Génération du Graphique (Livrable)
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df['temperature'], label='Température', color='blue')
    
    # On dessine les points rouges là où il y a des anomalies
    if not anomalies.empty:
        plt.scatter(anomalies.index, anomalies['temperature'], color='red', label='Anomalie', zorder=5)

    plt.title("Détection d'anomalies (Isolation Forest)")
    plt.xlabel("Index des mesures")
    plt.ylabel("Température (°C)")
    plt.legend()
    plt.savefig(IMG_FILE)
    plt.close() # Ferme la figure pour libérer la mémoire

# --- GESTION MQTT ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Backend IA Connecté !")
        # C'est la ligne qui manquait : on s'abonne au sujet
        client.subscribe(TOPIC) 
        print(f"📡 Abonné au topic : {TOPIC}")
    else:
        print(f"❌ Erreur connexion code: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        # On ajoute à notre liste mémoire
        data_buffer.append(payload)
        
        print(f"📥 Reçu: {payload['temperature']}°C (Total: {len(data_buffer)} mesures)")

        # On lance l'analyse tous les 10 messages reçus
        if len(data_buffer) % 10 == 0:
            analyser_donnees()

    except Exception as e:
        print(f"Erreur de lecture : {e}")

# Initialisation MQTT
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set()

# On lie les fonctions
client.on_connect = on_connect
client.on_message = on_message

print("🎧 Backend IA en écoute...")
client.connect(BROKER, PORT, 60)
client.loop_forever()