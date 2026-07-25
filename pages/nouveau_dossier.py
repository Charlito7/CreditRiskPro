from __future__ import annotations

import streamlit as st

from components.formulaire import (
    afficher_formulaire_multi_etapes,
)

from components.layout import (
    afficher_titre_section,
)

from services.database import (
    enregistrer_dossier,
    enregistrer_evaluation,
)

from services.prediction import (
    predire_risque,
)

from services.state import (
    sauvegarder_resultat_session,
)

from services.validation import (
    valider_dossier,
)


# ============================================================
# 1. En-tête de la page
# ============================================================

afficher_titre_section(
    titre="Nouveau dossier",
    description=(
        "Saisissez progressivement les informations du demandeur, "
        "vérifiez leur cohérence, puis lancez l’évaluation "
        "du risque de défaut."
    ),
)


# ============================================================
# 2. Affichage du formulaire multiétape
# ============================================================

(
    analyser,
    donnees_administratives,
    donnees_modele,
) = afficher_formulaire_multi_etapes()


# ============================================================
# 3. Traitement après clic sur « Analyser le dossier »
# ============================================================

if analyser:

    mode = donnees_administratives[
        "mode_evaluation"
    ]

    # --------------------------------------------------------
    # Validation backend complète
    # --------------------------------------------------------

    validation = valider_dossier(
        donnees=donnees_modele,
        avec_grade=(
            mode == "avec_grade"
        ),
    )

    # ========================================================
    # 4. Dossier invalide
    # ========================================================

    if not validation.valide:

        st.error(
            "Le dossier contient des données invalides. "
            "La prédiction n’a pas été lancée."
        )

        for erreur in validation.erreurs:
            st.write(
                f"❌ {erreur}"
            )

    # ========================================================
    # 5. Dossier valide
    # ========================================================

    else:

        # ----------------------------------------------------
        # Avertissements importants
        # ----------------------------------------------------
        #
        # Les avertissements restent directement visibles,
        # car ils nécessitent l'attention de l'analyste.

        for avertissement in validation.avertissements:
            st.warning(
                avertissement
            )

        # ----------------------------------------------------
        # Informations sur le domaine d'entraînement
        # ----------------------------------------------------
        #
        # Les informations sont regroupées afin d'éviter
        # plusieurs grands encadrés bleus sur la page.

        if validation.informations:

            with st.expander(
                "Position du dossier par rapport "
                "aux données d’entraînement"
            ):

                st.caption(
                    "Ces informations indiquent comment les valeurs "
                    "du dossier se positionnent par rapport au jeu "
                    "de données utilisé pour entraîner le modèle."
                )

                for information in validation.informations:

                    st.write(
                        f"• {information}"
                    )

        try:

            # =================================================
            # 6. Prédiction
            # =================================================

            resultat = predire_risque(
                donnees=donnees_modele,
                mode=mode,
            )

            # =================================================
            # 7. Enregistrement du dossier
            # =================================================

            dossier_id = enregistrer_dossier(
                donnees_administratives=(
                    donnees_administratives
                )
            )

            # =================================================
            # 8. Enregistrement de l'évaluation
            # =================================================

            evaluation_id = enregistrer_evaluation(
                dossier_id=dossier_id,
                donnees_modele=donnees_modele,
                resultat=resultat,
            )

            # =================================================
            # 9. Sauvegarde dans la session
            # =================================================

            sauvegarder_resultat_session(
                donnees_administratives=(
                    donnees_administratives
                ),
                donnees_modele=donnees_modele,
                resultat=resultat,
                evaluation_id=evaluation_id,
            )

            # =================================================
            # 10. Confirmation
            # =================================================

            st.success(
                "L’évaluation a été réalisée et enregistrée "
                "avec succès."
            )

            # =================================================
            # 11. Résultat principal
            # =================================================

            st.subheader(
                "Résultat de l’évaluation"
            )

            col1, col2, col3, col4 = st.columns(
                4
            )

            with col1:

                st.metric(
                    label="Probabilité de défaut",
                    value=(
                        f"{resultat['probabilite_defaut']:.2%}"
                    ),
                )

            with col2:

                st.metric(
                    label="Indice de risque",
                    value=(
                        f"{resultat['indice_risque']} / 1000"
                    ),
                )

            with col3:

                categorie_affichee = (
                    resultat[
                        "categorie_risque"
                    ]
                    .replace(
                        "_",
                        " ",
                    )
                    .title()
                )

                st.metric(
                    label="Catégorie",
                    value=categorie_affichee,
                )

            with col4:

                st.metric(
                    label="Seuil utilisé",
                    value=(
                        f"{resultat['seuil']:.2%}"
                    ),
                )

            # =================================================
            # 12. Interprétation du résultat
            # =================================================

            if resultat["classe_predite"] == 1:

                st.warning(
                    "Le modèle signale ce dossier comme présentant "
                    "un risque de défaut au seuil actuellement "
                    "configuré."
                )

            else:

                st.info(
                    "Le modèle ne signale pas ce dossier comme "
                    "présentant un risque de défaut au seuil "
                    "actuellement configuré."
                )

            # =================================================
            # 13. Informations techniques
            # =================================================

            with st.expander(
                "Voir les informations techniques"
            ):

                st.write(
                    f"**Mode utilisé :** "
                    f"{resultat['mode']}"
                )

                st.write(
                    f"**Algorithme :** "
                    f"{resultat.get('algorithme', 'XGBoost')}"
                )

                st.write(
                    f"**Version du modèle :** "
                    f"{resultat.get('version_modele', 'Non précisée')}"
                )

                st.write(
                    f"**Identifiant de l’évaluation :** "
                    f"{evaluation_id}"
                )

                if resultat["classe_predite"] == 1:

                    st.write(
                        "**Classe prédite :** "
                        "1 — Dossier signalé"
                    )

                else:

                    st.write(
                        "**Classe prédite :** "
                        "0 — Dossier non signalé"
                    )

            # =================================================
            # 14. Données transmises au modèle
            # =================================================

            with st.expander(
                "Voir les données utilisées par le modèle"
            ):

                st.dataframe(
                    resultat["dataframe"],
                    use_container_width=True,
                    hide_index=True,
                )

            # =================================================
            # 15. Information sur la suite du développement
            # =================================================

            st.info(
                "La prochaine étape ajoutera une page complète "
                "de résultat avec jauge de risque, recommandation "
                "métier, décision humaine et rapport PDF."
            )

        # ====================================================
        # 16. Modèle ou manifeste absent
        # ====================================================

        except FileNotFoundError as erreur:

            st.error(
                "Un fichier nécessaire à la prédiction "
                "est introuvable."
            )

            st.code(
                str(erreur)
            )

            st.info(
                "Vérifiez la présence des fichiers suivants "
                "dans le dossier modeles_scoring :\n\n"
                "- xgboost_avec_loan_grade.joblib\n"
                "- xgboost_sans_loan_grade.joblib\n"
                "- manifest_modeles.json"
            )

        # ====================================================
        # 17. Configuration incomplète
        # ====================================================

        except KeyError as erreur:

            st.error(
                "La configuration du modèle est incomplète."
            )

            st.code(
                str(erreur)
            )

        # ====================================================
        # 18. Valeur invalide
        # ====================================================

        except ValueError as erreur:

            st.error(
                "Une valeur ou une configuration est invalide."
            )

            st.code(
                str(erreur)
            )

        # ====================================================
        # 19. Erreur inattendue
        # ====================================================

        except Exception as erreur:

            st.error(
                "Une erreur inattendue est survenue pendant "
                "la prédiction ou l’enregistrement."
            )

            st.exception(
                erreur
            )