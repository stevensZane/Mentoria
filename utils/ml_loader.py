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
                # Format attendu récent : {'feature_order': [...], 'metrics': {...}}
                if "feature_order" in self.meta:
                    self.feature_order = self.meta["feature_order"]

                if "metrics" in self.meta and isinstance(self.meta["metrics"], dict):
                    self.metrics = self.meta["metrics"]
                else:
                    # Support d'un ancien format de métadonnées (ex : keys 'features','f1','precision',...)
                    # On mappe doucement les champs disponibles vers la structure attendue.
                    mapped = {
                        "model_name": self.meta.get("model_name", self.metrics.get("model_name")),
                        "accuracy": self.meta.get("accuracy", self.metrics.get("accuracy", "N/A")),
                        "recall": self.meta.get("recall", self.metrics.get("recall", "N/A")),
                        "f1_score": self.meta.get("f1", self.meta.get("f1_score", self.metrics.get("f1_score", "N/A"))),
                    }
                    # Remonter d'autres métriques si présentes
                    if "precision" in self.meta:
                        mapped["precision"] = self.meta.get("precision")
                    if "roc_auc" in self.meta:
                        mapped["roc_auc"] = self.meta.get("roc_auc")

                    self.metrics = mapped

                # Ancien nom de la liste de features -> 'features'
                if "features" in self.meta and "feature_order" not in self.meta:
                    self.feature_order = self.meta.get("features", self.feature_order)

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
