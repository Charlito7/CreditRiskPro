from __future__ import annotations

from pathlib import Path

import streamlit as st

from config import (
    APP_DESCRIPTION,
    APP_NAME,
    APP_VERSION,
    ASSETS_DIR,
)


# ============================================================
# Chargement du CSS
# ============================================================

def charger_css() -> None:
    """
    Charge l'identité visuelle principale de l'application.

    Le fichier CSS est séparé du code Python afin de faciliter :
        - la maintenance ;
        - l'évolution graphique ;
        - la cohérence entre les pages.
    """

    chemin_css: Path = (
        ASSETS_DIR
        / "styles.css"
    )

    if not chemin_css.exists():
        st.warning(
            "Le fichier de style assets/styles.css "
            "est introuvable."
        )

        return

    contenu_css = chemin_css.read_text(
        encoding="utf-8"
    )

    st.markdown(
        f"<style>{contenu_css}</style>",
        unsafe_allow_html=True,
    )


# ============================================================
# En-tête principal
# ============================================================

def afficher_entete() -> None:
    """
    Affiche le bandeau principal de CreditRisk Pro.

    Ce bandeau est partagé par toutes les pages.
    """

    st.markdown(
        f"""
<div class="page-header">
    <h1>🏦 {APP_NAME}</h1>
    <p>{APP_DESCRIPTION}</p>
</div>
""",
        unsafe_allow_html=True,
    )


# ============================================================
# Titre de page ou de section
# ============================================================

def afficher_titre_section(
    titre: str,
    description: str | None = None,
) -> None:
    """
    Affiche un titre standardisé.

    Parameters
    ----------
    titre:
        Titre principal de la section.

    description:
        Texte explicatif facultatif.
    """

    description_html = ""

    if description:
        description_html = (
            f"<p>{description}</p>"
        )

    st.markdown(
        f"""
<div class="section-title">
    <h2>{titre}</h2>
    {description_html}
</div>
""",
        unsafe_allow_html=True,
    )


# ============================================================
# Informations de la barre latérale
# ============================================================

def afficher_informations_sidebar() -> None:
    """
    Affiche les informations permanentes dans la barre latérale.
    """

    with st.sidebar:

        st.markdown("---")

        st.caption(
            f"Version {APP_VERSION}"
        )

        st.caption(
            "Outil d'aide à la décision. "
            "La décision finale doit rester humaine."
        )


# ============================================================
# Pied de page
# ============================================================

def afficher_pied_de_page() -> None:
    """
    Affiche le pied de page partagé par toutes les pages.
    """

    st.markdown(
        f"""
<div class="footer-text">
    {APP_NAME} — Plateforme d'aide à la décision crédit
</div>
""",
        unsafe_allow_html=True,
    )


# ============================================================
# Carte de statut
# ============================================================

def afficher_statut(
    libelle: str,
    statut: str,
) -> None:
    """
    Affiche un badge visuel selon un statut.

    Statuts autorisés :
        - actif ;
        - attention ;
        - inactif ;
        - information.
    """

    classes = {
        "actif": "status-active",
        "attention": "status-warning",
        "inactif": "status-inactive",
        "information": "status-information",
    }

    classe_css = classes.get(
        statut,
        "status-information",
    )

    st.markdown(
        f"""
<span class="status-chip {classe_css}">
    {libelle}
</span>
""",
        unsafe_allow_html=True,
    )