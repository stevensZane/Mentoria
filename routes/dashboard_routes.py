"""
dashboard_routes.py
===================
Blueprint affichant le tableau de bord principal, dont le contenu (onglets
visibles) est adapté selon le rôle de l'utilisateur connecté :
    - admin       : saisie individuelle + import de masse + alertes
    - enseignant  : saisie individuelle + alertes
    - tuteur      : alertes (lecture seule)
"""

from flask import Blueprint, render_template, session

from utils.auth import login_required
from utils.ml_loader import model_loader

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def index():
    """Affiche le tableau de bord principal, personnalisé par rôle."""
    return render_template(
        "index.html",
        role=session.get("role"),
        nom=session.get("nom"),
        label=session.get("label"),
        model_charge=model_loader.is_loaded,
        metrics=model_loader.metrics,
        feature_order=model_loader.feature_order,
    )
