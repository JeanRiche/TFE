# État de reprise — TFE PID auto-adaptatif (ELM) et comparaison

*Mis à jour le 8 octobre 2026 (versions finales). Dépôt `jeanriche/tfe`, branche `claude/clever-newton-1t2wt7`.*

Base commune v2.1 pour tout ce qui suit : circuit L = 10 mH, C = 47 µF, R = 5 Ω, Vin = 200 V, fs = 22 kHz, régulateur à Tc = 1/220 000 s. Il y a onze essais (S1 à S9, S7a/b, S8a/b). Le coût **J** est la moyenne de 13 rapports d'IAE à Ziegler-Nichols : 10 termes d'IAE de 30 ms à la fin (S1, S3–S9) et 3 termes d'IAE de démarrage (S1, S8a, S8b). Banc : `banc_commun.py`.

**En bref (8 oct.).** Les cinq méthodes sont figées : Ziegler-Nichols, PSO-PID (J = 0.714), Fuzzy-PID (0.877), ELM-PID option B (0.746), PINN-PID final (0.757). Les chiffres de référence sont ceux du banc Python. Scénarios du corps : S1, S2, S3, S8a. Reste à faire : Simulink de l'ELM-PID et du PINN-PID (Jean-Riche), puis la rédaction.

Dossiers de premier niveau : `COMPARAISON/`, `ELM_PID/` (retenu), `ELM_PID_INCREMENTAL/` (chapitre 4), `FUZZY_PID/`, `PINN_PID/` (version finale seule), `PSO_PID/`, `REDACTION/`, plus les archives et documents versés par Jean-Riche. Les versions abandonnées (`PINN_PID` du 5 octobre, `PINN_PID_B`, `PINN_PID_C` sous ce nom, `ELM_PID_B2`) ne sont plus que dans l'historique git.

---

## 1. Statuts utilisés

| Statut | Signification |
|---|---|
| **SIMULINK** | Exécuté sous MATLAB R2024a par Jean-Riche ; sortie console collée dans la conversation ou fichier `.mat` de résultats relu, et comparé au banc. **Aucune capture d'écran n'a été fournie** : les preuves sont textuelles (console) ou numériques (`.mat`). |
| **BANC** | Testé seulement sur le banc Python, ici. |
| **VÉRIF-FAB** | Vérificateur Python testé ici sur des modèles `.slx` fabriqués (un conforme, un faux) ou sur d'anciens modèles construits par Jean-Riche, sans MATLAB. |
| **NON TESTÉ** | Script MATLAB jamais exécuté (pas de MATLAB ici), ou exécuté seulement dans une version antérieure. |

---

## 2. Fichiers créés ou modifiés, avec leur statut réel

Les copies de la base commune présentes dans chaque dossier sont identiques et ne sont pas répétées : `Buck_Commun.slx`, trois `PID_Classique_Control*.slx`, `banc_commun.py`, `charger_scenario.m`, `scenario_S*.mat`, `scenarios_communs.json`, `verifier_modele_commun.py`, `predictions_banc_pid_classique.json` et `predictions_banc_pid_fige.json`. La base commune elle-même a été validée avant cette série de séances.

### 2.1 `FUZZY_PID/` — Fuzzy-PID (Zhao, Tomizuka, Isaka 1993)

| Fichier | Rôle | Statut |
|---|---|---|
| `criteres_fuzzy_pid.txt` | méthode, écarts, prévisions, résultats, amendement 1, validation Simulink | document |
| `banc_fuzzy_pid.py`, `banc_fuzzy_pid_sortie_console.txt`, `banc_fuzzy_pid_resultats.json`, `banc_fuzzy_pid.png`, `fuzzy_pid_surfaces.png` | banc et résultats (J = 0.877) | BANC, puis confirmé SIMULINK |
| `ordonnanceur_flou_zhao.m`, `fuzzy_pid_reglages.mat` | bloc MATLAB System | SIMULINK (6 oct., rejeu identique à 1e-16) |
| `Tester_Fuzzy_PID_Rejeu.m`, `reference_rejeu_fuzzy_pid.mat` | rejeu pas à pas | SIMULINK (6 oct.) |
| `Construction_Fuzzy_PID.m`, `verifier_modele_fuzzy_pid.py`, `Simuler_Fuzzy_PID.m`, `predictions_banc_fuzzy_pid.json` | modèle commun, 11 essais | SIMULINK (6 oct. : IAE à 0.2 % près ; S7a +4.8 %) |
| `Construction_Fuzzy_PID_Trois_Modeles.m`, `verifier_modeles_fuzzy_pid_trois.py`, `Simuler_Fuzzy_PID_Trois_Modeles.m` | nominal, F1, F2 | SIMULINK (6 oct. : 1.49 / 2.43 / 7.96 mV·s contre 1.49 / 2.43 / 7.94 au banc) |
| `Diagnostic_T1_Fuzzy.m`, `comparer_diagnostic_T1.py`, `diagnostic_T1_fuzzy.mat` | diagnostic de l'auto-test T1 | SIMULINK (6 oct.) |
| `LISEZMOI_FUZZY.txt` | mode d'emploi | document (rappels ELM et PINN corrigés le 8 oct.) |
| `banc_elm_pid_resultats.json`, `banc_pinn_pid_resultats.json` | copies pour le rappel des autres méthodes | copies des versions finales (ELM 0.746, PINN 0.757), rafraîchies le 8 oct. |

