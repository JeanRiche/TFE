## 5.3. L'ELM-PID face au PID de Ziegler-Nichols

L'ELM-PID part des gains de Ziegler-Nichols et les modifie ensuite en ligne. La comparaison entre ces deux régulateurs isole donc ce qu'apporte l'adaptation, sur le même bloc PID et le même convertisseur. Nous la menons scénario par scénario, du démarrage nominal au changement durable du point de fonctionnement, puis nous en faisons la synthèse (section 5.3.4).

### 5.3.1. Démarrage nominal (S1)

Au démarrage, les deux régulateurs donnent la même réponse : dépassement de 13,99 % et établissement dans la bande de ±1 V en 3,40 ms. Sur la fenêtre de 0 à 30 ms, l'IAE vaut 93,72 mV·s pour l'ELM-PID et 93,77 mV·s pour Ziegler-Nichols. L'ordre des deux méthodes est le même dans les cinq versions du circuit, et la règle de la section 5.2.3 les déclare donc séparées, mais l'écart de 0,05 % n'a pas de portée pratique. La figure 5.2 montre les deux tensions de sortie, presque superposées.

[FIGURE À INSÉRER : COMPARAISON/figures_chapitre5/Fig5_S1_A_ZN_ELM.png]

Figure 5.2 : Tension de sortie dans le scénario S1 (démarrage nominal) : PID de Ziegler-Nichols et ELM-PID. (a) Essai complet ; (b) agrandissement de 0 à 10 ms.

L'explication tient au rapport cyclique (figure 5.3). Pendant la montée en tension, il est en butée pendant 1,791 ms au total, la dernière fois à 2,077 ms, pour les deux régulateurs. Or la boucle d'adaptation, reprise de [Lu et al., 2021], travaille par fenêtres de 0,5 ms et reste bloquée tant que la commande est saturée dans la fenêtre courante ou dans l'une des deux précédentes : en saturation, le rapport cyclique ne dépend plus des gains, et le gradient calculé n'aurait pas de sens. Les gains ne changent donc qu'après la fin de la saturation. Sur S1, ils changent une seule fois, à 4 ms, et passent à 1,47 fois le gain proportionnel, 1,06 fois le gain intégral et 1,15 fois le gain dérivé de Ziegler-Nichols. Ils ne bougent plus ensuite. La montée elle-même s'est faite avec les gains de Ziegler-Nichols, d'où la même réponse.

[FIGURE À INSÉRER : COMPARAISON/figures_chapitre5/Fig5_S1_A_d_ZN_ELM.png]

Figure 5.3 : Rapport cyclique dans le scénario S1 : PID de Ziegler-Nichols et ELM-PID. (a) Essai complet ; (b) agrandissement de 0 à 10 ms.

### 5.3.2. Perturbations brèves (S2, S3)

Sur les perturbations brèves, l'ELM-PID fait mieux que Ziegler-Nichols. Sur S2, son IAE vaut 2,41 mV·s contre 2,84 mV·s, soit 15 % de moins ; sur S3, 6,41 mV·s contre 8,67 mV·s, soit 26 % de moins. Les deux paires sont séparées : l'IAE de Ziegler-Nichols dépasse celle de l'ELM-PID de 17,8 à 18,5 % sur S2 et de 34,8 à 35,7 % sur S3 selon la version du circuit. Les figures 5.4 et 5.5 donnent les tensions de sortie.

[FIGURE À INSÉRER : COMPARAISON/figures_chapitre5/Fig5_S2_A_ZN_ELM.png]

Figure 5.4 : Tension de sortie dans le scénario S2 (perturbation F1 sur la consigne) : PID de Ziegler-Nichols et ELM-PID. (a) Essai complet ; (b) agrandissement autour de 50 ms ; (c) agrandissement autour de 70 ms.

[FIGURE À INSÉRER : COMPARAISON/figures_chapitre5/Fig5_S3_A_ZN_ELM.png]

Figure 5.5 : Tension de sortie dans le scénario S3 (perturbation de charge F2) : PID de Ziegler-Nichols et ELM-PID. (a) Essai complet ; (b) agrandissement autour de 50 ms ; (c) agrandissement autour de 70 ms.

