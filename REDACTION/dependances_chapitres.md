# Dépendances des chapitres 5 et 6 envers les chapitres 1 à 4

**Décision de l'auteur (10 octobre 2026), vocabulaire des essais, valable dans tous les chapitres :**

- les onze essais S1 à S9 de la base commune (S7a, S7b, S8a et S8b compris) s'appellent « essais de développement » ; les termes « essais de jugement », « onze essais de jugement » et « essais du banc commun » ne sont plus employés ;
- les quatre essais E1 à E4 qui ont servi à régler les méthodes s'appellent « essais de réglage » ; « essais de mise au point » n'est plus employé ;
- le chapitre 3 doit définir ces deux catégories (contenu, rôle, et règle : aucun réglage sur les essais de développement).

Document de travail (non commité). Sources lues : `chapitre5/chapitre5_sections_5_1_5_2.md`, `chapitre5_section_5_3.md`, `chapitre5_section_5_4.md`, `chapitre5_sections_5_5_5_6.md`, `chapitre6/chapitre6_perspectives.md` (notes de relecture ignorées). Pour chaque élément : ce que les chapitres 5 et 6 supposent déjà posé, où ils l'utilisent, et ce que le chapitre amont doit fournir.

Renvois explicites relevés : « chapitre 3 » (5.2.1, trois fois : dimensionnement, calcul des gains ZN, validation du banc sur les onze essais) ; « chapitre 4 » (5.2.1 : ELM-PID) ; « les chapitres précédents » (5.1) ; « la proposition du travail » (5.2.2, 5.5.2, 6.4). Aucun renvoi à une section précise des chapitres 1 à 4.

## Chapitre 1 : introduction (question, hypothèses, règles de méthode)

| Élément supposé | Utilisé dans | Ce que le ch. 1 doit fournir |
| --- | --- | --- |
| « Proposition du travail » et ses trois cas prévus (régime normal, perturbation sur la commande, perturbation sur la charge) | 5.2.2, 5.5.2 | Rappel de la proposition et des trois cas, origine de S1, S2, S3 |
| Hypothèses H1 à H4, avec leur formulation du 8 octobre 2026 citée entre guillemets | 5.5.2 (tableau 5.9) | Énoncé exact, mot pour mot identique ; préciser que « PID à gains fixes » de H1 désigne le PID de ZN |
| Réécriture des hypothèses le 8 octobre 2026, avant le calcul du ch. 5, alors que J était déjà connu | 5.5.2 | Chronologie honnête : date, ce qui était connu à ce moment |
| Règles de méthode : critères et prévisions écrits et commités avant le calcul ; aucun réglage sur les onze essais de développement ; résultats publiés quels qu'ils soient | 5.1, 5.2.2, 5.2.3, 5.5.3, 6.1, 6.2, 6.3 | Exposé des règles et de leur raison |
| Règle « aucun réglage sur les essais de développement » et renvoi aux deux catégories d'essais (définies au chapitre 3) | 5.2.1, 5.4.1, 6.1 | Annonce de la règle ; la définition des catégories revient au chapitre 3 |
| Périmètre : simulation seule, aucun montage réel ; prototype physique exclu dès la proposition | 5.1, 5.5.3, 6.4 | Énoncé du périmètre et de sa raison |
| Choix des « méthodes avancées » (PSO-PID, Fuzzy-PID, PINN-PID) comparées à l'ELM-PID et à ZN | 5.1, 5.4 | Justification du choix des comparateurs |
| Annexe sur le dépôt GitHub (autres essais, classements, définition de J) | 5.2.2, 5.2.3 | Annonce de l'annexe et de son contenu |

## Chapitre 2 : état de l'art

