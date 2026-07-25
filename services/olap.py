from __future__ import annotations

from typing import Any

import pandas as pd


# ============================================================
# Mesures OLAP autorisées
# ============================================================

MESURES_OLAP = {
    "nombre_dossiers": {
        "colonne": "evaluation_id",
        "fonction": "count",
    },
    "probabilite_moyenne": {
        "colonne": "probabilite_defaut",
        "fonction": "mean",
    },
    "indice_moyen": {
        "colonne": "indice_risque",
        "fonction": "mean",
    },
    "taux_dossiers_signales": {
        "colonne": "classe_predite",
        "fonction": "mean",
    },
}


# ============================================================
# Filtres Slice et Dice
# ============================================================

def appliquer_filtres(
    donnees: pd.DataFrame,
    filtres: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """
    Applique des filtres de type slice ou dice.

    Exemple :
    {
        "categorie_risque": ["eleve", "tres_eleve"],
        "mode_evaluation": "avec_grade"
    }
    """

    resultat = donnees.copy()

    if not filtres:
        return resultat

    for colonne, valeur in filtres.items():

        if colonne not in resultat.columns:
            raise ValueError(
                f"Colonne inconnue : {colonne}"
            )

        if valeur is None:
            continue

        if isinstance(
            valeur,
            list | tuple | set,
        ):
            resultat = resultat[
                resultat[colonne].isin(
                    valeur
                )
            ]

        else:
            resultat = resultat[
                resultat[colonne] == valeur
            ]

    return resultat


# ============================================================
# Tableau croisé OLAP
# ============================================================

def construire_tableau_olap(
    donnees: pd.DataFrame,
    dimension_ligne: str,
    mesure: str,
    dimension_colonne: str | None = None,
    filtres: dict[str, Any] | None = None,
    ajouter_totaux: bool = True,
) -> pd.DataFrame:
    """
    Construit un tableau OLAP dynamique.
    """

    donnees_filtrees = appliquer_filtres(
        donnees=donnees,
        filtres=filtres,
    )

    if dimension_ligne not in donnees_filtrees.columns:
        raise ValueError(
            f"Dimension ligne inconnue : {dimension_ligne}"
        )

    if dimension_colonne is not None:
        if dimension_colonne not in donnees_filtrees.columns:
            raise ValueError(
                f"Dimension colonne inconnue : "
                f"{dimension_colonne}"
            )

    configuration_mesure = MESURES_OLAP.get(
        mesure
    )

    if configuration_mesure is None:
        raise ValueError(
            f"Mesure OLAP inconnue : {mesure}"
        )

    colonne_mesure = configuration_mesure[
        "colonne"
    ]

    fonction = configuration_mesure[
        "fonction"
    ]

    tableau = pd.pivot_table(
        donnees_filtrees,
        index=dimension_ligne,
        columns=dimension_colonne,
        values=colonne_mesure,
        aggfunc=fonction,
        fill_value=0,
        margins=ajouter_totaux,
        margins_name="Total",
    )

    return tableau


# ============================================================
# Agrégation simple
# ============================================================

def agreger_donnees(
    donnees: pd.DataFrame,
    dimensions: list[str],
    mesures: dict[str, str],
) -> pd.DataFrame:
    """
    Effectue une agrégation groupby.

    Exemple :
    dimensions = ["agence", "categorie_risque"]

    mesures = {
        "probabilite_defaut": "mean",
        "evaluation_id": "count"
    }
    """

    for dimension in dimensions:
        if dimension not in donnees.columns:
            raise ValueError(
                f"Dimension inconnue : {dimension}"
            )

    for colonne in mesures:
        if colonne not in donnees.columns:
            raise ValueError(
                f"Mesure inconnue : {colonne}"
            )

    return (
        donnees
        .groupby(
            dimensions,
            dropna=False,
        )
        .agg(
            mesures
        )
        .reset_index()
    )


# ============================================================
# Drill-down temporel
# ============================================================

def ajouter_dimensions_temporelles(
    donnees: pd.DataFrame,
    colonne_date: str = "date_evaluation",
) -> pd.DataFrame:
    """
    Ajoute les dimensions année, trimestre, mois et jour.
    """

    if colonne_date not in donnees.columns:
        raise ValueError(
            f"Colonne de date inconnue : {colonne_date}"
        )

    resultat = donnees.copy()

    resultat[colonne_date] = pd.to_datetime(
        resultat[colonne_date],
        errors="coerce",
    )

    resultat["annee"] = (
        resultat[colonne_date].dt.year
    )

    resultat["trimestre"] = (
        resultat[colonne_date]
        .dt.to_period("Q")
        .astype(str)
    )

    resultat["mois"] = (
        resultat[colonne_date]
        .dt.to_period("M")
        .astype(str)
    )

    resultat["jour"] = (
        resultat[colonne_date]
        .dt.date
        .astype(str)
    )

    return resultat


# ============================================================
# KPI OLAP
# ============================================================

def calculer_kpi(
    donnees: pd.DataFrame,
) -> dict[str, float | int]:
    """
    Calcule les principaux indicateurs du portefeuille.
    """

    if donnees.empty:
        return {
            "nombre_dossiers": 0,
            "probabilite_moyenne": 0.0,
            "indice_moyen": 0.0,
            "taux_signale": 0.0,
        }

    return {
        "nombre_dossiers": int(
            len(donnees)
        ),
        "probabilite_moyenne": float(
            donnees[
                "probabilite_defaut"
            ].mean()
        ),
        "indice_moyen": float(
            donnees[
                "indice_risque"
            ].mean()
        ),
        "taux_signale": float(
            donnees[
                "classe_predite"
            ].mean()
        ),
    }