### 2.2 `PSO_PID/` — PSO-PID (essaim de Gaing 2004, coût modifié)

| Fichier | Rôle | Statut |
|---|---|---|
| `criteres_pso_pid.txt` | méthode, modifications M1–M3 et références, prévisions R1–R7, résultats | document |
| `recherche_pso_pid.py`, `recherche_pso_pid.json`, `recherche_pso_pid_sortie_console.txt` | 5 recherches (graines 1–5), contrôle de reprise identique | BANC |
| `banc_pso_pid.py`, `banc_pso_pid_sortie_console.txt`, `banc_pso_pid_resultats.json`, `banc_pso_pid.png`, `pso_pid_convergence.png`, `predictions_banc_pso_pid.json` | jugement sur les 11 essais (J = 0.714) | BANC |
| `Construction_PSO_PID.m`, `Simuler_PSO_PID.m` | modèle commun | **NON TESTÉ** (jamais lancé sous MATLAB) |
| `verifier_pso_pid.py` | vérificateur du modèle commun | VÉRIF-FAB |
| `Construction_PSO_PID_Trois_Modeles.m`, `Simuler_PSO_PID_Trois_Modeles.m` | trois modèles de base | **NON TESTÉ** |
| `verifier_modeles_pso_pid_trois.py` | vérificateur des trois modèles | VÉRIF-FAB |
| `LISEZMOI_PSO.txt` | mode d'emploi | document (rappels ELM 0.746 et PINN 0.757 corrigés le 8 oct.) |
| `banc_elm_pid_resultats.json`, `banc_pinn_pid_resultats.json`, `banc_fuzzy_pid_resultats.json` | copies pour le rappel | copies des versions finales (8 oct.) |

### 2.3 `ELM_PID/` — ELM-PID option B (8 oct. : bloc PID commun à gains externes, M1–M4)

| Fichier | Rôle | Statut |
|---|---|---|
| `criteres_elm_pid.txt` | méthode, diagnostics, M1–M4 et références, prévisions Q1–Q8 (commit 1d16b45, avant calcul), résultats, lecture | document |
| données d'apprentissage, `entrainement_elm.py`, `elm_pid_modele.mat` | inchangés depuis la version incrémentale | SIMULINK (données) / BANC (modèle) |
| `ensemble_gains_elm.py` v2, `.mat`, `.json`, `…_sortie_console.txt` | ensemble admissible pour le bloc parallèle (marge du départ 24.93°) | BANC |
| `mise_au_point_elm_pid.py` v2, `…_sortie_console.txt` | contrôles E1–E4 avant prévisions | BANC |
| `banc_elm_pid.py` v4, sorties, `predictions_banc_elm_pid.json`, `reference_rejeu_elm_pid.mat`, `elm_pid_reglages.mat` | jugement (J = 0.746, Q1–Q8 justes) | BANC |
| `elm_pid_adaptatif.m` v4 | adaptateur : (e, mesure, u) → [P I D], sans traversée directe | **NON TESTÉ** sous MATLAB ; rejeu émulé en Python identique |
| `Tester_ELM_PID_Rejeu.m` v4, `Construction_ELM_PID.m` v4, `Simuler_ELM_PID.m`, les trois scripts « Trois_Modeles » | chaîne Simulink, montage du Fuzzy-PID | **NON TESTÉ** sous MATLAB |
| `verifier_modele_elm_pid.py` v4, `verifier_modeles_elm_pid_trois.py` v3 | vérificateurs | VÉRIF-FAB (modèles fabriqués conformes acceptés, entrées inversées rejetées) |
| `LISEZMOI_ELM.txt` | mode d'emploi | document |

### 2.3bis `ELM_PID_INCREMENTAL/` — version incrémentale (loi de Lu, M1–M3), gardée pour le chapitre 4

