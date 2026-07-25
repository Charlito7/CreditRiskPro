from __future__ import annotations

import streamlit as st

from components.layout import afficher_titre_section

from services.prediction import comparer_modeles

from services.utils import (
    calculer_ratio_pret_revenu,
    formater_montant,
    formater_pourcentage,
    traduire_categorie_risque,
)

from services.validation import valider_dossier


# ============================================================
# En-tête
# ============================================================

afficher_titre_section(
    titre="Comparer les modèles",
    description=(
        "Évaluez un même dossier avec le modèle utilisant "
        "loan_grade et avec le modèle autonome sans loan_grade."
    ),
)


# ============================================================
# Explication méthodologique
# ============================================================

st.info(
    "La comparaison mesure l’effet de l’information apportée "
    "par loan_grade. Elle ne signifie pas qu’un modèle est "
    "automatiquement correct et l’autre incorrect."
)


# ============================================================
# Formulaire de comparaison
# ============================================================

with st.form(
    key="formulaire_comparaison_modeles"
):

    st.subheader(
        "Profil du demandeur"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        person_age = st.number_input(
            "Âge",
            min_value=18,
            max_value=100,
            value=30,
            step=1,
        )

    with col2:

        person_income = st.number_input(
            "Revenu annuel",
            min_value=1.0,
            max_value=10_000_000.0,
            value=55_000.0,
            step=1_000.0,
            format="%.0f",
        )

    with col3:

        anciennete_maximum = max(
            0,
            person_age - 14,
        )

        person_emp_length = st.number_input(
            "Ancienneté professionnelle",
            min_value=0.0,
            max_value=float(
                anciennete_maximum
            ),
            value=min(
                4.0,
                float(
                    anciennete_maximum
                ),
            ),
            step=1.0,
        )

    person_home_ownership = st.selectbox(
        "Statut de logement",
        options=[
            "RENT",
            "MORTGAGE",
            "OWN",
            "OTHER",
        ],
        format_func=lambda valeur: {
            "RENT": "Locataire",
            "MORTGAGE": "Propriétaire avec hypothèque",
            "OWN": "Propriétaire sans hypothèque",
            "OTHER": "Autre",
        }[valeur],
    )

    st.subheader(
        "Caractéristiques du prêt"
    )

    col4, col5, col6 = st.columns(3)

    with col4:

        loan_amnt = st.number_input(
            "Montant du prêt",
            min_value=1.0,
            max_value=10_000_000.0,
            value=8_000.0,
            step=500.0,
            format="%.0f",
        )

    with col5:

        loan_int_rate = st.number_input(
            "Taux d’intérêt annuel (%)",
            min_value=0.0,
            max_value=100.0,
            value=10.99,
            step=0.1,
            format="%.2f",
        )

    with col6:

        loan_grade = st.selectbox(
            "Grade de crédit",
            options=[
                "A",
                "B",
                "C",
                "D",
                "E",
                "F",
                "G",
            ],
            index=1,
        )

    loan_intent = st.selectbox(
        "Objet du prêt",
        options=[
            "PERSONAL",
            "EDUCATION",
            "MEDICAL",
            "VENTURE",
            "HOMEIMPROVEMENT",
            "DEBTCONSOLIDATION",
        ],
        format_func=lambda valeur: {
            "PERSONAL": "Dépenses personnelles",
            "EDUCATION": "Éducation",
            "MEDICAL": "Santé",
            "VENTURE": "Projet entrepreneurial",
            "HOMEIMPROVEMENT": "Amélioration du logement",
            "DEBTCONSOLIDATION": "Consolidation de dettes",
        }[valeur],
    )

    st.subheader(
        "Historique de crédit"
    )

    col7, col8 = st.columns(2)

    with col7:

        cb_person_default_on_file = st.selectbox(
            "Défaut antérieur enregistré ?",
            options=[
                "N",
                "Y",
            ],
            format_func=lambda valeur: (
                "Non"
                if valeur == "N"
                else "Oui"
            ),
        )

    with col8:

        historique_maximum = max(
            0,
            person_age - 18,
        )

        cb_person_cred_hist_length = st.number_input(
            "Ancienneté de l’historique de crédit",
            min_value=0,
            max_value=historique_maximum,
            value=min(
                4,
                historique_maximum,
            ),
            step=1,
        )

    comparer = st.form_submit_button(
        "Comparer les deux modèles",
        type="primary",
        use_container_width=True,
    )


# ============================================================
# Construction des données
# ============================================================

loan_percent_income = (
    calculer_ratio_pret_revenu(
        montant_pret=loan_amnt,
        revenu_annuel=person_income,
    )
)

donnees_communes = {
    "person_age": person_age,
    "person_income": person_income,
    "person_home_ownership": (
        person_home_ownership
    ),
    "person_emp_length": (
        person_emp_length
    ),
    "loan_intent": loan_intent,
    "loan_amnt": loan_amnt,
    "loan_int_rate": loan_int_rate,
    "loan_percent_income": (
        loan_percent_income
    ),
    "cb_person_default_on_file": (
        cb_person_default_on_file
    ),
    "cb_person_cred_hist_length": (
        cb_person_cred_hist_length
    ),
}

donnees_avec_grade = (
    donnees_communes.copy()
)

donnees_avec_grade[
    "loan_grade"
] = loan_grade

donnees_sans_grade = (
    donnees_communes.copy()
)


# ============================================================
# Résultat de comparaison
# ============================================================

if comparer:

    validation_avec = valider_dossier(
        donnees=donnees_avec_grade,
        avec_grade=True,
    )

    validation_sans = valider_dossier(
        donnees=donnees_sans_grade,
        avec_grade=False,
    )

    erreurs = (
        validation_avec.erreurs
        + validation_sans.erreurs
    )

    if erreurs:

        st.error(
            "Le dossier contient des données invalides."
        )

        for erreur in sorted(
            set(erreurs)
        ):
            st.write(
                f"❌ {erreur}"
            )

    else:

        try:

            comparaison = comparer_modeles(
                donnees_avec_grade=(
                    donnees_avec_grade
                ),
                donnees_sans_grade=(
                    donnees_sans_grade
                ),
            )

            resultat_avec = comparaison[
                "avec_grade"
            ]

            resultat_sans = comparaison[
                "sans_grade"
            ]

            st.subheader(
                "Résultats comparés"
            )

            col_avec, col_sans = (
                st.columns(2)
            )

            with col_avec:

                with st.container(
                    border=True
                ):

                    st.markdown(
                        "### Avec loan_grade"
                    )

                    st.metric(
                        "Probabilité de défaut",
                        formater_pourcentage(
                            resultat_avec[
                                "probabilite_defaut"
                            ],
                            decimales=2,
                        ),
                    )

                    st.metric(
                        "Indice de solvabilité",
                        (
                            f"{resultat_avec['indice_risque']} "
                            "/ 1000"
                        ),
                    )

                    st.metric(
                        "Catégorie",
                        traduire_categorie_risque(
                            resultat_avec[
                                "categorie_risque"
                            ]
                        ),
                    )

                    st.metric(
                        "Seuil",
                        formater_pourcentage(
                            resultat_avec[
                                "seuil"
                            ],
                            decimales=2,
                        ),
                    )

            with col_sans:

                with st.container(
                    border=True
                ):

                    st.markdown(
                        "### Sans loan_grade"
                    )

                    st.metric(
                        "Probabilité de défaut",
                        formater_pourcentage(
                            resultat_sans[
                                "probabilite_defaut"
                            ],
                            decimales=2,
                        ),
                    )

                    st.metric(
                        "Indice de solvabilité",
                        (
                            f"{resultat_sans['indice_risque']} "
                            "/ 1000"
                        ),
                    )

                    st.metric(
                        "Catégorie",
                        traduire_categorie_risque(
                            resultat_sans[
                                "categorie_risque"
                            ]
                        ),
                    )

                    st.metric(
                        "Seuil",
                        formater_pourcentage(
                            resultat_sans[
                                "seuil"
                            ],
                            decimales=2,
                        ),
                    )

            st.subheader(
                "Analyse de l’écart"
            )

            col1, col2, col3 = st.columns(
                3
            )

            with col1:

                st.metric(
                    "Écart de probabilité",
                    formater_pourcentage(
                        comparaison[
                            "ecart_absolu"
                        ],
                        decimales=2,
                    ),
                )

            with col2:

                st.metric(
                    "Changement de catégorie",
                    (
                        "Oui"
                        if comparaison[
                            "changement_categorie"
                        ]
                        else "Non"
                    ),
                )

            with col3:

                st.metric(
                    "Changement de signal",
                    (
                        "Oui"
                        if comparaison[
                            "changement_classe"
                        ]
                        else "Non"
                    ),
                )

            if (
                resultat_avec[
                    "probabilite_defaut"
                ]
                < resultat_sans[
                    "probabilite_defaut"
                ]
            ):

                st.info(
                    "Dans ce dossier, l’utilisation de loan_grade "
                    "réduit la probabilité de défaut estimée."
                )

            elif (
                resultat_avec[
                    "probabilite_defaut"
                ]
                > resultat_sans[
                    "probabilite_defaut"
                ]
            ):

                st.info(
                    "Dans ce dossier, l’utilisation de loan_grade "
                    "augmente la probabilité de défaut estimée."
                )

            else:

                st.info(
                    "Les deux modèles produisent la même probabilité."
                )

            with st.expander(
                "Voir les données communes"
            ):

                st.json(
                    donnees_communes
                )

        except Exception as erreur:

            st.error(
                "La comparaison n’a pas pu être effectuée."
            )

            st.exception(
                erreur
            )