# Proposition de TFE : passer des résultats annoncés aux hypothèses à vérifier

Source : proposition de TFE (16 pages), texte extrait du PDF. Les citations
reprennent l'orthographe du document ; les ligatures cassées par l'extraction
(« ti » rendu par « A ») ont été rétablies.

Principe suivi pour chaque réécriture : la phrase dit ce qu'on attend, nomme
la grandeur qui sera mesurée parmi celles que le document annonce lui-même
(IAE, ISE, ITAE, dépassement, temps de montée, temps de rétablissement,
robustesse aux variations de R et de Vin, sensibilité au bruit de mesure), et
prévoit le cas où la mesure contredit l'attente.

Deux remarques valent pour toutes les phrases :

- « significatif » n'a pas de sens en simulation déterministe tant qu'aucun
  seuil n'est fixé. Il faut écrire le seuil (écart relatif minimal sur un
  indice) avant de lancer les essais, sinon le mot doit disparaître.
- « meilleur compromis » n'est vérifiable que si la règle d'agrégation des
  critères (pondération, classement par critère, dominance) est écrite avant
  les calculs. Sans cette règle, n'importe quel classement peut être présenté
  comme un compromis.

## 1. Phrases qui donnent des résultats chiffrables comme déjà obtenus

### 1.1 Page 13, résumé de l'article 1

Phrase d'origine :

> « Les résultats montrent une amélioration significative des performances
> dynamiques : réduction du dépassement, meilleure réponse transitoire, et
> adaptation efficace face aux variations du système. »

Réécriture :

> On fait l'hypothèse que l'ELM-PID réduirait le dépassement et le temps de
> rétablissement par rapport au PID à gains fixes, et que ses indices IAE, ISE
> et ITAE se dégraderaient moins que ceux du PID fixe lorsque la résistance de
> charge R et la tension d'entrée Vin varient. Un écart inférieur au seuil fixé
> avant les simulations sera considéré comme une absence d'amélioration. Si le
> PID fixe fait aussi bien ou mieux sur ces critères, le résultat sera rapporté
> tel quel et discuté.

### 1.2 Page 15, résumé de l'article 2 (première phrase)

Phrase d'origine :

> « Les résultats montrent que l'ELM-PID offre le meilleur compromis entre
> précision, rapidité et adaptabilité, tandis que le Fuzzy-PID offre une bonne
> robustesse avec une implémentation intuitive. »

Réécriture :

> On fait l'hypothèse que l'ELM-PID obtiendrait le meilleur compromis entre la
> précision (IAE, ISE), la rapidité (temps de montée, temps de rétablissement)
> et l'adaptabilité, mesurée par la dégradation de ces indices sous variations
> de R et de Vin et sous bruit de mesure. La règle qui définit ce compromis est
> fixée avant les essais. On s'attend aussi à ce que le Fuzzy-PID reste peu
> sensible aux perturbations. Ces deux attentes peuvent être démenties : une
> autre méthode peut l'emporter sur la plupart des critères, ou aucune ne
> dominer sur l'ensemble.

Note : « implémentation intuitive » n'est pas une grandeur mesurée. Elle relève
de l'évaluation qualitative annoncée page 16 (« implémentabilité ») et doit y
rester, présentée comme une appréciation.

### 1.3 Page 15, résumé de l'article 2 (deuxième phrase)

Phrase d'origine :

> « Le PSO-PID, bien que performant, souffre d'une complexité de mise en
> œuvre. »

Réécriture :

> Le PSO-PID pourrait atteindre des indices proches de ceux des autres
> méthodes, au prix d'un réglage plus coûteux. Ce coût sera mesuré par le
> nombre de simulations et le temps de calcul nécessaires au réglage. Si ce
> coût reste modeste, ou si le PSO-PID domine sur les indices, la conclusion le
> dira.

Note : l'optimisation par essaim se fait hors ligne. Une fois réglé, le PSO-PID
est un PID à gains fixes, donc le plus simple à embarquer avec le PID classique.
La « complexité » ne concerne que la phase de réglage, et la phrase doit le
préciser.

## 2. Phrases qui supposent le résultat acquis dans un objectif ou un titre

### 2.1 Page 1, contexte et motivation

Phrase d'origine :

> « Le recours à des méthodes intelligentes, en particulier le Extreme Learning
> Machine (ELM), permet une mise à jour rapide et efficace des paramètres PID
> pour maintenir la stabilité du système en temps réel. »

Réécriture :

> On fait l'hypothèse qu'un réseau ELM, grâce à son apprentissage en une seule
> résolution par moindres carrés, pourrait mettre à jour les gains du PID à
> chaque période d'échantillonnage sans compromettre la stabilité de la boucle.
> Le travail vérifiera cette hypothèse en simulation, en mesurant le temps de
> rétablissement et l'IAE après un échelon de R et de Vin, comparés à ceux du
> PID à gains fixes. Il se peut que l'adaptation n'apporte aucun gain, voire
> qu'elle dégrade la réponse.

