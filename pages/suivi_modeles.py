from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from components.layout import afficher_titre_section

from config import (
    MANIFEST_PATH,
    MODELS_DIR,
)

from services.database import (
    initialiser_base,
    lire_historique,
)

from services.prediction import (
    charger_manifest,
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
    titre="Suivi des modèles",
    description=(
        "Contrôlez l’état des fichiers, les versions, "
        "les seuils et les performances enregistrées."
    ),
)


# ============================================================
# État du manifeste
# ============================================================

st.subheader(
    "État des fichiers"
)

if MANIFEST_PATH.exists():

    st.success(
        "Le manifeste des modèles est disponible."
    )

else:

    st.error(
        "Le fichier manifest_modeles.json est absent."
    )


try:

    manifest = charger_manifest()

except Exception as erreur:

    st.error(
        "Le manifeste ne peut pas être chargé."
    )

    st.exception(
        erreur
    )

    st.stop()


# ============================================================
# Cartes des modèles
# ============================================================

modes = manifest.get(
    "modes",
    {}
)

colonnes = st.columns(
    max(
        len(modes),
        1,
    )
)

for colonne, (
    mode,
    configuration,
) in zip(
    colonnes,
    modes.items(),
):

    with colonne:

        with st.container(
            border=True
        ):

            st.markdown(
                f"### {mode.replace('_', ' ').title()}"
            )

            fichier_modele = (
                MODELS_DIR
                / configuration.get(
                    "fichier_modele",
                    "",
                )
            )

            if fichier_modele.exists():

                st.success(
                    "Fichier du modèle disponible"
                )

            else:

                st.error(
                    "Fichier du modèle absent"
                )

            st.write(
                "**Algorithme :** "
                + str(
                    configuration.get(
                        "algorithme",
                        "Non précisé",
                    )
                )
            )

            st.write(
                "**Version :** "
                + str(
                    configuration.get(
                        "version",
                        "Non précisée",
                    )
                )
            )

            st.write(
                "**Seuil opérationnel :** "
                + formater_pourcentage(
                    float(
                        configuration.get(
                            "seuil",
                            0.5,
                        )
                    ),
                    decimales=2,
                )
            )

            variables = configuration.get(
                "variables_attendues",
                [],
            )

            st.write(
                f"**Nombre de variables :** "
                f"{len(variables)}"
            )

            with st.expander(
                "Variables attendues"
            ):

                for variable in variables:
                    st.write(
                        f"• `{variable}`"
                    )


# ============================================================
# Métriques du manifeste
# ============================================================

st.subheader(
    "Performances enregistrées"
)

st.caption(
    "Les métriques ci-dessous proviennent de l’évaluation finale du dernier notebook, "
    "après application du seuil propre à chaque modèle."
)

lignes_metriques = []

for mode, configuration in modes.items():

    metriques = configuration.get(
        "metriques_test",
        configuration.get("metriques", {}),
    )

    ligne = {
        "mode": mode,
        "ROC-AUC": metriques.get("ROC-AUC", metriques.get("roc_auc")),
        "PR-AUC": metriques.get("PR-AUC", metriques.get("pr_auc")),
        "Accuracy": metriques.get("Accuracy", metriques.get("accuracy")),
        "Precision": metriques.get("Precision", metriques.get("precision")),
        "Recall": metriques.get("Recall", metriques.get("recall")),
        "F1": metriques.get("F1-score", metriques.get("f1")),
        "Brier": metriques.get("Brier", metriques.get("brier")),
    }

    lignes_metriques.append(
        ligne
    )


tableau_metriques = pd.DataFrame(
    lignes_metriques
)

if tableau_metriques.empty:

    st.info(
        "Aucune métrique n’est enregistrée dans le manifeste."
    )

else:

    st.dataframe(
        tableau_metriques,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# Analyse des prédictions enregistrées
# ============================================================

st.subheader(
    "Comportement en utilisation"
)

historique = lire_historique()

if historique.empty:

    st.info(
        "Aucune prédiction n’est encore enregistrée."
    )

else:

    analyse_modes = (
        historique
        .groupby(
            "mode_evaluation"
        )
        .agg(
            nombre_predictions=(
                "evaluation_id",
                "count",
            ),
            probabilite_moyenne=(
                "probabilite_defaut",
                "mean",
            ),
            indice_moyen=(
                "indice_risque",
                "mean",
            ),
            taux_signale=(
                "classe_predite",
                "mean",
            ),
        )
        .reset_index()
    )

    st.dataframe(
        analyse_modes,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Ces indicateurs décrivent les dossiers analysés "
        "par l’application. Ils ne mesurent pas encore la "
        "performance réelle, car les défauts observés après "
        "octroi ne sont pas encore enregistrés."
    )


# ============================================================
# Manifeste brut
# ============================================================

with st.expander(
    "Voir le manifeste complet"
):

    st.json(
        manifest
    )