# Plan de départ et travail réalisé

Document de travail pour réécrire le plan du mémoire, chapitre par chapitre.
État du dépôt au 10 octobre 2026 (branche `claude/clever-newton-1t2wt7`).

Sources :

- proposition de TFE de Jean-Riche (texte extrait du PDF, ligatures « ti »
  rétablies ; les autres artefacts d'extraction sont laissés tels quels dans
  les citations, par exemple « 8 » pour « ti » en italique et « 9 » pour
  « tt ») ;
- `ETAT_DE_REPRISE.md`, `CLAUDE.md`, `REDACTION/proposition_resultats_en_hypotheses.md` ;
- fichiers de critères et de résultats cités dans chaque ligne.

Les chiffres de résultats sont ceux du banc Python, qui sont les chiffres de
référence (décision du 8 octobre, `ETAT_DE_REPRISE.md` §3.1).

---

## 1. Le plan de départ, tel que la proposition le décrit

### 1.1 Identification

- Étudiant : « Jean-Riche NTUMBA PANZU, de la 2e année Technique en
  Électro-Énergétique à la Faculté Polytechnique de l'Université de
  Kinshasa ».
- Titre proposé : « Optimisation de la Régulation d'un Convertisseur Buck
  par un Contrôleur PID Auto-Adaptatif Basé sur Extreme Learning Machine
  (ELM) : Étude Théorique, Implémentation sous Simulink et Perspectives
  Améliorées ».
- Encadrement : « Directeur principal : Prof. Vianney Kyamakya (+ Prof.
  Liassa si interêt) » ; « Co-superviseurs : Assistant Ir. Ma9hieu
  Mubikayi ; et Ass. Vianney Kambale ».

### 1.2 Problématique

La proposition n'a pas de section « question de recherche » ni de section
« hypothèses ». La problématique se lit dans trois passages :

- Contexte : « la régulation de la tension de sortie dans des environnements
  perturbés reste un défi en raison des propriétés non linéaires du
  système. Le PID classique est performant mais rigide. Son adaptation
  dynamique à des changements de charges ou à des perturbations exogènes
  est limitée. »
- Plan du mémoire, 1.2 : « Définir clairement les limites du contrôle PID
  classique dans les systèmes non linéaires perturbés. Justifier l'intérêt
  d'une approche ELM-PID. »
- Article 2 : « peu d'études proposent une comparaison rigoureuse entre
  plusieurs régulateurs intelligents sur des critères pratiques et robustes
  appliqués à un convertisseur Buck. »

Ce qui tient lieu d'hypothèse est écrit comme un résultat acquis (voir la
partie 3 et `proposition_resultats_en_hypotheses.md`) : « Le recours à des
méthodes intelligentes, en particulier le Extreme Learning Machine (ELM),
permet une mise à jour rapide et efficace des paramètres PID pour maintenir
la stabilité du système en temps réel. »

### 1.3 Objectifs (section 2 de la proposition)

1. « Approfondissement théorique : Analyser les fondements des convertisseurs
   Buck, modélisation en mode CCM, linéarisation et transformation
   bilatérale. »
2. « Maîtrise du PID : Révision détaillée du fonctionnement du PID, de son
   algorithme incrémental et de ses limitations dans un contexte non
   linéaire. »
3. « Compréhension de l'ELM : Etudier la structure d'un SLFN [...], fonctions
   d'activation, moindres carrés, matrice pseudoinverse. »
4. « Implémentation Simulink : Reproduire les résultats du paper de référence
   dans Simulink, définir les paramètres de test, valider les performances
   du ELM-PID. »
5. « Résistance aux perturbations : Injecter des perturbations (charge,
   signal) et comparer les performances entre ELM-PID et PID classique. »
6. « Propositions d'amélioration : Tester d'autres approches intelligentes
   (PSO-PID, fuzzyPID, deep learning) et évaluer les gains. »
7. « Production scientifique : Rédiger deux articles de qualité conférence
   IEEE à partir des travaux. »

Innovation annoncée (section 3) : « Application d'un contrôleur adaptatif
ELM-PID à un convertisseur Buck en temps réel », « Étude comparative des
performances avec des approches traditionnelles et modernes »,
« Valorisation scientifique par la rédaction de deux articles techniques
structurés ».

### 1.4 Méthodologie annoncée

- Démarche (plan 1.4) : « étude théorique → modélisation → simulation →
  comparaison → rédaction ».
