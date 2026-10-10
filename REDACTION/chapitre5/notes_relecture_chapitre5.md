# Notes pour la relecture du chapitre 5

Notes retirées du fichier Word du chapitre 5, rassemblées dans l'ordre des fichiers sources.

## Source : `chapitre5_sections_5_1_5_2.md`

### Chiffres et leur source

| Chiffre | Source |
| --- | --- |
| *L* = 10 mH, *C* = 47 µF, *f*s = 22 kHz, *T*c = 1/220 000 s, *v*ref = 100 V, *d* dans [0,01 ; 0,99], *R*on = 0,1 Ω, *V*f = 0,8 V, *h* = 1/(22 000 × 1 200) s = 37,88 ns | `ELM_PID/banc_commun.py`, étape 0 (constantes) et en-tête |
| *R* = 5 Ω, *V*in = 200 V, durée 0,2 s | `ELM_PID/scenarios_communs.json` (`R0`, `Vin_nominale`, `duree`) ; `ETAT_DE_REPRISE.md`, ligne 5 |
| *T*c = période du régulateur, dix échantillons par période de découpage ; *v*ref = consigne de sortie (« consigne = 100 + dvref ») | `banc_commun.py`, en-tête ; `Determination_gains_PID_Ziegler_Nichols.docx`, tableau 1 et section 6 |
| Forme (5.1), Euler explicite, intégration conditionnelle (« clamping » dans le code), *N* = 64 122,9 rad/s | `banc_commun.py` (classe `PIDClassique`, `PID_N`) ; docx ZN, sections 7.2, 7.3 et tableau 12 |
| *P* = 0,093910, *I* = 301,089, *D* = 7,3227·10⁻⁶ | `banc_commun.py` ; `ELM_PID/criteres_elm_pid.txt`, ligne 37 ; docx ZN, tableau 12 |
| Méthode de la réponse indicielle (table 1 de Mudry) | docx ZN, sections 3.3 et 5 |
| Amortissement 1,46 à 5 Ω ; 0,29 à 25 Ω | docx ZN, tableau 2 (1,459) ; `COMPARAISON/S10/criteres_S10.txt`, « Pourquoi ce scénario » (1,46 et 0,29) |
| Écart d'IAE banc/Simulink ≤ 0,3 % sauf S7a | `ETAT_DE_REPRISE.md` §4.2 : PSO 0,1 %, ELM 0,1 %, PINN 0,3 %, Fuzzy 0,2 % ; S7a : +0,8 %, +2,5 %, −6,1 %, +4,8 % |
| Scénarios S1, S2, S3, S8a (formules, valeurs, instants) | `scenarios_communs.json` et `scenario_*.mat` relus (profils de *V*in, dvref, gx) |
| S10 (définition, 50 ms de réajustement, mesure à partir de 100 ms, ajouté après coup) | `COMPARAISON/S10/criteres_S10.txt` |
| Fenêtres de classement, définitions des grandeurs (bande ±1 V, 5 ms et 10 ms, ITAE depuis le début de la fenêtre, temps de calcul) | `COMPARAISON/metriques/definitions_metriques.txt` §1 à 7 |
| Règle de séparation (cinq variantes, *L* et *C* à ±0,1 %) | `COMPARAISON/separation/criteres_separation.txt` §2 |
| Indice global (appelé J dans le dépôt) : moyenne de 13 rapports sur les onze essais | `ETAT_DE_REPRISE.md`, ligne 5 |
| Règle de sélection écrite le 7 oct. avant les classements ; S8a désigné à sa réapplication du 8 oct. (ELM-PID option B, C3 = 0,567) ; aucun scénario désigné avec les versions finales | `COMPARAISON/criteres_comparaison.txt` (en-tête, « Mise à jour du 8 octobre », « Versions finales ») ; `ETAT_DE_REPRISE.md` §3.1 et §4.3 |
| S1, S2, S3 = trois cas du plan initial (régime normal, perturbation sur la commande, perturbation sur la charge) | proposition du TFE (`proposition_corrigee.md`, chapitre 5, 5.2 à 5.4, dans le dossier de travail) ; `REDACTION/plan_depart_contre_realise.md` §1.7 |
| F1 appliqué au terminal de commande chez Lu | `ETAT_DE_REPRISE.md` §4bis |
| Tolérance 1 %, 3 % sur S10 pour ELM et PINN | `COMPARAISON/figures_chapitre5/Figures_Chapitre5.m`, lignes 148-149 et 226 (`tol_S10`) |

