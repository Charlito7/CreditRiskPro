from __future__ import annotations

import streamlit as st

from config import MODE_AVEC_GRADE


def initialiser_session() -> None:
    """
    Initialise les principales variables de session.
    """

    valeurs_par_defaut = {
        "dossier_courant": {},
        "donnees_modele_courantes": {},
        "resultat_courant": None,
        "evaluation_id_courante": None,
        "mode_evaluation": MODE_AVEC_GRADE,
        "dossier_valide": False,
        "avertissements_dossier": [],
        "etape_formulaire": 1,
    }

    for cle, valeur in valeurs_par_defaut.items():

        if cle not in st.session_state:
            st.session_state[
                cle
            ] = valeur


def sauvegarder_resultat_session(
    donnees_administratives: dict,
    donnees_modele: dict,
    resultat: dict,
    evaluation_id: int | None = None,
) -> None:
    """
    Enregistre le dossier et le résultat dans la session.
    """

    st.session_state[
        "dossier_courant"
    ] = donnees_administratives

    st.session_state[
        "donnees_modele_courantes"
    ] = donnees_modele

    st.session_state[
        "resultat_courant"
    ] = resultat

    st.session_state[
        "evaluation_id_courante"
    ] = evaluation_id

    st.session_state[
        "dossier_valide"
    ] = True


def reinitialiser_dossier_session() -> None:
    """
    Supprime le dossier en cours.
    """

    st.session_state[
        "dossier_courant"
    ] = {}

    st.session_state[
        "donnees_modele_courantes"
    ] = {}

    st.session_state[
        "resultat_courant"
    ] = None

    st.session_state[
        "evaluation_id_courante"
    ] = None

    st.session_state[
        "dossier_valide"
    ] = False

    st.session_state[
        "avertissements_dossier"
    ] = []

    st.session_state[
        "etape_formulaire"
    ] = 1