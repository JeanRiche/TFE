# Consignes de travail (TFE de Jean-Riche Ntumba Panzu)

Sujet : régulation d'un convertisseur Buck par un PID auto-adaptatif basé sur
l'ELM, comparé à Ziegler-Nichols, PSO-PID, Fuzzy-PID et PINN-PID, sur la base
commune v2.1. État détaillé du travail : `ETAT_DE_REPRISE.md`.

## Posture

- Répondre en français.
- Jean-Riche demande un mentor exigeant : remettre en question ses hypothèses,
  ne pas valider par complaisance, dire ce qui ne tient pas et pourquoi.
- Méthode de travail : critères et prévisions écrits et commités avant chaque
  calcul ; aucun réglage sur les onze essais de développement (essais de réglage : E1 à E4) ; chaque modification
  d'une méthode est justifiée par une référence vérifiée et documentée ;
  résultats publiés même quand ils contredisent l'attente.
- Ne jamais choisir un scénario ou une grandeur d'après le classement qu'on
  veut obtenir.

## Rédaction (consigne du 8 octobre 2026)

- Les chapitres du mémoire sont rédigés avec Jean-Riche, chapitre par chapitre.
- Pour toute rédaction, et aussi pour le ton de la conversation, appliquer les
  skills `humanizer` (écriture naturelle, sans tics de texte généré),
  `remove-ai-marks` (nettoyer les marques de provenance des documents livrés)
  et `doc-to-markdown` (convertir les .docx fournis en Markdown avant de les
  travailler).
- Ordre de rédaction (consigne du 10 octobre 2026) : chapitre 5 (simulation
  et analyse des performances), puis chapitre 6 (perspectives et extension),
  puis, à rebours, les chapitres 4, 3, 2 et 1 (consigne du 10 octobre 2026).
  Les chapitres 1 à 4 sont écrits pour aboutir aux chapitres 5 et 6 : s'y
  référer pour éviter toute incohérence. Un registre
  `REDACTION/dependances_chapitres.md` liste ce que chaque chapitre écrit
  suppose des chapitres antérieurs (notations, définitions, équations) ;
  chaque chapitre antérieur doit le fournir, et rien de plus.
- Avant de rédiger un chapitre, soumettre d'abord son plan à Jean-Riche et
  attendre son accord.
- Forme : `REDACTION/guide_de_forme.md` (thèse de référence). Le travail doit
  être très bien référencé ; aucune source citée sans vérification.
- Corps du chapitre 5 : seulement les scénarios de comparaison (S1, S2, S3,
  S8a, S10) ; les autres essais sont renvoyés à l'annexe sur GitHub.
- Exigences (consigne du 10 octobre 2026) : la rigueur appliquée au
  chapitre 5 vaut pour tous les chapitres, et peut être renforcée (chaque
  chiffre vérifié dans le dépôt, chaque référence vérifiée, notes de
  relecture avec les sources). La skill `humanizer` est obligatoire pour
  toute rédaction. Travail final concis et clair, sans zone d'ombre, sans
  redondance ni passage non pertinent ; le chapitre 5 est le plus long, les
  autres se limitent au nécessaire.
- Chapitre 6 : il découle du chapitre 5 ; après validation de son plan, il
  est rédigé en entier d'un seul tenant.
- Livraison des chapitres : en Word (gabarit du guide de forme), nettoyé
  avec `remove-ai-marks` et audit des métadonnées et caractères invisibles.

## Organisation du travail (consigne du 8 octobre 2026)

- Claude ne fait pas le travail lui-même : il le délègue toujours à des
  sous-agents et garde le rôle d'orchestrateur (cadrage, vérification,
  synthèse).
- Routage : un modèle rapide pour le code simple et les résumés ; le modèle
  le plus puissant pour l'architecture et la refactorisation, avec
  parcimonie. La correspondance exacte des modèles est dans les préférences
  personnelles de Jean-Riche (pas de nom de modèle dans le dépôt).
- Chaque sous-agent reçoit le contexte minimal utile, plus les règles de
  méthode qui touchent sa tâche (critères écrits avant le calcul, aucun
  réglage sur les onze essais, références vérifiées).
- Chaque résultat de sous-agent est résumé en trois lignes pour Jean-Riche.
- Vérification : relire le diff avant de conclure.

## Décisions en vigueur

- ELM-PID : option B adoptée le 8 octobre 2026 (même bloc PID parallèle que les
  autres méthodes, l'ELM ajuste ses gains). La version à loi incrémentale de Lu
  est conservée comme référence pour justifier ce choix au chapitre 4.
- PINN-PID : version finale (dossier PINN_PID) : bloc PID commun, coût et
  optimisation d'Ito et Wasa en itération temps réel, zone morte commune avec
  l'ELM-PID ; les autres versions ne sont gardées que dans l'historique git.

## Dépôt

- Branche de travail : `claude/clever-newton-1t2wt7`.
- Pas d'identifiant de modèle dans les commits ni dans les fichiers.
