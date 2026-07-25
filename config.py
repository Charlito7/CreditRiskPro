from pathlib import Path


# =========================================================
# Chemins principaux de l'application
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

MODELS_DIR = BASE_DIR / "modeles_scoring"

DATA_DIR = BASE_DIR / "data"

ASSETS_DIR = BASE_DIR / "assets"

MANIFEST_PATH = MODELS_DIR / "manifest_modeles.json"

SEUILS_PATH = MODELS_DIR / "seuils_decision.joblib"

DATABASE_PATH = DATA_DIR / "creditrisk.db"


# =========================================================
# Informations générales de l'application
# =========================================================

APP_NAME = "CreditRisk Pro"

APP_VERSION = "0.1.0"

APP_DESCRIPTION = (
    "Plateforme intelligente d'aide à la décision "
    "pour l'évaluation et le suivi du risque de crédit."
)


# =========================================================
# Modes de prédiction
# =========================================================

MODE_AVEC_GRADE = "avec_grade"

MODE_SANS_GRADE = "sans_grade"

MODES_AUTORISES = [
    MODE_AVEC_GRADE,
    MODE_SANS_GRADE,
]


LIBELLES_MODES = {
    MODE_AVEC_GRADE: "Avec loan_grade",
    MODE_SANS_GRADE: "Sans loan_grade",
}


# =========================================================
# Fichiers des modèles
# =========================================================

FICHIERS_MODELES = {
    MODE_AVEC_GRADE: (
        MODELS_DIR
        / "xgboost_avec_loan_grade.joblib"
    ),
    MODE_SANS_GRADE: (
        MODELS_DIR
        / "xgboost_sans_loan_grade.joblib"
    ),
}


# Alias éventuel pour compatibilité avec d'autres fichiers
MODEL_FILES = FICHIERS_MODELES


# =========================================================
# Bandes de risque par défaut
# =========================================================

BANDES_RISQUE_PAR_DEFAUT = {
    "faible": [0.00, 0.10],
    "modere": [0.10, 0.20],
    "eleve": [0.20, 0.35],
    "tres_eleve": [0.35, 1.01],
}


# =========================================================
# Domaines observés dans les données d'entraînement
# =========================================================

DOMAINES_ENTRAINEMENT = {
    "person_age": {
        "minimum": 20,
        "q1": 23,
        "mediane": 26,
        "q3": 30,
    },
    "person_income": {
        "minimum": 4_000,
        "q1": 38_500,
        "mediane": 55_000,
        "q3": 79_200,
        "maximum_observe": 6_000_000,
    },
    "person_emp_length": {
        "minimum": 0,
        "q1": 2,
        "mediane": 4,
        "q3": 7,
    },
    "loan_amnt": {
        "minimum": 500,
        "q1": 5_000,
        "mediane": 8_000,
        "q3": 12_200,
        "maximum_observe": 35_000,
    },
    "loan_int_rate": {
        "minimum": 5.42,
        "q1": 7.90,
        "mediane": 10.99,
        "q3": 13.47,
        "maximum_observe": 23.22,
    },
    "loan_percent_income": {
        "minimum": 0,
        "q1": 0.09,
        "mediane": 0.15,
        "q3": 0.23,
        "maximum_observe": 0.83,
    },
    "cb_person_cred_hist_length": {
        "minimum": 2,
        "q1": 3,
        "mediane": 4,
        "q3": 8,
        "maximum_observe": 30,
    },
}


# =========================================================
# Création automatique des dossiers nécessaires
# =========================================================

MODELS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

ASSETS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)