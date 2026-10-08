# Consignes de travail (TFE de Jean-Riche Ntumba Panzu)

Sujet : régulation d'un convertisseur Buck par un PID auto-adaptatif basé sur
l'ELM, comparé à Ziegler-Nichols, PSO-PID, Fuzzy-PID et PINN-PID, sur la base
commune v2.1. État détaillé du travail : `ETAT_DE_REPRISE.md`.

## Posture

- Répondre en français.
- Jean-Riche demande un mentor exigeant : remettre en question ses hypothèses,
  ne pas valider par complaisance, dire ce qui ne tient pas et pourquoi.
- Méthode de travail : critères et prévisions écrits et commités avant chaque
  calcul ; aucun réglage sur les onze essais de jugement ; chaque modification
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

## Décisions en vigueur

- ELM-PID : option B adoptée le 8 octobre 2026 (même bloc PID parallèle que les
  autres méthodes, l'ELM ajuste ses gains). La version à loi incrémentale de Lu
  est conservée comme référence pour justifier ce choix au chapitre 4.
- PINN-PID : version du 5 octobre conservée pour l'instant ; elle sera reprise
  en suivant entièrement l'article d'Ito et Wasa une fois l'ELM terminé.

## Dépôt

- Branche de travail : `claude/clever-newton-1t2wt7`.
- Pas d'identifiant de modèle dans les commits ni dans les fichiers.
