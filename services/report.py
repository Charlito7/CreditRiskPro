from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from services.utils import (
    formater_montant,
    formater_pourcentage,
    obtenir_recommandation,
    traduire_categorie_risque,
)


def creer_tableau(
    donnees: list[list[str]],
    largeurs: list[float] | None = None,
) -> Table:
    """
    Crée un tableau ReportLab avec un style uniforme.
    """

    tableau = Table(
        donnees,
        colWidths=largeurs,
    )

    tableau.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#0B3A66"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#D9E4EC"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    return tableau


def generer_rapport_pdf(
    donnees_administratives: dict[str, Any],
    donnees_modele: dict[str, Any],
    resultat: dict[str, Any],
) -> bytes:
    """
    Génère un rapport PDF et retourne son contenu en mémoire.
    """

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="TextePetit",
            parent=styles["BodyText"],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#627D98"),
        )
    )

    elements = []

    elements.append(
        Paragraph(
            "CreditRisk Pro",
            styles["Title"],
        )
    )

    elements.append(
        Paragraph(
            "Rapport d'évaluation du risque de crédit",
            styles["Heading2"],
        )
    )

    elements.append(
        Spacer(
            1,
            0.4 * cm,
        )
    )

    reference = donnees_administratives.get(
        "reference_dossier",
        "Non renseignée",
    )

    elements.append(
        Paragraph(
            f"<b>Référence :</b> {reference}",
            styles["BodyText"],
        )
    )

    elements.append(
        Paragraph(
            f"<b>Date :</b> "
            f"{datetime.now().strftime('%d/%m/%Y %H:%M')}",
            styles["BodyText"],
        )
    )

    elements.append(
        Spacer(
            1,
            0.5 * cm,
        )
    )

    synthese = [
        [
            "Indicateur",
            "Résultat",
        ],
        [
            "Probabilité de défaut",
            formater_pourcentage(
                resultat["probabilite_defaut"],
                decimales=2,
            ),
        ],
        [
            "Indice de risque",
            f"{resultat['indice_risque']} / 1000",
        ],
        [
            "Catégorie",
            traduire_categorie_risque(
                resultat["categorie_risque"]
            ),
        ],
        [
            "Seuil opérationnel",
            formater_pourcentage(
                resultat["seuil"],
                decimales=2,
            ),
        ],
        [
            "Signal du modèle",
            (
                "Dossier signalé"
                if resultat["classe_predite"] == 1
                else "Dossier non signalé"
            ),
        ],
        [
            "Mode",
            resultat["mode"],
        ],
        [
            "Algorithme",
            resultat.get(
                "algorithme",
                "XGBoost",
            ),
        ],
    ]

    elements.append(
        creer_tableau(
            synthese,
            largeurs=[
                8 * cm,
                8 * cm,
            ],
        )
    )

    elements.append(
        Spacer(
            1,
            0.5 * cm,
        )
    )

    elements.append(
        Paragraph(
            "Recommandation",
            styles["Heading2"],
        )
    )

    elements.append(
        Paragraph(
            obtenir_recommandation(
                resultat["categorie_risque"]
            ),
            styles["BodyText"],
        )
    )

    elements.append(
        Spacer(
            1,
            0.5 * cm,
        )
    )

    informations_pret = [
        [
            "Variable",
            "Valeur",
        ],
        [
            "Âge",
            str(
                donnees_modele.get(
                    "person_age",
                    "",
                )
            ),
        ],
        [
            "Revenu annuel",
            formater_montant(
                float(
                    donnees_modele.get(
                        "person_income",
                        0,
                    )
                )
            ),
        ],
        [
            "Montant du prêt",
            formater_montant(
                float(
                    donnees_modele.get(
                        "loan_amnt",
                        0,
                    )
                )
            ),
        ],
        [
            "Taux d'intérêt",
            f"{donnees_modele.get('loan_int_rate', '')} %",
        ],
        [
            "Ratio prêt/revenu",
            formater_pourcentage(
                float(
                    donnees_modele.get(
                        "loan_percent_income",
                        0,
                    )
                ),
                decimales=2,
            ),
        ],
        [
            "Objet du prêt",
            str(
                donnees_modele.get(
                    "loan_intent",
                    "",
                )
            ),
        ],
    ]

    if "loan_grade" in donnees_modele:
        informations_pret.append(
            [
                "Grade",
                str(
                    donnees_modele["loan_grade"]
                ),
            ]
        )

    elements.append(
        Paragraph(
            "Données principales",
            styles["Heading2"],
        )
    )

    elements.append(
        creer_tableau(
            informations_pret,
            largeurs=[
                8 * cm,
                8 * cm,
            ],
        )
    )

    elements.append(
        Spacer(
            1,
            0.5 * cm,
        )
    )

    elements.append(
        Paragraph(
            "Ce rapport constitue une aide à la décision. "
            "La décision finale doit être prise conformément "
            "aux politiques de l'institution et validée par "
            "un utilisateur autorisé.",
            styles["TextePetit"],
        )
    )

    document.build(
        elements
    )

    contenu = buffer.getvalue()

    buffer.close()

    return contenu