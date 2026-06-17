"""
auth.py
=======
Authentification simplifiée par session pour les 3 profils utilisateurs :
    - admin       : Administrateur (Scolarité) — accès total
    - enseignant  : Enseignant — saisie individuelle + dashboard classe
    - tuteur      : Conseiller Pédagogique / Tuteur — lecture seule des alertes

En production : remplacer USERS_DB par une base de données et hasher les
mots de passe (ex. werkzeug.security.generate_password_hash).
"""

from functools import wraps
from flask import session, redirect, url_for, flash


# ============================================================
# UTILISATEURS FACTICES (3 PROFILS)
# ============================================================

USERS_DB = {
    "admin": {
        "password": "admin123",
        "role": "admin",
        "nom": "Service Scolarité",
        "label": "Administrateur (Scolarité)",
    },
    "enseignant": {
        "password": "ens123",
        "role": "enseignant",
        "nom": "Prof. Diallo",
        "label": "Enseignant",
    },
    "tuteur": {
        "password": "tut123",
        "role": "tuteur",
        "nom": "Conseiller Pédagogique",
        "label": "Conseiller Pédagogique / Tuteur",
    },
}


def verifier_identifiants(username, password):
    """
    Vérifie un couple identifiant/mot de passe.

    Returns:
        dict | None: les informations utilisateur si valides, sinon None.
    """
    user = USERS_DB.get(username)
    if user and user["password"] == password:
        return user
    return None


def login_required(f):
    """Vérifie que l'utilisateur est authentifié."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            flash("Veuillez vous connecter pour accéder à cette page.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    """Vérifie que l'utilisateur connecté a l'un des rôles autorisés."""
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user" not in session:
                flash("Veuillez vous connecter.", "warning")
                return redirect(url_for("auth.login"))
            if session.get("role") not in roles:
                flash("Accès refusé : permissions insuffisantes pour cette action.", "danger")
                return redirect(url_for("dashboard.index"))
            return f(*args, **kwargs)
        return decorated
    return wrapper
