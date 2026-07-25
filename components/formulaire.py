from __future__ import annotations

from typing import Any

import streamlit as st

from config import (
    LIBELLES_MODES,
    MODE_AVEC_GRADE,
    MODE_SANS_GRADE,
)

from services.utils import (
    calculer_ratio_pret_revenu,
    formater_montant,
)


# ============================================================
# Paramètres du formulaire
# ============================================================

NOMBRE_ETAPES = 5

NOMS_ETAPES = {
    1: "Informations générales",
    2: "Profil du demandeur",
    3: "Caractéristiques du prêt",
    4: "Historique de crédit",
    5: "Vérification",
}


# ============================================================
# Initialisation du formulaire
# ============================================================

def initialiser_formulaire() -> None:
    """
    Initialise les variables nécessaires au fonctionnement
    du formulaire multiétape.

    Streamlit réexécute toute la page après chaque interaction.
    st.session_state permet de conserver les informations saisies.
    """

    if "etape_formulaire" not in st.session_state:
        st.session_state["etape_formulaire"] = 1

    if "formulaire_credit" not in st.session_state:
        st.session_state["formulaire_credit"] = {
            # Informations générales
            "reference_dossier": "",
            "identifiant_client": "",
            "agence": "",
            "analyste": "",

            # Mode de scoring
            "mode_evaluation": MODE_AVEC_GRADE,

            # Profil du demandeur
            "person_age": 30,
            "person_income": 55_000.0,
            "person_emp_length": 4.0,
            "person_home_ownership": "RENT",

            # Prêt
            "loan_amnt": 8_000.0,
            "loan_int_rate": 10.99,
            "loan_intent": "PERSONAL",
            "loan_grade": "B",

            # Historique
            "cb_person_default_on_file": "N",
            "cb_person_cred_hist_length": 4,
        }


def reinitialiser_formulaire() -> None:
    """
    Supprime les données du formulaire actuel
    et revient à la première étape.
    """

    st.session_state.pop(
        "formulaire_credit",
        None,
    )

    st.session_state["etape_formulaire"] = 1

    initialiser_formulaire()


# ============================================================
# Navigation
# ============================================================

def aller_etape_suivante() -> None:
    """
    Passe à l'étape suivante sans dépasser l'étape finale.
    """

    st.session_state["etape_formulaire"] = min(
        NOMBRE_ETAPES,
        st.session_state["etape_formulaire"] + 1,
    )


def aller_etape_precedente() -> None:
    """
    Revient à l'étape précédente.
    """

    st.session_state["etape_formulaire"] = max(
        1,
        st.session_state["etape_formulaire"] - 1,
    )


# ============================================================
# Affichage de la progression
# ============================================================

def afficher_progression() -> None:
    """
    Affiche la position actuelle dans le parcours.
    """

    etape = st.session_state["etape_formulaire"]

    progression = etape / NOMBRE_ETAPES

    st.progress(
        progression,
        text=(
            f"Étape {etape} sur {NOMBRE_ETAPES} — "
            f"{NOMS_ETAPES[etape]}"
        ),
    )

    colonnes = st.columns(
        NOMBRE_ETAPES
    )

    for numero, colonne in enumerate(
        colonnes,
        start=1,
    ):
        with colonne:

            if numero < etape:
                st.caption(
                    f"✅ {numero}. {NOMS_ETAPES[numero]}"
                )

            elif numero == etape:
                st.caption(
                    f"🔵 {numero}. {NOMS_ETAPES[numero]}"
                )

            else:
                st.caption(
                    f"⚪ {numero}. {NOMS_ETAPES[numero]}"
                )


# ============================================================
# Étape 1 — Informations générales
# ============================================================