### Citations et statut (`REDACTION/references_chapitre5.md`)

| Citation | Statut |
| --- | --- |
| [Ziegler et Nichols, 1942] | vérifiée |
| [Mudry, 2006], p. 1 et p. 10 | vérifiée sur le document (note de cours, citée en complément) |
| [Åström et Hägglund, 1995] | vérifiée (livre non consulté : pas de page citée) |
| [Åström et Hägglund, 2006] | vérifiée |
| [Ogata, 2010] | vérifiée (pages à relever) |
| [Gaing, 2004] | vérifiée |
| [Liang et al., 2006] | vérifiée |
| [Ito et Wasa, 2025] | vérifiée comme prépublication arXiv |
| [Graham et Lathrop, 1953] | **avec réserve** |
| [Zhao et al., 1993] | **avec réserve** |
| [Lu et al., 2021] | **avec réserve** |
| Fleming et Wallace, 1986 | non vérifiée : marqueur seulement, pas de citation |

Étiquettes : forme courte sans initiales décidée par Jean-Riche (guide de forme §7 mis à jour) ; les entrées de la bibliographie gardent tous les auteurs avec leurs initiales.

### Repères à placer et points à trancher

- [FIGURE À INSÉRER] figure 5.1, à exporter depuis `ELM_PID/Buck_Commun.slx`.
- [URL DU DÉPÔT À INSÉRER] adresse du dépôt GitHub (annexe).
- [RÉF. À VÉRIFIER : Fleming et Wallace, 1986].
- Renvois de chapitre provisoires : modèle du convertisseur, calcul des gains de Ziegler-Nichols et validation du banc placés au « chapitre 3 », ELM-PID au « chapitre 4 ». L'endroit où sont décrites les mises en œuvre du PSO-PID, du Fuzzy-PID et du PINN-PID n'est pas fixé.
- La première consigne demandait « IAE à 0,13 % près » : ce chiffre est l'écart sur les **gains** de l'ELM-PID (S1 à S6), pas sur l'IAE. Le texte donne l'écart d'IAE réel (au plus 0,3 %, S7a excepté).
- Le dossier des références attribue les gains de Ziegler-Nichols à la méthode du point critique : c'est faux, le docx ZN écarte cette méthode et retient la réponse indicielle. Il dit aussi que le Buck est un processus oscillant : faux au point nominal (amortissement 1,46), vrai à 25 Ω (0,29). Le texte suit le docx.
- S10 n'a pas encore été simulé sous Simulink, et les modèles de comparaison des figures (`Figures_Chapitre5.m`) n'ont pas tous été lancés : la phrase « les figures sont tracées à partir des simulations Simulink » suppose ce travail fait.
- S2 : l'écart à Lu (F1 sur la consigne, pas sur la commande) est maintenant écrit dans le texte. Si Jean-Riche décide de refaire S2 avec F1 sur la commande, cette phrase et le tableau 5.2 changent.
- Statut de Ziegler-Nichols sur S10 : hors classement dans `criteres_S10.txt`, inclus dans les paires de `criteres_separation.txt`. Le texte ne tranche pas ; à fixer avant 5.5.
- Choix des scénarios (fin de 5.2.2) : S8a a été désigné à la réapplication du 8 octobre (ELM-PID option B, PINN-PID du 5 octobre). Avec les versions finales, la règle ne désigne aucun essai (`criteres_comparaison.txt`, « Versions finales »). Le texte le dit.
- Écarts d'IAE Simulink/banc sur les cinq scénarios (25 valeurs) : source « sortie console de Figures_Chapitre5.m transmise par Jean-Riche le 10 octobre 2026 ». Maxima : ELM-PID S2 0,10 % ; PINN-PID S2 0,09 % ; Fuzzy-PID S1 0,08 % ; Ziegler-Nichols S8a 0,36 % et S10 0,26 %. Archivée dans `COMPARAISON/figures_chapitre5/sortie_matlab_Figures_Chapitre5_10oct.txt`.
- Proposition du TFE (`proposition_corrigee.md`, plan du chapitre 5, rédigé avant tout résultat ; voir aussi `plan_depart_contre_realise.md` §1.7) : « 5.2 Étude en régime normal (sans perturbation) : Réponse temporelle, temps de montée, overshoot, régulation en régime établi. » ; « 5.3 Étude avec perturbation sur la commande : Injection de bruit ou d'un signal sinusoïdal sur la consigne, analyse de la robustesse. » ; « 5.4 Étude avec perturbation sur la charge : Simulation de variations rapides de résistance de charge, test de stabilité. » La proposition place elle-même la perturbation « sur la consigne », ce qui rejoint S2. Elle ne cite pas Lu et al. dans ce plan : le lien avec F1 et F2 vient des essais, pas du texte de la proposition.
- 5.1 annonce 5.3 à 5.6 selon le plan approuvé ; S10 est traité dans 5.3 et 5.4.
- Milliers : remplacer les espaces par des espaces fines insécables dans Word (guide §8).
- Vocabulaire des essais (décision de l'auteur, 10 octobre 2026) : « essais de développement » pour les onze essais S1 à S9, « essais de réglage » pour E1 à E4. Remplacements : 5.2.1, « distincts des essais de jugement » devient « distincts des essais de développement » ; 5.2.2, « onze essais du banc commun » devient « onze essais de développement » ; 5.4.1, « distincts des essais de jugement » devient « distincts des essais de développement ». Le chapitre 3 doit définir les deux catégories.

## Source : `chapitre5_section_5_3.md`

### Chiffres et leur source

| Chiffre | Source |
| --- | --- |
| S1 : dépassement 13,99 %, établissement 3,40 ms (ZN et ELM) ; IAE 93,77 / 93,72 | `COMPARAISON/metriques/metriques_banc.md`, tableau S1 |
| Écarts de séparation ZN/ELM (S1 0,053 à 0,055 % ; S2 17,75 à 18,50 % ; S3 34,77 à 35,69 % ; S8a 301,9 à 312,8 % ; S10 708,9 à 801,8 %) ; écart = IAE_ZN/IAE_ELM − 1 | `COMPARAISON/separation/separation_resultats.json` (paires ELM-PID / Ziegler-Nichols) ; définition dans `separation_methodes.py`, ligne 207 |
| Rapports ELM/ZN 0,999 ; 0,847 ; 0,739 ; 0,246 ; 0,122 | calculés sur les IAE nominales de `separation_resultats.json` (93,716/93,765 ; 2,406/2,841 ; 6,406/8,665 ; 2,965/12,072 ; 8,632/70,481) |
| Butée S1 : 1,791 ms au total, dernière à 2,077 ms (ZN et ELM) ; S10 : ELM 175,450 ms, PSO 160,205, PINN 160,141, ZN 53,532, Fuzzy 52,268 | `COMPARAISON/figures_chapitre5/sortie_matlab_Figures_Chapitre5_10oct.txt` (Simulink) |
| Boucle de 0,5 ms, porte sur trois fenêtres (saturation), zone morte 0,1 V | `ELM_PID/criteres_elm_pid.txt` §2 et M1 (§4) |
| Changement unique des gains à 4 ms sur S1, x(1,469 ; 1,058 ; 1,152) ; S1 : 1 fenêtre, S2 : 1, S3 : 2 (second à 72 ms), S8a : 7 | `criteres_elm_pid.txt` §8 |
| Porte fermée pendant F1/F2, réouverture 1,5 ms après la fin de la fenêtre saturée (1,5 à 2 ms après l'événement, règle de la section 4.4.2 et figure 4.3 ; `criteres_elm_pid.txt` §8 écrit « 1.5 ms plus tard »), erreur sous 0,1 V (S3 à 52 ms : −0,038 V) | `criteres_elm_pid.txt` §8 (« Ce que l'adaptation fait pendant une perturbation ») et §9 point 3 |
| PID figé aux gains de 4 ms : S3 6,41 ; S8a 3,87 (contre 2,96) | `criteres_elm_pid.txt` §8 (« Analyse ajoutée après coup », étape 4c du banc) |
| S2 e max 2,01 / 2,01 ; S3 5,73 / 5,66 ; retours S3 ZN 1,05 et 1,49 ms, ELM 0,87 et 0,87 ms | `metriques_banc.md`, tableaux S2, S3 et par événement |
| Amortissement 1,46 et 0,29 | `COMPARAISON/S10/criteres_S10.txt` ; docx ZN, tableau 2 |
| S8a : ondulation 252,4 / 22,7 mV (5 ms avant 70 ms) ; retours ZN et ELM | `metriques_banc.md`, tableaux S8a |
| S10 : ZN 70,48, 4 échelons non revenus (100, 115, 130, 160 ms), erreur finale 9,23 mV ; ELM 8,63, retours 0,16 à 1,22 ms | `metriques_banc.md`, tableaux S10 |
| Oscillation de ZN vers 1,4 kHz | `criteres_S10.txt`, résultats (« Par échelon ») |
| Tableau 5.3 (14,60 / 8,63 ; 2,29 / 1,91 ; retours 0,76 à 1,62 / 0,16 à 1,22 ms ; 129,97 / 129,89) | `COMPARAISON/S10/resultats_S10.json` (« ELM-PID fige », « ELM-PID ») ; `scenario_S10_sortie_console.txt`, lignes 48 à 62 et 90-91 |
| Gains (1,469 ; 1,058 ; 1,152), (2,476 ; 1,828 ; 1,218), (3,372 ; 2,067 ; 1,352) ; gain de l'adaptation 40,9 % | `scenario_S10_sortie_console.txt`, lignes 37 et 90 ; `resultats_S10.json` (`multiplicateurs_ZN`, `gain_adaptation`) |
| Butée sur la fenêtre de S10 : ELM 0,6 %, PSO 0,4 %, PINN 0,1 %, ZN et Fuzzy 0,0 % ; variation moyenne de *d* : ELM 0,0041, PSO 0,0062 | `metriques_banc.md`, tableau S10 (colonnes « butee (%) » et « |dd| moyen ») |
| ELM avec *L* + 0,1 % : 7,88 ; autres méthodes : moins de 2 % | `criteres_S10.txt`, résultats (« Robustesse ») ; `scenario_S10_sortie_console.txt`, ligne 83 |
| Erreur statique (fin d'essai) et écart maximal du tableau 5.4 | `metriques_banc.md`, résumé et tableaux par scénario |

### Citations

- [Lu et al., 2021] : vérifiée avec réserve (`REDACTION/references_chapitre5.md`).

### Corrections apportées à la commande

- « Le rapport cyclique le plus agité des cinq » (S10) n'est pas exact : la variation moyenne de *d* du PSO-PID (0,0062) dépasse celle de l'ELM-PID (0,0041). Ce qui est exact : le plus de temps en butée (0,6 %) et le dernier passage en butée (175,45 ms). Le texte dit cela.
- Premier changement des gains sur S1 : il est enregistré, à 4 ms (`criteres_elm_pid.txt` §8). C'est le seul changement sur S1 ; le texte donne ce chiffre.
- Écart maximal de S1 : remplacé par « – » dans le tableau 5.4 (erreur initiale de 100 V à *t* = 0, identique pour toutes les méthodes ; `metriques_banc.md`, tableau S1), avec une ligne d'explication sous le tableau.
- La part de l'adaptation poursuivie n'a été mesurée par un essai prévu que sur S10, mais une analyse non prévue existe sur S8a (3,87 contre 2,96 mV·s, soit 24 % de moins). Elle est citée comme telle dans 5.3.3. Sans elle, la synthèse laisserait croire que l'adaptation n'apporte rien sur S8a.
- « Le reste de l'écart vient d'un seul ajustement des gains, fait à 4 ms » : sur S10, figés à 50 ms, les gains de l'ELM-PID (ceux de 4 ms) donnent déjà 14,60 contre 70,48 mV·s.

### Repères

- Huit figures (5.2 à 5.9) à insérer depuis `COMPARAISON/figures_chapitre5/`. Lettres des panneaux d'après la règle de `Figures_Chapitre5.m` (S1 : un agrandissement ; S2 et S3 : deux ; S8a et S10 : quatre, et pour S10 les événements à 145, 160 et 175 ms seulement en (a)). La figure des gains a trois panneaux titrés « (a) gain P », « (b) gain I », « (c) gain D » (vérifié sur le PNG par le coordinateur).

## Source : `chapitre5_section_5_4.md`

### Chiffres et leur source

| Chiffre | Source |
| --- | --- |
| IAE du tableau 5.5 | `COMPARAISON/metriques/metriques_banc.md`, résumé |
| Groupes ordonnés, S2 non transitif, écarts min. et max. des paires (ELM/PINN S2 −0,22 à +1,90 % ; Fuzzy/PINN −1,14 à +0,51 % ; ELM/Fuzzy +0,76 à +1,38 % ; S3 PINN/ELM −0,26 à +0,55 % ; S8a PINN/ELM 0,13 à 1,24 % ; S10 66,53 à 69,85, 16,65 à 30,27, 6,30 à 16,69 %) | `COMPARAISON/separation/separation_resultats.json` ; `criteres_separation.txt` §5 |
| S1 : dépassements 7,06 / 13,20 / 13,99 / 27,34 % ; établissements 2,64 / 2,70 / 3,40 / 3,35 ms | `metriques_banc.md`, tableau S1 |
| Butée S1 : Fuzzy 2,250 / 2,605 ms ; PSO 1,595, PINN 1,773, ELM 1,791 ms ; butée S10 : 175,450 / 160,205 / 160,141 / 53,532 / 52,268 ms | `COMPARAISON/figures_chapitre5/sortie_matlab_Figures_Chapitre5_10oct.txt` (Simulink) |
| S2 : PSO 2,042 contre ELM 2,406 (−15,1 %) | `separation_resultats.json`, IAE nominales |
| S3 : écart max. 5,52 V pour tous à 50 ms ; à 70 ms PSO 5,43 V, ELM/Fuzzy/PINN 5,66 V | `metriques_banc.md`, S3 par événement |
| S8a : écart max. PSO 0,60, PINN 0,94, ELM 0,97 V | `metriques_banc.md`, tableau S8a |
| Tableau 5.6 (14,60 / 8,63 ; 17,19 / 6,63 ; 41 / 61 %, arrondis de `gain_adaptation` = 0,4089 et 0,6146 ; multiplicateurs à 50 ms, 100 ms, fin) | `COMPARAISON/S10/scenario_S10_sortie_console.txt`, lignes 37, 39, 48 à 51, 90 à 93 ; `resultats_S10.json` |
| I du PINN-PID : 0,296 (banc, fin) ; 0,250 (minimum Simulink) ; borne de la boîte 0,25 à 1 | `scenario_S10_sortie_console.txt`, ligne 39 ; sortie MATLAB ; `PINN_PID/criteres_pinn_pid.txt` §2.4 |
| I de l'ELM-PID : 2,067 (banc) ; 2,066 (maximum Simulink) | idem |
| Gains du PSO-PID ×(2,551 ; 1,369 ; 2,613) | `PSO_PID/criteres_pso_pid.txt` §6 ; sortie MATLAB |
| Essais de réglage E1 à E4 ; contraintes de marge ≥ 30° aux 12 coins (R = 4, 5, 25, 98 Ω ; *V*in = 160, 200, 240 V) ; recherche de 35 minutes, cinq graines, quatre cœurs ; 0,57 s par évaluation | `criteres_pso_pid.txt`, en-tête, §1 c, M1 et §6 |
| Aucun essai de réglage avec échelon de charge à 25 Ω sous 160 V | `COMPARAISON/S10/criteres_S10.txt`, « Contrôle d'identité » |
| « Gains dérivés à 50 ms sous la moitié de celui du PSO-PID » : ELM 1,15 et PINN 1,06 contre 2,61 | tableau 5.6 et gains du PSO-PID |
| Tableau 5.7 et rapports (3,59/38,93 ; 840,38/16 618,37 µs) | `metriques_banc.md`, « Coût de calcul » |
| PINN meilleur de 23 % sur S10 : 1 − 6,63/8,63 = 0,232 | `metriques_banc.md` |
| Fenêtre de 0,5 ms (ELM et PINN) ; 5 itérations d'Adam par fenêtre (PINN) | `ELM_PID/criteres_elm_pid.txt` §2 ; `criteres_pinn_pid.txt`, E3 |
| Apprentissage hors ligne du réseau ELM sur quatre enregistrements Simulink en boucle ouverte | `criteres_elm_pid.txt` §2 |

### Citations

- [Gaing, 2004] : vérifiée.

### Corrections et précisions par rapport à la commande

- S3, « PSO e max 5,52 V » : 5,52 V est le premier pic, identique pour les cinq méthodes. La différence porte sur le pic de 70 ms (5,43 contre 5,66 V). Le texte le dit ainsi.
- S1, Fuzzy-PID « qui oscille entre les butées jusqu'à 2,6 ms » : les fichiers donnent seulement le temps total en butée (2,250 ms) et le dernier instant en butée (2,605 ms), pas une oscillation entre les deux butées. Le texte s'en tient à ces chiffres ; Jean-Riche peut ajouter « entre les deux butées » s'il le voit sur la figure 5.11.
- Essais de réglage du PSO-PID : quatre familles (charge, *V*in, consigne, bruit et quantification), pas seulement charge et *V*in. Ce qui couvre le point de S10, c'est la contrainte de marge à 25 Ω et 160 V, pas un essai de réglage.
- « L'ELM-PID part de ZN sans réglage hors ligne » : c'est vrai pour les gains, mais son réseau est appris hors ligne (moindres carrés régularisés, C = 0,1, puis mise à jour OS-ELM en ligne ; `ELM_PID/entrainement_elm.py`, lignes 284-285). Il ne s'agit pas d'une pseudo-inverse de Moore-Penrose simple. Le texte le précise.
- Le temps Simulink d'environ 1 ms par période pour le PINN-PID (`criteres_pinn_pid.txt` §9) n'est pas utilisé : le PSO-PID, à gains fixes, prend environ 2 ms par période sous Simulink (`criteres_pso_pid.txt` §8). Ce temps est donc dominé par le circuit et l'exécution interprétée, pas par le régulateur (`definitions_metriques.txt` §6b).
- Autre point, non demandé : sur le banc, l'appel ordinaire du PINN-PID (31,28 µs) et l'appel moyen du Fuzzy-PID (12,74 µs) dépassent déjà la période du régulateur (4,545 µs). Cela ne dit rien d'une cible compilée, et ce n'est pas écrit dans le texte.
- « Jeu égal sur quatre scénarios sur cinq » : PINN/ELM non séparés sur S2 et S3, séparés mais à 1,8 % (S1) et 0,4 % (S8a).

### Repères

- Numérotation des tableaux : la commande donnait 5.7 au tableau de S10 et 5.6 au coût de calcul ; le tableau de S10 venant en premier dans le texte, il devient 5.6 et le coût 5.7.

- Figures 5.10 à 5.16 à insérer depuis `COMPARAISON/figures_chapitre5/`. Lettres des panneaux selon la règle de `Figures_Chapitre5.m` (même mise en page pour les figures « B » que pour les figures « A »).

## Source : `chapitre5_sections_5_5_5_6.md`

### Chiffres et leur source

| Chiffre | Source |
| --- | --- |
| Rapports IAE/IAE_ZN du tableau 5.8 | calculés sur les IAE nominales de `COMPARAISON/separation/separation_resultats.json` (identiques à `metriques_banc.csv` à 2,7e-10 près) |
| Dépassements S1 ; erreur statique en fin d'essai (maximum des cinq valeurs « 10 dernières ms », moyenne absolue) ; temps en butée sur S10 ; coût par appel | `COMPARAISON/metriques/metriques_banc.md` (résumé, tableaux S1 et S10, tableaux d'erreur en régime permanent, coût de calcul) |
| PSO hors ligne : 35 minutes, cinq graines, quatre cœurs ; population 50, 100 itérations | `PSO_PID/criteres_pso_pid.txt` §2 et §6 |
| ELM hors ligne : apprentissage 14,8 s ; ensemble admissible 181 s ; quatre enregistrements Simulink en boucle ouverte ; moindres carrés régularisés C = 0,1 | `ELM_PID/entrainement_elm_resultats.json` (`duree_s`) ; `ensemble_gains_elm_sortie_console.txt` (dernière ligne) ; `criteres_elm_pid.txt` §2 ; `entrainement_elm.py`, lignes 284-285 |
| PINN hors ligne : réseau tanh appris sur des enregistrements Simulink (durée non relevée) ; boîte de gains 32 s | `PINN_PID/criteres_pinn_pid.txt` §2.4 et 2.5 ; `boite_gains_pinn_sortie_console.txt`, ligne 37 |
| Fuzzy : règles de Zhao, plages de 0,533 à 1 fois P et de 1,067 à 2 fois D tirées des gains de ZN | `FUZZY_PID/criteres_fuzzy_pid.txt`, écart 1 |
| Hypothèses H1 à H4 (citations) | `REDACTION/proposition_resultats_en_hypotheses.md` §1.1 à 1.3 ; commit 4cb68ec du 8 octobre 2026 à 05:25, avant ceux de S10 (09:42) et des métriques (13:23) |
| S3, retours 0,87 / 1,05 et 1,49 ms | `metriques_banc.md`, S3 par événement |
| Ablations : +1,09 / +1,82 / +2,64 % ; S10 −9,76 (−9,76 à +4,01) ; sans OS-ELM 0 / 0 / −0,04 (−0,38 à −0,04) / −0,90 (−9,46 à +8,81) ; ELM 7,88 à 8,63 ; prévisions justes et fausses | `COMPARAISON/ablation_S10/criteres_ablation.txt` §3 et §5 ; `ablation_sortie_console.txt` |
| Jacobien : 4 615 fenêtres ; vrai 11,2 (4-6 Ω) à 15,8 (50-99 Ω) ; réseau 11,06 à 11,44 (médianes) ; corrélation de ln *J* (réseau) et ln *J* vrai −0,043 ; entrées du réseau ȳ(n−1), ȳ(n−2), d̄(n), d̄(n−1), d̄(n−2) (moyennes par fenêtre, `criteres_elm_pid.txt` §2) ; charge non observable | `ELM_PID/criteres_elm_pid.txt` §5 ; `ELM_PID/entrainement_elm_sortie_console.txt`, étape 5 (lignes 65 à 69) |
| Gradient normalisé (NLMS), porte de saturation (M1), projection (M2, M3) ; loi (4.7) du chapitre 4 (l'ancienne équation (5.4) est retirée), *η* = 0,5, *ε* = 1e-3, *α* = 0,001, *φ* = *J* (*s* .* *K*_ZN) ; *J* = ∂ŷ/∂d̄, équation (4.5) | `criteres_elm_pid.txt` §2, §4 (M4) ; explication du rôle de *J* (30 %) : `ELM_PID_INCREMENTAL/criteres_elm_pid.txt` §9, point 3 (même loi de gradient, gardée telle quelle en option B) |
| Facteurs 2,5 et 27 par rapport au PSO-PID : 3,59/1,43 = 2,51 et 38,93/1,43 = 27,2 (l'ancienne version donnait 2,6 et 28, qui sont les rapports à Ziegler-Nichols : 3,59/1,39 = 2,58 et 38,93/1,39 = 28,0) | `metriques_banc.md`, coût de calcul |
| Porte rouverte 1,5 à 2 ms après l'événement (1,5 ms après la fin de la fenêtre saturée) | chapitre 4, section 4.4.2 et figure 4.3 ; `banc_elm_pid.py`, en-tête point 4 (porte sur n, n−1, n−2) ; `criteres_elm_pid.txt` §8 et §9, point 3 (« 1.5 ms plus tard », « rattrapée en 1.5 ms ») |
| « 15 à 26 % », « 75 à 88 % », « 41 % », « dix fois » | sections 5.3 et 5.4 (`metriques_banc.md`, `resultats_S10.json`) |

### Citations

- [Liang et al., 2006] : vérifiée. [Lu et al., 2021] : vérifiée avec réserve.

### Corrections et précisions par rapport à la commande

- Plage du jacobien du réseau « 9,6 à 13,9 V par unité » : ce chiffre se trouve seulement dans `ELM_PID_INCREMENTAL/criteres_elm_pid.txt` (ligne 283), mesuré avec la version incrémentale, pas avec l'option B. Il n'est pas repris. Le texte utilise les médianes du réseau par classe de charge (11,06 à 11,44 V), tirées de l'entraînement, qui ne dépendent pas de la version. Les valeurs 11,2 à 15,8 et la corrélation −0,04 sont confirmées.
- Datation des hypothèses : la réécriture date du 8 octobre 2026, avant les résultats de ce chapitre, mais l'indice global (J dans le dépôt) des versions de mise au point (dont le PSO-PID à 0,714) était déjà connu. Le texte le dit.
- H2 : le PSO-PID ne domine pas sur toutes les grandeurs du tableau 5.8. Il est moins bon que Ziegler-Nichols et le Fuzzy-PID sur le temps en butée de S10 (0,4 % contre 0,0 %), et l'ELM-PID a la même erreur statique maximale que lui. Le verdict « non vérifiée » vaut pour les grandeurs de l'hypothèse elle-même (précision, rapidité, adaptabilité).
- H3 : sur S2, le Fuzzy-PID est au niveau de l'ELM-PID et du PINN-PID, et il devance Ziegler-Nichols partout sauf sur S1. Le verdict « non vérifiée » est relatif aux autres méthodes avancées.
- H4 : la proposition prévoyait de mesurer le coût par le nombre de simulations ; seul le temps total (35 minutes) est publié. La population (50) et le nombre d'itérations (100) sont connus, mais le nombre exact de simulations n'est pas relevé dans le dépôt.
- 5.6 : « ils viennent surtout de sa boucle d'adaptation » est une conclusion de 5.5.3 (jacobien : 1 à 3 % ; OS-ELM : rien de mesurable).

### Repères

- Aucune figure. Tableaux 5.8 et 5.9. Aucune équation dans 5.5 depuis le 10 octobre : l'ancienne (5.4) est remplacée par un renvoi à la loi (4.7). Le chapitre 5 garde les équations (5.1) à (5.3).

### Harmonisation du 10 octobre 2026 (cohérence chapitres 5 et 6)

- Notations : le dépassement n'a plus de symbole (*D* reste le gain dérivé) ; l'indice global de mise au point n'est plus noté J (5.2.3, 5.5.2), pour ne pas le confondre avec le jacobien *J* de (4.5). Dans le dépôt, il s'appelle toujours J.
- Anti-emballement : « intégration conditionnelle (blocage de l'intégrateur en butée) » en 5.2.1, puis « intégration conditionnelle », comme au chapitre 6. Le code (`banc_commun.py`) parle de « clamping ».
- PINN-PID : « boîte de gains » partout (5.4.1 disait « ensemble de gains admissibles ») ; « ensemble admissible » est réservé à l'ELM-PID.
- « Porte » définie à sa première occurrence (5.3.1).
- 5.5.1 : « facteur 2,6 et 28 par rapport au PSO-PID » remplacé par « 2,5 fois et 27 fois celui du PSO-PID » (3,59/1,43 = 2,51 ; 38,93/1,43 = 27,2 ; 2,6 et 28 étaient les rapports à Ziegler-Nichols, 1,39 µs).
- Tableau 5.6 : réductions arrondies à l'unité, 41 % et 61 % (`resultats_S10.json`, `gain_adaptation` = 0,4089 et 0,6146 ; la console affiche +40,9 et +61,5 %), comme dans le texte des chapitres 5 et 6.
- 5.5.3 : entrées exactes du réseau (`criteres_elm_pid.txt` §2 : ȳ(n−1), ȳ(n−2), d̄(n), d̄(n−1), d̄(n−2), moyennes par fenêtre) ; −0,04 est la corrélation de ln *J* du réseau et ln *J* vrai (`entrainement_elm_sortie_console.txt`, étape 5 : −0,043). Même formulation en 6.3.4.

### Alignement sur le chapitre 4 (10 octobre 2026)

- Équation (5.4) retirée : elle écrivait *φ* = *J* *s* et omettait l'inertie. 5.5.3 renvoie à la loi (4.7) (*φ*(*n*) = *J*(*n*) (*s*(*n*) ⊙ *K*ZN), terme *α* (*x*(*n*) − *x*(*n* − 1)), *α* = 0,001) et n'en garde que l'argument sur le signe et la longueur du pas. (5.4) était la dernière équation du chapitre : aucune renumérotation. La phrase « change la longueur du pas de 30 % » devient « change la longueur du pas » : avec *J* au dénominateur, une erreur de 30 % change la longueur d'un facteur 1/1,3 à 1/0,7, pas de 30 % exactement.
- Tension mesurée : « ∂*v*o/∂*d* » et « moyennes de la tension de sortie » remplacés par *J*(*n*) = ∂ŷ/∂d̄ (équation (4.5)) et « tension mesurée » (5.5.3) ; « sensibilité vraie » devient « jacobien vrai » (section 4.3.2).
- Réouverture de la porte : 1,5 ms après la fin de la fenêtre saturée, soit 1,5 à 2 ms après l'événement (5.3.2 et 5.5.3). 5.5.3 disait « une perturbation brève, que le PID rattrape en environ 1,5 ms » ; le retour dans ±1 V sur S3 prend 0,87 ms (ELM-PID), la phrase parle maintenant de la réouverture de la porte.
- Tableau 5.8 : apprentissage du réseau 14,8 s (au lieu de 15 s), comme au chapitre 4 (`entrainement_elm_resultats.json`, `duree_s`).
- 5.4.1 : premier essai de réglage du PSO-PID « échelon de charge de 7 à 4,5 Ω » (E1 du chapitre 4, `criteres_pso_pid.txt`), au lieu de « à 7 Ω ».
- Renvois précis ajoutés : porte (section 4.4.2) en 5.3.1 ; variantes d'ablation (section 4.4.4) en 5.5.3.