- Calendrier : 7 mois en 12 phases de deux semaines (lecture de l'article de
  Lu ; modélisation CCM ; PID classique sous Simulink ; ELM en Python ou
  MATLAB ; intégration ELM-PID par S-function ou MATLAB Function ;
  perturbations de commande « bruit, variation de consigne, retard » ;
  perturbations de charge « variation soudaine de R, chute de tension » ;
  PSO-PID et Fuzzy-PID ; article 1 ; article 2 ; mémoire ; soutenance).
- Jeux de données : « Dataset de test en régime nominal : 10 000 pas
  temporels », « perturbations de charge : Résistances variant de ±20 % »,
  « perturbations de commande : Entrées bruitées + rampes », « Temps de
  montée, dépassement, temps de stabilisation ».
- Critères : « IAE, ITAE, ISE », « Robustesse aux variations de R et Vin »,
  « Sensibilité au bruit de mesure » (article 1) ; « ITAE, ISE, temps de
  montée, % overshoot » et « Comparaison systématique sur 4 types de
  perturbations » (article 2).
- Pas de matériel : « Même si ce TFE ne prévoit pas de prototypage, voici
  quelques pistes matérielles pour une implémentation embarquée à
  considérer ».

### 1.5 Outils prévus

MATLAB (Symbolic Toolbox), Simulink (PID Tuner, S-Function, MATLAB Function
block, Signal Builder), Simscape Power Systems, Python (NumPy, SciPy,
scikit-learn, matplotlib), Excel ou LibreOffice Calc, FIS Editor, « PSO
scripts », LaTeX/Overleaf ou Word, Zotero/Mendeley, draw.io, Grammarly,
Antidote ; en option PLECS, LTSpice/PSIM, ModelSim.

### 1.6 Livrables prévus

- Phases 1 à 8 : résumé de l'article, modèle d'état documenté, fonction de
  transfert petit signal, « Fichier Simulink .slx complet avec bloc PID »,
  script ELM, « Bloc Simulink fonctionnel ELM-PID », « Vidéo/animation de la
  réponse du système », courbes PID classique contre ELM-PID sous
  perturbations, statistiques (« temps de rétablissement, erreur max,
  overshoot »), « Tableaux de comparaison multi-critères », « Graphes radar
  ou bar charts des performances ».
- Phases 9 à 12 : deux manuscrits d'articles (« Manuscrit complet prêt pour
  soumission IEEE »), mémoire, diaporama de soutenance.

### 1.7 Structure du mémoire prévue (section 6)

| Chapitre | Sous-chapitres prévus |
|---|---|
| 1 Introduction | 1.1 Contexte général ; 1.2 Problématique et motivation ; 1.3 Objectifs ; 1.4 Méthodologie de recherche ; 1.5 Structure du mémoire |
| 2 État de l'art | 2.1 Convertisseurs DC-DC ; 2.2 Modèles mathématiques du Buck ; 2.3 PID (Ziegler-Nichols, etc.) ; 2.4 « Contrôle intelligent : PSO-PID, Fuzzy, Sliding Mode, etc. » ; 2.5 Réseaux de neurones et ELM ; 2.6 Applications de l'ELM en électronique de puissance |
| 3 Modélisation du Buck | 3.1 Hypothèses (CCM) ; 3.2 Modèle ON/OFF ; 3.3 État moyen et transformation bilinéaire ; 3.4 Linéarisation ; 3.5 « Discrétisation [...] transformation bilinéaire (Tustin) » ; 3.6 Stabilité (lieu des racines, marges de phase) |
| 4 Conception de l'ELM-PID | 4.1 « Rappel sur le PID incrémental » ; 4.2 Architecture ELM ; 4.3 Apprentissage par Moore-Penrose ; 4.4 Ajustement des gains en ligne ; 4.5 Schéma global ; 4.6 Algorithme |
| 5 Simulation et analyse | 5.1 Paramètres (L, R, C, Vin, PWM, Vref) ; 5.2 Régime normal ; 5.3 Perturbation sur la commande ; 5.4 Perturbation sur la charge ; 5.5 Comparaison avec un PID classique (ISE, ITAE) ; 5.6 « Comparaison avec des méthodes avancées (PSO, Fuzzy) » ; 5.7 Discussion |
| 6 Perspectives | 6.1 Améliorations de l'ELM ; 6.2 Hybridation ; 6.3 Implémentation embarquée ; 6.4 « Prototypage physique (perspective de TFE 2) » ; 6.5 Publication |
| 7 Conclusion | 7.1 Objectifs atteints ; 7.2 « Mise en avant des performances atteintes, des améliorations prouvées » ; 7.3 Limites ; 7.4 Apports personnels ; 7.5 Ouverture |