| Élément supposé | Utilisé dans | Ce que le ch. 2 doit fournir |
| --- | --- | --- |
| PID parallèle, terme dérivé filtré (coefficient *N*), anti-emballement par blocage de l'intégrateur (clamping) [Åström et Hägglund, 2006] | 5.2.1 (5.1), 6.3.1 | Présentation générale ; harmoniser le nom (ch. 5 : « clamping / blocage » ; ch. 6 : « intégration conditionnelle ») |
| Méthode de Ziegler-Nichols par réponse indicielle [Ziegler et Nichols, 1942 ; Mudry, 2006] ; validité limitée aux processus non oscillants ; gains trop élevés, dépassement > 20 % | 5.2.1 | Règles, domaine de validité, pages citées de Mudry (p. 1, p. 10) vérifiées |
| IAE [Åström et Hägglund, 1995], ITAE [Graham et Lathrop, 1953], bandes d'établissement 2 % / 5 % [Ogata, 2010] | 5.2.3 | Définitions usuelles des indices (le ch. 5 se contente alors de les appliquer) |
| Limite d'une moyenne de rapports [RÉF. À VÉRIFIER : Fleming et Wallace, 1986] | 5.2.3, 5.5.1 | Référence à vérifier avant tout usage |
| PSO appliqué au réglage d'un PID [Gaing, 2004] | 5.2.1, 5.4.1, 6.3.3 | Principe de l'essaim particulaire, fonction coût de Gaing |
| Ordonnancement flou des gains [Zhao et al., 1993] | 5.2.1, 5.5.1 | Principe : règles, plages de gains, sorties |
| ELM (réseau à couche cachée aléatoire, sortie par moindres carrés) et OS-ELM, mise à jour séquentielle en ligne [Liang et al., 2006] | 5.2.1, 5.5.3, 6.3.4 | Principe de l'ELM et de l'OS-ELM, notion d'identificateur |
| Article de référence [Lu et al., 2021] : ELM-PID, signaux F1 (sur la commande) et F2 (charge 5 → 4,333 Ω), boucle par fenêtres, gradient normalisé, loi incrémentale | 5.2.2, 5.3.1, 5.5.3 (5.4) | Résumé de l'article, notamment F1 et F2, la boucle d'adaptation et sa forme d'origine |
| PINN et coût de [Ito et Wasa, 2025] | 5.2.1 | Principe du PINN-PID et de son coût |

## Chapitre 3 : modélisation et base commune

| Élément supposé | Utilisé dans | Ce que le ch. 3 doit fournir |
| --- | --- | --- |
| Dimensionnement du convertisseur : *L*, *C*, *R*, *V*in, *v*ref, *f*s, *R*on, *V*f | 5.2.1 (tableau 5.1, « dimensionné au chapitre 3 »), 6.2.1 | Choix et justification des valeurs |
| Symboles *v*o (tension vraie), *d* (rapport cyclique, bornes 0,01 à 0,99), *e* = *v*ref − *v*o, *k*, *T*c | 5.2.1, 5.2.3, 5.5.3, 6.3.4 | Notations fixées une fois pour toutes |
| Modèle moyen, fonction de transfert, facteur d'amortissement : 1,46 à 5 Ω, 0,29 à 25 Ω | 5.2.1, 5.3.3 | Calcul de l'amortissement et dépendance à *R* |
| Conduction continue / discontinue | 6.2.2, tableau 6.1 | Frontière de conduction et domaine couvert par les essais |
| Simulation commutée (pas *h* = 37,88 ns), régulateur échantillonné 10 fois par période (*T*c = 4,545 µs), rapport cyclique appliqué à la période suivante, MLI | 5.2.1, 6.4 | Schéma temporel commande / MLI |
| Chaîne de mesure : différence entre *v*o vraie et mesure, quantification CAN, bruit (essai S7a) | 5.2.1, 5.2.3 | Modèle de mesure |
| Bloc PID discret commun, équation (5.1), discrétisation d'Euler explicite, *N* = 64 122,9 rad/s, saturation, clamping | 5.2.1 | Dérivation et justification de *N* (le ch. 5 ne fait que rappeler) |
| Gains ZN *P* = 0,093910, *I* = 301,089, *D* = 7,3227·10⁻⁶, obtenus par réponse indicielle du modèle moyen | 5.2.1, 5.5.1 (tableau 5.8 : « règle appliquée au modèle moyen ») | Calcul complet (paramètres de la réponse indicielle, formules de Mudry) |
| « Base commune » (v2.1) : ce qui est identique pour toutes les méthodes | 5.2.1 | Définition et version de la base |
| Modèle Simulink `Buck_Commun` (figure 5.1) et banc Python ; validation croisée sur les onze essais (écart ≤ 0,3 % hors S7a) | 5.2.1 (« chapitre 3 »), 5.4.2, 6.4 | Description des deux outils et de la validation |
| Les onze essais de développement (dont S1, S2, S3, S7a, S8a) | 5.2.1, 5.2.2 | Liste et description des onze essais |
| Les quatre essais de réglage E1 à E4 (E1, charge de 7 à 4,5 Ω ; E2, *V*in de 210 V à 175 puis 235 V sous 15 Ω ; E3, échelon de consigne de 10 V à 60 Ω ; E4, bruit de mesure et quantification à 9 Ω), distincts des onze essais de développement | 4.4.4, 4.6, 5.2.1, 5.4.1 | Définition des deux catégories d'essais et de leur rôle (décision du 10 octobre 2026) |
| Règle de sélection écrite avant le calcul, qui a désigné S8a | 5.2.2 | Énoncé de la règle (ou renvoi au ch. 1) |
| Coût J : moyenne de treize rapports d'IAE à ZN sur les onze essais | 5.2.3, 5.5.2 | Mention et usage pendant la mise au point (définition détaillée sur GitHub) |

