# Chapitre 3 : Modélisation du convertisseur et base commune

## 3.1. Introduction

Les cinq régulateurs comparés agissent sur le même convertisseur, avec le même bloc PID, et sont jugés sur les mêmes essais. Cet ensemble, la « base commune » (version 2.1), est fixé avant toute comparaison, pour qu'un écart de résultat ne puisse venir que de la façon de régler les gains.

Dans ce chapitre, nous dimensionnons le convertisseur Buck (section 3.2) et en tirons le modèle moyen (section 3.3). La section 3.4 définit le bloc PID commun et calcule les gains de Ziegler-Nichols, la section 3.5 présente les outils de simulation et leur validation croisée, et la section 3.6 les essais.

## 3.2. Dimensionnement du convertisseur

Le convertisseur abaisse une tension d'entrée *V*in de 200 V à une tension de sortie de 100 V, sur une charge nominale *R* de 5 Ω, soit 20 A et 2 kW. Ces trois valeurs sont imposées ; les essais font varier *V*in de 160 à 240 V et la charge de 4 à 98 Ω. Sur le schéma de la figure 3.1, le MOSFET conduit pendant une fraction *d* de chaque période de découpage, la diode pendant le reste, et le filtre *LC* lisse la tension de sortie *v*o.

[FIGURE À INSÉRER : Fig3_1_convertisseur_Buck.png]

Figure 3.1 : Convertisseur Buck de la base commune, commandé par modulation de largeur d'impulsion (MLI) à partir du rapport cyclique *d*.

La fréquence de découpage *f*s = 22 kHz est la plus basse fréquence inaudible, avec 10 % de marge au-dessus de 20 kHz : les pertes par commutation croissent avec *f*s.

L'inductance et la capacité doivent tenir, pour des composants à ±20 %, une ondulation de courant d'au plus 20 % du courant de charge, une ondulation de tension d'au plus 0,1 V et un démarrage direct sans dépassement à la charge nominale (amortissement au moins critique). Les deux dernières exigences dimensionnent la bobine. Au pire cas, elles imposent une inductance d'au moins 5,94 mH. Dans la série normalisée E6 [RÉF. À VÉRIFIER : CEI 60063, série E6], la plus petite inductance qui admet un condensateur normalisé vaut 10 mH. Elle accepte 33 ou 47 µF ; 47 µF donne l'impédance caractéristique √(*L*/*C*) la plus faible (14,6 Ω contre 17,4 Ω), à laquelle l'écart de tension dû à un échelon de charge est proportionnel.

Les interrupteurs gardent les pertes de conduction des blocs Simscape par défaut. Avec *d* = 0,5 en boucle ouverte, elles ramènent la sortie à 98,60 V ; le régulateur doit fournir *d* = 0,507 pour obtenir 100 V. Le tableau 3.1 récapitule les valeurs retenues.

Tableau 3.1 : Valeurs retenues pour le convertisseur et la simulation.

| **Grandeur** | **Symbole** | **Valeur** |
| --- | --- | --- |
| Tension d'entrée | *V*in | 200 V (essais de 160 à 240 V) |
| Consigne de tension de sortie | *v*ref | 100 V |
| Charge nominale | *R* | 5 Ω (essais de 4 à 98 Ω) |
| Fréquence de découpage | *f*s | 22 kHz |
| Inductance | *L* | 10 mH |
| Capacité | *C* | 47 µF |
| Pertes du MOSFET | *R*on | 0,1 Ω |
| Pertes de la diode | *V*f | 0,8 V (et 1 mΩ) |
| Pas de calcul du circuit | *h* | 1/(22 000 × 1 200) s = 37,88 ns |

Le pas *h* place exactement 1 200 pas dans une période de découpage. Une impulsion ne pouvant changer d'état qu'à un instant de calcul, l'erreur qui en résulte sur la tension reste sous 0,02 V.

La conduction est continue tant que le courant de charge dépasse la moitié de l'ondulation du courant de la bobine, soit en régime établi [Erickson et Maksimović, 2020] :

*R* < 2 *L* *f*s / (1 − *d*),        (3.1)