---

## 2. Chapitre par chapitre : annoncé, réalisé, statut, preuve

Statuts : **tenu** (fait comme annoncé), **modifié** (fait autrement),
**abandonné** (ne sera pas fait), **ajouté** (absent de la proposition). Un
cinquième statut, **en suspens**, sert pour ce qui n'est ni fait ni
abandonné et doit être tranché avec Jean-Riche ou ses encadrants.

### Chapitre 1 : Introduction

| Annoncé | Réalisé | Statut | Preuve |
|---|---|---|---|
| 1.2 Problématique : « limites du contrôle PID classique dans les systèmes non linéaires perturbés » | Les résultats ne montrent pas de limite du PID fixe sur la plage étudiée : le PSO-PID, PID à gains fixes, est premier sur J et sur S1, S2, S3, S8a, S10. La problématique doit être reformulée en question ouverte. | modifié | `ETAT_DE_REPRISE.md` §4.1 et §4.3 ; `COMPARAISON/metriques/metriques_banc.md` |
| Hypothèses (absentes, résultats annoncés à leur place) | Phrases réécrites en hypothèses vérifiables | ajouté | `REDACTION/proposition_resultats_en_hypotheses.md` |
| 1.4 Méthodologie « étude théorique → modélisation → simulation → comparaison → rédaction » | Même enchaînement, plus une règle de méthode : critères et prévisions écrits et commités avant chaque calcul, aucun réglage sur les onze essais de développement, prévisions publiées justes ou fausses | modifié (élargi) | `CLAUDE.md` ; `ELM_PID/criteres_elm_pid.txt` (prévisions Q1 à Q8) ; `PINN_PID/criteres_pinn_pid.txt` ; `COMPARAISON/criteres_comparaison.txt` |

### Chapitre 2 : État de l'art

| Annoncé | Réalisé | Statut | Preuve |
|---|---|---|---|
| 2.3 PID et réglage « (Ziegler-Nichols, etc.) » | Ziegler-Nichols calculé et pris comme référence de normalisation du coût J | tenu | `Determination_gains_PID_Ziegler_Nichols.docx` ; `ELM_PID/criteres_elm_pid.txt` §1 |
| 2.4 « PSO-PID, Fuzzy, Sliding Mode, etc. » | PSO d'après Gaing (2004), Fuzzy d'après Zhao, Tomizuka et Isaka (1993). Mode glissant : rien dans le dépôt. | modifié | `PSO_PID/criteres_pso_pid.txt` ; `FUZZY_PID/criteres_fuzzy_pid.txt` |
| Objectif 6 : « deep learning » | PINN-PID d'après Ito et Wasa (2025, arXiv:2510.04591) | modifié | `PINN_PID/criteres_pinn_pid.txt` |
| 2.5 et 2.6 ELM et applications en électronique de puissance | Article de Lu et al. (2021) lu et comparé point par point à notre mise en œuvre. Pas de revue bibliographique structurée dans le dépôt. | en suspens | `ETAT_DE_REPRISE.md` §4bis ; `ELM_PID/criteres_elm_pid.txt` §2 et §11 |

### Chapitre 3 : Modélisation du convertisseur Buck

| Annoncé | Réalisé | Statut | Preuve |
|---|---|---|---|
| 3.1 à 3.4 CCM, modèle ON/OFF, modèle moyen, linéarisation | Dimensionnement du circuit (base commune v2.1 : L = 10 mH, C = 47 µF, R = 5 Ω, Vin = 200 V, fs = 22 kHz). Le banc simule le circuit commuté. Le circuit diffère de celui de Lu (L = 50 µH, C = 40 µF). | tenu, circuit modifié | `Dimensionnement_convertisseur_Buck.docx` (pas encore converti en Markdown) ; `ELM_PID/banc_commun.py` ; `ETAT_DE_REPRISE.md` §4bis |
| 3.5 Discrétisation par Tustin | Marges calculées sur le modèle moyen discrétisé avec un bloqueur d'ordre zéro ; Tustin non utilisé. Le chapitre devra expliquer les deux. | modifié | `ETAT_DE_REPRISE.md` §4bis ; `ELM_PID/ensemble_gains_elm.py` |
| 3.6 Stabilité (lieu des racines, marges) | Marges de phase et fréquence de coupure calculées et utilisées comme contraintes (PSO : marge 30.0°, coupure 2175 Hz ; ELM : marge du départ 24.93°, coupure au plus fs/10 aux neuf coins). Pas de lieu des racines. | modifié | `ETAT_DE_REPRISE.md` §4.2 ; `ELM_PID/criteres_elm_pid.txt` §2 |
| Simscape Power Systems | Modèle commun `Buck_Commun.slx` à blocs de puissance (MOSFET, powergui) | tenu | `ELM_PID/Buck_Commun.slx` |
| (absent) Banc Python reproduisant Simulink | Banc commun validé contre Simulink (IAE à 0.1 % à 0.3 % près, S7a excepté) | ajouté | `ELM_PID/banc_commun.py` ; `ETAT_DE_REPRISE.md` §1 et §4.2 |