def afficher_etape_informations_generales() -> None:
    """
    Affiche les informations administratives du dossier.

    Ces informations ne sont pas envoyées au modèle.
    Elles servent à la traçabilité.
    """

    donnees = st.session_state["formulaire_credit"]

    st.subheader(
        "Informations générales"
    )

    st.caption(
        "Ces informations permettent d'identifier le dossier "
        "et l'utilisateur responsable de l'analyse."
    )

    col1, col2 = st.columns(2)

    with col1:
        donnees["reference_dossier"] = st.text_input(
            "Référence du dossier",
            value=donnees["reference_dossier"],
            placeholder="Exemple : DOS-2026-001",
            help=(
                "Identifiant unique attribué au dossier "
                "par l'institution."
            ),
        )

    with col2:
        donnees["identifiant_client"] = st.text_input(
            "Identifiant du client",
            value=donnees["identifiant_client"],
            placeholder="Exemple : CLI-000154",
            help=(
                "Identifiant interne du demandeur. "
                "Évitez de saisir des données personnelles inutiles."
            ),
        )

    col3, col4 = st.columns(2)

    with col3:
        donnees["agence"] = st.text_input(
            "Agence ou caisse",
            value=donnees["agence"],
            placeholder="Exemple : Agence centrale",
        )

    with col4:
        donnees["analyste"] = st.text_input(
            "Analyste responsable",
            value=donnees["analyste"],
            placeholder="Nom ou identifiant de l'analyste",
        )

    st.markdown("#### Mode d'évaluation")

    mode_affiche = st.radio(
        "Choisissez le modèle à utiliser",
        options=[
            MODE_AVEC_GRADE,
            MODE_SANS_GRADE,
        ],
        format_func=lambda mode: LIBELLES_MODES[mode],
        index=(
            0
            if donnees["mode_evaluation"] == MODE_AVEC_GRADE
            else 1
        ),
        horizontal=True,
        help=(
            "Le modèle avec grade utilise loan_grade. "
            "Le modèle sans grade effectue une évaluation autonome."
        ),
    )

    donnees["mode_evaluation"] = (
        mode_affiche
    )


# ============================================================
# Étape 2 — Profil du demandeur
# ============================================================

def afficher_etape_profil() -> None:
    """
    Affiche les caractéristiques personnelles et financières
    utilisées par le modèle.
    """

    donnees = st.session_state["formulaire_credit"]

    st.subheader(
        "Profil du demandeur"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        donnees["person_age"] = st.number_input(
            "Âge",
            min_value=18,
            max_value=100,
            value=int(
                donnees["person_age"]
            ),
            step=1,
            help="Le demandeur doit être majeur.",
        )

    with col2:
        donnees["person_income"] = st.number_input(
            "Revenu annuel",
            min_value=1.0,
            max_value=10_000_000.0,
            value=float(
                donnees["person_income"]
            ),
            step=1_000.0,
            format="%.0f",
            help=(
                "Le revenu doit être exprimé dans la même unité "
                "monétaire que le montant du prêt."
            ),
        )

    with col3:
        anciennete_maximale = max(
            0,
            donnees["person_age"] - 14,
        )

        valeur_anciennete = min(
            float(
                donnees["person_emp_length"]
            ),
            float(
                anciennete_maximale
            ),
        )

        donnees["person_emp_length"] = st.number_input(
            "Ancienneté professionnelle",
            min_value=0.0,
            max_value=float(
                anciennete_maximale
            ),
            value=valeur_anciennete,
            step=1.0,
            help=(
                "L'ancienneté ne doit pas être supérieure "
                "à l'âge moins 14 ans."
            ),
        )

    donnees["person_home_ownership"] = st.selectbox(
        "Statut de logement",
        options=[
            "RENT",
            "MORTGAGE",
            "OWN",
            "OTHER",
        ],
        index=[
            "RENT",
            "MORTGAGE",
            "OWN",
            "OTHER",
        ].index(
            donnees["person_home_ownership"]
        ),
        format_func=lambda valeur: {
            "RENT": "Locataire",
            "MORTGAGE": "Propriétaire avec hypothèque",
            "OWN": "Propriétaire sans hypothèque",
            "OTHER": "Autre situation",
        }[valeur],
    )

    st.markdown("#### Position par rapport au dataset")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Âge",
            f"{donnees['person_age']} ans",
            help=(
                "La médiane du dataset est proche de 26 ans."
            ),
        )

    with col2:
        st.metric(
            "Revenu annuel",
            formater_montant(
                donnees["person_income"]
            ),
            help=(
                "La médiane du dataset est proche de 55 000."
            ),
        )

    with col3:
        st.metric(
            "Ancienneté",
            f"{donnees['person_emp_length']:.0f} ans",
            help=(
                "La médiane du dataset est proche de 4 ans."
            ),
        )