Ancien dossier `ELM_PID` renommé tel quel le 8 oct. (J = 0.728, validé SIMULINK le 7 oct., sauf les trois modèles de base jamais lancés). Seule modification : note en tête de `LISEZMOI_ELM.txt`. Les scripts de `COMPARAISON/diagnostic_lois/` le lisent.

### 2.4 `PINN_PID/` — PINN-PID final (Ito & Wasa 2025, arXiv:2510.04591)

Bloc PID commun à gains externes ; coût (éq. 13) et Adam d'Ito et Wasa en itération temps réel (5 itérations par fenêtre de 0.5 ms) ; projection sur une boîte ; observateur (EKF) car seule Vout est mesurée ; zone morte de 0.1 V sur l'erreur efficace de la fenêtre (même seuil que l'ELM-PID), choisie après un premier calcul sans elle parmi trois corrections testées sur E1–E4.

| Fichier | Rôle | Statut |
|---|---|---|
| `criteres_pinn_pid.txt` | document unique : reprise de l'article (pages, équations), écarts déclarés, contrôles, choix de la correction, prévisions, résultats, Simulink | document (réécrit le 8 oct.) |
| `criteres_etape2_pinn.txt`, `criteres_etape3_estimation.txt`, `entrainement_pinn*.{py,json}`, `pinn_candidat_*.npz`, `pinn_pid_modele.mat`, `estimation_etat_pinn.{py,json}` | PINN et estimation de l'état (5 oct.) | BANC (données d'apprentissage : SIMULINK) |
| `boite_gains_pinn.py`, `.json`, `…_sortie_console.txt` | boîte des gains pour le bloc parallèle | BANC (relancé le 8 oct. : JSON identique) |
| `regle_choix_correction_pinn.json`, `previsions_pinn_pid.json` | règle et prévisions commitées avant le calcul | gardées octet pour octet |
| `mise_au_point_pinn_pid.py`, `…_sortie_console.txt`, `choix_correction_pinn.json` | contrôles et choix de la correction sur E1–E4 (C1) | BANC (relancé le 8 oct. : identique) |
| `banc_pinn_pid.py`, sorties, `predictions_banc_pinn_pid.json`, `pinn_pid_reglages.mat` (VERSION 3), `reference_rejeu_pinn_pid.mat` | jugement sur les onze essais (J = 0.757) | BANC (relancé le 8 oct. après renommage : mêmes chiffres) |
| `ensemble_gains_elm.mat`, `.json` | ensemble de l'ELM-PID (candidate C3, ablations) | copie de `ELM_PID` |
| `pinn_pid_adaptatif.m` v3 | adaptateur : (e, mesure, u) → [P I D] | **NON TESTÉ** sous MATLAB ; rejeu émulé en Python identique (8 oct.) |
| `Tester_PINN_PID_Rejeu.m`, `Construction_PINN_PID.m`, `Simuler_PINN_PID.m`, les trois scripts « Trois_Modeles » | chaîne Simulink, même montage que l'ELM-PID | **NON TESTÉ** sous MATLAB |
| `verifier_modele_pinn_pid.py`, `verifier_modeles_pinn_pid_trois.py` | vérificateurs | VÉRIF-FAB |
| `LISEZMOI_PINN.txt` | mode d'emploi, ordre d'exécution MATLAB | document |

### 2.5 `COMPARAISON/`

| Fichier | Rôle | Statut |
|---|---|---|
| `criteres_comparaison.txt` | règle de choix du scénario (commitée avant le calcul, inchangée), résultats successifs ; dernière section : versions finales | document |
| `comparaison_methodes.py`, `…_sortie_console.txt`, `comparaison_resultats.json`, `classement_par_essai.png` | tableau par essai, critères C1–C4 ; avec les versions finales, aucun scénario désigné | BANC (8 oct.) |
| `simulations_scenario.py`, `simulations_scenario_sortie_console.txt` (S4), `simulations_scenario_S8a_sortie_console.txt`, `robustesse_S4.json`, `robustesse_S8a.json`, `comparaison_S4.png`, `comparaison_S8a.png`, `scenario_S4.npz`, `scenario_S8a.npz` | essai rejoué pour les 5 méthodes, robustesse L/C ±0.1 % | BANC (8 oct.) |
| `elm_incremental_contre_B.py` et sorties | les deux versions de l'ELM-PID (chapitre 4) | BANC |
| `banc_*_resultats.json` (4 copies) | données d'entrée | copies des versions finales (ELM 0.746, PINN 0.757) |
| `LISEZMOI_COMPARAISON.txt` | mode d'emploi | document |
| `diagnostic_lois/diagnostic_perturbations.py`, `diagnostic_cout_J.py` et leurs sorties | diagnostic de la loi de Lu (lisent `ELM_PID_INCREMENTAL`) | BANC (relancés le 8 oct. : mêmes chiffres) |

