from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from config import DOMAINES_ENTRAINEMENT
from services.utils import calculer_ratio_pret_revenu


# ============================================================
# Libellés destinés à l'utilisateur
# ============================================================

LIBELLES_VARIABLES = {
    "person_age": "Âge",
    "person_income": "Revenu annuel",
    "person_emp_length": "Ancienneté professionnelle",
    "loan_amnt": "Montant du prêt",
    "loan_int_rate": "Taux d’intérêt",
    "loan_percent_income": "Ratio prêt/revenu",
    "cb_person_cred_hist_length": (
        "Ancienneté de l’historique de crédit"
    ),
}


# ============================================================
# Structure du résultat de validation
# ============================================================

@dataclass
class ResultatValidation:
    """
    Représente le résultat complet de la validation.

    erreurs :
        Problèmes bloquants. La prédiction ne doit pas être lancée.

    avertissements :
        Situations inhabituelles nécessitant l'attention
        de l'analyste.

    informations :
        Informations non bloquantes sur la position du dossier
        par rapport aux données d'entraînement.
    """

    erreurs: list[str] = field(
        default_factory=list
    )

    avertissements: list[str] = field(
        default_factory=list
    )

    informations: list[str] = field(
        default_factory=list
    )

    @property
    def valide(self) -> bool:
        """
        Le dossier est valide lorsqu'aucune erreur
        bloquante n'a été détectée.
        """

        return len(self.erreurs) == 0


# ============================================================
# Variables obligatoires
# ============================================================

VARIABLES_COMMUNES = [
    "person_age",
    "person_income",
    "person_home_ownership",
    "person_emp_length",
    "loan_intent",
    "loan_amnt",
    "loan_int_rate",
    "loan_percent_income",
    "cb_person_default_on_file",
    "cb_person_cred_hist_length",
]


# ============================================================
# Validation des variables obligatoires
# ============================================================

def verifier_variables_obligatoires(
    donnees: dict[str, Any],
    avec_grade: bool,
    resultat: ResultatValidation,
) -> None:
    """
    Vérifie que toutes les variables nécessaires
    à la prédiction sont présentes.
    """

    variables_attendues = (
        VARIABLES_COMMUNES.copy()
    )

    if avec_grade:
        variables_attendues.append(
            "loan_grade"
        )

    variables_manquantes = [
        variable
        for variable in variables_attendues
        if variable not in donnees
    ]

    if variables_manquantes:
        resultat.erreurs.append(
            "Variables manquantes : "
            + ", ".join(
                variables_manquantes
            )
        )


# ============================================================
# Validation physique
# ============================================================

def verifier_contraintes_physiques(
    donnees: dict[str, Any],
    resultat: ResultatValidation,
) -> None:
    """
    Vérifie les valeurs impossibles ou incohérentes.
    """

    age = float(
        donnees["person_age"]
    )

    revenu = float(
        donnees["person_income"]
    )

    anciennete = float(
        donnees["person_emp_length"]
    )

    montant = float(
        donnees["loan_amnt"]
    )

    taux = float(
        donnees["loan_int_rate"]
    )

    historique = int(
        donnees[
            "cb_person_cred_hist_length"
        ]
    )

    if age < 18:
        resultat.erreurs.append(
            "Le demandeur doit avoir au moins 18 ans."
        )

    if age > 100:
        resultat.erreurs.append(
            "L’âge saisi dépasse la limite autorisée "
            "de 100 ans."
        )

    if revenu <= 0:
        resultat.erreurs.append(
            "Le revenu annuel doit être supérieur à zéro."
        )

    if montant <= 0:
        resultat.erreurs.append(
            "Le montant du prêt doit être supérieur à zéro."
        )

    if taux < 0:
        resultat.erreurs.append(
            "Le taux d’intérêt ne peut pas être négatif."
        )

    if taux > 100:
        resultat.erreurs.append(
            "Le taux d’intérêt ne peut pas dépasser 100 %."
        )

    if anciennete < 0:
        resultat.erreurs.append(
            "L’ancienneté professionnelle ne peut pas "
            "être négative."
        )

    if anciennete > age - 14:
        resultat.erreurs.append(
            "L’ancienneté professionnelle est incohérente "
            "avec l’âge du demandeur."
        )

    if historique < 0:
        resultat.erreurs.append(
            "L’ancienneté de l’historique de crédit "
            "ne peut pas être négative."
        )

    if historique > age - 18:
        resultat.erreurs.append(
            "L’ancienneté de l’historique de crédit "
            "est incohérente avec l’âge du demandeur."
        )


# ============================================================
# Validation des variables catégorielles
# ============================================================

def verifier_variables_categorielles(
    donnees: dict[str, Any],
    avec_grade: bool,
    resultat: ResultatValidation,
) -> None:
    """
    Vérifie que les catégories saisies correspondent
    aux catégories utilisées durant l'entraînement.
    """

    logements_autorises = {
        "RENT",
        "MORTGAGE",
        "OWN",
        "OTHER",
    }

    objets_autorises = {
        "PERSONAL",
        "EDUCATION",
        "MEDICAL",
        "VENTURE",
        "HOMEIMPROVEMENT",
        "DEBTCONSOLIDATION",
    }

    defauts_autorises = {
        "N",
        "Y",
    }

    grades_autorises = {
        "A",
        "B",
        "C",
        "D",
        "E",
        "F",
        "G",
    }

    if (
        donnees["person_home_ownership"]
        not in logements_autorises
    ):
        resultat.erreurs.append(
            "Le statut de logement est invalide."
        )

    if (
        donnees["loan_intent"]
        not in objets_autorises
    ):
        resultat.erreurs.append(
            "L’objet du prêt est invalide."
        )

    if (
        donnees["cb_person_default_on_file"]
        not in defauts_autorises
    ):
        resultat.erreurs.append(
            "La valeur indiquant le défaut antérieur "
            "est invalide."
        )

    if avec_grade:
        if (
            donnees.get("loan_grade")
            not in grades_autorises
        ):
            resultat.erreurs.append(
                "Le grade de crédit est invalide."
            )