# ============================================================
# Étape 3 — Caractéristiques du prêt
# ============================================================

def afficher_etape_pret() -> None:
    """
    Affiche les caractéristiques du prêt.

    Le ratio prêt/revenu est calculé automatiquement.
    """

    donnees = st.session_state["formulaire_credit"]

    st.subheader(
        "Caractéristiques du prêt"
    )

    col1, col2 = st.columns(2)

    with col1:
        donnees["loan_amnt"] = st.number_input(
            "Montant du prêt",
            min_value=1.0,
            max_value=10_000_000.0,
            value=float(
                donnees["loan_amnt"]
            ),
            step=500.0,
            format="%.0f",
        )

    with col2:
        donnees["loan_int_rate"] = st.number_input(
            "Taux d'intérêt annuel (%)",
            min_value=0.0,
            max_value=100.0,
            value=float(
                donnees["loan_int_rate"]
            ),
            step=0.1,
            format="%.2f",
        )

    donnees["loan_intent"] = st.selectbox(
        "Objet du prêt",
        options=[
            "PERSONAL",
            "EDUCATION",
            "MEDICAL",
            "VENTURE",
            "HOMEIMPROVEMENT",
            "DEBTCONSOLIDATION",
        ],
        index=[
            "PERSONAL",
            "EDUCATION",
            "MEDICAL",
            "VENTURE",
            "HOMEIMPROVEMENT",
            "DEBTCONSOLIDATION",
        ].index(
            donnees["loan_intent"]
        ),
        format_func=lambda valeur: {
            "PERSONAL": "Dépenses personnelles",
            "EDUCATION": "Éducation",
            "MEDICAL": "Santé",
            "VENTURE": "Projet entrepreneurial",
            "HOMEIMPROVEMENT": "Amélioration du logement",
            "DEBTCONSOLIDATION": "Consolidation de dettes",
        }[valeur],
    )

    if (
        donnees["mode_evaluation"]
        == MODE_AVEC_GRADE
    ):
        donnees["loan_grade"] = st.selectbox(
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
            index=[
                "A",
                "B",
                "C",
                "D",
                "E",
                "F",
                "G",
            ].index(
                donnees["loan_grade"]
            ),
            help=(
                "Ce champ est uniquement transmis "
                "au modèle avec loan_grade."
            ),
        )

    else:
        st.info(
            "Le grade de crédit n'est pas requis "
            "pour le modèle sélectionné."
        )

    # --------------------------------------------------------
    # Calcul automatique du ratio
    # --------------------------------------------------------

    ratio = calculer_ratio_pret_revenu(
        montant_pret=donnees["loan_amnt"],
        revenu_annuel=donnees["person_income"],
    )

    donnees["loan_percent_income"] = (
        ratio
    )

    st.markdown("#### Capacité financière")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Revenu annuel",
            formater_montant(
                donnees["person_income"]
            ),
        )

    with col2:
        st.metric(
            "Montant demandé",
            formater_montant(
                donnees["loan_amnt"]
            ),
        )

    with col3:
        st.metric(
            "Ratio prêt/revenu",
            f"{ratio:.1%}",
        )

    # --------------------------------------------------------
    # Lecture métier du ratio
    # --------------------------------------------------------

    if ratio <= 0.23:
        st.success(
            "Le ratio reste dans la zone couvrant environ "
            "75 % des observations du dataset."
        )

    elif ratio <= 0.35:
        st.info(
            "Le ratio dépasse le troisième quartile du dataset."
        )

    elif ratio <= 0.50:
        st.warning(
            "Le montant demandé représente une part importante "
            "du revenu annuel."
        )

    elif ratio <= 0.83:
        st.warning(
            "Le ratio est très élevé, mais reste dans le domaine "
            "maximum observé dans le dataset."
        )

    else:
        st.error(
            "Le ratio dépasse le maximum observé dans les données "
            "d'entraînement. La prédiction devra être interprétée "
            "avec une grande prudence."
        )


