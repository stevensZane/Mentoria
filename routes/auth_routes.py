"""
auth_routes.py
==============
Blueprint gérant la connexion, la déconnexion et la redirection racine.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from utils.auth import verifier_identifiants

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def home():
    """Redirige vers le dashboard si connecté, sinon vers la page de login."""
    if "user" in session:
        return redirect(url_for("dashboard.index"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Page et traitement de la connexion (auth simplifiée par session)."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = verifier_identifiants(username, password)
        if user:
            session["user"] = username
            session["role"] = user["role"]
            session["nom"] = user["nom"]
            session["label"] = user["label"]
            flash(f"Bienvenue, {user['nom']} !", "success")
            return redirect(url_for("dashboard.index"))
        else:
            flash("Identifiant ou mot de passe incorrect.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    """Déconnexion : vidage de la session."""
    session.clear()
    flash("Vous avez été déconnecté.", "info")
    return redirect(url_for("auth.login"))
