# Chapitre 6 : Perspectives et extension

## 6.1. Introduction

Le chapitre 5 s'est terminé sur des questions laissées ouvertes (section 5.6). Nous les reprenons ici une à une : pour chacune, la limite constatée, le travail à faire et la grandeur qui permettra de le juger. La méthode ne change pas. Les critères et les prévisions seront écrits avant le calcul, et aucun réglage ne sera fait sur les onze essais de développement.

## 6.2. Valider les résultats hors des conditions de simulation

### 6.2.1. Tolérances réelles des composants

La règle de séparation (section 5.2.3) ne fait varier *L* et *C* que de ±0,1 %. Elle dit si un ordre entre deux méthodes est reproductible, pas s'il résiste aux écarts d'un circuit réel. Cette petite variation suffit pourtant à faire passer l'IAE de l'ELM-PID sur S10 de 8,63 à 7,88 mV·s, quand celle des autres méthodes bouge de moins de 2 % (section 5.3.3). Avec des tolérances de fabrication de quelques pour cent, les classements serrés entre méthodes adaptatives pourraient changer.

Nous proposons une étude de Monte-Carlo sur les cinq scénarios. On tirerait *L*, *C* et la résistance à l'état passant du MOSFET (0,1 Ω dans le modèle commun, tableau 5.1) dans les plages des fiches techniques des composants retenus, les régulateurs gardant leurs réglages nominaux. Pour chaque paire de méthodes, on relèverait la distribution des écarts d'IAE et la part des tirages où l'ordre nominal se maintient. Le nombre de tirages, les plages et le seuil à partir duquel un ordre sera dit robuste seront commités avant le premier tirage.

### 6.2.2. Dynamique non linéaire sans retour au nominal

Un scénario de dynamique non linéaire, défini à partir de la physique avant tout calcul, a été envisagé pendant le travail mais n'a pas été simulé : excursions à travers la conduction discontinue, tension d'entrée de 150 à 240 V et sauts de consigne, sans retour au point nominal. On y mesurerait les grandeurs du chapitre 5 (IAE, retour dans ±1 V, temps en butée), avec la même règle de séparation, et le résultat serait publié quel qu'il soit.

## 6.3. Améliorer la loi d'adaptation

### 6.3.1. Agir malgré la saturation

Au démarrage, l'ELM-PID ne gagne que 0,05 % sur Ziegler-Nichols (section 5.3.1), parce que la porte bloque l'adaptation tant que la commande est saturée. Ce blocage est justifié : en butée, le rapport cyclique ne dépend plus des gains et le gradient n'a pas de sens. L'intégration conditionnelle [Åström et Hägglund, 2006] protège l'intégrateur pendant la saturation, mais elle ne règle pas les gains. La piste à étudier est donc de réduire la saturation elle-même, par exemple par une consigne en rampe appliquée aux cinq méthodes pour garder la comparaison équitable. On mesurerait le temps en butée, le dépassement et l'IAE de S1, ainsi que le nombre de pas d'adaptation faits pendant la montée.

### 6.3.2. Une boucle plus rapide que les perturbations

Sur S2 et S3, les gains restent immobiles pendant les perturbations (section 5.3.2). La boucle travaille par fenêtres de 0,5 ms ; quand elle se rouvre, 1,5 ms après la fin de la fenêtre saturée, soit 1,5 à 2 ms après l'événement, l'erreur moyenne est déjà sous la zone morte de 0,1 V. Pour agir pendant la perturbation, elle devrait être plus rapide que le PID qu'elle règle. Des fenêtres plus courtes moyennent l'erreur sur moins d'échantillons et la rapprochent du bruit ; la largeur des fenêtres et la zone morte sont donc à choisir ensemble, avant le calcul. Il faudrait compter les pas d'adaptation pendant F1 et F2, puis mesurer l'IAE de S2 et S3 et le coût de calcul (section 6.4).

### 6.3.3. Partir des gains du PSO-PID

Le PSO-PID a la plus petite IAE sur les cinq scénarios (section 5.5.1). Sur S10, l'adaptation poursuivie réduit pourtant l'IAE de 61 % pour le PINN-PID et de 41 % pour l'ELM-PID (section 5.4.1). L'expérience qui découle directement du chapitre 5 est d'associer les deux : des gains de départ réglés hors ligne par essaim particulaire [Gaing, 2004], puis adaptés en ligne. L'ensemble admissible des gains de l'ELM-PID, construit autour du départ de Ziegler-Nichols, devrait être recalculé autour du nouveau départ. La version hybride serait comparée au PSO-PID seul sur les cinq scénarios, avec la règle de séparation. Si l'écart n'est pas séparé, la conclusion sera que l'adaptation n'apporte rien à un PID fixe bien réglé sur ces scénarios.