### 2.6 Racine

| Fichier | Statut |
|---|---|
| `ETAT_DE_REPRISE.md` (ce fichier), `CLAUDE.md` | documents |
| `REDACTION/` | rédaction du mémoire |
| `ELM1–4.zip`, `PINN1–2.zip`, `FUZZY.zip`, `PSO.zip`, `*.docx` | archives et documents versés par Jean-Riche, non modifiés |

---

## 3. Décisions

### 3.1 Décisions prises par Jean-Riche

| Date | Décision |
|---|---|
| 5 oct. | PINN-PID : même loi (Lu), même départ, même boîte que l'ELM-PID. |
| 6 oct. | Chaque méthode est autonome et appliquée en entier ; elle ne partage que le système de base. Fuzzy et PSO n'ont rien à voir avec l'ELM. |
| 6 oct. | Fuzzy : méthode de Zhao directement dans la boîte, fenêtres de 0.5 ms, codé à la main, seuils du protocole ; repart du PID classique ; le point 4 reste hors de la méthode ; l'ancien Fuzzy est supprimé. |
| 6 oct. | PSO : hors ligne ; article de Gaing comme référence, mais corrigé là où il pose problème (« ne pas rester fidèle à l'article »). |
| 6 oct. | PSO : modifier l'article pour les meilleures performances, modifications documentées par la littérature. |
| 7 oct. | PSO : dossier propre ne contenant que la version améliorée. |
| 7 oct. | ELM : corriger l'absence d'adaptation « comme pour le PSO », dossier propre. « Le jacobien ne peut pas être constant » (affirmation de départ, voir §4). |
| 7 oct. | ELM : validation Simulink jugée bonne (« Je pense que c'est bon »). |
| 7 oct. | PINN : revenir à la version de départ (« Ok fais ça »). |
| 7 oct. | Comparaison : choisir un seul scénario et classer les cinq méthodes. |
| 8 oct. | Demande de rédiger cet état de reprise avant de trancher la suite. |
| 8 oct. | **Option B adoptée** pour l'ELM-PID (même bloc PID que les autres méthodes). La version actuelle à loi incrémentale est conservée pour justifier ce choix au chapitre 4 (S4 ou autre scénario adapté). |
| 8 oct. | Les chapitres du mémoire seront rédigés ensemble ; rédaction et conversation suivent les skills humanizer, remove-ai-marks et doc-to-markdown (voir `CLAUDE.md`). |
| 8 oct. | PINN-PID : à reprendre plus tard en suivant entièrement l'article d'Ito et Wasa, après l'ELM (fait le même jour, voir ci-dessous). |
| 8 oct. | **PINN-PID final retenu** (dossier `PINN_PID`) : bloc PID commun, coût et optimisation d'Ito et Wasa en itération temps réel, zone morte commune avec l'ELM-PID. On ne garde que cette version « comme si on n'avait eu qu'elle » ; les autres ne sont que dans l'historique git. |
| 8 oct. | ELM-PID : on garde `ELM_PID` (option B, retenue) et `ELM_PID_INCREMENTAL` (justification du choix au chapitre 4) ; `ELM_PID_B2` est abandonnée (historique git). |
| 8 oct. | **Gel des méthodes** : Ziegler-Nichols, PSO-PID, Fuzzy-PID, ELM-PID option B, PINN-PID final. Plus aucun réglage. |
| 8 oct. | **Scénarios du corps du mémoire : S1, S2, S3, S8a.** C'est un choix de l'auteur : la règle de comparaison, réappliquée, ne désigne plus aucun scénario (§4.3). |
| 8 oct. | **Chiffres de référence = banc Python.** Simulink sert de validation. |

### 3.2 Décisions prises par Claude sans arbitrage explicite (Jean-Riche n'a pas objecté)

- **PSO.** Coût IAE sur quatre essais de réglage E1–E4, distincts des onze ; poids du démarrage 3/13 ; règles de faisabilité de Deb ; conditions initiales du bloc ; bornes [0 ; 4] ; essaim de Gaing gardé tel quel ; 5 graines ; graine retenue = plus petit J_réglage.
- **PSO, dossier propre.** Quatre lignes ont été gardées en tête de `criteres_pso_pid.txt`. Elles signalent qu'une première application avec le coût d'origine avait donné J = 1.69. C'est contraire à la lettre de la demande (« comme si l'autre n'avait pas existé »), pour ne pas laisser croire à des prévisions écrites à l'aveugle.
- **ELM.**
  - Conception de M1 (porte sur saturation, zone morte d'estimation de 0.1 V), M2 (ensemble admissible) et M3 (restauration de Rosen, 10 itérations).
  - Le modèle ELM n'est pas modifié (jacobien jugé non informatif).
  - T1 compare les gains au banc à 1 % près ; S3 ajouté au rejeu.
- **PINN** (version du 5 octobre, abandonnée le 8 oct. ; historique git).
  - Essai d'une variante (ensemble admissible), puis recommandation de garder la version du 5 octobre.
  - Cette recommandation **s'écarte de la règle que Claude avait écrite avant le calcul** (« garder la variante si J reste à 0.02 près »). Elle est justifiée par la simplicité et la validation Simulink existante, pas par J. C'est écrit dans `criteres_pinn_pid.txt` §6.
- **Comparaison.**
  - Grandeur : IAE de 30 ms à la fin. S1 et S7a sont exclus des candidats.
  - Seuils C1 (5 % entre voisins) et C2 (tau de Kendall ≥ 0.6 avec l'ordre par J).
- **Refus** de chercher un scénario qui donne l'ordre attendu PINN > ELM > Fuzzy > PSO > Z-N : ce serait choisir l'essai d'après son résultat.

### 3.3 Propositions de Claude non tranchées par Jean-Riche

| N° | Proposition | Où | Ce que Claude recommande |
|---|---|---|---|
| P1 (tranchée le 8 oct. : B pour l'ELM, PINN repoussé) | Corriger la loi des méthodes adaptatives : **A** dérivée sur la mesure seule ; **B** dérivée sur la mesure + PID parallèle du bloc (même PID pour les cinq méthodes, changements de gains sans à-coup) ; **C** rien changer et écrire le diagnostic | réponse du 8 oct., `COMPARAISON/diagnostic_lois/` | **B** |
| P2 | Scénario « dynamique non linéaire » défini par la physique avant le calcul (excursions à travers la conduction discontinue, Vin 150–240 V, sauts de consigne), résultat publié quel qu'il soit | réponse du 7 oct. | à faire après P1 |
| P3 (tranchée le 8 oct. : S1, S2, S3, S8a) | Présenter dans le mémoire J (tableau), les scénarios du corps et l'annexe essai par essai, plutôt qu'un seul scénario | `COMPARAISON/criteres_comparaison.txt` | oui |
| P4 (faite le 8 oct.) | Relire Ito & Wasa pour vérifier les écarts | `PINN_PID/criteres_pinn_pid.txt` §2–3 | texte relu ; écarts réécrits pour la version finale |
| P5 | Garder ou retirer les lignes d'origine en tête des documents PSO, ELM, PINN | les trois `criteres_*.txt` | garder |

---

## 4. Chiffres obtenus, avec script et scénario

Tous les chiffres viennent du banc Python (chiffres de référence), sauf mention SIMULINK. IAE en mV·s.

### 4.1 Coût J sur les onze essais (versions finales)

| Méthode | J | Après 30 ms | Démarrage | Évén. non revenus | Script (dossier) |
|---|---|---|---|---|---|
| PSO-PID | 0.714 | 0.672 | 0.855 | — | `banc_pso_pid.py` (PSO_PID) |
| meilleur PID figé (grille) | 0.738 | 0.710 | 0.831 | — | référence de la base commune |
| ELM-PID option B (retenu) | 0.746 | 0.680 | 0.967 | — | `banc_elm_pid.py` (ELM_PID) |
| PINN-PID final | 0.757 | 0.702 | 0.942 | — | `banc_pinn_pid.py` (PINN_PID) |
| Fuzzy-PID | 0.877 | 0.827 | 1.041 | — | `banc_fuzzy_pid.py` (FUZZY_PID) |
| Ziegler-Nichols | 1.000 | 1.000 | 1.000 | S8b, S9 | — |

Pour le chapitre 4 : ELM-PID incrémental (M1–M3) 0.728 (0.747 / 0.664), `ELM_PID_INCREMENTAL` ; R0 (loi de Lu, gains Z-N) 0.917.

Historique (versions abandonnées, dans l'historique git) :
- PSO selon Gaing : J = 5.03 (intégrateur préchargé), puis 1.692 (état nul).
- ELM de départ : 0.784 ; ELM avec M1–M2 seuls : 0.744.
- PINN-PID du 5 octobre (loi de Lu) : 0.684 ; sa variante « ensemble admissible » : 0.692.
- PINN-PID final sans zone morte (premier calcul) : 0.893.

### 4.2 Par méthode

**PSO-PID** (`recherche_pso_pid.py`, essais de réglage E1–E4)
- J_réglage de 0.5939 à 0.6015 selon la graine.
- Graine retenue : 3. Gains P = 0.239585, I = 412.0556, D = 1.913247e-5 (×ZN : 2.551, 1.369, 2.613).
- Marge 30.0°, coupure 2175 Hz.

**ELM-PID option B** (`banc_elm_pid.py`, 11 essais) : J = 0.746 ; prévisions Q1–Q8 justes (`ELM_PID/criteres_elm_pid.txt`). Un PID figé aux gains atteints à 4 ms sur S1 donne 0.754. Simulink : à faire.

**PINN-PID final** (`banc_pinn_pid.py`, 11 essais ; `PINN_PID/criteres_pinn_pid.txt`)
- J = 0.757116218 (0.702 / 0.942) ; tous les événements reviennent.
- Ablations : sans zone morte 0.893 ; C1+C2 0.752 ; C1+C3 0.754 ; plafond (modèle physique) 0.757 ; PID figé aux gains finaux de S1 0.768.
- Sensibilité L ou C ±0.1 % : 0.748 à 0.763.
- Prévisions : 7 justes sur 10 (P1, P2, P7 connues d'avance), P6, P9, P10 fausses.
- Simulink : à faire.

**Fuzzy-PID** (`banc_fuzzy_pid.py`)
- J = 0.877 ; SIMULINK (6 oct.) : IAE à 0.2 % près, J estimé sous Simulink 0.881.

### 4.3 Comparaison (`COMPARAISON/`, versions finales, 8 oct.)

- **La règle, réappliquée sans changement, ne désigne aucun scénario** : aucun candidat ne passe C1 (écart minimal entre voisins ≥ 5 %). ELM-PID et PINN-PID sont à 0.03 % (S3), 0.4 % (S8a), 2.4 % (S8b), 3.1 % (S4).
- Scénarios du corps fixés par Jean-Riche : S1, S2, S3, S8a. « = » : moins de 5 % d'écart, lu comme une égalité.
  - S1, IAE de démarrage : PSO 87.62 < PINN 92.06 = ELM 93.72 = Z-N 93.77 < Fuzzy 110.91 (PSO devant PINN de 5.1 %).
  - S2, IAE après 30 ms : PSO 2.04 < ELM 2.41 = Fuzzy 2.43 = PINN 2.44 < Z-N 2.84.
  - S3 : PSO 5.46 < PINN 6.40 = ELM 6.41 < Fuzzy 7.94 < Z-N 8.67.
  - S8a : PSO 2.46 < PINN 2.95 = ELM 2.96 < Fuzzy 4.12 < Z-N 12.07 (même ordre à L ou C ±0.1 %, mais PINN/ELM à 0.1–1.2 %).
- S4 pour mémoire : PSO 16.54 < PINN 18.30 = ELM 18.87 < Fuzzy 22.38 < Z-N 23.61.
- Les deux méthodes adaptatives ne se séparent ni sur J (1.5 %) ni sur les quatre essais du corps.
- La recherche sur 99 combinaisons du 7–8 oct. (anciennes versions) n'est pas sauvegardée en script ; elle n'a plus d'objet depuis le choix des scénarios.

### 4.4 Diagnostic de la loi de Lu (`COMPARAISON/diagnostic_lois/`, 8 oct.)

`diagnostic_perturbations.py` (IAE de 30 ms à la fin / écart maximal en V) :

| Variante | S2 | S3 | S4 |
|---|---|---|---|
| Z-N, PID du bloc | 2.84 / 2.01 | 8.67 | 23.61 |
| R0, loi de Lu | 5.27 / 4.81 | 8.48 | 22.74 |
| R0, dérivée sur la mesure | 3.10 / 2.01 | 8.48 | 22.74 |
| Gains PSO, PID du bloc | 2.04 | 5.46 | 16.54 |
| Gains PSO, loi de Lu | 6.56 | 7.53 | 23.50 |

Adaptation de l'ELM sur S4 : les gains changent à 52.0, 52.5, 102.0 et 102.5 ms, donc après les pointes des événements (50.2 et 100.2 ms).

`diagnostic_cout_J.py` (gains figés) :

| Gains | Loi | J | Après 30 ms | Démarrage |
|---|---|---|---|---|
| Z-N | PID du bloc | 1.000 | 1.000 | 1.000 |
| Z-N | bloc, dérivée sur la mesure | 0.970 | 1.008 | 0.843 |
| Z-N | loi de Lu | 0.917 | 0.986 | 0.687 |
| Z-N | loi de Lu, dérivée sur la mesure | 0.915 | 0.984 | 0.687 |
| PSO | PID du bloc | 0.714 | 0.672 | 0.855 |
| PSO | bloc, dérivée sur la mesure | 0.702 | 0.685 | 0.758 |
| PSO | loi de Lu | 0.707 | 0.739 | 0.600 |
| PSO | loi de Lu, dérivée sur la mesure | 0.706 | 0.737 | 0.600 |

---

## 4bis. Lecture de la proposition de TFE et de l'article de Lu et al. (8 octobre)

Points de l'article de référence (Lu et al. 2021) qui comptent pour la suite :

- La sortie μ du PID de Lu n'est pas le rapport cyclique. Elle monte à 800 au démarrage et oscille autour de ±2 en régime (fig. 9), et c'est le bloc PWM qui borne. Notre loi de Lu bornait μ à [0.01 ; 0.99] à l'intérieur de la loi : c'est un écart à l'article, déjà présent dans la version d'octobre, qui n'avait pas été écrit comme tel.
- Les gains partent de zéro chez Lu (Kp(0) = Ki(0) = Kd(0) = 0) et se stabilisent à 17.97, 10.96 et 1.65e-4. Nous partons des gains de Ziegler-Nichols.
- La sensibilité de Lu (éq. 16) utilise les incréments du pas courant (xc1, xc2, xc3), pas des sommes sur une fenêtre.
- Lu compare l'ELM-PID à une commande en boucle ouverte, jamais à un PID classique. Notre comparaison à Ziegler-Nichols et aux autres méthodes va plus loin que l'article.
- **F1 est appliqué « au terminal de commande »**, c'est-à-dire sur le signal de commande, pas sur la consigne. En boucle ouverte, la tension monte vers 190 V (fig. 12), ce qu'une perturbation de consigne de 5.4 V ne peut pas produire. Notre essai S2 et le modèle `PID_Classique_Control_control_disturbance.slx` ajoutent F1 à la consigne : c'est probablement un écart à l'article, à trancher (S2 n'entre pas dans J).
- Circuit de Lu : L = 50 µH, C = 40 µF ; base commune v2 : L = 10 mH, C = 47 µF (redimensionnement déjà décidé).

Points de la proposition de TFE à revoir plus tard avec Jean-Riche :

- Le résumé proposé pour l'article 2 annonce déjà le résultat (« l'ELM-PID offre le meilleur compromis… »). Il faudra l'écrire après les résultats.
- La proposition annonce un Fuzzy-PID de type Mamdani ; la méthode retenue est l'ordonnancement flou de Zhao, Tomizuka et Isaka (1993).
- Chapitre 3 : la proposition prévoit une discrétisation de Tustin, comme Lu ; le banc simule le circuit commuté exactement et les marges sont calculées avec un bloqueur d'ordre zéro. Le chapitre devra expliquer les deux.
- Le titre du 4.1 (« Rappel sur le PID incrémental ») change avec l'option B.

## 5. Bugs rencontrés et corrections

| Méthode / outil | Problème | Correction |
|---|---|---|
| Fuzzy | Auto-test T1 à 148 mV. Le rejeu montre un régulateur identique ; un écart de 1 mV du circuit est amplifié entre 2 et 6 ms. | Amendement 1 : T1 ≤ 0.5 V sur 20 ms et ≤ 0.01 V de 10 à 19 ms (0.02 V pour les trois modèles, charge F2 à 5.001 Ω). |
| Fuzzy | Le vérificateur signalait les variantes de masque (`ParallelPVariant`, `IVariant`, `DVariant`, `NVariant`) que Simulink change seul en passant aux paramètres externes. | Seul le passage Internal → External de ces quatre réglages est accepté (testé sur modèles fabriqués). |
| Fuzzy | Erreur NumPy 2 / matplotlib dans Spyder (environnement de Jean-Riche). | `pip install --upgrade matplotlib` conseillé. |
| PSO | Boîte [0 ; 16] : 0.05 % de points admissibles. | Bornes [0 ; 4] (amendement 1). |
| PSO | J = 5.03 : W de Gaing calculé avec l'intégrateur préchargé à 0.5, donc Ki → 0. | Réglage depuis l'état nul (amendement 2), puis coût entièrement remplacé (version finale). |
| PSO | Le W de Gaing ignore le rejet de perturbation : J = 1.69. | Coût IAE avec perturbations (M1, version finale). |
| PSO (outillage) | Erreur de sérialisation avec `runpy` et `multiprocessing` ; `KeyError 'essais'` quand aucune particule n'est admissible ; garde-fou sur `rm` ; motifs de heredoc ; marqueur `"# %% ETAPE 2"` présent dans la ligne `exec` elle-même. | Copie modifiée par sed ; `rg.get` et drapeau `admissible` ; copie par boucle ; correctifs écrits dans des fichiers ; marqueur `"\n# %% ETAPE 2 :"`. |
| PSO | Ziegler-Nichols refusé par les contraintes (marge −3.1°), alors que le contrôle supposait J_réglage(ZN) = 1. | Z-N sert seulement à normaliser ; message adapté. |
| ELM | V1 : porte fermée par l'erreur de prédiction (1.4 V en moyenne). | M1 : porte sur la seule saturation. |
| ELM | V2 : boîte au coin (Ki ne peut que baisser). | M2 : ensemble admissible tabulé. |
| ELM | V3 : départ sur la frontière d'un ensemble non convexe ; glissement annulé ; prévision P1 fausse (J = 0.744, gains immobiles sur S1–S3). | M3 : projection avec restauration (Rosen 1961). |
| ELM | `Tester_ELM_PID_Rejeu.m` lisait `J_TEST(i,3)` alors que le modèle n'a qu'une colonne : erreur d'index certaine. | `J_TEST(i,1)` ; S3 ajouté au rejeu. |
| ELM | Les auto-tests de construction exigeaient des gains inchangés au démarrage, faux avec M3. | Comparaison aux gains du banc à 1 % près. |
| ELM | `predictions_banc_elm_pid.json` en version 3, alors que `Simuler_ELM_PID.m` exige la version 2. | Version 2 (format de la base commune). |
| ELM | Calcul du banc interrompu par une perte de contexte (sortie tronquée après R0). | Relancé. |
| ELM, Simulink | S7a : 0 fenêtre adaptée sous Simulink contre 2 au banc. | Pas un bug : la quantification fait diverger les décisions ; documenté. |
| PINN | Chiffres périmés dans l'ancien document d'étape 4 (0.722, 0.750, 0.681 au lieu de 0.724, 0.745, 0.684 du JSON). | Document réécrit avec les valeurs du JSON ; la réponse du 7 oct. citait encore 0.722, corrigé. |
| PINN | `variante_ensemble_admissible_pinn.py` : f-string coupée par un heredoc (`\n` devenu un vrai saut de ligne). | Correction de la ligne. |
| PINN | `arxiv.org` bloqué par le proxy : impossible de relire Ito & Wasa. | Texte de l'article fourni ensuite ; pages et équations citées dans `PINN_PID/criteres_pinn_pid.txt` vérifiées sur ce texte (P4). |
| Comparaison | Avec les versions finales, aucun essai ne passe C1 : `comparaison_methodes.py` s'arrêtait sur une erreur (`max()` d'une liste vide). | Le script dit que la règle ne désigne aucun scénario ; règle inchangée (8 oct.). |
| Comparaison | `NameError: PIDParallele` dans le premier script de diagnostic (classe définie après la marque d'exécution). | Classe définie dans le script. |
| Documentation | Rappels « ELM-PID 0.784 » et « PINN-PID 0.684 » dans les copies et LISEZMOI des dossiers PSO et Fuzzy. | Corrigé le 8 oct. (copies et LISEZMOI ; les sorties console anciennes restent telles quelles). |

---

## 6. Ce qui reste à faire

1. **ELM-PID option B sous Simulink** (Jean-Riche) : `Tester_ELM_PID_Rejeu`, `Construction_ELM_PID`, `verifier_modele_elm_pid.py`, `Simuler_ELM_PID`, puis les trois scripts « Trois_Modeles » (`ELM_PID/LISEZMOI_ELM.txt`).
2. **PINN-PID final sous Simulink** (Jean-Riche) : même chaîne dans `PINN_PID/` (`LISEZMOI_PINN.txt`, étapes 1 à 7).
3. **Rédaction** des chapitres avec Jean-Riche (corps : J, S1, S2, S3, S8a ; annexe : classement essai par essai ; chapitre 4 : ELM incrémental contre option B).
4. Points ouverts non tranchés, à décider par Jean-Riche : PSO-PID jamais lancé sous MATLAB (les chiffres de référence restent ceux du banc) ; F1 appliqué à la consigne plutôt qu'à la commande (§4bis) ; scénario « dynamique non linéaire » (P2).
