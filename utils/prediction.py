"""
prediction.py
=============
Logique métier du pipeline de prédiction :
    1. Validation / nettoyage des entrées (anti valeurs aberrantes)
    2. Calcul automatique de la variable composite 'score_s1'
    3. Construction du vecteur de features dans l'ordre attendu par le modèle
    4. Prédiction (statut_ajourne) + génération de recommandations de tutorat

Aucune donnée de fin d'année (moyenne_annuelle, mention, etc.) n'est utilisée
ici, afin d'éviter tout data leakage.
"""

import numpy as np
import pandas as pd

from utils.ml_loader import model_loader


def calculer_score_s1(heures_etude_hebdo, taux_presence_S1, note_TD_S1):
    """
    Calcule la variable composite 'score_s1', réplique exacte de la formule
    utilisée dans le notebook de préparation des données.

    Pondération métier :
        - 40% : performance pédagogique (note_TD_S1 ramenée sur 100)
        - 35% : assiduité (taux_presence_S1, déjà en %)
        - 25% : engagement personnel (heures_etude_hebdo ramenées sur 100,
                avec un plafond réaliste de 40h/semaine)

    Returns:
        float: score_s1 (0-100), arrondi à 2 décimales
    """
    note_normalisee = (note_TD_S1 / 20) * 100
    heures_normalisees = min((heures_etude_hebdo / 40) * 100, 100)

    score = (
        0.40 * note_normalisee +
        0.35 * taux_presence_S1 +
        0.25 * heures_normalisees
    )
    return round(score, 2)


def valider_et_nettoyer_valeurs(heures_etude_hebdo, taux_presence_S1, note_TD_S1):
    """
    Valide et borne les valeurs d'entrée pour éviter les valeurs aberrantes.

    Raises:
        ValueError: si une donnée est non numérique ou manquante (NaN).

    Returns:
        tuple(float, float, float): valeurs nettoyées et bornées
    """
    try:
        heures_etude_hebdo = float(heures_etude_hebdo)
        taux_presence_S1 = float(taux_presence_S1)
        note_TD_S1 = float(note_TD_S1)
    except (ValueError, TypeError):
        raise ValueError(
            "Les valeurs 'heures_etude_hebdo', 'taux_presence_S1' et "
            "'note_TD_S1' doivent être numériques."
        )

    if np.isnan(heures_etude_hebdo) or np.isnan(taux_presence_S1) or np.isnan(note_TD_S1):
        raise ValueError("Des valeurs manquantes (NaN) ont été détectées.")

    # Bornage des valeurs aberrantes (clipping métier)
    heures_etude_hebdo = max(0, min(heures_etude_hebdo, 80))
    taux_presence_S1 = max(0, min(taux_presence_S1, 100))
    note_TD_S1 = max(0, min(note_TD_S1, 20))

    return heures_etude_hebdo, taux_presence_S1, note_TD_S1


def generer_recommandation(prediction, proba, taux_presence_S1, heures_etude_hebdo, note_TD_S1):
    """
    Génère une recommandation de plan d'action pour le tutorat, basée sur la
    prédiction et les facteurs individuels les plus critiques.
    """
    if prediction == 0:
        return "Profil stable. Suivi de routine recommandé."

    causes = []
    if taux_presence_S1 < 60:
        causes.append("absentéisme élevé")
    if note_TD_S1 < 8:
        causes.append("difficultés académiques importantes (notes faibles)")
    if heures_etude_hebdo < 5:
        causes.append("temps de travail personnel insuffisant")

    if not causes:
        causes.append("profil global fragile (combinaison de facteurs)")

    plan = "ALERTE - Plan d'action : Convocation par le tuteur. Causes probables : " + ", ".join(causes) + "."

    if "absentéisme élevé" in causes:
        plan += " -> Entretien individuel sur l'assiduité + signalement à la scolarité."
    if "difficultés académiques importantes (notes faibles)" in causes:
        plan += " -> Orientation vers des séances de soutien/tutorat disciplinaire."
    if "temps de travail personnel insuffisant" in causes:
        plan += " -> Mise en place d'un planning de révision personnalisé."

    return plan


def predire_etudiant(heures_etude_hebdo, taux_presence_S1, note_TD_S1):
    """
    Pipeline complet de prédiction pour UN étudiant.

    Étapes :
        1. Validation/nettoyage des entrées
        2. Calcul automatique de score_s1
        3. Construction du vecteur de features dans l'ordre attendu par le modèle
        4. Prédiction via le pipeline (scaler + RandomForest)

    Returns:
        dict: résultat complet (entrées, score_s1, prédiction, probabilité, recommandation)
    """
    if not model_loader.is_loaded:
        raise RuntimeError("Le modèle n'est pas chargé. Vérifiez 'model.joblib'.")

    heures_etude_hebdo, taux_presence_S1, note_TD_S1 = valider_et_nettoyer_valeurs(
        heures_etude_hebdo, taux_presence_S1, note_TD_S1
    )

    # Calcul automatique de la variable composite (anti data-leakage)
    score_s1 = calculer_score_s1(heures_etude_hebdo, taux_presence_S1, note_TD_S1)

    # Construction du vecteur dans l'ordre attendu (cf. model_meta.joblib)
    features_dict = {
        "heures_etude_hebdo": heures_etude_hebdo,
        "taux_presence_S1": taux_presence_S1,
        "note_TD_S1": note_TD_S1,
        "score_s1": score_s1,
    }
    X = pd.DataFrame(
        [[features_dict[col] for col in model_loader.feature_order]],
        columns=model_loader.feature_order,
    )

    prediction = model_loader.predict(X)
    proba = model_loader.predict_proba(X)

    return {
        "heures_etude_hebdo": heures_etude_hebdo,
        "taux_presence_S1": taux_presence_S1,
        "note_TD_S1": note_TD_S1,
        "score_s1": score_s1,
        "prediction": prediction,
        "statut": "Ajourné" if prediction == 1 else "Admis",
        "proba_risque": proba,
        "recommandation": generer_recommandation(
            prediction, proba, taux_presence_S1, heures_etude_hebdo, note_TD_S1
        ),
    }
