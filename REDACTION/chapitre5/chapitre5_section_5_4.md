## 5.4. L'ELM-PID face aux méthodes avancées

La section 5.3 a montré ce que l'ELM-PID gagne sur son point de départ. Il reste à le situer face aux trois méthodes avancées, sur les mêmes scénarios et avec la même règle de séparation. Nous comparons d'abord les performances, puis leur coût de calcul.

### 5.4.1. Performances sur les cinq scénarios

Le tableau 5.5 donne l'IAE des cinq méthodes et les groupes que forme la règle de séparation de la section 5.2.3. Deux méthodes du même groupe ne sont pas séparées : leur ordre change selon la version du circuit.

Tableau 5.5 : IAE de la fenêtre de classement (mV·s) des cinq méthodes et groupes ordonnés par la règle de séparation.

| **Scénario** | **ZN** | **PSO-PID** | **Fuzzy-PID** | **ELM-PID** | **PINN-PID** | **Groupes ordonnés** |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | 93,77 | 87,62 | 110,91 | 93,72 | 92,06 | {PSO} < {PINN} < {ELM} < {ZN} < {Fuzzy} |
| S2 | 2,84 | 2,04 | 2,43 | 2,41 | 2,44 | {PSO} < {ELM, Fuzzy, PINN} < {ZN}, relation non transitive (voir le texte) |
| S3 | 8,67 | 5,46 | 7,94 | 6,41 | 6,40 | {PSO} < {PINN, ELM} < {Fuzzy} < {ZN} |
| S8a | 12,07 | 2,46 | 4,12 | 2,96 | 2,95 | {PSO} < {PINN} < {ELM} < {Fuzzy} < {ZN} |
| S10 | 70,48 | 3,98 | 9,18 | 8,63 | 6,63 | {PSO} < {PINN} < {ELM} < {Fuzzy} < {ZN} |

Le PSO-PID a la plus petite IAE sur les cinq scénarios, et il est séparé de toutes les autres méthodes partout. Les paragraphes qui suivent reprennent chaque scénario.

Sur S1 (figures 5.9 et 5.10), le PSO-PID a le plus petit dépassement (7,06 %) et l'établissement le plus rapide (2,64 ms). Suivent le PINN-PID (13,20 % ; 2,70 ms) et l'ELM-PID (13,99 % ; 3,40 ms). Le Fuzzy-PID dépasse de 27,34 % et s'établit en 3,35 ms ; c'est aussi lui dont le rapport cyclique reste le plus longtemps en butée pendant la montée (2,250 ms au total, la dernière fois à 2,605 ms, contre 1,6 à 1,8 ms pour les trois autres).

[FIGURE À INSÉRER : COMPARAISON/figures_chapitre5/Fig5_S1_B_ELM_PSO_Fuzzy_PINN.png]

Figure 5.9 : Tension de sortie dans le scénario S1 : ELM-PID, PSO-PID, Fuzzy-PID et PINN-PID. (a) Essai complet ; (b) agrandissement de 0 à 10 ms.

[FIGURE À INSÉRER : COMPARAISON/figures_chapitre5/Fig5_S1_B_d_ELM_PSO_Fuzzy_PINN.png]

Figure 5.10 : Rapport cyclique dans le scénario S1 : ELM-PID, PSO-PID, Fuzzy-PID et PINN-PID. (a) Essai complet ; (b) agrandissement de 0 à 10 ms.

Sur S2 (figure 5.11), l'ELM-PID, le Fuzzy-PID et le PINN-PID sont à moins de 1,4 % l'un de l'autre. La règle ne sépare ni l'ELM-PID du PINN-PID (écart de −0,22 à +1,90 % selon la version du circuit) ni le Fuzzy-PID du PINN-PID (−1,14 à +0,51 %), mais elle sépare l'ELM-PID du Fuzzy-PID (+0,76 à +1,38 %). La relation n'est donc pas transitive, et aucun groupe ne peut être formé ; en pratique, les trois méthodes sont au même niveau. Le PSO-PID fait 15 % de moins que l'ELM-PID (2,04 contre 2,41 mV·s).

