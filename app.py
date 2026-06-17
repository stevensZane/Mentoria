"""
app.py
======
MentorIA - Application de détection précoce du décrochage étudiant (Fin S1)

Projet de Licence 3 Informatique & Data Science - DIT (Sénégal)
Supervision : Dr. Seydou Nourou Sylla

Point d'entrée principal : utilise le "application factory pattern" et
enregistre les blueprints (auth, dashboard, api).
"""

from flask import Flask, render_template, jsonify

from config import Config
from utils.ml_loader import model_loader

from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.api_routes import api_bp


def create_app():
    """Factory de création de l'application Flask."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enregistrement des blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)

    # ============================================================
    # GESTION D'ERREURS GLOBALES
    # ============================================================

    @app.errorhandler(404)
    def page_non_trouvee(e):
        return render_template("login.html"), 404

    @app.errorhandler(413)
    def fichier_trop_volumineux(e):
        return jsonify({
            "success": False,
            "error": "Le fichier dépasse la taille maximale autorisée (10 Mo).",
        }), 413

    @app.errorhandler(500)
    def erreur_serveur(e):
        return jsonify({"success": False, "error": "Erreur interne du serveur."}), 500

    return app


app = create_app()


if __name__ == "__main__":
    print("=" * 60)
    print("MentorIA - Détection précoce du décrochage (L3 - DIT)")
    print(f"Modèle chargé : {'OUI' if model_loader.is_loaded else 'NON - vérifier models/model.joblib'}")
    print(f"Ordre des features : {model_loader.feature_order}")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5000)