L'écart maximal, lui, change à peine : 2,01 V pour les deux régulateurs sur S2, 5,66 V pour l'ELM-PID contre 5,73 V pour Ziegler-Nichols sur S3. La différence porte sur le retour. Sur S3, l'ELM-PID revient dans la bande de ±1 V en 0,87 ms aux deux échelons de charge, contre 1,05 et 1,49 ms pour Ziegler-Nichols.

Les gains ne changent pas pendant les 20 ms de perturbation. À chaque événement, la fenêtre de l'événement et les deux suivantes sont saturées ou suivent une saturation, et la boucle d'adaptation reste bloquée. Quand elle se rouvre, 1,5 ms plus tard, l'erreur moyenne de la fenêtre est déjà sous la zone morte de 0,1 V : la perturbation est rattrapée par le PID avant que la boucle lente puisse agir. Le gain de 15 à 26 % vient donc des gains atteints à 4 ms, à la fin du démarrage. Un PID aux gains fixes de 1,47, 1,06 et 1,15 fois ceux de Ziegler-Nichols, sans aucune adaptation, donne d'ailleurs la même IAE sur S3 (6,41 mV·s). Sur ces deux scénarios, l'ELM-PID a trouvé en ligne un meilleur réglage fixe ; il n'a pas réagi à la perturbation.

### 5.3.3. Changement du point de fonctionnement (S8a, S10)

À 25 Ω, l'amortissement apporté par la charge tombe de 1,46 à 0,29 (section 5.2.1). Les gains de Ziegler-Nichols, calculés au point nominal, ne conviennent plus. Sur S8a, l'IAE de Ziegler-Nichols vaut 12,07 mV·s contre 2,96 mV·s pour l'ELM-PID, soit 75 % de moins pour ce dernier. Juste avant le retour de la tension d'entrée à 200 V (5 ms avant 70 ms), l'ondulation de la tension de sortie atteint 252 mV crête à crête avec Ziegler-Nichols, contre 23 mV avec l'ELM-PID (figure 5.6). Les deux régulateurs ramènent cependant la tension dans la bande de ±1 V après chaque événement.

[FIGURE À INSÉRER : COMPARAISON/figures_chapitre5/Fig5_S8a_A_ZN_ELM.png]

Figure 5.6 : Tension de sortie dans le scénario S8a (charge de 25 Ω, variations de *V*in) : PID de Ziegler-Nichols et ELM-PID. (a) Essai complet ; (b) à (e) agrandissements autour de 50, 70, 100 et 120 ms.

S10 accentue cet écart (figure 5.7). Au nouveau point de fonctionnement (160 V, 25 Ω), Ziegler-Nichols oscille vers 1,4 kHz et la tension ne revient pas dans la bande de ±1 V avant l'événement suivant pour quatre des six échelons de charge. Son IAE de 100 ms à la fin vaut 70,48 mV·s, et son erreur moyenne sur les 10 dernières millisecondes est encore de 9,23 mV. L'ELM-PID obtient 8,63 mV·s, soit 88 % de moins, et revient dans la bande après chaque échelon, en 0,16 à 1,22 ms.

[FIGURE À INSÉRER : COMPARAISON/figures_chapitre5/Fig5_S10_A_ZN_ELM.png]

Figure 5.7 : Tension de sortie dans le scénario S10 (changement durable du point de fonctionnement) : PID de Ziegler-Nichols et ELM-PID. (a) Essai complet ; (b) à (e) agrandissements autour de 50, 100, 115 et 130 ms. Les événements à 145, 160 et 175 ms ne figurent que dans le panneau (a).

Une part de cet écart ne doit rien à l'adaptation au nouveau point. S10 a été conçu pour la mesurer : la même simulation est refaite en figeant les gains de l'ELM-PID à 50 ms, juste avant le changement de point de fonctionnement. Le tableau 5.3 compare les deux versions.

Tableau 5.3 : ELM-PID adaptatif et ELM-PID à gains figés à 50 ms dans le scénario S10.

