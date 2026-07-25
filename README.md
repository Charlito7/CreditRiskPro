# Application de scoring de crédit

Cette application Streamlit permet de choisir entre deux modèles XGBoost :

- avec `loan_grade` ;
- sans `loan_grade`.

## Installation sous Windows

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Modèles attendus

Copiez dans `modeles_scoring/` :

- `xgboost_avec_loan_grade.joblib`
- `xgboost_sans_loan_grade.joblib`
- `manifest_modeles.json`

Le fichier `manifest_modeles_exemple.json` montre la structure attendue.