Note : le TFE ne prévoit pas de prototype (page 8). Le « temps réel » ne peut
donc pas être démontré ; on peut au mieux mesurer le temps de calcul par pas
de simulation et le comparer à la période d'échantillonnage.

### 2.2 Page 1, objectif 4

Phrase d'origine :

> « Reproduire les résultats du paper de référence dans Simulink, définir les
> paramètres de test, valider les performances du ELM-PID. »

Réécriture :

> Tenter de reproduire dans Simulink les résultats de l'article de référence,
> définir les paramètres de test, puis mesurer les performances de l'ELM-PID
> et vérifier si elles concordent avec celles de l'article. Un écart éventuel
> sera documenté et analysé.

### 2.3 Page 2, objectif 6

Phrase d'origine :

> « Tester d'autres approches intelligentes (PSO-PID, fuzzy-PID, deep learning)
> et évaluer les gains. »

Réécriture :

> Tester d'autres approches intelligentes (PSO-PID, Fuzzy-PID, apprentissage
> profond) et évaluer, sur les mêmes critères (IAE, ISE, ITAE, dépassement,
> temps de rétablissement), si elles font mieux, aussi bien ou moins bien que
> l'ELM-PID et le PID classique.

### 2.4 Page 12, sous-chapitre 7.2 du plan du mémoire

Phrase d'origine :

> « Mise en avant des performances atteintes, des améliorations prouvées. »

Réécriture :

> Bilan chiffré des performances mesurées. Pour chaque hypothèse posée au
> départ, on indique si elle est confirmée, infirmée, ou si l'écart observé
> reste sous le seuil fixé et ne permet pas de conclure.

### 2.5 Page 12, objectif de l'article 1

Phrase d'origine :

> « Objectif : Montrer l'efficacité de l'approche ELM-PID. »

Réécriture :

> Objectif : évaluer si l'approche ELM-PID améliore la régulation du
> convertisseur Buck par rapport à un PID à gains fixes, et dans quelles
> conditions de charge, de tension d'entrée et de bruit.

### 2.6 Page 13, problématique de l'article 1

Phrase d'origine :

> « L'Extreme Learning Machine (ELM), en tant que réseau de neurones à
> apprentissage rapide, offre une solution prometteuse pour adapter
> dynamiquement les gains du PID en fonction du contexte opérationnel du
> système. »

Réécriture :

> L'Extreme Learning Machine (ELM), réseau de neurones à apprentissage rapide,
> pourrait servir à adapter en ligne les gains du PID au point de
> fonctionnement du système. L'article met cette possibilité à l'épreuve ; il
> n'en présuppose pas le succès.

### 2.7 Page 13, objectif général de l'article 1

Phrase d'origine :

> « Présenter la conception, l'implémentation, et la validation d'un
> régulateur adaptatif ELM-PID pour un convertisseur Buck, en comparaison avec
> un PID classique. »

Réécriture :

> Présenter la conception et l'implémentation d'un régulateur adaptatif
> ELM-PID pour un convertisseur Buck, puis le comparer à un PID classique afin
> de vérifier s'il apporte un gain mesurable sur les critères IAE, ISE, ITAE,
> dépassement et temps de rétablissement.

### 2.8 Pages 14 et 16, intitulé « Validation attendue »

Intitulé d'origine (identique pour les deux articles) :

> « Validation attendue : »

Réécriture :

> Critères de vérification :

Les éléments listés sous cet intitulé (IAE, ITAE, ISE, robustesse aux
variations de R et Vin, sensibilité au bruit de mesure) restent valables.
C'est le mot « validation » qui annonce l'issue.

## 3. Prémisses présentées comme acquises

Ces phrases ne parlent pas des résultats du TFE, mais le TFE les met à
l'épreuve. Mieux vaut ne pas les poser comme des certitudes.

### 3.1 Page 1, contexte et motivation

Phrase d'origine :

> « Le PID classique est performant mais rigide. Son adaptation dynamique à des
> changements de charges ou à des perturbations exogènes est limitée. »

Réécriture :

> Un PID à gains fixes est réglé pour un point de fonctionnement. On peut
> s'attendre à ce que ses performances se dégradent lorsque la charge ou la
> tension d'entrée s'éloignent de ce point ; l'ampleur de cette dégradation
> sera mesurée, et il n'est pas exclu qu'elle reste faible sur la plage de
> variation étudiée (±20 % sur R).

### 3.2 Page 13, problématique de l'article 1

Phrase d'origine :

> « Les convertisseurs DC-DC présentent un comportement fortement non
> linéaire. »

Réécriture :

> Les convertisseurs DC-DC présentent des non-linéarités (commutation,
> saturation du rapport cyclique, passage en conduction discontinue). Leur
> poids dans le cas étudié reste à établir : en conduction continue, le modèle
> moyen idéal du Buck est linéaire vis-à-vis du rapport cyclique.

Note : ce point compte pour l'argumentation. Si le modèle étudié est
pratiquement linéaire en CCM, l'intérêt d'un régulateur adaptatif doit
s'appuyer sur les variations de R et de Vin plutôt que sur la non-linéarité.