# ============================================================
# Étape 4 — Historique de crédit
# ============================================================

def afficher_etape_historique() -> None:
    """
    Affiche les variables relatives à l'historique de crédit.
    """

    donnees = st.session_state["formulaire_credit"]

    st.subheader(
        "Historique de crédit"
    )

    col1, col2 = st.columns(2)

    with col1:
        donnees[
            "cb_person_default_on_file"
        ] = st.selectbox(
            "Défaut de paiement déjà enregistré ?",
            options=[
                "N",
                "Y",
            ],
            index=(
                0
                if donnees[
                    "cb_person_default_on_file"
                ] == "N"
                else 1
            ),
            format_func=lambda valeur: (
                "Non"
                if valeur == "N"
                else "Oui"
            ),
            help=(
                "Cette variable indique si un défaut antérieur "
                "figure dans le dossier de crédit."
            ),
        )

    with col2:
        historique_maximum = max(
            0,
            donnees["person_age"] - 18,
        )

        valeur_historique = min(
            int(
                donnees[
                    "cb_person_cred_hist_length"
                ]
            ),
            historique_maximum,
        )

        donnees[
            "cb_person_cred_hist_length"
        ] = st.number_input(
            "Ancienneté de l'historique de crédit",
            min_value=0,
            max_value=historique_maximum,
            value=valeur_historique,
            step=1,
            help=(
                "Une personne ne peut normalement pas avoir "
                "un historique de crédit antérieur à sa majorité."
            ),
        )

    if (
        donnees["cb_person_cred_hist_length"]
        > 30
    ):
        st.warning(
            "Cette valeur dépasse le maximum observé "
            "dans le dataset d'entraînement."
        )


# ============================================================
# Étape 5 — Vérification
# ============================================================

def construire_donnees_modele() -> dict[str, Any]:
    """
    Construit uniquement le dictionnaire attendu par le modèle.

    Les données administratives comme l'agence ou le nom
    de l'analyste ne doivent pas être transmises au pipeline ML.
    """

    donnees = st.session_state["formulaire_credit"]

    donnees_modele: dict[str, Any] = {
        "person_age": donnees["person_age"],
        "person_income": donnees["person_income"],
        "person_home_ownership": (
            donnees["person_home_ownership"]
        ),
        "person_emp_length": (
            donnees["person_emp_length"]
        ),
        "loan_intent": donnees["loan_intent"],
        "loan_amnt": donnees["loan_amnt"],
        "loan_int_rate": donnees["loan_int_rate"],
        "loan_percent_income": (
            calculer_ratio_pret_revenu(
                montant_pret=donnees["loan_amnt"],
                revenu_annuel=donnees["person_income"],
            )
        ),
        "cb_person_default_on_file": (
            donnees[
                "cb_person_default_on_file"
            ]
        ),
        "cb_person_cred_hist_length": (
            donnees[
                "cb_person_cred_hist_length"
            ]
        ),
    }

    if (
        donnees["mode_evaluation"]
        == MODE_AVEC_GRADE
    ):
        donnees_modele["loan_grade"] = (
            donnees["loan_grade"]
        )

    return donnees_modele