[FIGURE À INSÉRER : COMPARAISON/figures_chapitre5/Fig5_S2_B_ELM_PSO_Fuzzy_PINN.png]

Figure 5.11 : Tension de sortie dans le scénario S2 : ELM-PID, PSO-PID, Fuzzy-PID et PINN-PID. (a) Essai complet ; (b) agrandissement autour de 50 ms ; (c) agrandissement autour de 70 ms.

Sur S3 (figure 5.12), l'ELM-PID et le PINN-PID ne sont pas séparés (6,41 et 6,40 mV·s). Le PSO-PID obtient 5,46 mV·s. Au premier échelon de charge, l'écart maximal est le même pour toutes les méthodes (5,52 V) ; au retour de la charge à 70 ms, il vaut 5,43 V pour le PSO-PID contre 5,66 V pour l'ELM-PID, le Fuzzy-PID et le PINN-PID.

[FIGURE À INSÉRER : COMPARAISON/figures_chapitre5/Fig5_S3_B_ELM_PSO_Fuzzy_PINN.png]

Figure 5.12 : Tension de sortie dans le scénario S3 : ELM-PID, PSO-PID, Fuzzy-PID et PINN-PID. (a) Essai complet ; (b) agrandissement autour de 50 ms ; (c) agrandissement autour de 70 ms.

Sur S8a (figure 5.13), le PINN-PID devance l'ELM-PID de 0,4 %. L'ordre est le même dans les cinq versions du circuit (écart de 0,13 à 1,24 %), mais un tel écart n'a pas de poids pratique. Le PSO-PID garde la tension plus près de la consigne : écart maximal de 0,60 V, contre 0,94 V pour le PINN-PID et 0,97 V pour l'ELM-PID.

[FIGURE À INSÉRER : COMPARAISON/figures_chapitre5/Fig5_S8a_B_ELM_PSO_Fuzzy_PINN.png]

Figure 5.13 : Tension de sortie dans le scénario S8a : ELM-PID, PSO-PID, Fuzzy-PID et PINN-PID. (a) Essai complet ; (b) à (e) agrandissements autour de 50, 70, 100 et 120 ms.

S10 écarte nettement les quatre méthodes avancées, toutes séparées (figure 5.14) : PSO-PID 3,98 mV·s, PINN-PID 6,63, ELM-PID 8,63 et Fuzzy-PID 9,18. Le PINN-PID dépasse le PSO-PID de 66,5 à 69,9 % selon la version du circuit, l'ELM-PID dépasse le PINN-PID de 16,7 à 30,3 %, et le Fuzzy-PID dépasse l'ELM-PID de 6,3 à 16,7 %.

[FIGURE À INSÉRER : COMPARAISON/figures_chapitre5/Fig5_S10_B_ELM_PSO_Fuzzy_PINN.png]

Figure 5.14 : Tension de sortie dans le scénario S10 : ELM-PID, PSO-PID, Fuzzy-PID et PINN-PID. (a) Essai complet ; (b) à (e) agrandissements autour de 50, 100, 115 et 130 ms. Les événements à 145, 160 et 175 ms ne figurent que dans le panneau (a).

Le tableau 5.6 mesure, pour les deux méthodes adaptatives, ce qu'apporte l'adaptation poursuivie après le changement de point de fonctionnement, par la même comparaison qu'à la section 5.3.3 : gains figés à 50 ms contre adaptation continue.

Tableau 5.6 : IAE de 100 ms à la fin (mV·s) et gains rapportés à ceux de Ziegler-Nichols (*P* ; *I* ; *D*) des deux méthodes adaptatives dans le scénario S10.

| **Grandeur** | **ELM-PID** | **PINN-PID** |
| --- | --- | --- |
| IAE, gains figés à 50 ms | 14,60 | 17,19 |
| IAE, adaptation continue | 8,63 | 6,63 |
| Réduction due à l'adaptation | 41 % | 61 % |
| Gains à 50 ms | 1,47 ; 1,06 ; 1,15 | 1,30 ; 0,90 ; 1,06 |
| Gains à 100 ms | 2,48 ; 1,83 ; 1,22 | 1,65 ; 0,75 ; 1,53 |
| Gains en fin d'essai | 3,37 ; 2,07 ; 1,35 | 1,70 ; 0,30 ; 1,26 |

