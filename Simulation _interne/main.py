import numpy as np
import random
from fastapi import FastAPI
import joblib
import pandas as pd
import time
import requests

def simulate_cell_state():
    return {
        "rsrp": np.random.normal(-95, 10),
        "rsrq": np.random.normal(-10, 3),
        "wbcqi": np.random.randint(1, 15),
        "macStats_totalPrbDl": np.random.randint(10, 100),
        "macStats_prbRetxDl": np.random.randint(0, 150),
        "pdcpStats_pktRxOo": np.random.randint(0, 20),
        "pdcpStats_pktRxAiat": np.random.uniform(1, 50),
        "macStats_totalPduDl": np.random.randint(100, 10000),
        "macStats_totalPduUl": np.random.randint(100, 8000),
        "macStats_totalTbsDl": np.random.randint(1000, 20000),
        "macStats_totalTbsUl": np.random.randint(1000, 15000)
    }

def decision_engine(latency, energy, anomaly, row):

    actions = []

    # anomalie
    if anomaly == -1:
        actions.append("ALERTE : anomalie détectée")

    # latence élevée
    if latency > 70:
        actions.append("Activer load balancing / handover")

    # énergie élevée
    if energy > 70:
        actions.append("Réduire PRB / activer sleep mode")

    # congestion PRB
    if row["macStats_totalPrbDl"] > 80:
        actions.append("Redistribution ressources")

    # retransmissions
    if row["macStats_prbRetxDl"] > 100:
        actions.append("Optimisation MCS")

    if not actions:
        actions.append("Réseau stable")

    return actions


app = FastAPI()

latency_model = joblib.load("models/model_latency.pkl")
energy_model = joblib.load("models/model_energy.pkl")
anomaly_model = joblib.load("models/maintenance_model.pkl")


@app.post("/predict")
def predict(data: dict):

    df = pd.DataFrame([data])

    latency = latency_model.predict(df)[0]
    energy = energy_model.predict(df)[0]
    anomaly = anomaly_model.predict(df)[0]

    return {
        "latency": float(latency),
        "energy": float(energy),
        "anomaly": int(anomaly)
    }
import streamlit as st
import requests

st.title("4G/5G Network Digital Twin")

if st.button("Simulate step"):

    response = requests.post(
        "http://localhost:8000/predict",
        json={}
    ).json()

    st.json(response)


while True:

    # 1. simuler antenne
    cell = simulate_cell_state()

    # 2. envoyer au modèle
    response = requests.post(
        "http://localhost:8000/predict",
        json=cell
    ).json()

    # 3. décision
    actions = decision_engine(
        response["latency"],
        response["energy"],
        response["anomaly"],
        cell
    )

    # 4. affichage
    print("STATE:", cell)
    print("PRED:", response)
    print("ACTIONS:", actions)
    print("-"*50)

    time.sleep(2)