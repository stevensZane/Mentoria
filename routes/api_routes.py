"""
api_routes.py
=============
Blueprint exposant les endpoints AJAX (JSON) :
    - /api/predict  : prédiction individuelle (admin, enseignant)
    - /api/import   : import de masse Excel/CSV (admin uniquement)
    - /api/users    : liste des utilisateurs (admin uniquement)
"""

from flask import Blueprint, request, jsonify

from utils.auth import role_required, USERS_DB
from utils.prediction import predire_etudiant
from utils.file_processing import lire_fichier_eleves, traiter_dataframe

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/predict", methods=["POST"])
@role_required("admin", "enseignant")
def predict():
    """
    Endpoint AJAX (JSON) pour la prédiction individuelle.
    Accessible par : Administrateur, Enseignant.
    """
    try:
        data = request.get_json(silent=True) or request.form

        heures_etude_hebdo = data.get("heures_etude_hebdo")
        taux_presence_S1 = data.get("taux_presence_S1")
        note_TD_S1 = data.get("note_TD_S1")
        nom_etudiant = (data.get("nom_etudiant") or "Étudiant").strip() or "Étudiant"

        if heures_etude_hebdo is None or taux_presence_S1 is None or note_TD_S1 is None:
            return jsonify({
                "success": False,
                "error": "Tous les champs (heures d'étude, taux de présence, note TD) sont obligatoires."
            }), 400

        resultat = predire_etudiant(heures_etude_hebdo, taux_presence_S1, note_TD_S1)
        resultat["nom_etudiant"] = nom_etudiant

        return jsonify({"success": True, "resultat": resultat})

    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except RuntimeError as re_err:
        return jsonify({"success": False, "error": str(re_err)}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"Erreur inattendue : {e}"}), 500


@api_bp.route("/import", methods=["POST"])
@role_required("admin")
def import_fichier():
    """
    Endpoint AJAX pour l'import de masse (Excel/CSV).
    Accessible uniquement par : Administrateur (Scolarité).
    """
    try:
        if "fichier" not in request.files:
            return jsonify({"success": False, "error": "Aucun fichier reçu."}), 400

        fichier = request.files["fichier"]

        if fichier.filename == "":
            return jsonify({"success": False, "error": "Aucun fichier sélectionné."}), 400

        df = lire_fichier_eleves(fichier)
        resultats, erreurs = traiter_dataframe(df)

        nb_total = len(resultats)
        nb_ajournes = sum(1 for r in resultats if r["prediction"] == 1)
        nb_admis = nb_total - nb_ajournes

        return jsonify({
            "success": True,
            "resultats": resultats,
            "erreurs": erreurs,
            "stats": {
                "total": nb_total,
                "ajournes": nb_ajournes,
                "admis": nb_admis,
                "taux_risque": round((nb_ajournes / nb_total) * 100, 1) if nb_total > 0 else 0,
            },
        })

    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Erreur lors du traitement du fichier : {e}"}), 500


@api_bp.route("/users", methods=["GET"])
@role_required("admin")
def gestion_utilisateurs():
    """Liste des utilisateurs (vue admin uniquement)."""
    utilisateurs = [
        {"username": u, "role": v["role"], "nom": v["nom"], "label": v["label"]}
        for u, v in USERS_DB.items()
    ]
    return jsonify({"success": True, "utilisateurs": utilisateurs})