### Chapitre 4 : Conception du contrôleur ELM-PID

| Annoncé | Réalisé | Statut | Preuve |
|---|---|---|---|
| 4.1 « Rappel sur le PID incrémental » | Option B : l'ELM règle les gains du bloc PID parallèle commun aux cinq méthodes. La loi incrémentale de Lu est gardée pour justifier ce choix. | modifié | `CLAUDE.md` (décisions) ; `ELM_PID/criteres_elm_pid.txt` (M4) ; `ELM_PID_INCREMENTAL/` ; `COMPARAISON/elm_incremental_contre_B.py` ; `COMPARAISON/diagnostic_lois/` |
| 4.2 et 4.3 Architecture ELM, Moore-Penrose | ELM à liaisons directes (RVFL), 12 neurones logistiques, C = 0.1, mise à jour en ligne OS-ELM | tenu | `ELM_PID/entrainement_elm.py` ; `ELM_PID/criteres_elm_pid.txt` §2 |
| 4.4 Règle de mise à jour des gains | Gradient normalisé de Lu, plus quatre modifications documentées par la littérature (M1 porte sur la saturation, M2 ensemble admissible, M3 projection de Rosen, M4 bloc parallèle) | modifié | `ELM_PID/criteres_elm_pid.txt` §3 et §4 |
| Objectif 4 : « Reproduire les résultats du paper de référence » | Non reproduit tel quel : circuit redimensionné, gains de départ de Ziegler-Nichols au lieu de zéro, F1 appliqué à la consigne au lieu de la commande (écart probable, à trancher). Lu compare l'ELM-PID à la boucle ouverte, pas à un PID. | modifié | `ETAT_DE_REPRISE.md` §4bis et §6 point 6 |
| Phase 5 : « Bloc Simulink fonctionnel ELM-PID » | Bloc `elm_pid_adaptatif.m` dans le modèle commun, validé sous Simulink le 8 octobre. Rejeu pas à pas et trois modèles de base non lancés. | tenu, validation incomplète | `ELM_PID/elm_pid_adaptatif.m` ; `ELM_PID/criteres_elm_pid.txt` §10 ; `ETAT_DE_REPRISE.md` §6 |
| Phase 5 : « Vidéo/animation de la réponse du système » | Rien dans le dépôt | en suspens | |

### Chapitre 5 : Simulation et analyse des performances