### 6.3.4. Donner un rôle réel au réseau, ou s'en passer

Le réseau ELM pèse peu dans le résultat (section 5.5.3). Sur S10, un jacobien constant fait aussi bien que lui (écart non séparé), la mise à jour en ligne OS-ELM [Liang et al., 2006] n'apporte rien de mesurable, et la corrélation entre les logarithmes du jacobien du réseau et du jacobien vrai vaut −0,04. On peut chercher un identificateur dont le jacobien ∂ŷ/∂d̄ (équation (4.5)) suive vraiment le jacobien vrai. Le réseau actuel ne voit que des moyennes par fenêtre : la tension mesurée sur les deux fenêtres précédentes, le rapport cyclique sur la fenêtre courante et les deux précédentes ; une entrée de plus, le courant de l'inductance par exemple, est une piste à tester, pas un résultat acquis. Son jacobien serait comparé au jacobien vrai sur les mêmes 4 615 fenêtres de contrôle, puis l'ablation de la section 5.5.3 serait refaite. L'autre option est d'assumer une loi à jacobien constant, sans réseau à apprendre, et de la juger contre l'ELM-PID actuel sur les cinq scénarios.

## 6.4. Vers une mise en œuvre embarquée

Aucune méthode adaptative n'a été montrée compatible avec le temps réel (section 5.4.2). Sur le banc Python, un pas d'adaptation de l'ELM-PID dure 0,84 ms, plus que sa fenêtre de 0,5 ms, et celui du PINN-PID 16,6 ms. Ces durées sont celles d'un langage interprété. Il faudrait écrire les régulateurs en code compilé et en virgule fixe sur un microcontrôleur ou un processeur de signal, puis mesurer le temps d'exécution au pire cas : celui de l'appel ordinaire, à comparer à la période du régulateur (4,545 µs), et celui du pas d'adaptation, à comparer à la fenêtre. Il faudrait aussi vérifier que la virgule fixe ne change pas les IAE des cinq scénarios au-delà d'une tolérance fixée d'avance. Le prototype physique, exclu dès la proposition de ce travail, relève d'un travail ultérieur.

## 6.5. Conclusion

Chaque perspective de ce chapitre part d'une limite chiffrée du chapitre 5. L'expérience la plus directe est l'association du réglage par essaim et de l'adaptation en ligne. La validation hors simulation, par une étude de tolérances puis un essai sur cible, conditionne la portée des résultats. Le tableau 6.1 récapitule ces perspectives.

Tableau 6.1 : Limites constatées au chapitre 5 et perspectives.

| **Limite constatée (section du chapitre 5)** | **Perspective** | **Grandeur à mesurer** |
| --- | --- | --- |
| Séparation limitée à ±0,1 % de *L* et *C* ; IAE de l'ELM-PID de 7,88 à 8,63 mV·s sur S10 (5.3.3) | Étude de Monte-Carlo sur *L*, *C* et *R*on | Distribution des écarts d'IAE ; part des tirages où l'ordre se maintient |
| Aucun scénario conçu pour traverser la conduction discontinue (non traité au chapitre 5 ; section 6.2.2) | Scénario de dynamique non linéaire | IAE, retour dans ±1 V, temps en butée, séparation |
| Gain de 0,05 % au démarrage (5.3.1) | Réduire la saturation pour les cinq méthodes | Temps en butée, dépassement, IAE de S1 |
| Gains immobiles pendant F1 et F2 (5.3.2) | Boucle d'adaptation plus rapide | Pas d'adaptation pendant F1 et F2 ; IAE de S2 et S3 ; coût |
| PSO-PID meilleur partout ; adaptation −41 et −61 % sur S10 (5.4.1, 5.5.1) | Départ des gains du PSO-PID, puis adaptation | Écart d'IAE avec le PSO-PID seul, séparé ou non |
| Corrélation de −0,04 (en logarithme) avec le jacobien vrai ; OS-ELM sans effet (5.5.3) | Identificateur avec une entrée de plus, ou jacobien constant | Corrélation avec le jacobien vrai ; IAE des cinq scénarios |
| Pas d'adaptation de 0,84 ms pour une fenêtre de 0,5 ms (5.4.2) | Code compilé en virgule fixe sur cible | Temps d'exécution au pire cas ; écart d'IAE dû à la virgule fixe |