| **Grandeur** | **Gains figés à 50 ms** | **Adaptatif** |
| --- | --- | --- |
| IAE de 100 ms à la fin (mV·s) | 14,60 | 8,63 |
| Écart maximal de 100 ms à la fin (V) | 2,29 | 1,91 |
| Temps de retour dans ±1 V par échelon (ms) | 0,76 à 1,62 | 0,16 à 1,22 |
| IAE de 50 à 100 ms, réajustement (mV·s) | 129,97 | 129,89 |
| Gains *P*, *I*, *D* à la fin, rapportés à Ziegler-Nichols | 1,47 ; 1,06 ; 1,15 | 3,37 ; 2,07 ; 1,35 |

Figés à 50 ms, les gains de l'ELM-PID donnent déjà 14,60 mV·s, contre 70,48 mV·s pour Ziegler-Nichols : la plus grande part de l'écart vient du réglage trouvé à la fin du démarrage. L'adaptation poursuivie après 50 ms réduit encore l'IAE de 41 %, de 14,60 à 8,63 mV·s. Elle n'agit pas pendant le réajustement de 50 à 100 ms (129,89 contre 129,97 mV·s), dominé par la surtension qui suit la chute du courant de charge, mais ensuite, d'un échelon de charge à l'autre. Sur S8a, une analyse faite après le calcul, et non prévue, donne un résultat de même sens : un PID aux gains fixes de 1,47, 1,06 et 1,15 fois ceux de Ziegler-Nichols obtient 3,87 mV·s, contre 2,96 mV·s pour l'ELM-PID adaptatif.

La figure 5.8 montre comment les gains évoluent. Ceux de l'ELM-PID passent de 1,47, 1,06 et 1,15 fois ceux de Ziegler-Nichols à 50 ms, à 2,48, 1,83 et 1,22 fois à 100 ms, puis à 3,37, 2,07 et 1,35 fois en fin d'essai. L'ELM-PID monte surtout les gains proportionnel et intégral, et presque pas le gain dérivé. La figure donne aussi les gains des autres méthodes, discutés à la section 5.4.

[FIGURE À INSÉRER : COMPARAISON/figures_chapitre5/Fig5_S10_gains.png]

Figure 5.8 : Gains *P* (a), *I* (b) et *D* (c) rapportés à ceux de Ziegler-Nichols dans le scénario S10, pour les cinq méthodes.

L'adaptation a un coût sur la commande (figure 5.9). Sur la fenêtre de classement de S10, l'ELM-PID est la méthode qui passe le plus de temps avec le rapport cyclique en butée (0,6 % des instants), et la seule qui y touche encore à 175 ms (dernier instant à 175,45 ms, contre environ 160 ms pour le PSO-PID et le PINN-PID, et 53,5 et 52,3 ms pour Ziegler-Nichols et le Fuzzy-PID). Sa variation moyenne du rapport cyclique d'une période à l'autre (0,0041) reste en revanche inférieure à celle du PSO-PID (0,0062). Son résultat est enfin sensible à de très petits écarts du circuit : avec *L* augmentée de 0,1 %, son IAE sur S10 passe de 8,63 à 7,88 mV·s, alors que celle des autres méthodes bouge de moins de 2 %. Cette sensibilité ne change pas le verdict face à Ziegler-Nichols, dont l'IAE reste de 709 à 802 % plus élevée selon la version du circuit.

[FIGURE À INSÉRER : COMPARAISON/figures_chapitre5/Fig5_S10_A_d_ZN_ELM.png]

Figure 5.9 : Rapport cyclique dans le scénario S10 : PID de Ziegler-Nichols et ELM-PID. (a) Essai complet ; (b) à (e) agrandissements autour de 50, 100, 115 et 130 ms.

### 5.3.4. Synthèse

Le tableau 5.4 rassemble les résultats des cinq scénarios.

Tableau 5.4 : Comparaison de l'ELM-PID et du PID de Ziegler-Nichols (ZN) sur les cinq scénarios.

