"""
file_processing.py
===================
Lecture, normalisation et traitement en masse des fichiers Excel/CSV importés
par l'Administrateur (Scolarité).

Gère :
    - la détection automatique du format (csv / xls / xlsx)
    - la normalisation des noms de colonnes (alias FR/EN)
    - la vérification des colonnes obligatoires
    - le traitement ligne par ligne via le pipeline de prédiction, avec
      isolation des erreurs par ligne (une ligne défectueuse n'interrompt
      pas le traitement global)
"""

import io
import os

import pandas as pd

from config import Config
from utils.prediction import predire_etudiant


# Mapping FR/EN -> noms internes attendus, pour robustesse face aux fichiers
COLUMN_ALIASES = {
    "heures_etude_hebdo": [
        "heures_etude_hebdo", "heures etude hebdo", "study_hours_weekly",
        "weekly_study_hours", "heures_etude", "heures_d_etude"
    ],
    "taux_presence_S1": [
        "taux_presence_s1", "taux presence s1", "attendance_rate_s1",
        "attendance_s1", "taux_presence", "presence_s1"
    ],
    "note_TD_S1": [
        "note_td_s1", "note td s1", "td_grade_s1", "grade_td_s1",
        "note_td", "td_s1"
    ],
    "nom_etudiant": [
        "nom_etudiant", "nom etudiant", "student_name", "nom", "name", "etudiant"
    ],
    "matricule": [
        "matricule", "student_id", "id_etudiant", "id"
    ],
}


def normaliser_colonnes(df):
    """
    Renomme les colonnes du DataFrame importé selon les alias connus
    (français ou anglais) pour les faire correspondre aux clés internes.

    Returns:
        pd.DataFrame: dataframe avec colonnes normalisées
    """
    df.columns = [str(c).strip() for c in df.columns]
    lower_map = {c.lower().strip(): c for c in df.columns}

    rename_map = {}
    for internal_name, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias.lower() in lower_map:
                rename_map[lower_map[alias.lower()]] = internal_name
                break

    return df.rename(columns=rename_map)


def lire_fichier_eleves(fichier):
    """
    Lit un fichier CSV ou Excel uploadé et retourne un DataFrame normalisé.

    Args:
        fichier (FileStorage): fichier transmis via request.files

    Returns:
        pd.DataFrame

    Raises:
        ValueError: si le format est invalide ou les colonnes obligatoires manquent
    """
    filename = fichier.filename.lower()
    ext = os.path.splitext(filename)[1]

    if ext not in Config.UPLOAD_EXTENSIONS:
        raise ValueError(
            f"Format de fichier non supporté ({ext}). "
            "Veuillez fournir un fichier .csv, .xls ou .xlsx."
        )

    try:
        content = fichier.read()
        buffer = io.BytesIO(content)

        if ext == ".csv":
            # Tentative auto-détection séparateur (',' ou ';')
            try:
                df = pd.read_csv(buffer, sep=None, engine="python")
            except Exception:
                buffer.seek(0)
                df = pd.read_csv(buffer, sep=";")
        else:
            df = pd.read_excel(buffer)

    except Exception as e:
        raise ValueError(f"Le fichier est corrompu ou mal formaté : {e}")

    if df.empty:
        raise ValueError("Le fichier importé est vide.")

    df = normaliser_colonnes(df)

    colonnes_obligatoires = ["heures_etude_hebdo", "taux_presence_S1", "note_TD_S1"]
    colonnes_manquantes = [c for c in colonnes_obligatoires if c not in df.columns]

    if colonnes_manquantes:
        raise ValueError(
            "Colonnes obligatoires manquantes : " + ", ".join(colonnes_manquantes) +
            ". Colonnes attendues (FR ou EN) : heures_etude_hebdo, taux_presence_S1, note_TD_S1 "
            "(+ optionnel : nom_etudiant, matricule)."
        )

    if "nom_etudiant" not in df.columns:
        df["nom_etudiant"] = [f"Étudiant_{i+1}" for i in range(len(df))]
    if "matricule" not in df.columns:
        df["matricule"] = [f"N/A-{i+1}" for i in range(len(df))]

    return df


def traiter_dataframe(df):
    """
    Applique le pipeline de prédiction sur chaque ligne d'un DataFrame.
    Gère les lignes individuellement défectueuses sans interrompre tout le
    traitement.

    Returns:
        tuple(list[dict], list[dict]): (résultats valides, erreurs par ligne)
    """
    resultats = []
    erreurs = []

    for idx, row in df.iterrows():
        try:
            res = predire_etudiant(
                row.get("heures_etude_hebdo"),
                row.get("taux_presence_S1"),
                row.get("note_TD_S1"),
            )
            res["nom_etudiant"] = str(row.get("nom_etudiant", f"Étudiant_{idx+1}"))
            res["matricule"] = str(row.get("matricule", "N/A"))
            resultats.append(res)
        except Exception as e:
            erreurs.append({
                "ligne": idx + 2,  # +2 = compense l'en-tête + index 0-based
                "erreur": str(e),
                "nom_etudiant": str(row.get("nom_etudiant", f"Ligne {idx+2}")),
            })

    return resultats, erreurs
