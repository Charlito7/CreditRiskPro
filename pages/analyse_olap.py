from __future__ import annotations

import pandas as pd
import streamlit as st

from components.layout import afficher_titre_section

from services.database import (
    initialiser_base,
    lire_historique,
)

from services.olap import (
    ajouter_dimensions_temporelles,
    appliquer_filtres,
    calculer_kpi,
    construire_tableau_olap,
)

from services.utils import (
    formater_pourcentage,
)


# ============================================================
# Initialisation
# ============================================================

initialiser_base()


# ============================================================
# En-tête
# ============================================================

afficher_titre_section(
    titre="Analyse OLAP",
    description=(
        "Explorez les évaluations selon plusieurs dimensions, "
        "mesures et filtres."
    ),
)


# ============================================================
# Chargement
# ============================================================

try:

    donnees = lire_historique()

except Exception as erreur:

    st.error(
        "Impossible de charger les données OLAP."
    )

    st.exception(
        erreur
    )

    donnees = pd.DataFrame()


if donnees.empty:

    st.info(
        "Aucune donnée n’est disponible pour l’analyse OLAP."
    )

    st.stop()


# ============================================================
# Dimensions temporelles
# ============================================================

donnees = ajouter_dimensions_temporelles(
    donnees=donnees,
    colonne_date="date_evaluation",
)


# ============================================================
# Filtres Slice / Dice
# ============================================================

st.subheader(
    "Filtres Slice et Dice"
)

col1, col2, col3 = st.columns(3)

with col1:

    modes = sorted(
        donnees[
            "mode_evaluation"
        ].dropna().unique()
    )

    filtre_modes = st.multiselect(
        "Mode",
        options=modes,
        default=modes,
    )

with col2:

    categories = sorted(
        donnees[
            "categorie_risque"
        ].dropna().unique()
    )

    filtre_categories = st.multiselect(
        "Catégorie de risque",
        options=categories,
        default=categories,
    )

with col3:

    agences = sorted(
        donnees[
            "agence"
        ].dropna().astype(str).unique()
    )

    filtre_agences = st.multiselect(
        "Agence",
        options=agences,
        default=agences,
    )


filtres = {}

if filtre_modes:
    filtres[
        "mode_evaluation"
    ] = filtre_modes

if filtre_categories:
    filtres[
        "categorie_risque"
    ] = filtre_categories

if filtre_agences:
    filtres[
        "agence"
    ] = filtre_agences


donnees_filtrees = appliquer_filtres(
    donnees=donnees,
    filtres=filtres,
)


# ============================================================
# KPI
# ============================================================

kpi = calculer_kpi(
    donnees_filtrees
)

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Nombre d’évaluations",
    kpi[
        "nombre_dossiers"
    ],
)

k2.metric(
    "Probabilité moyenne",
    formater_pourcentage(
        kpi[
            "probabilite_moyenne"
        ]
    ),
)

k3.metric(
    "Indice moyen",
    f"{kpi['indice_moyen']:.0f} / 1000",
)

k4.metric(
    "Taux signalé",
    formater_pourcentage(
        kpi[
            "taux_signale"
        ]
    ),
)


# ============================================================
# Configuration du cube
# ============================================================

st.subheader(
    "Construction du tableau OLAP"
)

dimensions_disponibles = [
    "agence",
    "analyste",
    "mode_evaluation",
    "categorie_risque",
    "classe_predite",
    "annee",
    "trimestre",
    "mois",
    "jour",
]

dimensions_disponibles = [
    dimension
    for dimension in dimensions_disponibles
    if dimension in donnees_filtrees.columns
]

col_dimension_1, col_dimension_2, col_mesure = (
    st.columns(3)
)

with col_dimension_1:

    dimension_ligne = st.selectbox(
        "Dimension des lignes",
        options=dimensions_disponibles,
        index=0,
    )

with col_dimension_2:

    options_colonnes = [
        "Aucune"
    ] + dimensions_disponibles

    dimension_colonne_affichee = (
        st.selectbox(
            "Dimension des colonnes",
            options=options_colonnes,
            index=0,
        )
    )

    dimension_colonne = (
        None
        if dimension_colonne_affichee
        == "Aucune"
        else dimension_colonne_affichee
    )

with col_mesure:

    mesure = st.selectbox(
        "Mesure",
        options=[
            "nombre_dossiers",
            "probabilite_moyenne",
            "indice_moyen",
            "taux_dossiers_signales",
        ],
        format_func=lambda valeur: {
            "nombre_dossiers": "Nombre de dossiers",
            "probabilite_moyenne": "Probabilité moyenne",
            "indice_moyen": "Indice moyen",
            "taux_dossiers_signales": "Taux signalé",
        }[valeur],
    )


# ============================================================
# Tableau OLAP
# ============================================================

try:

    tableau_olap = construire_tableau_olap(
        donnees=donnees_filtrees,
        dimension_ligne=dimension_ligne,
        dimension_colonne=dimension_colonne,
        mesure=mesure,
        filtres=None,
        ajouter_totaux=True,
    )

    st.dataframe(
        tableau_olap,
        use_container_width=True,
    )

    csv = tableau_olap.to_csv().encode(
        "utf-8-sig"
    )

    st.download_button(
        "Exporter le tableau OLAP",
        data=csv,
        file_name="analyse_olap.csv",
        mime="text/csv",
    )

except Exception as erreur:

    st.error(
        "Le tableau OLAP n’a pas pu être construit."
    )

    st.exception(
        erreur
    )


# ============================================================
# Graphique
# ============================================================

st.subheader(
    "Visualisation"
)

if (
    dimension_colonne is None
    and not donnees_filtrees.empty
):

    if mesure == "nombre_dossiers":

        graphique = (
            donnees_filtrees[
                dimension_ligne
            ]
            .value_counts()
            .rename_axis(
                dimension_ligne
            )
            .reset_index(
                name="valeur"
            )
        )

    else:

        colonne_mesure = {
            "probabilite_moyenne": (
                "probabilite_defaut"
            ),
            "indice_moyen": (
                "indice_risque"
            ),
            "taux_dossiers_signales": (
                "classe_predite"
            ),
        }[mesure]

        graphique = (
            donnees_filtrees
            .groupby(
                dimension_ligne,
                dropna=False,
            )[
                colonne_mesure
            ]
            .mean()
            .reset_index(
                name="valeur"
            )
        )

    st.bar_chart(
        graphique,
        x=dimension_ligne,
        y="valeur",
        use_container_width=True,
    )

else:

    st.caption(
        "Le graphique simple est affiché lorsque "
        "la dimension des colonnes est définie sur Aucune."
    )