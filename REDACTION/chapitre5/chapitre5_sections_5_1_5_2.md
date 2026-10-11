# Chapitre 5 : Simulation et analyse des performances

## 5.1. Introduction

Les chapitres précédents ont posé le modèle du convertisseur Buck, le régulateur PID de Ziegler-Nichols qui sert de point de départ, puis la conception de l'ELM-PID. Il reste à mesurer ce que l'adaptation des gains change à la régulation, et à situer ce changement par rapport à d'autres façons de régler un PID.

Dans ce chapitre, nous comparons en simulation l'ELM-PID d'abord au PID de Ziegler-Nichols dont il part, puis à trois méthodes avancées : le PSO-PID, le Fuzzy-PID et le PINN-PID. Les cinq régulateurs sont soumis aux mêmes cinq scénarios et jugés sur les mêmes grandeurs, fixées avant le calcul. Toute la comparaison se fait en simulation ; aucun essai sur montage réel n'a été réalisé.

La section 5.2 décrit les conditions de simulation, les scénarios et les critères d'évaluation. La section 5.3 confronte l'ELM-PID au PID de Ziegler-Nichols, et la section 5.4 le confronte aux trois méthodes avancées. La section 5.5 fait le bilan multicritère et la discussion des résultats, et la section 5.6 conclut le chapitre.

## 5.2. Conditions de simulation et critères d'évaluation

### 5.2.1. Convertisseur et base commune

Les cinq méthodes sont simulées sur le même convertisseur, dimensionné à la section 3.2. Le tableau 5.1 en rappelle les paramètres.

Tableau 5.1 : Paramètres du convertisseur et de la simulation.

| **Grandeur** | **Symbole** | **Valeur** |
| --- | --- | --- |
| Inductance | *L* | 10 mH |
| Capacité | *C* | 47 µF |
| Charge nominale | *R* | 5 Ω |
| Tension d'entrée nominale | *V*in | 200 V |
| Consigne de tension de sortie | *v*ref | 100 V |
| Fréquence de découpage | *f*s | 22 kHz |
| Période du régulateur | *T*c | 1/220 000 s (4,545 µs) |
| Bornes du rapport cyclique | *d* | 0,01 à 0,99 |
| Pertes de l'interrupteur | *R*on, *V*f | 0,1 Ω (MOSFET), 0,8 V (diode) |
| Pas de calcul du circuit | *h* | 1/(22 000 × 1 200) s (37,88 ns) |
| Durée d'un essai | | 0,2 s |

Le régulateur est échantillonné dix fois par période de découpage ; le rapport cyclique calculé à l'instant *k*·*T*c est maintenu pendant la période *T*c suivante (section 3.5.1). Le circuit est simulé commuté, et non par son modèle moyen.

Les cinq méthodes utilisent le bloc PID discret commun défini par l'équation (3.4) : forme parallèle, terme dérivé filtré (*N* = 64 122,9 rad/s), sortie bornée à [0,01 ; 0,99] et anti-emballement par intégration conditionnelle (section 3.4.1).

Les gains initiaux sont ceux de Ziegler-Nichols : *P* = 0,093910, *I* = 301,089 et *D* = 7,3227·10⁻⁶. Ils ont été calculés à la section 3.4.2 par la méthode de la réponse indicielle [Ziegler et Nichols, 1942], dans la présentation qu'en donne [Mudry, 2006]. Ce réglage sert ici de référence commune et de point de départ, pas de réglage optimal. Les règles de Ziegler-Nichols ne visent que des processus non oscillants [Mudry, 2006, p. 1]. Au point nominal, le convertisseur en fait partie (amortissement de 1,46 à 5 Ω), mais plus à charge légère : l'amortissement tombe à 0,29 à 25 Ω (section 3.3). La même note signale en outre que ces gains sont en général trop élevés et donnent un dépassement supérieur à 20 % [Mudry, 2006, p. 10].

