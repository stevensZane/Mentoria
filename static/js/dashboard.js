/* ============================================================
   dashboard.js - MentorIA
   Gère les appels AJAX vers /api/predict et /api/import,
   ainsi que l'affichage dynamique des résultats et du
   tableau cumulé des alertes.
   ============================================================ */

// Stockage local (session navigateur) des alertes cumulées
let alertesData = [];

function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function ajouterAlerte(resultat) {
    if (resultat.prediction === 1) {
        alertesData.push(resultat);
        rafraichirTableauAlertes();
    }
}

function rafraichirTableauAlertes() {
    const tbody = document.getElementById('table-alertes-body');
    const table = document.getElementById('table-alertes');
    const vide = document.getElementById('alertes-vide');

    if (!tbody || !table || !vide) return;

    if (alertesData.length === 0) {
        vide.classList.remove('d-none');
        table.classList.add('d-none');
        return;
    }

    vide.classList.add('d-none');
    table.classList.remove('d-none');
    tbody.innerHTML = '';

    alertesData.forEach(r => {
        const tr = document.createElement('tr');
        tr.classList.add('table-danger');
        tr.innerHTML = `
            <td>${escapeHtml(r.nom_etudiant || 'Étudiant')}</td>
            <td>${r.score_s1}</td>
            <td>${r.taux_presence_S1}</td>
            <td>${r.note_TD_S1}</td>
            <td><span class="badge bg-danger">${r.statut}</span></td>
            <td>${r.proba_risque !== null ? r.proba_risque + '%' : 'N/A'}</td>
            <td class="small">${escapeHtml(r.recommandation)}</td>
        `;
        tbody.appendChild(tr);
    });
}

// ============================================================
// ONGLET 1 : Saisie individuelle
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
    const formIndividuel = document.getElementById('form-individuel');
    if (formIndividuel) {
        formIndividuel.addEventListener('submit', async function (e) {
            e.preventDefault();

            const erreurBox = document.getElementById('erreur-individuel');
            const resultBox = document.getElementById('resultat-individuel');
            erreurBox.classList.add('d-none');
            resultBox.classList.add('d-none');

            const payload = {
                nom_etudiant: document.getElementById('nom_etudiant').value || 'Étudiant',
                heures_etude_hebdo: document.getElementById('heures_etude_hebdo').value,
                taux_presence_S1: document.getElementById('taux_presence_S1').value,
                note_TD_S1: document.getElementById('note_TD_S1').value,
            };

            try {
                const response = await fetch('/api/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });
                const data = await response.json();

                if (!data.success) {
                    erreurBox.textContent = data.error || 'Erreur inconnue.';
                    erreurBox.classList.remove('d-none');
                    return;
                }

                const r = data.resultat;
                document.getElementById('res-nom').textContent = r.nom_etudiant;
                document.getElementById('res-score').textContent = r.score_s1;
                document.getElementById('res-proba').textContent =
                    (r.proba_risque !== null ? r.proba_risque + ' %' : 'N/A');

                const statutCell = document.getElementById('res-statut');
                statutCell.innerHTML = r.prediction === 1
                    ? '<span class="badge bg-danger">Ajourné — Risque élevé</span>'
                    : '<span class="badge bg-success">Admis — Profil stable</span>';

                const recoBox = document.getElementById('recommandation-box');
                recoBox.className = 'p-3 rounded border ' +
                    (r.prediction === 1 ? 'border-danger bg-danger-subtle' : 'border-success bg-success-subtle');
                recoBox.innerHTML = '<strong><i class="bi bi-lightbulb"></i> Recommandation :</strong><br>' +
                    escapeHtml(r.recommandation);

                resultBox.classList.remove('d-none');

                ajouterAlerte(r);

            } catch (err) {
                erreurBox.textContent = 'Erreur réseau : ' + err.message;
                erreurBox.classList.remove('d-none');
            }
        });
    }

    // ============================================================
    // ONGLET 2 : Importation de masse
    // ============================================================
    const formImport = document.getElementById('form-import');
    if (formImport) {
        formImport.addEventListener('submit', async function (e) {
            e.preventDefault();

            const erreurBox = document.getElementById('erreur-import');
            const erreursLignesBox = document.getElementById('erreurs-lignes');
            const statsBox = document.getElementById('stats-import');
            const table = document.getElementById('table-import');
            const tbody = document.getElementById('table-import-body');

            erreurBox.classList.add('d-none');
            erreursLignesBox.classList.add('d-none');

            const fileInput = document.getElementById('fichier');
            if (!fileInput.files.length) {
                erreurBox.textContent = 'Veuillez sélectionner un fichier.';
                erreurBox.classList.remove('d-none');
                return;
            }

            const formData = new FormData();
            formData.append('fichier', fileInput.files[0]);

            try {
                const response = await fetch('/api/import', {
                    method: 'POST',
                    body: formData,
                });
                const data = await response.json();

                if (!data.success) {
                    erreurBox.textContent = data.error || "Erreur inconnue lors de l'import.";
                    erreurBox.classList.remove('d-none');
                    return;
                }

                // Statistiques
                document.getElementById('stat-total').textContent = data.stats.total;
                document.getElementById('stat-ajournes').textContent = data.stats.ajournes;
                document.getElementById('stat-taux').textContent = data.stats.taux_risque + '%';
                statsBox.classList.remove('d-none');

                // Erreurs de lignes (s'il y en a)
                if (data.erreurs && data.erreurs.length > 0) {
                    erreursLignesBox.innerHTML = '<strong><i class="bi bi-exclamation-triangle"></i> ' +
                        data.erreurs.length + ' ligne(s) ignorée(s) :</strong><ul class="mb-0">' +
                        data.erreurs.map(e => `<li>Ligne ${e.ligne} (${escapeHtml(e.nom_etudiant)}) : ${escapeHtml(e.erreur)}</li>`).join('') +
                        '</ul>';
                    erreursLignesBox.classList.remove('d-none');
                }

                // Tableau de résultats
                tbody.innerHTML = '';
                data.resultats.forEach(r => {
                    const tr = document.createElement('tr');
                    if (r.prediction === 1) tr.classList.add('table-danger');

                    tr.innerHTML = `
                        <td>${escapeHtml(r.matricule)}</td>
                        <td>${escapeHtml(r.nom_etudiant)}</td>
                        <td>${r.heures_etude_hebdo}</td>
                        <td>${r.taux_presence_S1}</td>
                        <td>${r.note_TD_S1}</td>
                        <td>${r.score_s1}</td>
                        <td>${r.prediction === 1 ? '<span class="badge bg-danger">Ajourné</span>' : '<span class="badge bg-success">Admis</span>'}</td>
                        <td>${r.proba_risque !== null ? r.proba_risque + '%' : 'N/A'}</td>
                        <td class="small">${escapeHtml(r.recommandation)}</td>
                    `;
                    tbody.appendChild(tr);

                    ajouterAlerte(r);
                });
                table.classList.remove('d-none');

            } catch (err) {
                erreurBox.textContent = 'Erreur réseau : ' + err.message;
                erreurBox.classList.remove('d-none');
            }
        });
    }
});
