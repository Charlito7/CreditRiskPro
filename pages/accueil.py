from __future__ import annotations

import pandas as pd
import streamlit as st

from components.layout import afficher_titre_section
from services.database import (
    initialiser_base,
    lire_historique,
)
from services.utils import (
    formater_pourcentage,
)


# ============================================================
# 1. Initialisation de la base de données
# ============================================================
#
# Cette fonction crée les tables si elles n'existent pas encore.
# Elle ne supprime aucune donnée existante.

initialiser_base()


# ============================================================
# 2. En-tête de la page
# ============================================================

afficher_titre_section(
    titre="Tableau de bord",
    description=(
        "Vue générale de l’activité de scoring, "
        "des dossiers évalués et de l’état des modèles."
    ),
)


# ============================================================
# 3. Chargement de l'historique
# ============================================================
#
# lire_historique() retourne un DataFrame contenant
# toutes les évaluations enregistrées dans SQLite.

try:

    historique = lire_historique()

except Exception as erreur:

    st.error(
        "Impossible de charger les données du tableau de bord."
    )

    st.exception(erreur)

    historique = pd.DataFrame()


# ============================================================
# 4. Calcul des indicateurs
# ============================================================

if historique.empty:

    nombre_dossiers = 0
    nombre_signales = 0
    probabilite_moyenne = 0.0
    indice_moyen = 0.0
    taux_signale = 0.0

else:

    nombre_dossiers = len(
        historique
    )

    nombre_signales = int(
        historique[
            "classe_predite"
        ].sum()
    )

    probabilite_moyenne = float(
        historique[
            "probabilite_defaut"
        ].mean()
    )

    indice_moyen = float(
        historique[
            "indice_risque"
        ].mean()
    )

    taux_signale = (
        nombre_signales
        / nombre_dossiers
        if nombre_dossiers > 0
        else 0.0
    )


# ============================================================
# 5. Affichage des KPI
# ============================================================

col1, col2, col3, col4 = st.columns(
    4
)

with col1:

    st.metric(
        label="Dossiers évalués",
        value=nombre_dossiers,
    )

with col2:

    st.metric(
        label="Dossiers signalés",
        value=nombre_signales,
        delta=(
            formater_pourcentage(
                taux_signale
            )
            if nombre_dossiers > 0
            else None
        ),
        help=(
            "Nombre de dossiers dont la probabilité de défaut "
            "dépasse le seuil opérationnel du modèle."
        ),
    )

with col3:

    st.metric(
        label="Probabilité moyenne",
        value=formater_pourcentage(
            probabilite_moyenne
        ),
    )

with col4:

    st.metric(
        label="Indice moyen",
        value=(
            f"{indice_moyen:.0f} / 1000"
        ),
        help=(
            "Plus l’indice est élevé, plus la probabilité "
            "de défaut estimée est faible."
        ),
    )


# ============================================================
# 6. État des modèles
# ============================================================

st.subheader(
    "État du système"
)

col_modele_avec, col_modele_sans = (
    st.columns(2)
)

with col_modele_avec:

    with st.container(
        border=True
    ):

        st.markdown(
            "### Modèle avec `loan_grade`"
        )

        st.write(
            "**Algorithme :** XGBoost"
        )

        st.write(
            "**Utilisation :** évaluation enrichie"
        )

        st.write(
            "**ROC-AUC observée :** environ 0,95"
        )

        st.write(
            "**PR-AUC observée :** environ 0,91"
        )

        st.success(
            "Modèle opérationnel"
        )


with col_modele_sans:

    with st.container(
        border=True
    ):

        st.markdown(
            "### Modèle sans `loan_grade`"
        )

        st.write(
            "**Algorithme :** XGBoost"
        )

        st.write(
            "**Utilisation :** évaluation autonome"
        )

        st.write(
            "**ROC-AUC observée :** environ 0,94"
        )

        st.write(
            "**PR-AUC observée :** environ 0,89"
        )

        st.success(
            "Modèle opérationnel"
        )


# ============================================================
# 7. Répartition des risques
# ============================================================

st.subheader(
    "Répartition des catégories de risque"
)

if historique.empty:

    st.info(
        "Aucune évaluation n’est encore disponible. "
        "Analysez un premier dossier pour alimenter "
        "le tableau de bord."
    )

