# 🏭 5BIM IoT Supervision Project

Un système complet de supervision IoT intégrant simulation de capteurs, détection d'anomalies par IA et tableau de bord temps réel.

## 🚀 Architecture du Projet

Le projet est divisé en trois modules interconnectés :

1.  **📡 Simulateur IoT (`iot_simulator.py`)** :
    *   Simule des capteurs (C001, C002, C003).
    *   Génère des données de température et humidité avec du bruit aléatoire.
    *   Injecte des anomalies artificielles (pics/chutes de température) aléatoirement.
    *   Envoie les données via **MQTT** (protocole sécurisé TLS sur HiveMQ).

2.  **🧠 Backend IA (`ai_backend.py`)** :
    *   Écoute le flux MQTT en temps réel.
    *   Utilise un modèle **Isolation Forest** (Scikit-Learn) pour détecter les anomalies.
    *   Stocke les mesures et les anomalies détectées dans **MongoDB Atlas**.
    *   Génère un graphique statique (`anomalies_detectees.png`) pour analyse.

3.  **📊 Dashboard de Supervision (`dashboard.py`)** :
    *   Application web construite avec **Streamlit**.
    *   Affiche les KPI temps réel (Température, Humidité, Statut).
    *   Trace des graphiques d'évolution.
    *   Affiche un journal dédié aux anomalies détectées.
    *   Permet le filtrage par capteur et la configuration du rafraîchissement.

## 🛠️ Technologies Utilisées

*   **Langage** : Python 3.11+
*   **Protocols** : MQTT (Paho-MQTT), TLS
*   **Base de Données** : MongoDB Atlas (Cloud NoSQL)
*   **Data Science / IA** : Pandas, Scikit-Learn (Isolation Forest), Matplotlib
*   **Frontend** : Streamlit

## ⚙️ Installation

Prérequis : Avoir Python installé (et idéalement `uv` pour la gestion de dépendances).

1.  **Installer les dépendances** :
    ```bash
    uv sync
    # Ou via pip classique :
    pip install pandas paho-mqtt scikit-learn matplotlib streamlit pymongo certifi
    ```

2.  **Configuration** :
    *   Vérifiez que les identifiants MQTT dans `iot_simulator.py` et `ai_backend.py` sont corrects.
    *   Vérifiez que l'URI MongoDB dans `ai_backend.py` et `dashboard.py` est configuré avec vos accès.

## ▶️ Démarrage

Lancez les 3 composants (dans 3 terminaux séparés) :

**Terminal 1 : Le Backend IA** (doit être lancé pour traiter les données)
```bash
uv run ai_backend.py
```

**Terminal 2 : Le Simulateur** (pour envoyer des données)
```bash
uv run iot_simulator.py
```

**Terminal 3 : Le Dashboard** (pour visualiser)
```bash
streamlit run dashboard.py
```

## ✨ Fonctionnalités Clés

*   **Détection d'anomalies** : L'IA identifie automatiquement les valeurs aberrantes en temps réel.
*   **Persistance Cloud** : Toutes les données sont sauvegardées sur MongoDB (Collections `measures` et `anomalies`).
*   **Interface Responsive** : Le dashboard s'adapte et permet de visualiser l'historique des incidents via l'onglet dédié.
