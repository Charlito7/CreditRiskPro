# Adaptation au dernier notebook

## Seuils opérationnels

- Modèle avec `loan_grade` : **0,45**
- Modèle sans `loan_grade` : **0,40**
- Méthode : seuil maximisant le F1-score par validation croisée sur les données d'entraînement.

## Modifications réalisées

- ajout de `modeles_scoring/seuils_decision.joblib` ;
- chargement automatique du seuil propre au modèle sélectionné ;
- repli sécurisé sur `manifest_modeles.json` si le fichier de seuils est absent ;
- mise à jour du manifeste avec les paramètres, seuils et métriques du dernier notebook ;
- correction de la page « Suivi des modèles » pour afficher `metriques_test` ;
- validation des seuils et test d'une prédiction pour chaque mode.

## Résultats du dernier notebook

| Métrique | Avec loan_grade | Sans loan_grade |
|---|---:|---:|
| Accuracy | 0,9340 | 0,9211 |
| Precision | 0,9550 | 0,9104 |
| Recall | 0,7334 | 0,7097 |
| F1-score | 0,8297 | 0,7976 |
| ROC-AUC | 0,9463 | 0,9365 |
| PR-AUC | 0,8991 | 0,8812 |