| Annoncé | Réalisé | Statut | Preuve |
|---|---|---|---|
| 5.2 Régime normal | S1 (nominal, 5 Ω) | tenu | `ELM_PID/scenarios_communs.json` |
| 5.3 Perturbation sur la commande : « bruit, variation de consigne, retard » | S2 (F1 sur la consigne), S6 (rampe de consigne), S7a (quantification 12 bits), S7b (bruit de mesure). Retard : pas d'essai. | modifié | `ELM_PID/scenarios_communs.json` |
| 5.4 Perturbation sur la charge, « Résistances variant de ±20 % » | S3 (F2 de l'article), S4 (charge ±20 %), S5 (Vin ±20 %), S8a et S8b (charges légères), S9 (profil grand signal) | tenu, élargi | `ELM_PID/scenarios_communs.json` |
| 5.5 Comparaison avec un PID classique | Ziegler-Nichols comme référence ; ELM-PID J = 0.746 contre 1.000 | tenu | `ETAT_DE_REPRISE.md` §4.1 ; `ELM_PID/banc_elm_pid_resultats.json` |
| 5.6 Comparaison PSO et Fuzzy | PSO-PID (J = 0.714), Fuzzy-PID (J = 0.877), plus PINN-PID (J = 0.757) | tenu, élargi | `COMPARAISON/comparaison_resultats.json` ; `COMPARAISON/criteres_comparaison.txt` |
| Critères IAE, ISE, ITAE, dépassement, temps de montée et d'établissement | Coût J (13 rapports d'IAE à Ziegler-Nichols) pour le classement ; ISE, ITAE, dépassement, montée, établissement, retour dans ±1 V publiés à côté, sans changer l'ordre | modifié | `COMPARAISON/metriques/definitions_metriques.txt` ; `COMPARAISON/metriques/metriques_banc.md` |
| « Comparaison systématique sur 4 types de perturbations » | Onze essais de développement, plus S10 (changement durable du point de fonctionnement), ajouté après coup avec l'encadrant et hors du coût J | modifié (élargi) | `COMPARAISON/S10/criteres_S10.txt` |
| « Graphes radar ou bar charts » | Graphe de classement par essai et courbes des scénarios ; pas de radar | modifié | `COMPARAISON/classement_par_essai.png` ; `COMPARAISON/comparaison_S8a.png` |
| « Visualisation de la convergence (PSO) » | Fait | tenu | `PSO_PID/pso_pid_convergence.png` |
| (absent) Règle de choix des scénarios fixée avant calcul | Règle C1 à C4 ; avec les versions finales elle ne désigne aucun scénario. Scénarios du corps choisis par l'auteur : S1, S2, S3, S8a. | ajouté | `COMPARAISON/criteres_comparaison.txt` ; `ETAT_DE_REPRISE.md` §3.1 |
| (absent) Robustesse aux paramètres L et C ±0.1 % | Fait sur S4 et S8a | ajouté | `COMPARAISON/robustesse_S4.json`, `robustesse_S8a.json` |
| (absent) Coût de calcul par appel du régulateur | Mesuré en Python (ordre de grandeur relatif) | ajouté | `COMPARAISON/metriques/metriques_banc.md` (dernières tables) |
| (absent) Validation de chaque méthode sous Simulink | Modèle commun validé pour les cinq méthodes ; restent les rejeux ELM et PINN, les trois modèles de base PSO, ELM, PINN | ajouté, incomplet | `ETAT_DE_REPRISE.md` §2 et §6 |
| Excel pour les courbes, FIS Editor, scikit-learn | Python (NumPy, matplotlib) ; Fuzzy codé à la main, pas de FIS Editor | modifié | `FUZZY_PID/ordonnanceur_flou_zhao.m` ; `ELM_PID/entrainement_elm.py` |
| Fuzzy-PID « de type Mamdani » (article 2) | Ordonnancement flou des gains de Zhao, Tomizuka et Isaka | modifié | `FUZZY_PID/criteres_fuzzy_pid.txt` ; `ETAT_DE_REPRISE.md` §4bis |

### Chapitre 6 : Perspectives

| Annoncé | Réalisé | Statut | Preuve |
|---|---|---|---|
| 6.1 à 6.5 | Reste un chapitre de perspectives. Matériaux nouveaux : scénario « dynamique non linéaire » (P2, non fait), temps de calcul du PINN-PID (environ 1 ms par période du régulateur en MATLAB interprété, pour Tc = 4.5 µs) | tenu (à rédiger) | `ETAT_DE_REPRISE.md` §3.3 (P2) et §4.2 |
| 6.3 et 6.4 embarqué et prototype | Hors du TFE dès la proposition ; rien de matériel n'a été fait | tenu (perspective seulement) | proposition, section 5 |

### Chapitre 7 : Conclusion

| Annoncé | Réalisé | Statut | Preuve |
|---|---|---|---|
| 7.2 « Mise en avant [...] des améliorations prouvées » | À remplacer par un bilan hypothèse par hypothèse : confirmée, infirmée, ou écart sous le seuil | modifié | `REDACTION/proposition_resultats_en_hypotheses.md` §2.4 |

### Hors mémoire

| Annoncé | Réalisé | Statut | Preuve |
|---|---|---|---|
| Objectif 7 et section 7 : deux articles IEEE | Aucun manuscrit dans le dépôt. Les deux résumés proposés annoncent des résultats que les calculs contredisent (partie 3). | en suspens | absence dans `REDACTION/` |
| Calendrier de 7 mois en 12 phases | L'historique git ne couvre que du 6 au 9 octobre 2026 ; il ne permet pas de juger le calendrier | non vérifiable | `git log` |

