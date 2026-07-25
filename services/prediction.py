from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib

from config import (
    BANDES_RISQUE_PAR_DEFAUT,
    MANIFEST_PATH,
    MODELS_DIR,
    MODES_AUTORISES,
    SEUILS_PATH,
)

from services.utils import (
    calculer_indice_risque,
    construire_dataframe,
)


# ============================================================
# Chargement du manifeste
# ============================================================

@lru_cache(maxsize=1)
def charger_manifest() -> dict[str, Any]:
    """
    Charge le manifeste des modèles une seule fois.

    lru_cache évite de relire le fichier JSON à chaque prédiction.
    """

    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            "Le fichier manifest_modeles.json est introuvable : "
            f"{MANIFEST_PATH}"
        )

    with MANIFEST_PATH.open(
        mode="r",
        encoding="utf-8",
    ) as fichier:
        manifest = json.load(fichier)

    if "modes" not in manifest:
        raise ValueError(
            "Le manifeste doit contenir une clé 'modes'."
        )

    return manifest




# ============================================================
# Chargement des seuils de décision
# ============================================================

@lru_cache(maxsize=1)
def charger_seuils_decision() -> dict[str, float]:
    """Charge les seuils optimisés sauvegardés par le notebook.

    Le fichier ``seuils_decision.joblib`` constitue la source principale.
    Le manifeste reste un mécanisme de secours pour assurer la compatibilité.
    """

    if SEUILS_PATH.exists():
        seuils_bruts = joblib.load(SEUILS_PATH)
        if not isinstance(seuils_bruts, dict):
            raise TypeError(
                "Le fichier seuils_decision.joblib doit contenir un dictionnaire."
            )

        seuils = {
            str(cle): float(valeur)
            for cle, valeur in seuils_bruts.items()
        }

        cles_requises = {"avec_loan_grade", "sans_loan_grade"}
        cles_manquantes = cles_requises.difference(seuils)
        if cles_manquantes:
            raise KeyError(
                "Seuil(s) absent(s) du fichier : "
                + ", ".join(sorted(cles_manquantes))
            )

        return seuils

    manifest = charger_manifest()
    return {
        "avec_loan_grade": float(
            manifest["modes"]["avec_grade"].get("seuil", 0.5)
        ),
        "sans_loan_grade": float(
            manifest["modes"]["sans_grade"].get("seuil", 0.5)
        ),
    }


def obtenir_seuil_mode(mode: str) -> float:
    """Retourne le seuil optimisé correspondant au modèle sélectionné."""

    correspondance = {
        "avec_grade": "avec_loan_grade",
        "sans_grade": "sans_loan_grade",
    }

    if mode not in correspondance:
        raise ValueError(f"Mode invalide : {mode}")

    seuil = float(charger_seuils_decision()[correspondance[mode]])
    if not 0.0 <= seuil <= 1.0:
        raise ValueError(
            f"Le seuil du mode '{mode}' doit être compris entre 0 et 1."
        )
    return seuil


# ============================================================
# Configuration d'un mode
# ============================================================

def obtenir_configuration_mode(
    mode: str,
) -> dict[str, Any]:
    """
    Retourne la configuration d'un modèle.
    """

    if mode not in MODES_AUTORISES:
        raise ValueError(
            f"Mode invalide : {mode}"
        )

    manifest = charger_manifest()

    configuration = manifest["modes"].get(
        mode
    )

    if configuration is None:
        raise KeyError(
            f"Le mode '{mode}' est absent du manifeste."
        )

    return configuration


# ============================================================
# Chargement du modèle
# ============================================================

