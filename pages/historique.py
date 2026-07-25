from __future__ import annotations

import pandas as pd
import streamlit as st

from components.layout import afficher_titre_section

from services.database import (
    initialiser_base,
    lire_evaluation,
    lire_historique,
)

from services.utils import (
    formater_pourcentage,
    traduire_categorie_risque,
)


# ============================================================
# Initialisation
# ============================================================

initialiser_base()


# ============================================================
# En-tête
# ============================================================

afficher_titre_section(
    titre="Historique des évaluations",
    description=(
        "Consultez, filtrez et exportez les dossiers "
        "ayant déjà été analysés."
    ),
)


# ============================================================
# Chargement des données
# ============================================================

try:

    historique = lire_historique()

except Exception as erreur:

    st.error(
        "Impossible de charger l’historique."
    )

    st.exception(
        erreur
    )

    historique = pd.DataFrame()


# ============================================================
# Cas sans données
# ============================================================

if historique.empty:

    st.info(
        "Aucune évaluation n’est encore enregistrée."
    )

    st.stop()


# ============================================================
# Filtres
# ============================================================

st.subheader(
    "Filtres"
)

col1, col2, col3 = st.columns(3)

with col1:

    modes_disponibles = sorted(
        historique[
            "mode_evaluation"
        ].dropna().unique()
    )

    modes_selectionnes = st.multiselect(
        "Mode d’évaluation",
        options=modes_disponibles,
        default=modes_disponibles,
        format_func=lambda mode: {
            "avec_grade": "Avec grade",
            "sans_grade": "Sans grade",
        }.get(
            mode,
            mode,
        ),
    )

with col2:

    categories_disponibles = sorted(
        historique[
            "categorie_risque"
        ].dropna().unique()
    )

    categories_selectionnees = (
        st.multiselect(
            "Catégorie de risque",
            options=categories_disponibles,
            default=categories_disponibles,
            format_func=(
                traduire_categorie_risque
            ),
        )
    )

with col3:

    agences_disponibles = sorted(
        historique[
            "agence"
        ].dropna().astype(str).unique()
    )

    agences_selectionnees = st.multiselect(
        "Agence",
        options=agences_disponibles,
        default=agences_disponibles,
    )


# ============================================================
# Application des filtres
# ============================================================

historique_filtre = historique.copy()

if modes_selectionnes:

    historique_filtre = historique_filtre[
        historique_filtre[
            "mode_evaluation"
        ].isin(
            modes_selectionnes
        )
    ]

if categories_selectionnees:

    historique_filtre = historique_filtre[
        historique_filtre[
            "categorie_risque"
        ].isin(
            categories_selectionnees
        )
    ]

if agences_selectionnees:

    historique_filtre = historique_filtre[
        historique_filtre[
            "agence"
        ].astype(str).isin(
            agences_selectionnees
        )
    ]


# ============================================================
# KPI
# ============================================================

st.subheader(
    "Résumé"
)

nombre = len(
    historique_filtre
)

probabilite_moyenne = (
    historique_filtre[
        "probabilite_defaut"
    ].mean()
    if nombre > 0
    else 0
)

taux_signale = (
    historique_filtre[
        "classe_predite"
    ].mean()
    if nombre > 0
    else 0
)

indice_moyen = (
    historique_filtre[
        "indice_risque"
    ].mean()
    if nombre > 0
    else 0
)

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Évaluations",
    nombre,
)

k2.metric(
    "Probabilité moyenne",
    formater_pourcentage(
        probabilite_moyenne
    ),
)

k3.metric(
    "Taux signalé",
    formater_pourcentage(
        taux_signale
    ),
)

k4.metric(
    "Indice moyen",
    f"{indice_moyen:.0f} / 1000",
)


# ============================================================
# Tableau
# ============================================================

st.subheader(
    "Liste des évaluations"
)

tableau = historique_filtre.copy()

tableau[
    "probabilite_defaut"
] = tableau[
    "probabilite_defaut"
].map(
    lambda valeur: (
        f"{valeur:.2%}"
    )
)

tableau[
    "seuil"
] = tableau[
    "seuil"
].map(
    lambda valeur: (
        f"{valeur:.2%}"
    )
)

tableau[
    "categorie_risque"
] = tableau[
    "categorie_risque"
].map(
    traduire_categorie_risque
)

tableau[
    "mode_evaluation"
] = tableau[
    "mode_evaluation"
].replace(
    {
        "avec_grade": "Avec grade",
        "sans_grade": "Sans grade",
    }
)

tableau[
    "classe_predite"
] = tableau[
    "classe_predite"
].replace(
    {
        0: "Non signalé",
        1: "Signalé",
    }
)

colonnes = [
    "evaluation_id",
    "date_evaluation",
    "reference_dossier",
    "identifiant_client",
    "agence",
    "analyste",
    "mode_evaluation",
    "probabilite_defaut",
    "indice_risque",
    "categorie_risque",
    "seuil",
    "classe_predite",
]

colonnes = [
    colonne
    for colonne in colonnes
    if colonne in tableau.columns
]

st.dataframe(
    tableau[
        colonnes
    ],
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# Export CSV
# ============================================================

csv = historique_filtre.to_csv(
    index=False
).encode(
    "utf-8-sig"
)

st.download_button(
    label="Exporter l’historique filtré en CSV",
    data=csv,
    file_name="historique_creditrisk.csv",
    mime="text/csv",
)


# ============================================================
# Consultation détaillée
# ============================================================

st.subheader(
    "Consulter une évaluation"
)

identifiants = (
    historique_filtre[
        "evaluation_id"
    ]
    .astype(int)
    .tolist()
)

if identifiants:

    evaluation_selectionnee = st.selectbox(
        "Identifiant de l’évaluation",
        options=identifiants,
    )

    if st.button(
        "Afficher le détail"
    ):

        detail = lire_evaluation(
            evaluation_id=int(
                evaluation_selectionnee
            )
        )

        if detail is None:

            st.warning(
                "Évaluation introuvable."
            )

        else:

            col1, col2 = st.columns(2)

            with col1:

                with st.container(
                    border=True
                ):

                    st.markdown(
                        "### Informations administratives"
                    )

                    st.json(
                        detail[
                            "donnees_administratives"
                        ]
                    )

            with col2:

                with st.container(
                    border=True
                ):

                    st.markdown(
                        "### Variables du modèle"
                    )

                    st.json(
                        detail[
                            "donnees_modele"
                        ]
                    )