## Chapitre 4 : conception de l'ELM-PID et mise en œuvre des méthodes de comparaison

| Élément supposé | Utilisé dans | Ce que le ch. 4 doit fournir |
| --- | --- | --- |
| Option B : l'ELM ajuste les gains du bloc PID commun ; écart avec la loi incrémentale de Lu | implicite en 5.2.1 (« seule la manière de fixer les gains distingue »), 5.5.3 (« reprise de Lu et modifiée ») | Justification du choix, version de Lu gardée en référence |
| Réseau ELM : entrées (moyennes passées de *v*o et de *d*, selon 6.3.4), sortie, jacobien ∂*v*o/∂*d* | 5.5.3, 6.3.4 | Architecture, entrées exactes, calcul du jacobien |
| Apprentissage hors ligne sur quatre enregistrements en boucle ouverte (15 s), paramètre de régularisation *C* = 0,1 | 5.4.2, 5.5.1 (tableau 5.8), 5.6 | Protocole d'apprentissage et choix de *C* (non cité au ch. 5) |
| Mise à jour en ligne OS-ELM | 5.5.3, 6.3.4 | Mise en œuvre |
| Boucle d'adaptation par fenêtres de 0,5 ms ; erreur moyenne de fenêtre *ē* | 5.3.1, 5.3.2, 5.5.3, 6.3.2 | Définition |
| Porte : blocage si la commande est saturée dans la fenêtre courante ou l'une des deux précédentes | 5.3.1, 5.3.2, 5.5.3 (« porte »), 6.3.1 (« la porte ») | Définition et nom (le mot « porte » n'est pas défini au ch. 5) |
| Zone morte de 0,1 V sur *ē* (commune avec le PINN-PID) | 5.3.2, 6.3.2 | Valeur et justification |
| Gradient normalisé (5.4) : *x* gains rapportés à ZN, *s* sensibilité de la commande aux gains sur la fenêtre, *η* = 0,5, *ε* = 10⁻³ | 5.5.3 | Dérivation, calcul de *s*, choix de *η* et *ε*, raison de la normalisation par les gains ZN |
| Ensemble de gains admissibles et projection (calcul : 181 s), construit autour du départ ZN | 5.5.1, 5.5.3, 6.3.3 | Construction de l'ensemble et opérateur de projection |
| Variantes de mise au point : jacobien constant, sans OS-ELM | 5.5.3 | Définition de ces variantes (« déjà définies lors de sa mise au point ») |
| Calcul de la sensibilité vraie ∂*v*o/∂*d* sur 4 615 fenêtres | 5.5.3, 6.3.4 | Méthode de calcul (ou la renvoyer au ch. 5) |
| PSO-PID : quatre essais de réglage (E1 à E4 : charge 7 Ω ; *V*in 175 / 235 V à 15 Ω ; consigne à 60 Ω ; bruit et quantification), contrainte de marge de phase ≥ 30° sur douze points (4 à 98 Ω, 160 à 240 V), cinq graines, 0,57 s par évaluation, 35 min sur quatre cœurs ; gains 2,55 / 1,37 / 2,61 × ZN | 5.4.1, 5.4.2, 5.5.1 | Protocole de réglage complet ; préciser que le PSO travaille sur un modèle du même convertisseur |
| Fuzzy-PID : règles de Zhao, plages tirées des gains ZN, sans optimisation | 5.2.1, 5.5.1 | Mise en œuvre et choix des plages |
| PINN-PID : réseau appris sur des enregistrements Simulink, coût d'Ito et Wasa, itération temps réel (non nommée au ch. 5), boîte de gains (32 s, borne basse 0,25 × ZN sur *I*), zone morte commune, fenêtres d'adaptation | 5.2.1, 5.4.1, 5.4.2, 5.5.1 | Mise en œuvre complète |

