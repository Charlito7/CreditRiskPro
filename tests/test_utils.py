from __future__ import annotations

from services.utils import (
    calculer_indice_risque,
    calculer_ratio_pret_revenu,
    construire_dataframe,
    formater_montant,
    formater_pourcentage,
    traduire_categorie_risque,
)


def executer_tests() -> None:
    """
    Exécute quelques tests simples sur services.utils.
    """

    # --------------------------------------------------------
    # Test du ratio prêt/revenu
    # --------------------------------------------------------

    ratio = calculer_ratio_pret_revenu(
        montant_pret=8_000,
        revenu_annuel=55_000,
    )

    assert round(ratio, 4) == 0.1455

    # --------------------------------------------------------
    # Test de l'indice sur 1000
    # --------------------------------------------------------

    indice = calculer_indice_risque(
        probabilite_defaut=0.10
    )

    assert indice == 900

    # --------------------------------------------------------
    # Test du formatage
    # --------------------------------------------------------

    assert formater_montant(55_000) == "55 000"

    assert (
        formater_montant(
            55_000,
            devise="HTG",
        )
        == "55 000 HTG"
    )

    assert formater_pourcentage(0.145) == "14,5 %"

    # --------------------------------------------------------
    # Test de traduction
    # --------------------------------------------------------

    assert (
        traduire_categorie_risque("tres_eleve")
        == "Risque très élevé"
    )

    # --------------------------------------------------------
    # Test du DataFrame
    # --------------------------------------------------------

    donnees = {
        "person_age": 30,
        "person_income": 55_000,
    }

    dataframe = construire_dataframe(
        donnees=donnees,
        variables_attendues=[
            "person_age",
            "person_income",
        ],
    )

    assert dataframe.shape == (1, 2)

    assert list(dataframe.columns) == [
        "person_age",
        "person_income",
    ]

    print(
        "Tous les tests de services.utils ont réussi."
    )


if __name__ == "__main__":
    executer_tests()