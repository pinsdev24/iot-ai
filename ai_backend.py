import paho.mqtt.client as mqtt
import json
import pandas as pd
from sklearn.ensemble import IsolationForest
import matplotlib.pyplot as plt
from datetime import datetime
import os
from pymongo import MongoClient
import certifi

# --- CONFIGURATION ---
BROKER = "HIVEMQ_BROKER_URL"
PORT = 8883
USERNAME = "HIVEMQ_USERNAME"
PASSWORD = "HIVEMQ_PASSWORD"
TOPIC = "iotsystem/capteurs/temperature"

# --- MONGODB CONFIGURATION ---
MONGO_URI = "YOUR_MONGO_URI"
DB_NAME = "iot_db"
COLLECTION_NAME = "measures"
COLLECTION_ANOMALIES = "anomalies"

IMG_FILE = "anomalies_detectees.png"

# Connexion MongoDB
try:
    mongo_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = mongo_client[DB_NAME]
    collection = db[COLLECTION_NAME]
    anomalies_collection = db[COLLECTION_ANOMALIES]
    print("✅ Connecté à MongoDB Atlas !")
except Exception as e:
    print(f"❌ Erreur connexion MongoDB : {e}")
    collection = None
    anomalies_collection = None

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

        # Sauvegarde des anomalies dans la collection dédiée
        if anomalies_collection is not None:
            try:
                # On convertit en liste de dictionnaires
                anomalies_records = anomalies.to_dict(orient='records')
                # On insère dans la collection anomalies
                anomalies_collection.insert_many(anomalies_records)
                print(f"🚨 {len(anomalies_records)} anomalies archivées dans la collection '{COLLECTION_ANOMALIES}'")
            except Exception as e:
                print(f"❌ Erreur sauvegarde anomalies : {e}")

    # 3. Sauvegarde MongoDB (On remplace les données pour cet exercice simple)
    if collection is not None:
        try:
            # On vide tout et on remet tout le buffer (comme un fichier CSV)
            collection.delete_many({})
            
            # On convertit le DataFrame en dictionnaire pour MongoDB
            records = df.to_dict(orient='records')
            collection.insert_many(records)
            print(f"💾 {len(records)} mesures sauvegardées dans MongoDB")
        except Exception as e:
            print(f"❌ Erreur écriture MongoDB : {e}")

    # Retirer les commentaires pour générer le graphique
    # 4. Génération du Graphique (Livrable)
    # plt.figure(figsize=(10, 6))
    # plt.plot(df.index, df['temperature'], label='Température', color='blue')
    
    # # On dessine les points rouges là où il y a des anomalies
    # if not anomalies.empty:
    #     plt.scatter(anomalies.index, anomalies['temperature'], color='red', label='Anomalie', zorder=5)

    # plt.title("Détection d'anomalies (Isolation Forest)")
    # plt.xlabel("Index des mesures")
    # plt.ylabel("Température (°C)")
    # plt.legend()
    # plt.savefig(IMG_FILE)
    # plt.close() # Ferme la figure pour libérer la mémoire

# --- GESTION MQTT ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Backend IA Connecté !")
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