# ============================================================
# Vérification du ratio prêt/revenu
# ============================================================

def verifier_ratio(
    donnees: dict[str, Any],
    resultat: ResultatValidation,
) -> None:
    """
    Vérifie que le ratio prêt/revenu correspond bien
    au montant et au revenu saisis.
    """

    ratio_attendu = (
        calculer_ratio_pret_revenu(
            montant_pret=float(
                donnees["loan_amnt"]
            ),
            revenu_annuel=float(
                donnees["person_income"]
            ),
        )
    )

    ratio_recu = float(
        donnees[
            "loan_percent_income"
        ]
    )

    if (
        abs(
            ratio_attendu
            - ratio_recu
        )
        > 0.0001
    ):
        resultat.erreurs.append(
            "Le ratio prêt/revenu ne correspond pas "
            "au montant et au revenu saisis."
        )


# ============================================================
# Validation du domaine d'entraînement
# ============================================================

def verifier_domaine_entrainement(
    donnees: dict[str, Any],
    resultat: ResultatValidation,
) -> None:
    """
    Compare les valeurs du dossier au domaine observé
    durant l'entraînement.

    Une valeur hors domaine n'est pas nécessairement impossible,
    mais la prédiction peut être moins fiable.
    """

    for (
        variable,
        statistiques,
    ) in DOMAINES_ENTRAINEMENT.items():

        if variable not in donnees:
            continue

        valeur = float(
            donnees[variable]
        )

        libelle = (
            LIBELLES_VARIABLES.get(
                variable,
                variable,
            )
        )

        minimum = statistiques.get(
            "minimum"
        )

        maximum = statistiques.get(
            "maximum_observe"
        )

        q1 = statistiques.get(
            "q1"
        )

        q3 = statistiques.get(
            "q3"
        )

        # ----------------------------------------------------
        # Valeur inférieure au domaine observé
        # ----------------------------------------------------

        if (
            minimum is not None
            and valeur < minimum
        ):
            resultat.avertissements.append(
                f"{libelle} est inférieur au minimum "
                f"observé pendant l’entraînement "
                f"({minimum})."
            )

        # ----------------------------------------------------
        # Valeur supérieure au domaine observé
        # ----------------------------------------------------

        if (
            maximum is not None
            and valeur > maximum
        ):
            resultat.avertissements.append(
                f"{libelle} dépasse le maximum "
                f"observé pendant l’entraînement "
                f"({maximum})."
            )

        # ----------------------------------------------------
        # Valeur située dans la zone centrale
        # ----------------------------------------------------

        if (
            q1 is not None
            and q3 is not None
            and q1 <= valeur <= q3
        ):
            resultat.informations.append(
                f"{libelle} se situe dans la zone centrale "
                "des données d’entraînement."
            )


# ============================================================
# Alertes métier
# ============================================================

def verifier_alertes_metier(
    donnees: dict[str, Any],
    resultat: ResultatValidation,
) -> None:
    """
    Génère des alertes métier non bloquantes.
    """

    ratio = float(
        donnees[
            "loan_percent_income"
        ]
    )

    taux = float(
        donnees[
            "loan_int_rate"
        ]
    )

    # --------------------------------------------------------
    # Alertes liées au ratio prêt/revenu
    # --------------------------------------------------------

    if ratio > 1:
        resultat.avertissements.append(
            "Le montant du prêt dépasse le revenu annuel."
        )

    elif ratio > 0.50:
        resultat.avertissements.append(
            "Le montant du prêt représente plus de 50 % "
            "du revenu annuel."
        )

    elif ratio > 0.35:
        resultat.avertissements.append(
            "Le ratio prêt/revenu est élevé."
        )

    elif ratio > 0.23:
        resultat.informations.append(
            "Le ratio prêt/revenu dépasse le troisième "
            "quartile des données d’entraînement."
        )

    # --------------------------------------------------------
    # Alerte liée au taux d'intérêt
    # --------------------------------------------------------

    if taux > 23.22:
        resultat.avertissements.append(
            "Le taux d’intérêt dépasse le maximum observé "
            "dans les données d’entraînement."
        )


# ============================================================
# Fonction principale
# ============================================================

def valider_dossier(
    donnees: dict[str, Any],
    avec_grade: bool = True,
) -> ResultatValidation:
    """
    Exécute l'ensemble des validations du dossier.

    Parameters
    ----------
    donnees:
        Variables préparées pour le modèle.

    avec_grade:
        True lorsque le modèle avec loan_grade est utilisé.

    Returns
    -------
    ResultatValidation
        Objet contenant les erreurs, avertissements
        et informations.
    """

    resultat = ResultatValidation()

    verifier_variables_obligatoires(
        donnees=donnees,
        avec_grade=avec_grade,
        resultat=resultat,
    )

    # Si une variable obligatoire manque, les autres contrôles
    # ne peuvent pas être exécutés correctement.
    if not resultat.valide:
        return resultat

    verifier_contraintes_physiques(
        donnees=donnees,
        resultat=resultat,
    )

    verifier_variables_categorielles(
        donnees=donnees,
        avec_grade=avec_grade,
        resultat=resultat,
    )

    verifier_ratio(
        donnees=donnees,
        resultat=resultat,
    )

    verifier_domaine_entrainement(
        donnees=donnees,
        resultat=resultat,
    )

    verifier_alertes_metier(
        donnees=donnees,
        resultat=resultat,
    )

    return resultat