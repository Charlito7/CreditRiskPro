from __future__ import annotations

from typing import Any

import pandas as pd


# ============================================================
# Calculs financiers simples
# ============================================================

def calculer_ratio_pret_revenu(
    montant_pret: float,
    revenu_annuel: float,
) -> float:
    """
    Calcule le ratio entre le montant du prêt et le revenu annuel.

    Formule
    -------
    ratio = montant du prêt / revenu annuel

    Exemple
    -------
    Pour un prêt de 8 000 et un revenu annuel de 55 000 :

        ratio = 8 000 / 55 000
        ratio ≈ 0,1455
        ratio ≈ 14,55 %

    Parameters
    ----------
    montant_pret:
        Montant demandé par l'emprunteur.

    revenu_annuel:
        Revenu annuel déclaré par l'emprunteur.

    Returns
    -------
    float
        Ratio prêt/revenu exprimé sous forme décimale.

    Raises
    ------
    ValueError
        Lorsque le montant est négatif ou lorsque
        le revenu est inférieur ou égal à zéro.
    """

    if montant_pret < 0:
        raise ValueError(
            "Le montant du prêt ne peut pas être négatif."
        )

    if revenu_annuel <= 0:
        raise ValueError(
            "Le revenu annuel doit être supérieur à zéro."
        )

    return montant_pret / revenu_annuel


def calculer_indice_risque(
    probabilite_defaut: float,
) -> int:
    """
    Transforme une probabilité de défaut en indice sur 1000.

    L'indice évolue dans le sens inverse de la probabilité :

        probabilité faible -> indice élevé
        probabilité élevée -> indice faible

    Formule provisoire
    ------------------
    indice = 1000 × (1 - probabilité)

    Cette formule est intuitive pour l'interface, mais ne constitue
    pas encore une carte de score bancaire officielle.

    Parameters
    ----------
    probabilite_defaut:
        Probabilité comprise entre 0 et 1.

    Returns
    -------
    int
        Indice compris entre 0 et 1000.
    """

    if not 0 <= probabilite_defaut <= 1:
        raise ValueError(
            "La probabilité de défaut doit être comprise entre 0 et 1."
        )

    indice = round(
        1000 * (1 - probabilite_defaut)
    )

    return int(
        max(
            0,
            min(1000, indice),
        )
    )


# ============================================================
# Formatage destiné à l'interface
# ============================================================

def formater_montant(
    montant: float,
    devise: str | None = None,
) -> str:
    """
    Formate un montant avec des espaces comme séparateurs.

    Exemple
    -------
    55000 devient :

        55 000

    Avec une devise :

        55 000 HTG

    Parameters
    ----------
    montant:
        Valeur numérique à formater.

    devise:
        Devise facultative, par exemple HTG ou USD.
    """

    montant_formate = (
        f"{montant:,.0f}"
        .replace(",", " ")
    )

    if devise:
        return f"{montant_formate} {devise}"

    return montant_formate


def formater_pourcentage(
    valeur: float,
    decimales: int = 1,
) -> str:
    """
    Transforme une valeur décimale en pourcentage lisible.

    Exemple
    -------
    0.145 devient :

        14,5 %
    """

    pourcentage = valeur * 100

    texte = f"{pourcentage:.{decimales}f}"

    # Affichage avec virgule décimale en français.
    texte = texte.replace(".", ",")

    return f"{texte} %"


# ============================================================
# Catégories et libellés métier
# ============================================================

def traduire_categorie_risque(
    categorie: str,
) -> str:
    """
    Traduit une catégorie technique en libellé utilisateur.
    """

    traductions = {
        "faible": "Risque faible",
        "modere": "Risque modéré",
        "eleve": "Risque élevé",
        "tres_eleve": "Risque très élevé",
        "indetermine": "Risque indéterminé",
    }

    return traductions.get(
        categorie,
        categorie.replace("_", " ").title(),
    )


def obtenir_recommandation(
    categorie: str,
) -> str:
    """
    Retourne une recommandation métier indicative.

    La recommandation ne constitue pas une décision automatique.
    """

    recommandations = {
        "faible": (
            "Le dossier peut poursuivre le processus normal "
            "de validation."
        ),
        "modere": (
            "Une vérification complémentaire des revenus, "
            "de l'ancienneté et de la capacité de remboursement "
            "est recommandée."
        ),
        "eleve": (
            "Une analyse renforcée du dossier est recommandée "
            "avant toute décision."
        ),
        "tres_eleve": (
            "Le dossier doit être examiné par un analyste "
            "expérimenté ou un superviseur."
        ),
    }

    return recommandations.get(
        categorie,
        "Une revue humaine du dossier est nécessaire.",
    )


# ============================================================
# Préparation des données pour le modèle
# ============================================================

def construire_dataframe(
    donnees: dict[str, Any],
    variables_attendues: list[str] | None = None,
) -> pd.DataFrame:
    """
    Transforme un dossier en DataFrame pandas d'une ligne.

    Parameters
    ----------
    donnees:
        Dictionnaire contenant les variables du dossier.

    variables_attendues:
        Liste facultative définissant :
        - les variables autorisées ;
        - leur ordre exact.

    Returns
    -------
    pandas.DataFrame
        DataFrame d'une ligne prêt à être transmis au pipeline ML.

    Raises
    ------
    ValueError
        Lorsqu'une variable attendue est absente.
    """

    if variables_attendues is None:
        return pd.DataFrame(
            [donnees]
        )

    variables_manquantes = [
        variable
        for variable in variables_attendues
        if variable not in donnees
    ]

    if variables_manquantes:
        raise ValueError(
            "Variables manquantes : "
            + ", ".join(variables_manquantes)
        )

    donnees_ordonnees = {
        variable: donnees[variable]
        for variable in variables_attendues
    }

    return pd.DataFrame(
        [donnees_ordonnees]
    )