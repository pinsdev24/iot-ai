import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime

# --- CONFIGURATION MQTT ---
# A remplacer par tes identifiants HiveMQ
BROKER = "HIVEMQ_BROKER_URL"  # Ton Host
PORT = 8883                                # Port TLS standard
USERNAME = "HIVEMQ_USERNAME"                  # Ton utilisateur
PASSWORD = "HIVEMQ_PASSWORD"                  # Ton mot de passe

TOPIC = "iotsystem/capteurs/temperature"   # Le sujet défini dans l'étape 1 [cite: 27]

# --- FONCTION DE CONNEXION ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connecté au Broker MQTT !")
    else:
        print(f"❌ Échec de connexion, code retour : {rc}")

# Initialisation du client MQTT
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD) # Authentification [cite: 47]
client.tls_set()                           # Sécurisation TLS obligatoire pour HiveMQ [cite: 47]
client.on_connect = on_connect

# Connexion
print("Connexion au Cloud en cours...")
try:
    client.connect(BROKER, PORT, 60)
except Exception as e:
    print(f"Erreur de connexion : {e}")
    exit()

client.loop_start() # Démarre la boucle de gestion réseau en arrière-plan

# --- BOUCLE DE SIMULATION ---
try:
    while True:
        # 1. Génération de données normales (autour de 25°C et 40% humidité)
        temp = 25 + random.gauss(0, 0.8)  
        hum = 40 + random.gauss(0, 2)
        
        # 2. Injection d'ANOMALIES (5% de chance) [cite: 49, 52]
        # Cela permet de tester si ton IA détectera bien les problèmes plus tard
        if random.random() < 0.05:
            print("⚠️ GÉNÉRATION D'UNE ANOMALIE !")
            # On ajoute artificiellement une valeur extrême (ex: +12°C ou -10°C)
            temp += random.choice([-10, 12]) 

        # 3. Création du message JSON (Payload) [cite: 52]
        payload = {
            "sensor_id": random.choice(["C001", "C002", "C003"]), # Simule plusieurs capteurs [cite: 49]
            "timestamp": datetime.utcnow().isoformat() + "Z",     # Format ISO 8601
            "temperature": round(temp, 2),
            "humidity": round(hum, 1)
        }

        # 4. Envoi vers le Cloud
        client.publish(TOPIC, json.dumps(payload))
        
        print(f"📡 Données envoyées : {payload}")
        
        # Attente de 3 secondes avant le prochain envoi [cite: 57]
        time.sleep(3)

except KeyboardInterrupt:
    print("Arrêt du simulateur.")
    client.loop_stop()
    client.disconnect()