else:

    repartition_risque = (
        historique[
            "categorie_risque"
        ]
        .value_counts()
        .rename_axis(
            "categorie_risque"
        )
        .reset_index(
            name="nombre_dossiers"
        )
    )

    libelles_categories = {
        "faible": "Risque faible",
        "modere": "Risque modéré",
        "eleve": "Risque élevé",
        "tres_eleve": "Risque très élevé",
        "indetermine": "Risque indéterminé",
    }

    repartition_risque[
        "categorie"
    ] = repartition_risque[
        "categorie_risque"
    ].map(
        libelles_categories
    ).fillna(
        repartition_risque[
            "categorie_risque"
        ]
    )

    st.bar_chart(
        data=repartition_risque,
        x="categorie",
        y="nombre_dossiers",
        use_container_width=True,
    )


# ============================================================
# 8. Répartition selon le modèle utilisé
# ============================================================

st.subheader(
    "Utilisation des modèles"
)

if not historique.empty:

    utilisation_modeles = (
        historique[
            "mode_evaluation"
        ]
        .value_counts()
        .rename_axis(
            "mode"
        )
        .reset_index(
            name="nombre"
        )
    )

    utilisation_modeles[
        "libelle"
    ] = utilisation_modeles[
        "mode"
    ].replace(
        {
            "avec_grade": "Avec loan_grade",
            "sans_grade": "Sans loan_grade",
        }
    )

    st.bar_chart(
        utilisation_modeles,
        x="libelle",
        y="nombre",
        use_container_width=True,
    )

else:

    st.info(
        "Aucune donnée disponible pour comparer "
        "l’utilisation des deux modèles."
    )


# ============================================================
# 9. Dernières évaluations
# ============================================================

st.subheader(
    "Dernières évaluations"
)

if historique.empty:

    st.info(
        "L’historique est vide."
    )

else:

    colonnes_affichees = [
        "date_evaluation",
        "reference_dossier",
        "mode_evaluation",
        "probabilite_defaut",
        "indice_risque",
        "categorie_risque",
        "classe_predite",
    ]

    colonnes_disponibles = [
        colonne
        for colonne in colonnes_affichees
        if colonne in historique.columns
    ]

    dernieres_evaluations = (
        historique[
            colonnes_disponibles
        ]
        .head(10)
        .copy()
    )

    if (
        "probabilite_defaut"
        in dernieres_evaluations.columns
    ):

        dernieres_evaluations[
            "probabilite_defaut"
        ] = dernieres_evaluations[
            "probabilite_defaut"
        ].map(
            lambda valeur: (
                f"{valeur:.2%}"
            )
        )

    if (
        "mode_evaluation"
        in dernieres_evaluations.columns
    ):

        dernieres_evaluations[
            "mode_evaluation"
        ] = dernieres_evaluations[
            "mode_evaluation"
        ].replace(
            {
                "avec_grade": "Avec grade",
                "sans_grade": "Sans grade",
            }
        )

    if (
        "categorie_risque"
        in dernieres_evaluations.columns
    ):

        dernieres_evaluations[
            "categorie_risque"
        ] = dernieres_evaluations[
            "categorie_risque"
        ].replace(
            {
                "faible": "Faible",
                "modere": "Modéré",
                "eleve": "Élevé",
                "tres_eleve": "Très élevé",
            }
        )

    if (
        "classe_predite"
        in dernieres_evaluations.columns
    ):

        dernieres_evaluations[
            "classe_predite"
        ] = dernieres_evaluations[
            "classe_predite"
        ].replace(
            {
                0: "Non signalé",
                1: "Signalé",
            }
        )

    st.dataframe(
        dernieres_evaluations,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# 10. Message de pilotage
# ============================================================

if nombre_dossiers > 0:

    if taux_signale >= 0.50:

        st.warning(
            "Plus de la moitié des dossiers évalués sont "
            "actuellement signalés. Il est recommandé de vérifier "
            "la qualité des données saisies, le portefeuille analysé "
            "et le seuil opérationnel utilisé."
        )

    elif taux_signale >= 0.25:

        st.info(
            "Une proportion importante des dossiers est signalée. "
            "Une analyse par catégorie, agence et objet du prêt "
            "peut être utile dans le module OLAP."
        )

    else:

        st.success(
            "Le taux global de dossiers signalés reste inférieur "
            "à 25 %."
        )