Figés à 50 ms, le PINN-PID ferait moins bien que l'ELM-PID (17,19 contre 14,60 mV·s) ; c'est son adaptation qui le fait passer devant. Les deux méthodes montent le gain proportionnel, mais elles traitent l'action intégrale en sens opposés (figure 5.7) : l'ELM-PID la porte à 2,07 fois celle de Ziegler-Nichols en fin d'essai, tandis que le PINN-PID la réduit à 0,30 fois sur le banc, et jusqu'à 0,25 fois sous Simulink, borne basse de sa boîte de gains. Le PINN-PID obtient la plus petite IAE des deux. Nous constatons cette différence sans pouvoir l'expliquer : aucun essai de ce travail n'isole l'effet de l'action intégrale de celui des autres gains.

Le PSO-PID, à gains fixes, reste pourtant devant les deux. Ses gains valent 2,55, 1,37 et 2,61 fois ceux de Ziegler-Nichols, sur tout l'essai. Ils ont été réglés hors ligne [Gaing, 2004] sur quatre essais de réglage distincts des essais de développement : un échelon de charge de 7 à 4,5 Ω, des échelons de tension d'entrée (175 puis 235 V) à 15 Ω, un échelon de consigne à charge légère (60 Ω) et un essai avec bruit de mesure et quantification. Le réglage imposait en outre une marge de phase d'au moins 30° à douze points de fonctionnement, de 4 à 98 Ω et de 160 à 240 V, ce qui inclut le point de S10. Aucun de ces essais ne contient d'échelon de charge à 25 Ω sous 160 V. Les méthodes adaptatives, elles, partent des gains de Ziegler-Nichols et les font monter en ligne ; à 50 ms, leurs gains dérivés n'atteignent pas la moitié de celui du PSO-PID.

Sur la commande (figure 5.15), le dernier passage du rapport cyclique en butée a lieu à 175,45 ms pour l'ELM-PID, à 160,2 ms pour le PSO-PID, à 160,1 ms pour le PINN-PID, et dès 53,5 et 52,3 ms pour Ziegler-Nichols et le Fuzzy-PID.

[FIGURE À INSÉRER : COMPARAISON/figures_chapitre5/Fig5_S10_B_d_ELM_PSO_Fuzzy_PINN.png]

Figure 5.15 : Rapport cyclique dans le scénario S10 : ELM-PID, PSO-PID, Fuzzy-PID et PINN-PID. (a) Essai complet ; (b) à (e) agrandissements autour de 50, 100, 115 et 130 ms.

### 5.4.2. Précision et coût de calcul

Le tableau 5.7 donne le temps de calcul d'un appel au régulateur, mesuré sur le banc Python et cumulé sur les cinq scénarios. Il s'agit de Python interprété sur un ordinateur de bureau : seuls les rapports entre méthodes ont un sens, pas les valeurs absolues.

Tableau 5.7 : Temps de calcul par appel du régulateur sur le banc Python (µs, cinq scénarios réunis).

| **Méthode** | **Appel moyen** | **Appel ordinaire** | **Fin de fenêtre avec adaptation (nombre)** |
| --- | --- | --- | --- |
| Ziegler-Nichols | 1,39 | – | – |
| PSO-PID | 1,43 | – | – |
| Fuzzy-PID | 12,74 | – | – |
| ELM-PID | 3,59 | 3,22 | 840,38 (20) |
| PINN-PID | 38,93 | 31,28 | 16 618,37 (100) |

L'appel moyen de l'ELM-PID coûte environ dix fois moins que celui du PINN-PID (3,59 contre 38,93 µs), et un pas d'adaptation environ vingt fois moins (0,84 contre 16,6 ms). Pour ce coût, l'ELM-PID atteint la même précision que le PINN-PID sur S1 à S8a (écarts de 0,03 à 1,8 %). S10 fait exception : le PINN-PID y obtient une IAE inférieure de 23 %.