@lru_cache(maxsize=2)
def charger_modele(
    mode: str,
):
    """
    Charge le pipeline correspondant au mode choisi.
    """

    configuration = obtenir_configuration_mode(
        mode
    )

    nom_fichier = configuration.get(
        "fichier_modele"
    )

    if not nom_fichier:
        raise ValueError(
            f"Aucun fichier de modèle n'est défini pour {mode}."
        )

    chemin_modele: Path = (
        MODELS_DIR / nom_fichier
    )

    if not chemin_modele.exists():
        raise FileNotFoundError(
            f"Le modèle est introuvable : {chemin_modele}"
        )

    return joblib.load(
        chemin_modele
    )


# ============================================================
# Catégorie de risque
# ============================================================

def determiner_categorie_risque(
    probabilite: float,
    bandes: dict[str, list[float]],
) -> str:
    """
    Associe une probabilité à une bande de risque.
    """

    for categorie, limites in bandes.items():

        minimum = float(
            limites[0]
        )

        maximum = float(
            limites[1]
        )

        if minimum <= probabilite < maximum:
            return categorie

    return "indetermine"


# ============================================================
# Prédiction principale
# ============================================================

def predire_risque(
    donnees: dict[str, Any],
    mode: str,
) -> dict[str, Any]:
    """
    Effectue une prédiction complète.
    """

    configuration = obtenir_configuration_mode(
        mode
    )

    modele = charger_modele(
        mode
    )

    variables_attendues = configuration.get(
        "variables_attendues"
    )

    if not variables_attendues:
        raise ValueError(
            "La liste des variables attendues est absente."
        )

    dataframe = construire_dataframe(
        donnees=donnees,
        variables_attendues=variables_attendues,
    )

    if not hasattr(modele, "predict_proba"):
        raise TypeError(
            "Le modèle chargé ne possède pas predict_proba()."
        )

    probabilites = modele.predict_proba(
        dataframe
    )

    probabilite_defaut = float(
        probabilites[0, 1]
    )

    # Le seuil provient du fichier sauvegardé par le notebook :
    # 0,45 avec loan_grade et 0,40 sans loan_grade.
    seuil = obtenir_seuil_mode(mode)

    classe_predite = int(
        probabilite_defaut >= seuil
    )

    bandes = configuration.get(
        "bandes_risque",
        BANDES_RISQUE_PAR_DEFAUT,
    )

    categorie = determiner_categorie_risque(
        probabilite=probabilite_defaut,
        bandes=bandes,
    )

    indice = calculer_indice_risque(
        probabilite_defaut
    )

    return {
        "mode": mode,
        "algorithme": configuration.get(
            "algorithme",
            "XGBoost",
        ),
        "version_modele": configuration.get(
            "version",
            "Non précisée",
        ),
        "probabilite_defaut": probabilite_defaut,
        "indice_risque": indice,
        "score_credit": indice,
        "categorie_risque": categorie,
        "seuil": seuil,
        "classe_predite": classe_predite,
        "dataframe": dataframe,
        "configuration": configuration,
    }


# ============================================================
# Comparaison des deux modèles
# ============================================================

def comparer_modeles(
    donnees_avec_grade: dict[str, Any],
    donnees_sans_grade: dict[str, Any],
) -> dict[str, Any]:
    """
    Évalue le même dossier avec les deux modèles.
    """

    resultat_avec = predire_risque(
        donnees=donnees_avec_grade,
        mode="avec_grade",
    )

    resultat_sans = predire_risque(
        donnees=donnees_sans_grade,
        mode="sans_grade",
    )

    ecart_probabilite = (
        resultat_avec["probabilite_defaut"]
        - resultat_sans["probabilite_defaut"]
    )

    changement_categorie = (
        resultat_avec["categorie_risque"]
        != resultat_sans["categorie_risque"]
    )

    changement_classe = (
        resultat_avec["classe_predite"]
        != resultat_sans["classe_predite"]
    )

    return {
        "avec_grade": resultat_avec,
        "sans_grade": resultat_sans,
        "ecart_probabilite": ecart_probabilite,
        "ecart_absolu": abs(ecart_probabilite),
        "changement_categorie": changement_categorie,
        "changement_classe": changement_classe,
    }