---

## Notes pour la relecture (à retirer)

### Chiffres et leur source

| Chiffre | Source vérifiée |
| --- | --- |
| ±0,1 % de *L* et *C*, cinq versions du circuit ; « pas une étude de tolérance » | `COMPARAISON/separation/criteres_separation.txt` §2 (« Portée annoncée ») ; chapitre 5, section 5.2.3 |
| IAE de l'ELM-PID sur S10 : 8,63 (nominal) et 7,88 mV·s (*L* + 0,1 %) ; autres méthodes : moins de 2 % | `COMPARAISON/ablation_S10/criteres_ablation.txt` §5 (« 7.88 a 8.63 selon la variante ») ; `ablation_sortie_console.txt`, lignes 12 et 124 (7,87725) ; `COMPARAISON/S10/scenario_S10_sortie_console.txt`, ligne 83 ; chapitre 5, section 5.3.3 |
| *R*on = 0,1 Ω ; *T*c = 1/220 000 s = 4,545 µs | `ELM_PID/banc_commun.py`, lignes 120 et 124-125 ; chapitre 5, tableau 5.1 |
| Scénario P2 : conduction discontinue, *V*in 150 à 240 V, sauts de consigne, non fait | `ETAT_DE_REPRISE.md` §3.3, P2 ; `REDACTION/plan_depart_contre_realise.md`, chapitre 6 |
| S1 : 0,05 % ; porte fermée pendant la saturation (trois fenêtres) | chapitre 5, section 5.3.1 et tableau 5.4 ; `separation_resultats.json` (0,053 à 0,055 %) ; `ELM_PID/criteres_elm_pid.txt` §4, M1 |
| Fenêtres de 0,5 ms ; réouverture 1,5 ms après la fin de la fenêtre saturée, soit 1,5 à 2 ms après l'événement (chapitre 4, section 4.4.2 et figure 4.3) ; zone morte 0,1 V ; gains immobiles pendant F1 et F2 | `ELM_PID/criteres_elm_pid.txt` §2, §8 (« Ce que l'adaptation fait pendant une perturbation ») et §9 point 3 (« il faudrait une boucle plus rapide que le régulateur qu'elle règle ») |
| PSO-PID meilleure IAE sur les cinq scénarios | chapitre 5, tableau 5.8 ; `COMPARAISON/metriques/metriques_banc.md`, résumé |
| Adaptation sur S10 : 61 % (PINN-PID, 0,6146) et 41 % (ELM-PID, 0,4089), même arrondi à l'unité que le tableau 5.6 depuis le 10 octobre (qui donnait 61,5 et 40,9 %) | `COMPARAISON/S10/resultats_S10.json`, clé `gain_adaptation` ; chapitre 5, tableau 5.6 (section 5.4.1) |
| Ensemble admissible construit autour du départ de Ziegler-Nichols (marge nominale au moins celle du départ, 24,93°) | `ELM_PID/criteres_elm_pid.txt` §2 et M2 ; `ELM_PID/ensemble_gains_elm_sortie_console.txt`, ligne 3 |
| Jacobien constant sur S10 : −9,76 %, non séparé (−9,76 à +4,01) ; OS-ELM : rien de mesurable | `criteres_ablation.txt` §5 |
| Corrélation −0,04 (−0,043 : corrélation de ln *J* du réseau et ln *J* vrai, « Correlation de ln J (modele) et ln J_vrai ») ; 4 615 fenêtres | `ELM_PID/entrainement_elm_sortie_console.txt`, étape 5 (lignes 65 à 69 : 1 212 + 625 + 40 + 2 738 = 4 615) ; `criteres_elm_pid.txt` §5 |
| Pas d'adaptation : ELM 840,38 µs (0,84 ms), PINN 16 618,37 µs (16,6 ms) | `COMPARAISON/metriques/metriques_banc.md`, « Coût de calcul », lignes 163-164 |
| Prototype exclu par la proposition | `REDACTION/plan_depart_contre_realise.md` (« ce TFE ne prévoit pas de prototypage ») ; `REDACTION/proposition_resultats_en_hypotheses.md`, note de la ligne 106 |

### Citations

- [Åström et Hägglund, 2006] : vérifiée (`REDACTION/references_chapitre5.md` §2). Utilisée seulement pour l'intégration conditionnelle, comme contexte ; pas de page citée (livre non consulté en entier).
- [Gaing, 2004] : vérifiée.
- [Liang et al., 2006] : vérifiée.
- Aucun repère [RÉF. À VÉRIFIER] : aucune référence nouvelle n'a été nécessaire. Une étude de Monte-Carlo ou une mise en œuvre en virgule fixe gagnerait à être appuyée par une référence ; à ajouter seulement après vérification.

### Corrections et précisions par rapport à la commande

- Section du 7,88 à 8,63 mV·s : le chiffre est dans les sections 5.3.3 (*L* + 0,1 %) et 5.5.3 (plage). Le texte renvoie à 5.3.3, où la comparaison avec les autres méthodes (moins de 2 %) est donnée.
- « Adapter aussi pendant la saturation » : en butée, le rapport cyclique ne dépend pas des gains et le gradient est nul (`criteres_elm_pid.txt` M1). Rouvrir la porte n'aurait pas de sens ; le texte propose plutôt de réduire la saturation (consigne en rampe), appliquée aux cinq méthodes, ce qui change S1 et doit être décidé avant le calcul.
- « Les gains ne bougent pas sur S2, S3 » : ils changent une fois à 4 ms (fin du démarrage) et, sur S3, une seconde fois à 72 ms (fin de F2). Le texte dit « immobiles pendant les perturbations », ce qui est exact.
- Point à trancher pour P2 : avec *L* = 10 mH et *f*s = 22 kHz, la limite de la conduction continue en régime établi est *R* = 2*L f*s/(1 − *D*), soit environ 880 Ω à 200 V et 1 170 Ω à 160 V (calcul de relecture, non commité). Traverser la conduction discontinue suppose donc une charge presque à vide : la définition physique de P2 est à écrire avec cette contrainte.
- 6.3.4 (demande du coordinateur) : la phrase « la charge n'est pas observable sur une fenêtre de 0,5 ms : il lui faudrait une entrée de plus » a été remplacée. L'affirmation n'était pas démontrée (`criteres_elm_pid.txt` §5 la donne comme lecture, sans preuve). Le texte s'en tient à ce qui est établi : les entrées du réseau sont des moyennes par fenêtre, ȳ(n−1), ȳ(n−2) pour la tension et d̄(n), d̄(n−1), d̄(n−2) pour le rapport cyclique (`criteres_elm_pid.txt` §2), formulation reprise mot pour mot en 5.5.3 depuis le 10 octobre. Le courant de l'inductance y est présenté comme une piste à tester.
- Tableau 6.1 : la limite « aucun scénario conçu pour traverser la conduction discontinue » était attribuée à 5.2.2, qui n'en parle pas ; elle renvoie maintenant à 6.2.2 (« non traité au chapitre 5 »).
- Vocabulaire aligné sur le chapitre 5 (10 octobre) : « intégration conditionnelle », « ensemble admissible » pour l'ELM-PID, corrélation « entre les logarithmes », réductions arrondies à 41 et 61 %.
- Les tolérances des composants ne sont pas chiffrées, faute de source (« plages des fiches techniques des composants retenus »).

### Repères

- Aucune figure. Un tableau (6.1). Aucune équation.

### Alignement sur le chapitre 4 (10 octobre 2026)

- 6.3.2 : la porte se rouvre 1,5 ms après la fin de la fenêtre saturée, soit 1,5 à 2 ms après l'événement (section 4.4.2, figure 4.3), et non « 1,5 ms après l'événement » ; « l'erreur » devient « l'erreur moyenne » (la zone morte porte sur ē).
- 6.3.4 : « ∂*v*o/∂*d* » remplacé par le jacobien ∂ŷ/∂d̄ du réseau (équation (4.5)), comparé au jacobien vrai ; « la tension de sortie » devient « la tension mesurée » (entrées ȳ(*n* − 1), ȳ(*n* − 2) du réseau, section 4.3.1).
- Tableau 6.1 : aucune mention de ∂*v*o/∂*d* ni de la tension de sortie ; rien à changer.

### Vocabulaire des essais (décision de l'auteur, 10 octobre 2026)

- 6.1 : « aucun réglage ne sera fait sur les essais de jugement » devient « aucun réglage ne sera fait sur les onze essais de développement » (S1 à S9). Les essais E1 à E4 s'appellent « essais de réglage » ; le chapitre 6 ne les cite pas.