Seule la manière de fixer les gains *P*, *I* et *D* du bloc (3.4) distingue les cinq méthodes. Le PID de Ziegler-Nichols garde ses gains fixes. Le PSO-PID garde aussi des gains fixes, réglés hors ligne par essaim particulaire [Gaing, 2004] sur des essais de réglage distincts des essais de développement. Le Fuzzy-PID modifie ses gains en ligne par l'ordonnancement flou de [Zhao et al., 1993]. L'ELM-PID les adapte à partir d'un réseau ELM mis à jour en ligne [Lu et al., 2021 ; Liang et al., 2006] (chapitre 4). Le PINN-PID les adapte en minimisant le coût de [Ito et Wasa, 2025]. Le modèle du convertisseur, les bornes, l'intégration conditionnelle et les conditions de simulation sont identiques pour tous.

Les résultats chiffrés de ce chapitre viennent du banc de simulation Python, validé contre le modèle Simulink commun (figure 3.3) sur les onze essais de développement (section 3.5.3). Sur les cinq scénarios de ce chapitre, le script qui trace les figures compare en outre les IAE des modèles Simulink à celles du banc, avec une tolérance de 1 % (3 % sur S10 pour l'ELM-PID et le PINN-PID). L'écart le plus grand est de 0,10 % pour les quatre méthodes (ELM-PID sur S2) et de 0,36 % pour Ziegler-Nichols (S8a). Les figures sont tracées à partir des simulations Simulink.

### 5.2.2. Scénarios retenus

Le corps du chapitre porte sur cinq scénarios, décrits au tableau 5.2. Les quatre premiers font partie des onze essais de développement ; S10 a été défini et ajouté après ces onze essais, avec ses critères et ses prévisions écrits avant tout calcul. Les autres essais et l'ensemble de leurs résultats sont publiés en annexe, sur le dépôt GitHub du travail [URL DU DÉPÔT À INSÉRER].

Tableau 5.2 : Scénarios de comparaison.

| **Code** | **Description** | **Événements (ms)** | **Fenêtre de classement** | **Ce qui est observé** |
| --- | --- | --- | --- | --- |
| S1 | Point nominal : *R* = 5 Ω, *V*in = 200 V, aucune perturbation | aucun | 0 à 30 ms | démarrage et régime nominal |
| S2 | Consigne 100 + 2 exp(cos(10π*t*)) V sur [50 ; 70) ms, 100 V ailleurs | 50, 70 | 30 ms à la fin | suivi d'une consigne perturbée |
| S3 | Charge de 4,333 Ω sur [50 ; 70) ms, 5 Ω ailleurs | 50, 70 | 30 ms à la fin | rejet d'une perturbation de charge brève |
| S8a | Charge de 25 Ω pendant tout l'essai ; *V*in = 160 V sur [50 ; 70) ms, 240 V sur [100 ; 120) ms, 200 V ailleurs | 50, 70, 100, 120 | 30 ms à la fin | variations de la tension d'entrée à charge légère |
| S10 | 0 à 50 ms comme S1 ; à partir de 50 ms, *V*in = 160 V et *R* = 25 Ω ; échelons de 15 ms à 20 Ω, 30 Ω et 20 Ω à 100, 130 et 160 ms | 50, 100, 115, 130, 145, 160, 175 | 100 ms à la fin | changement durable du point de fonctionnement |

S1 donne le comportement de référence, sans perturbation. S2 reprend le signal F1 de l'article de référence [Lu et al., 2021], avec un écart : l'article applique F1 au signal de commande, alors que nous l'ajoutons ici à la consigne. S2 mesure donc le suivi d'une consigne perturbée, et non le rejet d'une perturbation sur la commande. S3 reprend la perturbation de charge F2 du même article : la charge passe de 5 à 4,333 Ω pendant 20 ms puis revient. S8a place le convertisseur à charge légère, où son amortissement est faible, et y fait varier la tension d'entrée de ±20 %.

Dans les quatre premiers scénarios, le convertisseur revient au point nominal ou y reste, et une méthode adaptative n'y a rien à retenir. S10 change le point de fonctionnement pour de bon : la tension d'entrée baisse de 20 % et la charge passe à 25 Ω. Après 50 ms de réajustement, on mesure le rejet d'échelons de charge au nouveau point, cas pour lequel l'adaptation des gains est faite.

S1, S2 et S3 correspondent aux trois cas prévus dans la proposition du travail, avant tout résultat : régime normal, perturbation sur la commande et perturbation sur la charge. S8a a été désigné par une règle de sélection écrite avant le calcul des classements par essai ; appliquée ensuite aux versions finales des méthodes, cette règle ne désignait plus aucun essai, et S8a a été conservé. S10 a été défini plus tard, avec ses critères et ses prévisions écrits avant le calcul. Les classements des onze essais sont tous publiés sur le dépôt GitHub.

### 5.2.3. Grandeurs de performance

Toutes les grandeurs sont calculées aux instants *k*·*T*c sur l'erreur *e*(*k*) = *v*ref(*k*) − *v*o(*k*), où *v*o est la tension de sortie vraie et non la mesure. La grandeur de classement est l'intégrale de la valeur absolue de l'erreur (IAE) [Åström et Hägglund, 1995], calculée sur la fenêtre de classement du tableau 5.2 :

IAE = Σ |*e*(*k*)| *T*c,  pour *k*a ≤ *k* < *k*b,        (5.1)

où *k*a et *k*b sont les instants de début et de fin de la fenêtre. Elle s'exprime en mV·s. Cette grandeur et ses fenêtres ont été fixées avant le calcul. Dans les tableaux, le rapport IAE/IAE de Ziegler-Nichols est donné à côté pour faciliter la lecture ; il n'est jamais moyenné.

D'autres grandeurs sont publiées à côté, sans changer le classement. Le dépassement est l'écart maximal de la tension au-dessus de 100 V pendant le démarrage, en pourcentage de la consigne. Le temps d'établissement est le dernier instant du démarrage où |*e*| dépasse 1 V, soit une bande de 1 % de la consigne, plus étroite que les bandes de 2 % ou 5 % usuelles [Ogata, 2010]. Après chaque événement, nous relevons l'écart maximal |*e*| dans la fenêtre de l'événement et le temps de retour dans la bande de ±1 V. Une tension qui sort encore de cette bande dans les 10 dernières millisecondes de la fenêtre est déclarée « non revenue ».

L'erreur en régime permanent est la valeur absolue de la moyenne de *e* sur les 5 ms qui précèdent chaque événement et sur les 10 dernières millisecondes de l'essai. Elle mesure un biais statique ; l'ondulation de la tension est donnée à part. L'ITAE [Graham et Lathrop, 1953] est publiée à titre descriptif :

ITAE = Σ *τ*(*k*) |*e*(*k*)| *T*c,  pour *k*a ≤ *k* < *k*b,        (5.2)

où *τ*(*k*) = (*k* − *k*a) *T*c est le temps compté depuis le début de la fenêtre de classement. Enfin, le temps de calcul d'un appel au régulateur, mesuré sur le banc Python, ne donne qu'un ordre de grandeur relatif entre méthodes, pas un temps d'exécution sur une cible embarquée.

Deux méthodes ne sont classées l'une devant l'autre sur un scénario que si leur ordre reste le même dans cinq versions du circuit : le circuit nominal, puis *L* à ±0,1 % et *C* à ±0,1 %, les régulateurs restant inchangés. Sinon, elles sont déclarées « non séparées ». Cette règle tient au fonctionnement des méthodes adaptatives : un très petit changement du circuit peut avancer ou retarder un pas d'adaptation, et un écart d'IAE de quelques pour cent entre deux méthodes peut alors s'inverser. La règle mesure si un écart est structurel. Elle ne constitue pas une étude de robustesse aux tolérances réelles des composants, laissée au chapitre 6.

Pendant la mise au point des méthodes, nous avons suivi un indice global, moyenne de treize rapports d'IAE à Ziegler-Nichols calculés sur les onze essais. Il ne sert pas à juger dans ce chapitre : une moyenne arithmétique de rapports dépend de la référence choisie au dénominateur et donne le même poids à tous les essais [RÉF. À VÉRIFIER : Fleming et Wallace, 1986]. Sa définition et ses valeurs sont publiées sur le dépôt GitHub.

---

## Notes pour la relecture (à retirer)

### Chiffres et leur source

| Chiffre | Source |
| --- | --- |
| *L* = 10 mH, *C* = 47 µF, *f*s = 22 kHz, *T*c = 1/220 000 s, *v*ref = 100 V, *d* dans [0,01 ; 0,99], *R*on = 0,1 Ω, *V*f = 0,8 V, *h* = 1/(22 000 × 1 200) s = 37,88 ns | `ELM_PID/banc_commun.py`, étape 0 (constantes) et en-tête |
| *R* = 5 Ω, *V*in = 200 V, durée 0,2 s | `ELM_PID/scenarios_communs.json` (`R0`, `Vin_nominale`, `duree`) ; `ETAT_DE_REPRISE.md`, ligne 5 |
| *T*c = période du régulateur, dix échantillons par période de découpage ; *v*ref = consigne de sortie (« consigne = 100 + dvref ») | `banc_commun.py`, en-tête ; `Determination_gains_PID_Ziegler_Nichols.docx`, tableau 1 et section 6 |
| Bloc PID commun : renvoi à l'équation (3.4) et à la section 3.4.1 (forme parallèle, Euler explicite, intégration conditionnelle, « clamping » dans le code), *N* = 64 122,9 rad/s | `banc_commun.py` (classe `PIDClassique`, `PID_N`) ; docx ZN, sections 7.2, 7.3 et tableau 12 ; chapitre 3, section 3.4 |
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

- Déplacements du 11 octobre 2026 vers le chapitre 3 : l'ancienne figure 5.1 (modèle Simulink commun) devient la figure 3.3 ; l'ancienne équation (5.1) du bloc PID et sa description deviennent l'équation (3.4) et la section 3.4.1 ; la validation banc/Simulink sur les onze essais passe en 3.5.3 (5.2.1 ne garde que le contrôle des cinq scénarios, 0,10 % et 0,36 %). Figures renumérotées 5.2 → 5.1 … 5.16 → 5.15 ; équations IAE et ITAE renumérotées (5.1) et (5.2).
- [URL DU DÉPÔT À INSÉRER] adresse du dépôt GitHub (annexe).
- [RÉF. À VÉRIFIER : Fleming et Wallace, 1986].
- Renvois au chapitre 3 précisés le 11 octobre 2026 : dimensionnement en 3.2, amortissement en 3.3, bloc PID (3.4) en 3.4.1, gains de Ziegler-Nichols en 3.4.2, échantillonnage et MLI en 3.5.1, validation du banc en 3.5.3. ELM-PID au chapitre 4 ; mises en œuvre du PSO-PID, du Fuzzy-PID et du PINN-PID en 4.6.
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
- Vocabulaire des essais (décision de l'auteur, 10 octobre 2026) : « essais de développement » pour les onze essais S1 à S9, « essais de réglage » pour E1 à E4. Remplacements : 5.2.1, « distincts des essais de jugement » devient « distincts des essais de développement » ; 5.2.2, « onze essais du banc commun » devient « onze essais de développement » ; 5.4.1, « distincts des essais de jugement » devient « distincts des essais de développement ». Les deux catégories sont définies au chapitre 3, section 3.6.