## Incohérences et points à corriger

| Point | Où | Constat |
| --- | --- | --- |
| *D* désigne à la fois le gain dérivé et le dépassement | 5.2.1 (5.1) / 5.2.3 | Collision de notation ; renommer le dépassement (*D*% ou *M*p) |
| *J* désigne à la fois le coût global et le jacobien | 5.2.3, 5.5.2 / 5.5.3 (5.4) | Collision de notation |
| PINN : « boîte de gains » contre « ensemble de gains admissibles » | 5.5.1 / 5.4.1 | Terme à unifier (le ch. 4 doit trancher) |
| Anti-emballement : « clamping, blocage de l'intégrateur » contre « intégration conditionnelle » | 5.2.1 / 6.3.1 | Terme à unifier |
| Tableau 6.1 attribue à 5.2.2 l'absence de scénario traversant la conduction discontinue ; 5.2.2 n'en parle pas, ni aucune section du ch. 5 (de même, le scénario « envisagé » de 6.2.2 n'apparaît pas au ch. 5) | 6.2.2, tableau 6.1 | Ajouter la limite en 5.5.3 ou changer le renvoi |
| Corrélation −0,04 « en logarithme » au ch. 5, sans cette précision au ch. 6 | 5.5.3 / 6.3.4 | Préciser au ch. 6 |
| Entrées du réseau : « tensions et rapports cycliques passés » (ch. 5) contre « moyennes passées » (ch. 6) | 5.5.3 / 6.3.4 | Le ch. 4 doit fixer la formulation |
| Facteurs 2,6 et 28 « par rapport au PSO-PID » : 3,59/1,43 = 2,5 et 38,93/1,43 = 27,2 ; 2,6 et 28 correspondent à ZN (1,39 µs) | 5.5.1 | Corriger la référence ou les chiffres |
| Réduction PINN : 61,5 % (tableau 5.6) contre 61 % (6.3.3) ; avec les valeurs arrondies, 1 − 6,63/17,19 = 61,4 % | 5.4.1 / 6.3.3 | Vérifier dans le dépôt, sans gravité |
| Option B, loi incrémentale de Lu, itération temps réel, base v2.1, *C* = 0,1, codes E1 à E4 : jamais nommés au ch. 5/6 | – | Pas une incohérence, mais le ch. 4 doit les nommer pour que 5.5.3 (« reprise de Lu et modifiée ») soit compréhensible |
| [Fleming et Wallace, 1986] encore marquée « À VÉRIFIER » | 5.2.3 | Vérifier avant livraison |

## Suivi des incohérences (10 octobre 2026)

Toutes les incohérences listées ci-dessus entre les chapitres 5 et 6 ont été
corrigées le 10 octobre 2026 : dépassement sans symbole, indice global sans
la lettre J (réservée au jacobien), « boîte de gains » pour le PINN-PID,
« intégration conditionnelle » partout, définition de la porte en 5.3.1,
ligne du tableau 6.1 rattachée au chapitre 6, entrées du réseau et
corrélation des logarithmes (−0,04) décrites de la même façon, facteurs de
coût 2,5 et 27 par rapport au PSO-PID, 41 % et 61 % sur S10.