Sur ce compromis, le PSO-PID domine. En ligne, il coûte autant que Ziegler-Nichols (1,43 contre 1,39 µs par appel) et il a la meilleure IAE partout. Son coût est reporté hors ligne : la recherche par essaim a pris 35 minutes sur quatre cœurs pour cinq graines, à raison de 0,57 s par évaluation des gains.

Aucune méthode adaptative n'est démontrée compatible avec le temps réel. Sur le banc, un pas d'adaptation de l'ELM-PID dure 0,84 ms, plus que sa fenêtre de 0,5 ms ; celui du PINN-PID dure 16,6 ms. Un code compilé sur une cible embarquée irait plus vite, mais ce travail ne l'a pas mesuré.

En chiffres, l'ELM-PID peut revendiquer trois choses. Il ne fait jamais moins bien que le PID de Ziegler-Nichols dont il part. Il fait jeu égal avec le PINN-PID sur quatre scénarios sur cinq, pour un calcul environ dix fois moins coûteux, mais il reste derrière lui sur S10. Il part des gains de Ziegler-Nichols sans réglage hors ligne des gains sur des essais, ce que le PSO-PID exige ; son réseau demande en revanche un apprentissage hors ligne sur des enregistrements du convertisseur en boucle ouverte. La section 5.5 fait le bilan multicritère de ces résultats et discute le rôle réel du réseau ELM.

---

## Notes pour la relecture (à retirer)

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
- S1, Fuzzy-PID « qui oscille entre les butées jusqu'à 2,6 ms » : les fichiers donnent seulement le temps total en butée (2,250 ms) et le dernier instant en butée (2,605 ms), pas une oscillation entre les deux butées. Le texte s'en tient à ces chiffres ; Jean-Riche peut ajouter « entre les deux butées » s'il le voit sur la figure 5.10.
- Essais de réglage du PSO-PID : quatre familles (charge, *V*in, consigne, bruit et quantification), pas seulement charge et *V*in. Ce qui couvre le point de S10, c'est la contrainte de marge à 25 Ω et 160 V, pas un essai de réglage.
- « L'ELM-PID part de ZN sans réglage hors ligne » : c'est vrai pour les gains, mais son réseau est appris hors ligne (moindres carrés régularisés, C = 0,1, puis mise à jour OS-ELM en ligne ; `ELM_PID/entrainement_elm.py`, lignes 284-285). Il ne s'agit pas d'une pseudo-inverse de Moore-Penrose simple. Le texte le précise.
- Le temps Simulink d'environ 1 ms par période pour le PINN-PID (`criteres_pinn_pid.txt` §9) n'est pas utilisé : le PSO-PID, à gains fixes, prend environ 2 ms par période sous Simulink (`criteres_pso_pid.txt` §8). Ce temps est donc dominé par le circuit et l'exécution interprétée, pas par le régulateur (`definitions_metriques.txt` §6b).
- Autre point, non demandé : sur le banc, l'appel ordinaire du PINN-PID (31,28 µs) et l'appel moyen du Fuzzy-PID (12,74 µs) dépassent déjà la période du régulateur (4,545 µs). Cela ne dit rien d'une cible compilée, et ce n'est pas écrit dans le texte.
- « Jeu égal sur quatre scénarios sur cinq » : PINN/ELM non séparés sur S2 et S3, séparés mais à 1,8 % (S1) et 0,4 % (S8a).

### Repères

- Numérotation des tableaux : la commande donnait 5.7 au tableau de S10 et 5.6 au coût de calcul ; le tableau de S10 venant en premier dans le texte, il devient 5.6 et le coût 5.7.

- Figures 5.9 à 5.15 à insérer depuis `COMPARAISON/figures_chapitre5/`. Lettres des panneaux selon la règle de `Figures_Chapitre5.m` (même mise en page pour les figures « B » que pour les figures « A »).
