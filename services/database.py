from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Generator

import pandas as pd

from config import (
    DATABASE_PATH,
    DATA_DIR,
)


# ============================================================
# Connexion à SQLite
# ============================================================

@contextmanager
def connexion_db() -> Generator[
    sqlite3.Connection,
    None,
    None,
]:
    """
    Ouvre une connexion SQLite et garantit sa fermeture.
    """

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    connexion = sqlite3.connect(
        DATABASE_PATH
    )

    connexion.row_factory = sqlite3.Row

    try:
        yield connexion
        connexion.commit()

    except Exception:
        connexion.rollback()
        raise

    finally:
        connexion.close()


# ============================================================
# Initialisation de la base
# ============================================================

def initialiser_base() -> None:
    """
    Crée les tables nécessaires.
    """

    with connexion_db() as connexion:

        connexion.execute(
            """
            CREATE TABLE IF NOT EXISTS dossiers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference_dossier TEXT UNIQUE NOT NULL,
                identifiant_client TEXT,
                agence TEXT,
                analyste TEXT,
                date_creation TEXT NOT NULL,
                donnees_administratives_json TEXT NOT NULL
            )
            """
        )

        connexion.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dossier_id INTEGER NOT NULL,
                date_evaluation TEXT NOT NULL,
                mode_evaluation TEXT NOT NULL,
                algorithme TEXT,
                version_modele TEXT,
                probabilite_defaut REAL NOT NULL,
                indice_risque INTEGER NOT NULL,
                categorie_risque TEXT NOT NULL,
                seuil REAL NOT NULL,
                classe_predite INTEGER NOT NULL,
                donnees_modele_json TEXT NOT NULL,
                FOREIGN KEY (dossier_id)
                    REFERENCES dossiers(id)
            )
            """
        )

        connexion.execute(
            """
            CREATE TABLE IF NOT EXISTS decisions_humaines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evaluation_id INTEGER NOT NULL,
                decision TEXT NOT NULL,
                justification TEXT,
                utilisateur TEXT,
                date_decision TEXT NOT NULL,
                FOREIGN KEY (evaluation_id)
                    REFERENCES evaluations(id)
            )
            """
        )


# ============================================================
# Enregistrement du dossier
# ============================================================

def enregistrer_dossier(
    donnees_administratives: dict[str, Any],
) -> int:
    """
    Enregistre ou retrouve un dossier selon sa référence.
    """

    reference = donnees_administratives.get(
        "reference_dossier"
    )

    if not reference:
        raise ValueError(
            "La référence du dossier est obligatoire."
        )

    with connexion_db() as connexion:

        existant = connexion.execute(
            """
            SELECT id
            FROM dossiers
            WHERE reference_dossier = ?
            """,
            (reference,),
        ).fetchone()

        if existant:
            return int(
                existant["id"]
            )

        curseur = connexion.execute(
            """
            INSERT INTO dossiers (
                reference_dossier,
                identifiant_client,
                agence,
                analyste,
                date_creation,
                donnees_administratives_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                reference,
                donnees_administratives.get(
                    "identifiant_client"
                ),
                donnees_administratives.get(
                    "agence"
                ),
                donnees_administratives.get(
                    "analyste"
                ),
                datetime.now().isoformat(
                    timespec="seconds"
                ),
                json.dumps(
                    donnees_administratives,
                    ensure_ascii=False,
                    default=str,
                ),
            ),
        )

        return int(
            curseur.lastrowid
        )


# ============================================================
# Enregistrement d'une évaluation
# ============================================================

def enregistrer_evaluation(
    dossier_id: int,
    donnees_modele: dict[str, Any],
    resultat: dict[str, Any],
) -> int:
    """
    Enregistre le résultat d'une prédiction.
    """

    with connexion_db() as connexion:

        curseur = connexion.execute(
            """
            INSERT INTO evaluations (
                dossier_id,
                date_evaluation,
                mode_evaluation,
                algorithme,
                version_modele,
                probabilite_defaut,
                indice_risque,
                categorie_risque,
                seuil,
                classe_predite,
                donnees_modele_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                dossier_id,
                datetime.now().isoformat(
                    timespec="seconds"
                ),
                resultat["mode"],
                resultat.get("algorithme"),
                resultat.get("version_modele"),
                resultat["probabilite_defaut"],
                resultat["indice_risque"],
                resultat["categorie_risque"],
                resultat["seuil"],
                resultat["classe_predite"],
                json.dumps(
                    donnees_modele,
                    ensure_ascii=False,
                    default=str,
                ),
            ),
        )

        return int(
            curseur.lastrowid
        )


# ============================================================
# Décision humaine
# ============================================================

def enregistrer_decision_humaine(
    evaluation_id: int,
    decision: str,
    justification: str,
    utilisateur: str,
) -> int:
    """
    Enregistre la décision finale prise par l'analyste.
    """

    decisions_autorisees = {
        "APPROUVE",
        "REFUSE",
        "REVUE",
    }

    if decision not in decisions_autorisees:
        raise ValueError(
            "Décision humaine invalide."
        )

    with connexion_db() as connexion:

        curseur = connexion.execute(
            """
            INSERT INTO decisions_humaines (
                evaluation_id,
                decision,
                justification,
                utilisateur,
                date_decision
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                evaluation_id,
                decision,
                justification,
                utilisateur,
                datetime.now().isoformat(
                    timespec="seconds"
                ),
            ),
        )

        return int(
            curseur.lastrowid
        )


# ============================================================
# Lecture de l'historique
# ============================================================

def lire_historique(
    limite: int | None = None,
) -> pd.DataFrame:
    """
    Retourne l'historique des évaluations.
    """

    requete = """
        SELECT
            e.id AS evaluation_id,
            d.reference_dossier,
            d.identifiant_client,
            d.agence,
            d.analyste,
            e.date_evaluation,
            e.mode_evaluation,
            e.algorithme,
            e.version_modele,
            e.probabilite_defaut,
            e.indice_risque,
            e.categorie_risque,
            e.seuil,
            e.classe_predite
        FROM evaluations e
        INNER JOIN dossiers d
            ON e.dossier_id = d.id
        ORDER BY e.date_evaluation DESC
    """

    parametres: tuple[Any, ...] = ()

    if limite is not None:
        requete += " LIMIT ?"
        parametres = (
            int(limite),
        )

    with connexion_db() as connexion:
        return pd.read_sql_query(
            requete,
            connexion,
            params=parametres,
        )


# ============================================================
# Lecture détaillée d'une évaluation
# ============================================================

def lire_evaluation(
    evaluation_id: int,
) -> dict[str, Any] | None:
    """
    Retourne une évaluation complète.
    """

    with connexion_db() as connexion:

        ligne = connexion.execute(
            """
            SELECT
                e.*,
                d.reference_dossier,
                d.identifiant_client,
                d.agence,
                d.analyste,
                d.donnees_administratives_json
            FROM evaluations e
            INNER JOIN dossiers d
                ON e.dossier_id = d.id
            WHERE e.id = ?
            """,
            (evaluation_id,),
        ).fetchone()

    if ligne is None:
        return None

    resultat = dict(
        ligne
    )

    resultat["donnees_modele"] = json.loads(
        resultat.pop(
            "donnees_modele_json"
        )
    )

    resultat["donnees_administratives"] = json.loads(
        resultat.pop(
            "donnees_administratives_json"
        )
    )

    return resultat