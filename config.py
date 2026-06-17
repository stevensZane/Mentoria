"""
Configuration centrale de l'application MentorIA.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Configuration de base de l'application Flask."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "mentoria_dit_2026_secret_key_change_in_prod")

    # Upload
    UPLOAD_EXTENSIONS = [".xlsx", ".xls", ".csv"]
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 Mo max

    # Chemins des modèles ML
    MODEL_PATH = os.path.join(BASE_DIR, "models", "model.joblib")
    MODEL_META_PATH = os.path.join(BASE_DIR, "models", "model_meta.joblib")

    # Ordre par défaut des features si model_meta.joblib est absent/incomplet
    DEFAULT_FEATURE_ORDER = ["heures_etude_hebdo", "taux_presence_S1", "note_TD_S1", "score_s1"]

    DEFAULT_METRICS = {
        "accuracy": "N/A",
        "recall": "N/A",
        "f1_score": "N/A",
        "model_name": "RandomForestClassifier",
    }