| **Scénario** | **IAE ZN (mV·s)** | **IAE ELM-PID (mV·s)** | **ELM-PID/ZN** | **Séparation (écart de ZN sur l'ELM-PID)** | **Écart maximal ZN / ELM-PID (V)** | **Erreur statique ZN / ELM-PID (mV)** |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | 93,77 | 93,72 | 0,999 | séparés, 0,05 à 0,06 % | – / – | 0,01 / 0,00 |
| S2 | 2,84 | 2,41 | 0,847 | séparés, 17,8 à 18,5 % | 2,01 / 2,01 | 0,00 / 0,01 |
| S3 | 8,67 | 6,41 | 0,739 | séparés, 34,8 à 35,7 % | 5,73 / 5,66 | 0,00 / 0,00 |
| S8a | 12,07 | 2,96 | 0,246 | séparés, 302 à 313 % | 1,43 / 0,97 | 0,00 / 0,00 |
| S10 | 70,48 | 8,63 | 0,122 | séparés, 709 à 802 % | 3,22 / 1,91 | 9,23 / 0,01 |

Sur S1, l'écart maximal est l'erreur initiale de 100 V à *t* = 0, identique pour toutes les méthodes ; il n'est pas reporté.

Sur aucun des cinq scénarios l'ELM-PID ne fait moins bien que Ziegler-Nichols. Son avantage dépend du scénario : nul au démarrage, où l'adaptation est bloquée par la saturation ; de 15 à 26 % près du point nominal, où il vient des gains trouvés à la fin du démarrage ; de 75 à 88 % à charge légère, là où le réglage de Ziegler-Nichols ne convient plus. La part due à l'adaptation poursuivie après le démarrage n'a été mesurée comme prévu que sur S10, où elle réduit l'IAE de 41 %. Le reste de l'écart vient d'un seul ajustement des gains, fait à 4 ms.

La section 5.4 compare l'ELM-PID aux trois méthodes avancées, dont le PSO-PID, qui garde des gains fixes. La section 5.5 discute le rôle réel du réseau ELM dans ces résultats.

---

## Notes pour la relecture (à retirer)

### Chiffres et leur source

| Chiffre | Source |
| --- | --- |
| S1 : dépassement 13,99 %, établissement 3,40 ms (ZN et ELM) ; IAE 93,77 / 93,72 | `COMPARAISON/metriques/metriques_banc.md`, tableau S1 |
| Écarts de séparation ZN/ELM (S1 0,053 à 0,055 % ; S2 17,75 à 18,50 % ; S3 34,77 à 35,69 % ; S8a 301,9 à 312,8 % ; S10 708,9 à 801,8 %) ; écart = IAE_ZN/IAE_ELM − 1 | `COMPARAISON/separation/separation_resultats.json` (paires ELM-PID / Ziegler-Nichols) ; définition dans `separation_methodes.py`, ligne 207 |
| Rapports ELM/ZN 0,999 ; 0,847 ; 0,739 ; 0,246 ; 0,122 | calculés sur les IAE nominales de `separation_resultats.json` (93,716/93,765 ; 2,406/2,841 ; 6,406/8,665 ; 2,965/12,072 ; 8,632/70,481) |
| Butée S1 : 1,791 ms au total, dernière à 2,077 ms (ZN et ELM) ; S10 : ELM 175,450 ms, PSO 160,205, PINN 160,141, ZN 53,532, Fuzzy 52,268 | `COMPARAISON/figures_chapitre5/sortie_matlab_Figures_Chapitre5_10oct.txt` (Simulink) |
| Boucle de 0,5 ms, porte sur trois fenêtres (saturation), zone morte 0,1 V | `ELM_PID/criteres_elm_pid.txt` §2 et M1 (§4) |
| Changement unique des gains à 4 ms sur S1, x(1,469 ; 1,058 ; 1,152) ; S1 : 1 fenêtre, S2 : 1, S3 : 2 (second à 72 ms), S8a : 7 | `criteres_elm_pid.txt` §8 |
| Porte fermée pendant F1/F2, réouverture 1,5 ms plus tard, erreur sous 0,1 V (S3 à 52 ms : −0,038 V) | `criteres_elm_pid.txt` §8 (« Ce que l'adaptation fait pendant une perturbation ») et §9 point 3 |
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
