"""
ml_loader.py
============
Chargement statique du modèle ML (pipeline scaler + RandomForest) et de ses
métadonnées (ordre des features + métriques de performance), au démarrage
de l'application.
"""

import joblib
from config import Config


class ModelLoader:
    """
    Encapsule le chargement et l'accès au modèle de prédiction et à ses
    métadonnées. Conçu comme un singleton chargé une seule fois au démarrage.
    """

    def __init__(self, model_path=None, meta_path=None):
        self.model = None
        self.meta = None
        self.feature_order = Config.DEFAULT_FEATURE_ORDER
        self.metrics = Config.DEFAULT_METRICS

        self._charger_modele(model_path or Config.MODEL_PATH)
        self._charger_meta(meta_path or Config.MODEL_META_PATH)

    def _charger_modele(self, path):
        try:
            self.model = joblib.load(path)
            print(f"[OK] Modèle chargé depuis {path}")
        except Exception as e:
            print(f"[ERREUR] Impossible de charger le modèle ({path}) : {e}")
            self.model = None

    def _charger_meta(self, path):
        try:
            self.meta = joblib.load(path)
            if isinstance(self.meta, dict):
                if "feature_order" in self.meta:
                    self.feature_order = self.meta["feature_order"]
                if "metrics" in self.meta:
                    self.metrics = self.meta["metrics"]
            print(f"[OK] Métadonnées chargées depuis {path}")
        except Exception as e:
            print(f"[ATTENTION] model_meta.joblib non chargé ({path}) : {e}")
            self.meta = {
                "feature_order": self.feature_order,
                "metrics": self.metrics,
            }

    @property
    def is_loaded(self):
        return self.model is not None

    def predict(self, X):
        """Effectue une prédiction binaire sur un DataFrame X."""
        if self.model is None:
            raise RuntimeError("Le modèle n'est pas chargé. Vérifiez 'model.joblib'.")
        return int(self.model.predict(X)[0])

    def predict_proba(self, X):
        """Retourne la probabilité de la classe 1 (Ajourné), ou None si indisponible."""
        if self.model is None:
            raise RuntimeError("Le modèle n'est pas chargé. Vérifiez 'model.joblib'.")
        if hasattr(self.model, "predict_proba"):
            proba_array = self.model.predict_proba(X)[0]
            return round(float(proba_array[1]) * 100, 1)
        return None


# Instance unique chargée au démarrage de l'application
model_loader = ModelLoader()
