"""
generate_dummy_model.py
========================
Script UTILITAIRE (optionnel) permettant de générer un modèle factice
'model.joblib' et ses métadonnées 'model_meta.joblib' à des fins de TEST
de l'application, en l'absence du modèle entraîné sur les vraies données.

⚠️ Ce modèle est entraîné sur des données SYNTHÉTIQUES et ne doit PAS être
utilisé pour la soutenance. Remplacez ensuite models/model.joblib et
models/model_meta.joblib par vos fichiers réels issus du notebook.

Usage :
    python generate_dummy_model.py
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURE_ORDER = ["heures_etude_hebdo", "taux_presence_S1", "note_TD_S1", "score_s1"]

np.random.seed(42)
n = 500

heures_etude_hebdo = np.random.uniform(0, 40, n)
taux_presence_S1 = np.random.uniform(20, 100, n)
note_TD_S1 = np.random.uniform(0, 20, n)

note_normalisee = (note_TD_S1 / 20) * 100
heures_normalisees = np.minimum((heures_etude_hebdo / 40) * 100, 100)
score_s1 = 0.40 * note_normalisee + 0.35 * taux_presence_S1 + 0.25 * heures_normalisees

# Cible : ajourné si score_s1 faible (+ bruit)
proba_ajourne = 1 / (1 + np.exp((score_s1 - 50) / 8))
statut_ajourne = (np.random.rand(n) < proba_ajourne).astype(int)

X = pd.DataFrame({
    "heures_etude_hebdo": heures_etude_hebdo,
    "taux_presence_S1": taux_presence_S1,
    "note_TD_S1": note_TD_S1,
    "score_s1": score_s1,
})[FEATURE_ORDER]

y = statut_ajourne

pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("rf", RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)),
])
pipeline.fit(X, y)

train_acc = pipeline.score(X, y)

os.makedirs("models", exist_ok=True)
joblib.dump(pipeline, "models/model.joblib")
joblib.dump({
    "feature_order": FEATURE_ORDER,
    "metrics": {
        "model_name": "RandomForestClassifier (DEMO)",
        "accuracy": round(train_acc, 3),
        "recall": "N/A (démo)",
        "f1_score": "N/A (démo)",
    },
}, "models/model_meta.joblib")

print("Modèle factice généré : models/model.joblib, models/model_meta.joblib")
print(f"Accuracy (train, démo) : {train_acc:.3f}")