où *d* est le rapport cyclique de régime, proche de *v*ref/*V*in. La limite vaut environ 880 Ω sous 200 V et 1 170 Ω sous 160 V, et 603 Ω au pire cas (240 V, bobine à −20 %). Toutes les charges des essais (au plus 98 Ω) sont donc en conduction continue en régime établi. La conduction discontinue n'y apparaît que de façon passagère, lors d'oscillations ; les deux outils de simulation la représentent.

## 3.3. Modèle moyen et amortissement

En conduction continue, le modèle moyen sur une période de découpage relie le rapport cyclique à la tension de sortie [Erickson et Maksimović, 2020]. Pertes négligées, sa fonction de transfert est un second ordre :

*G*vd(*s*) = *V*in / (*L* *C* *s*² + (*L*/*R*) *s* + 1),        (3.2)

de pulsation propre *ω*0 = 1/√(*LC*) = 1 459 rad/s (232 Hz) et de facteur d'amortissement :

*ζ* = (1/(2*R*)) √(*L*/*C*).        (3.3)

L'amortissement varie comme 1/*R*. À 5 Ω, *ζ* = 1,46 : les deux pôles sont réels, à −578,7 et −3 676,6 s⁻¹, soit des constantes de temps de 1,73 ms et 0,272 ms. À 25 Ω, *ζ* tombe à 0,29, et à 98 Ω à 0,074 : à charge légère, seul le régulateur peut empêcher la tension d'osciller.

Le modèle moyen ne vaut qu'aux fréquences nettement inférieures à *f*s, ici 95 fois la fréquence propre. Il sert au calcul des gains de Ziegler-Nichols et, discrétisé avec un bloqueur d'ordre zéro à *T*c, à celui des marges de stabilité ; les résultats chiffrés des chapitres 4 et 5 viennent de la simulation du circuit commuté.

## 3.4. Le régulateur de référence

### 3.4.1. Le bloc PID commun

Le régulateur est échantillonné à *T*c = 1/220 000 s (4,545 µs), soit dix fois par période de découpage, aux mêmes instants de chaque période. À l'instant *k*·*T*c, il reçoit l'erreur *e*(*k*) = *v*ref(*k*) − *y*(*k*), où *y* est la tension de sortie mesurée. Les cinq méthodes utilisent le même bloc PID discret de forme parallèle, dont la sortie avant saturation s'écrit [Åström et Hägglund, 2006] :

*u*(*z*) = [ *P* + *I* *T*c/(*z* − 1) + *D* *N* (*z* − 1)/(*z* − 1 + *N* *T*c) ] *e*(*z*),        (3.4)

où *P*, *I* et *D* sont les gains proportionnel, intégral et dérivé, et *N* le coefficient du filtre du terme dérivé, en rad/s. L'intégrateur et le filtre sont discrétisés par la méthode d'Euler explicite, qui remplace 1/*s* par *T*c/(*z* − 1). Le rapport cyclique appliqué est *d*(*k*) = *u*(*k*) borné à [0,01 ; 0,99]. Quand *u* sort de ces bornes et que l'entrée de l'intégrateur pousse dans le même sens, l'intégration s'arrête : c'est l'anti-emballement par intégration conditionnelle [Åström et Hägglund, 2006]. L'intégrateur part de 0,5 (*v*ref/*V*in) et le filtre de 0,01, plus petite valeur acceptée par le bloc de Simulink ; ce départ du filtre porte le maximum au démarrage nominal à 114,0 V, contre 104,0 V sans à-coup.

Les méthodes ne diffèrent que par la façon de fixer *P*, *I* et *D*.

### 3.4.2. Les gains de Ziegler-Nichols

La note de Mudry présente deux variantes de la méthode de [Ziegler et Nichols, 1942], toutes deux réservées aux processus non oscillants dont la phase franchit −180° [Mudry, 2006, p. 1]. Avec le retard d'une demi-période d'échantillonnage dû au bloqueur, la phase du convertisseur atteint −180° vers 6,9 kHz. La variante du point critique a été écartée : essayée sur le banc, elle fait apparaître une zone d'oscillation au quart de la fréquence de découpage, qui disparaît quand le gain augmente, et des oscillations entre *f*s/5 et *f*s/3, là où le modèle moyen ne décrit plus le convertisseur.

Nous avons donc retenu la méthode de la réponse indicielle. Elle se lit sur la réponse du modèle moyen (3.2) à un échelon de rapport cyclique, calculée de façon exacte : la tangente au point d'inflexion coupe l'axe des temps au retard apparent *L*a = 0,155951 ms, noté ainsi pour ne pas le confondre avec l'inductance (figure 3.2). La pente de la réponse normalisée y vaut *p* = 409,687 s⁻¹ et la constante de temps apparente *T* = 1,857541 ms. La ligne PID de la table 1 de Mudry donne [Mudry, 2006, p. 10] :

*K*p = 1,2/(*p* *L*a *K*0),  *T*i = 2 *L*a,  *T*d = 0,5 *L*a,        (3.5)

où *K*0 = *V*in = 200 V est le gain statique. Il vient *K*p = 0,093910, *T*i = 0,311901 ms et *T*d = 0,077975 ms. La note écrit le PID sous forme standard *K*p (1 + 1/(*T*i *s*) + *T*d *s*) ; dans la forme parallèle (3.4), *P* = *K*p, *I* = *K*p/*T*i = 301,089 et *D* = *K*p *T*d = 7,3227·10⁻⁶.

[FIGURE À INSÉRER : figures_zn/releve_Ziegler_Nichols.png, produite par REDACTION/chapitre3/figures/Figure_Releve_Ziegler_Nichols.m]

Figure 3.2 : Relevé de Ziegler-Nichols sur la réponse indicielle du modèle moyen (*R* = 5 Ω).

Sur la réponse du circuit commuté, le retard apparent est plus court de 11,9 µs, de l'ordre d'un quart de période de découpage, et *K*p plus grand de 8,9 %. Cet écart dépend de la phase de la porteuse à l'instant de l'échelon, ce qui n'est pas le cas du modèle moyen, que nous avons gardé.

La note conseille un coefficient de filtre entre 5 et 20 dans sa convention, où le pôle du filtre est à *N*Mudry/*T*d [Mudry, 2006, p. 3]. La modulation n'échantillonnant le rapport cyclique qu'une fois par période de découpage, le pôle doit rester sous *f*s/2 = 11 kHz, ce qui limite ce coefficient à 5,39. Avec *N*Mudry = 5, le bloc reçoit *N* = 5/*T*d = 64 122,9 rad/s, soit un pôle à 10,2 kHz. Le filtre discrétisé a son pôle en *z* = 1 − *N* *T*c ; il est stable si 0 < *N* *T*c < 2, et *N* *T*c vaut ici 0,29.

Mudry conseille de réduire *K*p de moitié, ces gains étant en général trop élevés [Mudry, 2006, p. 10]. Sur ce convertisseur, diviser *K*p par 2 ou par 3 fait tomber la marge de phase nominale de 32,0° à 24,5° puis 22,1° : le réglage de la table est gardé. Sa marge reste entre 24,9° et 39,5° de 4 à 6 Ω et de 160 à 240 V, mais tombe entre 3,1° et 12,3° à 25 Ω, et à −3,1° à 98 Ω sous 160 V, où la boucle linéaire est instable. Ce réglage est une référence commune et un point de départ, non un réglage optimal.

## 3.5. Les outils de simulation

### 3.5.1. Le modèle Simulink commun

Le modèle `Buck_Commun.slx` (figure 3.3) est construit sous MATLAB R2024a avec la bibliothèque Simscape Electrical (Specialized Power Systems), en mode discret au pas *h*. Au circuit et au PID de Ziegler-Nichols, il ajoute ce que demandent les essais : une source de tension commandée pour faire varier *V*in, une charge électronique en parallèle avec *R*, des profils lus à la période *T*c et une quantification de la mesure.

[FIGURE À INSÉRER : modèle Simulink commun, exporté de ELM_PID/Buck_Commun.slx (File > Export Model To > Image)]

Figure 3.3 : Modèle Simulink commun aux cinq méthodes.

Le générateur MLI compare le rapport cyclique à une porteuse à 22 kHz. Le rapport cyclique calculé à l'instant *k*·*T*c est maintenu pendant la période *T*c qui suit, soit 120 pas du circuit ; un changement de *d* peut donc avancer ou retarder l'ouverture du MOSFET dans la période de découpage en cours. La mesure vaut *y* = *v*o + bruit, quantifiée au pas *q* ; dans neuf des onze essais de développement, le bruit est nul et *q* = 10⁻⁹ V. L'essai S7a quantifie la mesure au pas de 48,8 mV d'un convertisseur analogique-numérique (CAN) de 12 bits ; S7b ajoute un bruit gaussien d'écart type 10 mV, filtré à 10 kHz. Les méthodes adaptatives ajoutent un bloc qui calcule les gains et les envoie au bloc PID, réglé en gains externes (section 4.5).

### 3.5.2. Le banc Python

Le banc `banc_commun.py` résout le même circuit commuté au même pas *h*, par la méthode des trapèzes, avec les mêmes conventions que Simscape (un pas de retard pour l'interrupteur et les sources commandées) et la conduction discontinue. Il regroupe les pas identiques d'une période *T*c en puissances d'une même matrice, ce qui donne, au nombre flottant près, le résultat d'un calcul pas à pas, en une dizaine de secondes pour les onze essais du PID de Ziegler-Nichols. Chaque méthode reprend ce banc avec son propre régulateur. Les chiffres de référence du travail sont ceux du banc ; Simulink sert à les valider.

### 3.5.3. Validation croisée

Avec le PID de Ziegler-Nichols, sur les modèles Simulink de départ (point nominal et échelon de charge de 5 à 4,333 Ω), les écarts restent sous 0,01 V et 0,01 ms. Pour le PSO-PID, le Fuzzy-PID, l'ELM-PID et le PINN-PID, les IAE après 30 ms concordent sur les onze essais de développement à 0,1 %, 0,2 %, 0,1 % et 0,3 % près.

L'essai S7a fait exception, avec des écarts de +0,8 %, +4,8 %, +2,5 % et −6,1 % pour les mêmes méthodes. Au pas de 48,8 mV, une différence d'arrondi infime entre les deux simulateurs suffit à changer un code du CAN, donc la commande, et les deux trajectoires se séparent ensuite. Pour l'ELM-PID, Simulink n'adapte les gains sur aucune fenêtre de S7a, contre deux pour le banc.

## 3.6. Les essais

### 3.6.1. Les essais de développement

Les onze essais S1 à S9 de la base commune (S7a, S7b, S8a et S8b compris) sont appelés « essais de développement ». Ils commencent tous par un démarrage et durent 0,2 s, sauf S9 (0,42 s) ; le tableau 3.2 les décrit.

Tableau 3.2 : Les onze essais de développement.

| **Code** | **Description** |
| --- | --- |
| S1 | Point nominal : 5 Ω, 200 V, aucune perturbation |
| S2 | Consigne 100 + 2 exp(cos(10π*t*)) V sur [50 ; 70) ms (signal F1 de [Lu et al., 2021]) |
| S3 | Charge de 4,333 Ω sur [50 ; 70) ms (signal F2 du même article) |
| S4 | Charge de 4 Ω sur [50 ; 70) ms et de 6 Ω sur [100 ; 120) ms |
| S5 | *V*in = 160 V sur [50 ; 70) ms et 240 V sur [100 ; 120) ms |
| S6 | Rampe de consigne de 100 à 110 V sur [50 ; 70) ms, palier, retour à 100 V sur [100 ; 120) ms |
| S7a | Mesure quantifiée au pas de 48,8 mV (CAN de 12 bits) |
| S7b | Bruit de mesure gaussien de 10 mV, filtré à 10 kHz |
| S8a | Charge de 25 Ω pendant tout l'essai ; *V*in = 160 V sur [50 ; 70) ms et 240 V sur [100 ; 120) ms |
| S8b | Comme S8a, à 98 Ω |
| S9 | Grand signal : rampe de charge de 5 à 98 Ω, consigne à 150 puis 50 V, *V*in à 150 V, retour à 100 V, 200 V et 5 Ω |

Ces essais ont servi à suivre les méthodes pendant leur mise au point, par un indice global : la moyenne de treize rapports d'IAE à Ziegler-Nichols (dix après 30 ms, trois au démarrage), définie sur le dépôt GitHub du travail [URL DU DÉPÔT À INSÉRER]. Une règle écrite le 7 octobre 2026, avant le calcul des classements par essai, devait ensuite y désigner l'essai qui sépare le mieux les méthodes (section 5.2.2).

Aucune valeur numérique d'une méthode n'a été ajustée sur ces onze essais : les gains du PSO-PID et la zone morte du PINN-PID ont été choisis sur les essais de réglage de la section 3.6.2, et les réglages de l'ELM-PID viennent de l'article de référence ou de critères écrits avant le calcul. En revanche, plusieurs changements de structure ont été décidés en connaissant des résultats sur ces essais : le coût du PSO-PID, la porte, la projection et l'option B de l'ELM-PID, la présence d'une zone morte pour le PINN-PID. Le chapitre 4 les déclare ; pour le PSO-PID, le coût d'origine avait d'abord donné un indice global de 1,69.

Un douzième essai, S10, défini après coup avec ses critères et ses prévisions écrits avant le calcul, change durablement le point de fonctionnement ; hors de l'indice global, il est décrit au chapitre 5 (tableau 5.2).

### 3.6.2. Les essais de réglage

Quatre « essais de réglage », E1 à E4, ont servi à régler les méthodes. Ils reprennent les familles de perturbations des essais de développement (charge, tension d'entrée, consigne, mesure) sur d'autres points de fonctionnement, à d'autres instants et avec une autre graine de bruit (tableau 3.3).

Tableau 3.3 : Les quatre essais de réglage.

| **Code** | **Point de départ** | **Perturbation** | **Durée** |
| --- | --- | --- | --- |
| E1 | 7 Ω, 190 V | charge de 4,5 Ω sur [40 ; 65) ms | 90 ms |
| E2 | 15 Ω, 210 V | *V*in = 175 V sur [40 ; 65) ms, puis 235 V | 90 ms |
| E3 | 60 Ω, 220 V | échelon de consigne de +10 V sur [40 ; 65) ms | 90 ms |
| E4 | 9 Ω, 200 V | bruit de mesure de 10 mV (autre graine) et CAN de 12 bits | 60 ms |

Le PSO-PID y a cherché ses gains, le PINN-PID y a choisi sa zone morte parmi trois corrections candidates, et l'ELM-PID ne s'en est servi que pour contrôler son code (section 4.4.4). Le Fuzzy-PID n'optimise rien.

## 3.7. Conclusion

Le convertisseur de la base commune (*L* = 10 mH, *C* = 47 µF, *f*s = 22 kHz) démarre sans dépassement à la charge nominale, mais son amortissement tombe de 1,46 à 5 Ω à 0,29 à 25 Ω : un réglage fait au point nominal ne vaut plus à charge légère. Les cinq méthodes partagent le bloc PID (3.4), échantillonné à *T*c = 1/220 000 s, et partent des gains de Ziegler-Nichols tirés de la réponse indicielle du modèle moyen.

Le banc Python et le modèle Simulink s'accordent à 0,3 % près sur les IAE, l'essai quantifié S7a excepté. Les essais de développement ont servi à suivre les méthodes, les essais de réglage à les régler. Le chapitre 4 construit l'ELM-PID et les méthodes de comparaison sur cette base.

---

## Notes pour la relecture (à retirer)

### Chiffres et leur source

Sigles des sources : DIM = `Dimensionnement_convertisseur_Buck.docx` (converti en Markdown) ; ZN = `Determination_gains_PID_Ziegler_Nichols.docx` (converti) ; script ZN = `REDACTION/chapitre3/figures/Figure_Releve_Ziegler_Nichols.m`.

| Chiffre | Source |
| --- | --- |
| 200 V, 100 V, 5 Ω, 20 A, 2 kW ; *V*in 160 à 240 V ; charges 4 à 98 Ω | DIM, tableau 1 |
| *f*s = 22 kHz : plus basse fréquence inaudible, 10 % au-dessus de 20 kHz ; pertes par commutation proportionnelles à *f*s | DIM, tableau 2 (E1) et section 4 |
| Exigences : Δ*i*L ≤ 20 % de *I*o, Δ*V*o ≤ 0,1 V, démarrage sans dépassement (*ζ* ≥ 1) à 5 Ω, tolérances ±20 % | DIM, tableau 2 (E2 à E5) |
| *L*/*C* ≥ 150 Ω², *L*·*C* ≥ 2,354·10⁻⁷ H·F, *L*min = 5,94 mH, série E6, 10 mH avec 33 ou 47 µF, 14,6 contre 17,4 Ω | DIM, sections 7 et 8 (tableaux 3 à 5) |
| *R*on = 0,1 Ω, *V*f = 0,8 V, *R*d = 1 mΩ (Simscape par défaut) ; 98,60 V à *d* = 0,5 ; *d* = 0,5071 pour 100 V | DIM, section 3 ; `ELM_PID/banc_commun.py`, étape 0 (RON, VF, RDIODE) |
| *h* = 1/(22 000 × 1 200) s = 37,88 ns ; erreur due au pas < 0,02 V ; pas entier (raie de battement sinon) | DIM, section 10.1 et tableau 13 ; `banc_commun.py` (H, NPER) |
| Limite de conduction continue (3.1) : 880 Ω à 200 V, 1 173 Ω à 160 V, 603 Ω à 240 V avec *L* à −20 % | calcul refait (2 × 0,01 × 22 000/(1 − *d*)) ; 603 Ω : DIM, section 9.2 |
| Conduction discontinue passagère représentée par le banc et Simulink (ZN à 98 Ω : 0,2 % du temps) | `banc_commun.py`, en-tête « LE CIRCUIT SIMULE » ; ZN, tableau 17 |
| (3.2), *ω*0 = 1 459 rad/s (232 Hz), (3.3) | DIM, section 3 et tableau 5 ; ZN, tableau 2 |
| *ζ* = 1,46 à 5 Ω (1,19 au pire cas), 0,29 à 25 Ω, 0,074 à 98 Ω ; pôles −578,70 et −3 676,62 s⁻¹ ; *τ* 1,7280 et 0,27199 ms | DIM, tableaux 5 et 6, section 12.1 ; ZN, tableau 2 ; recalcul Python (1,4586 ; 0,2917 ; 0,0744) |
| *f*s = 95 *f*0 | DIM, section 9.1 |
| *T*c = 1/220 000 s, dix échantillons par période, synchronisés | ZN, section 6 et tableau 8 ; `banc_commun.py` (NREG = 120) |
| Forme (3.4), Euler explicite, bornes [0,01 ; 0,99], clamping (« même signe que le dépassement »), conditions initiales 0,5 et 0,01 ; 114,0 V contre 104,0 V | `banc_commun.py`, classe `PIDClassique` et constantes ; ZN, sections 7.2 à 7.4, tableaux 11 et 12 |
| Mudry : processus non oscillants, phase franchissant −180° (p. 1) ; −180° atteint vers 6,9 kHz avec le bloqueur | `references_chapitre5.md` §1 ; ZN, section 3.1 |
| Point critique écarté : oscillation à *f*s/4 pour *P* = 3 à 3,5, puis stable, puis oscillations entre *f*s/5 et *f*s/3 | ZN, section 3.2 et tableau 3 |
| Inflexion 0,59684 ms ; *L*a = 0,155951 ms ; *p* = 409,687 s⁻¹ ; *T* = 1,857541 ms ; temps mort relatif 0,0775 | ZN, tableau 5 ; script ZN, « VALEURS ATTENDUES » ; recalcul Python (0,59684 ; 0,1559506 ; 409,6866 ; 1,8575409 ; 0,07745) |
| (3.5), *K*p = 0,093910, *T*i = 0,311901 ms, *T*d = 0,077975 ms, *P*, *I*, *D* | ZN, tableaux 7, 9 et 19 ; script ZN, section 5 ; recalcul Python (0,0939102 ; 301,0895 ; 7,32267·10⁻⁶) |
| Réponse commutée : *L*a plus court de 11,9 µs (0,155951 − 0,14410 ms), *K*p + 8,9 % (0,10226/0,09391) | ZN, tableau 6 et section 4.3 |
| *N* entre 5 et 20 (Mudry p. 3) ; 5 à 5,39 sous *f*s/2 ; *N* = 64 122,9 rad/s ; 10,2 kHz ; *N* *T*c = 0,29 | ZN, section 7.2 ; script ZN (N_max = π *f*s *T*d = 5,389) ; recalcul Python (0,2915) |
| *K*p/2 et *K*p/3 : marges 32,0°, 24,5°, 22,1° ; réglage brut gardé | ZN, section 8 et tableau 13 |
| Marges : 24,9° à 39,5° (4 à 6 Ω, 160 à 240 V) ; 3,1° à 12,3° à 25 Ω ; −3,1° à 98 Ω sous 160 V | ZN, tableaux 16 et 17 |
| MATLAB R2024a, Simscape Electrical (Specialized Power Systems), powergui discret | DIM, section 10 |
| Contenu de `Buck_Commun.slx` : source de tension commandée, charge électronique, profils From Workspace à *T*c, quantification au pas q, retards d'un pas | `ELM_PID/verifier_modele_commun.py`, en-tête ; `banc_commun.py`, en-tête |
| *d* maintenu pendant 120 pas ; comparaison à la phase de la porteuse (g = 1 si phase < *d* × 1 200) | `banc_commun.py`, en-tête et `simuler_pas_a_pas` |
| Bruit nul et *q* = 10⁻⁹ V hors S7a et S7b ; S7a 48,8 mV (12 bits, 2,5 V, 1/80) ; S7b 10 mV filtré à 10 kHz | `scenarios_communs.json` ; `scenario_S*.mat` relus (bruit de S1 nul, écart type de S7b 0,0100 V) |
| Banc : trapèzes, un pas de retard, puissances de matrice, conduction discontinue ; « une dizaine de secondes » pour les onze essais | `banc_commun.py`, en-tête (« Duree : une dizaine de secondes ») |
| 98,60 V à *d* = 0,5 ; ZN nominal et F2 sous 0,01 V et 0,01 ms, mesurés sur les trois modèles `PID_Classique_Control*.slx` | DIM, tableau 11 ; ZN, section 11 et tableau 18 |
| IAE banc/Simulink : PSO 0,1 %, Fuzzy 0,2 %, ELM 0,1 %, PINN 0,3 % ; S7a +0,8, +4,8, +2,5, −6,1 % ; ELM : 0 fenêtre adaptée sous Simulink contre 2 au banc | `ETAT_DE_REPRISE.md` §2.1 à 2.4, §4.2 et §5 (ligne « ELM, Simulink ») |
| Arrondi qui change une décision du CAN | `COMPARAISON/criteres_comparaison.txt`, « Essais candidats » |
| Onze essais (descriptions, instants, durées 0,2 s et 0,42 s) | `ELM_PID/scenarios_communs.json` ; `scenario_S9.mat` relu (rampe 50 à 90 ms, consigne 150 V à 120 ms et 50 V à 150 ms, *V*in 150 V à 210 ms, consigne 100 V à 270 ms, *V*in 200 V et rampe vers 5 Ω de 330 à 370 ms) |
| Indice global : 13 rapports, 10 après 30 ms (S1, S3 à S9), 3 de démarrage (S1, S8a, S8b) | `ETAT_DE_REPRISE.md`, ligne 5 |
| Règle de sélection du 7 octobre 2026 | `COMPARAISON/criteres_comparaison.txt`, en-tête |
| E1 à E4 (points, perturbations, instants, durées, graine 7) | `PSO_PID/criteres_pso_pid.txt` §3, M1 |
| Rôle de E1 à E4 : PSO (coût), PINN (choix de C1 parmi trois corrections), ELM (contrôle du code), Fuzzy (rien) | `criteres_pso_pid.txt` §1 b et §3 ; `PINN_PID/criteres_pinn_pid.txt` §3 ; `ELM_PID/criteres_elm_pid.txt`, en-tête et §6 ; chapitre 4, sections 4.4.4, 4.6.2 et 4.6.3 |
| S10 ajouté après coup, hors indice global | `scenarios_communs.json` (« note_essais_complementaires ») ; `COMPARAISON/S10/criteres_S10.txt` |

### Citations et statut

| Citation | Statut | Fichier |
| --- | --- | --- |
| [Erickson et Maksimović, 2020] | vérifiée (appui : Buck, conduction continue, modèle moyen ; pas de page citée) | `references_chapitre5.md` §2 |
| [Åström et Hägglund, 2006] | vérifiée (livre non consulté : pas de page) | `references_chapitre5.md` §2 |
| [Ziegler et Nichols, 1942] | vérifiée | `references_chapitre5.md` §2 |
| [Mudry, 2006], p. 1, p. 3, p. 10 | vérifiée sur le document | `references_chapitre5.md` §1 |
| [Lu et al., 2021] | avec réserve | `references_chapitre5.md` |
| CEI 60063 (série E6) | non vérifiée : repère jaune seulement | la note de dimensionnement cite la norme et une page Wikipédia |

### Points à trancher et remarques

- Affirmation « les onze essais ont servi à suivre les méthodes, jamais à régler leurs paramètres » : vraie pour les valeurs numériques, pas pour la structure. Les fichiers de critères montrent que le coût du PSO-PID a été changé après un J de 1,69 calculé sur les onze essais (`criteres_pso_pid.txt`, en-tête), que les corrections M1 à M3 de l'ELM-PID et l'option B ont été décidées après des résultats sur S1 à S3 (M1 à M3) et sur S2 à S4 (option B) (`criteres_elm_pid.txt` ; `ETAT_DE_REPRISE.md` §5), et que la valeur de la zone morte du PINN-PID sur les onze essais était connue par une ablation (chapitre 4, 4.6.3). Le texte (3.6.1) le dit.
- Écart de *K*p sur la réponse commutée : le docx ZN (tableau 6) donne +8,9 %, chaque réponse prise avec son propre *K*0 (197,2 V) ; l'en-tête du script MATLAB écrit « 7,4 % », valeur qu'on retrouve en gardant *K*0 = 200 V pour la réponse commutée (1,2/(412,94 × 0,14410·10⁻³ × 200) = 0,10083, soit +7,4 %). Le texte suit le docx ; corriger l'en-tête du script ou le tableau.
- Rapport cyclique « appliqué à la période suivante » (registre des dépendances) : le banc maintient *d* pendant la période *T*c suivante (120 pas) et le compare à la porteuse ; *d* n'attend pas la période de découpage suivante. Le texte (3.5.1) décrit ce mécanisme.
- Erreur *e* : le régulateur reçoit *v*ref − *y* (mesure) ; les grandeurs de performance du chapitre 5 sont calculées sur *v*ref − *v*o (tension vraie, section 5.2.3). Les deux coïncident hors S7a et S7b.
- Validation du PID de Ziegler-Nichols sur les onze essais du modèle commun : aucun écart chiffré n'est archivé dans le dépôt ; le texte ne donne que les contrôles du docx ZN (point nominal et F2) et ceux du chapitre 5 (0,36 % sur S8a).
- Figure 3.1 : schéma produit par `REDACTION/chapitre3/figures/schema_chapitre3.py` (schemdraw et matplotlib), PNG 300 dpi et PDF.
- Figure 3.3 (numérotée dans l'ordre du texte : le relevé de Ziegler-Nichols, en 3.4.2, vient avant le modèle Simulink, en 3.5.1 ; la consigne proposait l'ordre inverse) : à exporter de `ELM_PID/Buck_Commun.slx` (File > Export Model To > Image), sans fond gris (guide de forme §4). C'est l'ancienne figure 5.1.
- Figure 3.2 : produite par `Figure_Releve_Ziegler_Nichols.m` dans `figures_zn/`. Le script place un titre dans le tracé (ligne `title({'Releve de Ziegler-Nichols ...'})`) ; le guide de forme veut le titre dans la légende seulement. Commenter cette ligne avant l'export. Les étiquettes du script sont sans accents et l'axe s'appelle « V_{out} » : à harmoniser avec *v*o si possible.
- Équation (3.4) : c'est l'ancienne équation (5.1), désormais la définition du bloc PID commun ; les chapitres 4 et 5 y renvoient.
- [URL DU DÉPÔT À INSÉRER] adresse du dépôt GitHub.
- Milliers : espaces fines insécables dans Word (guide §8).