def afficher_etape_verification() -> None:
    """
    Affiche le résumé complet avant la prédiction.
    """

    donnees = st.session_state["formulaire_credit"]

    ratio = calculer_ratio_pret_revenu(
        montant_pret=donnees["loan_amnt"],
        revenu_annuel=donnees["person_income"],
    )

    st.subheader(
        "Vérification du dossier"
    )

    st.caption(
        "Contrôlez les informations avant de lancer "
        "l'analyse du risque."
    )

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown(
                "#### Informations générales"
            )

            st.write(
                f"**Référence :** "
                f"{donnees['reference_dossier'] or 'Non renseignée'}"
            )

            st.write(
                f"**Client :** "
                f"{donnees['identifiant_client'] or 'Non renseigné'}"
            )

            st.write(
                f"**Agence :** "
                f"{donnees['agence'] or 'Non renseignée'}"
            )

            st.write(
                f"**Analyste :** "
                f"{donnees['analyste'] or 'Non renseigné'}"
            )

            st.write(
                "**Mode :** "
                f"{LIBELLES_MODES[donnees['mode_evaluation']]}"
            )

    with col2:
        with st.container(border=True):
            st.markdown(
                "#### Profil du demandeur"
            )

            st.write(
                f"**Âge :** {donnees['person_age']} ans"
            )

            st.write(
                "**Revenu annuel :** "
                f"{formater_montant(donnees['person_income'])}"
            )

            st.write(
                "**Ancienneté professionnelle :** "
                f"{donnees['person_emp_length']:.0f} ans"
            )

            st.write(
                "**Statut de logement :** "
                f"{donnees['person_home_ownership']}"
            )

    col3, col4 = st.columns(2)

    with col3:
        with st.container(border=True):
            st.markdown(
                "#### Prêt"
            )

            st.write(
                "**Montant :** "
                f"{formater_montant(donnees['loan_amnt'])}"
            )

            st.write(
                "**Taux annuel :** "
                f"{donnees['loan_int_rate']:.2f} %"
            )

            st.write(
                "**Ratio prêt/revenu :** "
                f"{ratio:.1%}"
            )

            st.write(
                "**Objet :** "
                f"{donnees['loan_intent']}"
            )

            if (
                donnees["mode_evaluation"]
                == MODE_AVEC_GRADE
            ):
                st.write(
                    "**Grade :** "
                    f"{donnees['loan_grade']}"
                )

    with col4:
        with st.container(border=True):
            st.markdown(
                "#### Historique de crédit"
            )

            st.write(
                "**Défaut antérieur :** "
                + (
                    "Oui"
                    if donnees[
                        "cb_person_default_on_file"
                    ] == "Y"
                    else "Non"
                )
            )

            st.write(
                "**Ancienneté de l'historique :** "
                f"{donnees['cb_person_cred_hist_length']} ans"
            )


# ============================================================
# Boutons de navigation
# ============================================================

def afficher_boutons_navigation() -> bool:
    """
    Affiche les boutons Précédent, Suivant ou Analyser.

    Retourne True lorsque l'utilisateur clique sur
    le bouton final Analyser le dossier.
    """

    etape = st.session_state["etape_formulaire"]

    col_gauche, col_centre, col_droite = st.columns(
        [1, 2, 1]
    )

    with col_gauche:
        if etape > 1:
            st.button(
                "← Précédent",
                on_click=aller_etape_precedente,
                use_container_width=True,
            )

    with col_centre:
        if st.button(
            "Réinitialiser le formulaire",
            on_click=reinitialiser_formulaire,
            use_container_width=True,
        ):
            pass

    with col_droite:

        if etape < NOMBRE_ETAPES:
            st.button(
                "Suivant →",
                type="primary",
                on_click=aller_etape_suivante,
                use_container_width=True,
            )

            return False

        return st.button(
            "Analyser le dossier",
            type="primary",
            use_container_width=True,
        )


# ============================================================
# Fonction principale du composant
# ============================================================

def afficher_formulaire_multi_etapes() -> tuple[
    bool,
    dict[str, Any],
    dict[str, Any],
]:
    """
    Affiche l'étape actuelle du formulaire.

    Retourne :
        - analyser : indique si le bouton final a été cliqué ;
        - donnees_administratives : toutes les données du dossier ;
        - donnees_modele : uniquement les variables ML.
    """

    initialiser_formulaire()

    afficher_progression()

    etape = st.session_state["etape_formulaire"]

    with st.container(border=True):

        if etape == 1:
            afficher_etape_informations_generales()

        elif etape == 2:
            afficher_etape_profil()

        elif etape == 3:
            afficher_etape_pret()

        elif etape == 4:
            afficher_etape_historique()

        elif etape == 5:
            afficher_etape_verification()

    analyser = afficher_boutons_navigation()

    donnees_administratives = (
        st.session_state["formulaire_credit"].copy()
    )

    donnees_modele = construire_donnees_modele()

    return (
        analyser,
        donnees_administratives,
        donnees_modele,
    )