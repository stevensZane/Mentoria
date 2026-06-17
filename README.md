# MentorIA — Détection précoce du décrochage étudiant (Fin S1)

Projet de Licence 3 Informatique & Data Science — DIT (Sénégal)
Supervision : **Dr. Seydou Nourou Sylla**

## Structure du projet

```
mentoria/
├── app.py                     # Point d'entrée Flask (application factory)
├── config.py                  # Configuration centrale
├── requirements.txt
├── models/
│   ├── model.joblib            # ⚠️ À FOURNIR (pipeline scaler + RandomForest)
│   └── model_meta.joblib        # ⚠️ À FOURNIR (feature_order + metrics)
├── routes/
│   ├── auth_routes.py          # Login / logout
│   ├── dashboard_routes.py     # Tableau de bord principal
│   └── api_routes.py           # API JSON (predict, import, users)
├── utils/
│   ├── auth.py                 # Auth factice par session (3 rôles)
│   ├── ml_loader.py             # Chargement statique du modèle joblib
│   ├── prediction.py            # Calcul score_s1 + pipeline de prédiction
│   └── file_processing.py      # Lecture/normalisation Excel/CSV
├── templates/
│   ├── login.html
│   └── index.html
└── static/
    ├── css/style.css
    └── js/dashboard.js
```

## Installation

```bash
cd mentoria
python -m venv venv
source venv/bin/activate   # ou venv\Scripts\activate sous Windows
pip install -r requirements.txt
```

## Placement des modèles

Placez vos fichiers entraînés dans `models/` :

- `models/model.joblib` : pipeline complet (StandardScaler + RandomForestClassifier)
- `models/model_meta.joblib` : dict `{"feature_order": [...], "metrics": {...}}`

Si `model_meta.joblib` est absent, l'ordre par défaut
`["heures_etude_hebdo", "taux_presence_S1", "note_TD_S1", "score_s1"]` est utilisé.

## Lancement

```bash
python app.py
```

Accès : http://localhost:5000

## Comptes de démonstration (auth factice par session)

| Rôle                          | Identifiant | Mot de passe | Accès                                              |
|-------------------------------|-------------|--------------|-----------------------------------------------------|
| Administrateur (Scolarité)     | admin       | admin123     | Total : saisie, import de masse, alertes, users     |
| Enseignant                    | enseignant  | ens123       | Saisie individuelle + alertes                       |
| Conseiller Pédagogique/Tuteur | tuteur      | tut123       | Lecture seule des alertes                            |

## Point d'attention métier

La variable composite `score_s1` est calculée automatiquement côté backend
(`utils/prediction.py`, fonction `calculer_score_s1`) selon la pondération :

- 40% : note_TD_S1 (normalisée sur 100)
- 35% : taux_presence_S1
- 25% : heures_etude_hebdo (normalisées sur 100, plafond 40h/semaine)

⚠️ **Ajustez cette pondération si elle diffère de celle utilisée dans votre
notebook de préparation des données**, afin de garantir la cohérence
train/inférence.

Aucune donnée de fin d'année (moyenne_annuelle, mention) n'est demandée en
entrée — la cible prédite est `statut_ajourne` (1 = Ajourné, 0 = Admis).
