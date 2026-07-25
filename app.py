from __future__ import annotations

import streamlit as st

from components.layout import (
    afficher_entete,
    afficher_informations_sidebar,
    afficher_pied_de_page,
    charger_css,
)

from config import APP_NAME

from services.database import (
    initialiser_base,
)

from services.state import (
    initialiser_session,
)


# ============================================================
# Configuration générale de la page
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# Initialisation technique
# ============================================================

# Charge l'identité visuelle.
charger_css()

# Crée les tables SQLite lorsqu'elles n'existent pas.
initialiser_base()

# Initialise les variables de session Streamlit.
initialiser_session()


# ============================================================
# En-tête commun
# ============================================================

afficher_entete()


# ============================================================
# Déclaration des pages
# ============================================================

page_accueil = st.Page(
    page="pages/accueil.py",
    title="Accueil",
    icon="🏠",
    default=True,
)

page_nouveau_dossier = st.Page(
    page="pages/nouveau_dossier.py",
    title="Nouveau dossier",
    icon="📝",
)

page_comparaison = st.Page(
    page="pages/comparaison.py",
    title="Comparer les modèles",
    icon="⚖️",
)

page_historique = st.Page(
    page="pages/historique.py",
    title="Historique",
    icon="📚",
)

page_olap = st.Page(
    page="pages/analyse_olap.py",
    title="Analyse OLAP",
    icon="📊",
)

page_suivi_modeles = st.Page(
    page="pages/suivi_modeles.py",
    title="Suivi des modèles",
    icon="🧠",
)


# ============================================================
# Construction de la navigation
# ============================================================

navigation = st.navigation(
    {
        "Pilotage": [
            page_accueil,
        ],

        "Évaluation du crédit": [
            page_nouveau_dossier,
            page_comparaison,
            page_historique,
        ],

        "Analyse et gouvernance": [
            page_olap,
            page_suivi_modeles,
        ],
    }
)


# ============================================================
# Informations de la barre latérale
# ============================================================

afficher_informations_sidebar()


# ============================================================
# Exécution de la page sélectionnée
# ============================================================

navigation.run()


# ============================================================
# Pied de page
# ============================================================

afficher_pied_de_page()