---

## 3. Promesses que les résultats contredisent ou ne soutiennent pas

### 3.1 « L'ELM-PID offre le meilleur compromis » (résumé de l'article 2)

Citation : « Les résultats montrent que l'ELM-PID offre le meilleur compromis
entre précision, rapidité et adaptabilité, tandis que le Fuzzy-PID offre une
bonne robustesse avec une implémentation intuitive. »

Ce que disent les calculs (`ETAT_DE_REPRISE.md` §4.1 et §4.3,
`COMPARAISON/metriques/metriques_banc.md`) :

- Coût J : PSO-PID 0.714 ; ELM-PID 0.746 ; PINN-PID 0.757 ; Fuzzy-PID
  0.877 ; Ziegler-Nichols 1.000. L'ELM-PID est deuxième des cinq méthodes,
  et un PID figé trouvé par grille fait déjà 0.738.
- Le PSO-PID est premier sur chacun des scénarios du corps et sur S10 :
  S1 (87.62 contre 93.72 mV·s pour l'ELM-PID), S2 (2.04 contre 2.41), S3
  (5.46 contre 6.41), S8a (2.46 contre 2.96), S10 (3.98 contre 8.63).
- Si on lit J avec le seuil de clarté de 5 % entre voisins fixé dans
  `COMPARAISON/criteres_comparaison.txt` (critère C1, écrit pour les IAE par
  essai), PSO-PID et ELM-PID sont à 4.5 % et ELM-PID et PINN-PID à 1.5 % :
  les trois ne se séparent pas. Le texte peut dire que les deux méthodes
  adaptatives font aussi bien qu'un PID fixe bien réglé, pas mieux.
- Les deux méthodes adaptatives ne se séparent ni sur J ni sur les quatre
  essais du corps (`ETAT_DE_REPRISE.md` §4.3). Sur S10 seul, le PINN-PID
  passe devant l'ELM-PID (6.63 contre 8.63).

Fuzzy-PID « bonne robustesse » : J = 0.877, quatrième ; plus fort
dépassement au démarrage (27.34 % sur S1, contre 13.99 % pour Ziegler-Nichols
et l'ELM-PID) ; dernière des quatre méthodes classées sur S10. La phrase n'est
pas soutenue.

### 3.2 « Le PSO-PID, bien que performant, souffre d'une complexité de mise en œuvre »

Une fois réglé hors ligne, le PSO-PID est un PID à gains fixes. Son coût par
appel est celui de Ziegler-Nichols (1.43 µs contre 1.39 µs en Python), loin
de l'ELM-PID (3.59 µs) et du PINN-PID (38.93 µs)
(`COMPARAISON/metriques/metriques_banc.md`). La complexité ne concerne que le
réglage (cinq recherches par essaim, `PSO_PID/recherche_pso_pid.py`). La
phrase est contredite pour l'exécution et doit être limitée au réglage.

### 3.3 Résumé de l'article 1 : « amélioration significative [...] réduction du dépassement »

Citation : « Les résultats montrent une amélioration significative des
performances dynamiques : réduction du dépassement, meilleure réponse
transitoire, et adaptation efficace face aux variations du système. »

- Face à Ziegler-Nichols, l'ELM-PID améliore J (0.746 contre 1.000). C'est
  soutenu.
- Le dépassement au démarrage n'est pas réduit : 13.99 % sur S1 pour les
  deux, 52.23 % sur S8a pour les deux (`metriques_banc.md`). L'IAE de
  démarrage de S1 est la même à 0.05 % près (93.72 contre 93.77).
- Face à un PID fixe bien réglé (PSO-PID), l'amélioration n'existe pas.
- L'adaptation aide là où le point de fonctionnement change durablement :
  sur S10, l'ELM-PID adaptatif fait 40.9 % mieux que le même PID figé à ses
  gains de départ (prévision P10, `COMPARAISON/S10/criteres_S10.txt`). C'est
  le résultat le plus favorable à l'adaptation, et il a été obtenu sur un
  scénario ajouté après coup.

### 3.4 « mise à jour rapide et efficace des paramètres PID [...] en temps réel »

- L'ELM ajuste ses gains par fenêtres de 0.5 ms. Sur S4, les gains changent
  à 52.0 et 102.0 ms, après les pointes des événements (50.2 et 100.2 ms)
  (`ETAT_DE_REPRISE.md` §4.4). L'adaptation ne joue donc pas pendant la
  pointe.
- Le temps réel n'est pas démontré : tout est en simulation, ce que la
  proposition prévoyait (« ce TFE ne prévoit pas de prototypage »). Le
  PINN-PID demande environ 1 ms de calcul par période du régulateur en
  MATLAB interprété, pour une période de 4.5 µs (`ETAT_DE_REPRISE.md` §4.2).
- Innovation annoncée : « Application d'un contrôleur adaptatif ELM-PID à un
  convertisseur Buck en temps réel ». À reformuler en « en simulation ».

### 3.5 « Le PID classique est performant mais rigide »

Prémisse non soutenue sur la plage étudiée : le meilleur résultat global vient
d'un PID à gains fixes. Le mémoire peut garder l'idée comme hypothèse de
départ et rapporter qu'elle est infirmée ici, en précisant les limites (essais
qui reviennent presque tous au point nominal, ce qui a motivé S10).

### 3.6 Objectif 4 : « Reproduire les résultats du paper de référence »

Pas fait au sens strict. Circuit différent, gains de départ différents,
perturbation F1 appliquée ailleurs que chez Lu. Lu ne compare pas à un PID
classique, donc il n'y a pas de résultat comparatif à reproduire
(`ETAT_DE_REPRISE.md` §4bis). Le mémoire doit le dire.

### 3.7 Éléments annoncés et non faits

- Deux articles IEEE : « Dans le cadre du TFE, deux articles scientifiques
  seront produits ». Rien n'est écrit.
- « Vidéo/animation de la réponse du système » (phase 5) : non fait.
- « Graphes radar » (phase 8 et figures de l'article 2) : non fait.
- « retard » dans les perturbations de commande (phase 6) : pas d'essai.
- « Sliding Mode » (plan 2.4) : seulement cité, pas de méthode codée ; le
  plan ne promettait qu'une présentation.
- Lieu des racines (plan 3.6) et discrétisation de Tustin (plan 3.5) : non
  utilisés.
- Implémentation matérielle (Arduino, STM32, FPGA) : la proposition ne la
  promet pas (« ce TFE ne prévoit pas de prototypage ») ; elle reste au
  chapitre des perspectives. Ce n'est pas une promesse manquée.

---

## 4. Squelette du mémoire (PROVISOIRE)

Ce squelette est une base de discussion. Le plan définitif sera fixé à la fin
de la rédaction, quand chaque chapitre sera écrit. Il garde la structure de
la proposition là où elle tient encore ; le principal changement est la
séparation des méthodes de comparaison (devenues de vraies mises en œuvre,
chacune avec ses écarts à l'article d'origine) et des résultats.

**Introduction générale**
- Contexte et problématique (reformulée en question)
- Objectifs et hypothèses
- Démarche et règles de méthode
- Plan du mémoire

Sources : `REDACTION/proposition_resultats_en_hypotheses.md`, `CLAUDE.md`,
la proposition.

**Chapitre 1. État de l'art**
- 1.1 Convertisseurs DC-DC et convertisseur Buck
- 1.2 Régulateur PID et réglage de Ziegler-Nichols
- 1.3 Réglage et adaptation des gains : PSO, ordonnancement flou, ELM, PINN
- 1.4 L'ELM-PID de Lu et al. (2021) et ses limites

Sources : `ELM_PID/criteres_elm_pid.txt` §2 et §11,
`PSO_PID/criteres_pso_pid.txt`, `FUZZY_PID/criteres_fuzzy_pid.txt`,
`PINN_PID/criteres_pinn_pid.txt` (références), `ETAT_DE_REPRISE.md` §4bis,
`Determination_gains_PID_Ziegler_Nichols.docx`.

**Chapitre 2. Modélisation du convertisseur et base commune**
- 2.1 Dimensionnement et hypothèses (CCM)
- 2.2 Modèle commuté, modèle moyen, linéarisation
- 2.3 Discrétisation et marges de stabilité
- 2.4 Modèle Simulink commun et banc Python
- 2.5 Essais S1 à S9, coût J et validation du banc contre Simulink

Sources : `Dimensionnement_convertisseur_Buck.docx`, `ELM_PID/banc_commun.py`,
`ELM_PID/Buck_Commun.slx`, `ELM_PID/scenarios_communs.json`,
`ELM_PID/ensemble_gains_elm.py`, `ETAT_DE_REPRISE.md` §1.

**Chapitre 3. Conception de l'ELM-PID**
- 3.1 Réseau ELM et apprentissage
- 3.2 Loi d'adaptation des gains et modifications M1 à M4
- 3.3 De la loi incrémentale de Lu au bloc PID commun (option B)
- 3.4 Mise en œuvre et validation sous Simulink

Sources : `ELM_PID/criteres_elm_pid.txt`, `ELM_PID/entrainement_elm.py`,
`ELM_PID/elm_pid_adaptatif.m`, `ELM_PID_INCREMENTAL/`,
`COMPARAISON/elm_incremental_contre_B.py`, `COMPARAISON/diagnostic_lois/`.

**Chapitre 4. Méthodes de comparaison**
- 4.1 Ziegler-Nichols
- 4.2 PSO-PID
- 4.3 Fuzzy-PID
- 4.4 PINN-PID

Sources : `PSO_PID/criteres_pso_pid.txt`, `FUZZY_PID/criteres_fuzzy_pid.txt`,
`PINN_PID/criteres_pinn_pid.txt` et les `LISEZMOI_*.txt` de chaque dossier.

**Chapitre 5. Résultats et discussion**
- 5.1 Protocole de comparaison et règle de choix des scénarios
- 5.2 Coût J sur les onze essais
- 5.3 Scénarios du corps : S1, S2, S3, S8a
- 5.4 Changement durable du point de fonctionnement (S10)
- 5.5 Robustesse, métriques complémentaires et coût de calcul
- 5.6 Hypothèses confrontées aux résultats

Sources : `COMPARAISON/criteres_comparaison.txt`,
`COMPARAISON/comparaison_resultats.json`, `COMPARAISON/S10/criteres_S10.txt`,
`COMPARAISON/metriques/metriques_banc.md`, `COMPARAISON/robustesse_S*.json`,
`ETAT_DE_REPRISE.md` §4.

**Chapitre 6. Perspectives**
- 6.1 Améliorations des méthodes adaptatives
- 6.2 Scénarios non linéaires et non-retour au nominal
- 6.3 Vers une implémentation embarquée et un prototype

Sources : la proposition (chapitre 6 prévu), `ETAT_DE_REPRISE.md` §3.3 (P2)
et §4.2 (temps de calcul).

**Conclusion générale**
- Bilan des hypothèses
- Limites du travail
- Apports personnels

**Annexes**
- Classement essai par essai (onze essais)
- Critères et prévisions écrits avant calcul, avec leur issue
- Validation Simulink de chaque méthode
- Modes d'emploi et code

Sources : `COMPARAISON/comparaison_methodes_sortie_console.txt`,
`COMPARAISON/classement_par_essai.png`, les fichiers `criteres_*.txt`,
`LISEZMOI_*.txt` et `MODE_EMPLOI_*.txt`.

Numérotation : la proposition numérote l'introduction comme chapitre 1 ; le
squelette ci-dessus la sort de la numérotation. C'est à décider selon l'usage
de la faculté (question 2 ci-dessous).

---

## 5. Questions à poser à Jean-Riche

La proposition donne déjà l'université, la faculté, la filière et les noms
des encadrants. Restent :

1. Année académique et date prévue du dépôt et de la soutenance.
2. Règles de forme de la Faculté Polytechnique pour le mémoire : nombre de
   pages attendu, gabarit imposé, introduction et conclusion numérotées ou
   non, pièces liminaires obligatoires (résumé, abstract en anglais,
   dédicace, remerciements, liste des symboles).
3. Style de citation imposé (IEEE numérique, auteur-date, autre) et outil de
   rédaction imposé ou libre (Word ou LaTeX, la proposition cite les deux).
4. Encadrement : le Prof. Liassa (« si interêt ») fait-il partie de
   l'encadrement ? Qui est l'encadrant qui a défini S10 avec toi ?
5. Les encadrants ont-ils validé les changements de périmètre : ajout du
   PINN-PID à la place du « deep learning », Fuzzy de Zhao au lieu de
   Mamdani, option B pour l'ELM-PID, circuit redimensionné ?
6. Les deux articles IEEE restent-ils une exigence du TFE, une option, ou
   sont-ils abandonnés ?
7. La faculté demande-t-elle une déclaration sur l'usage d'outils d'IA dans
   le travail ?
8. Intitulé exact du diplôme à mettre en page de garde (la proposition dit
   « 2e année Technique en Électro-Énergétique »).
