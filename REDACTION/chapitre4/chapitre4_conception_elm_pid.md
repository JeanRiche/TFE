# Chapitre 4 : Conception de l'ELM-PID

## 4.1. Introduction

L'ELM-PID de ce travail reprend la méthode de [Lu et al., 2021] : un réseau ELM identifie le convertisseur, et son jacobien guide l'ajustement en ligne des gains d'un PID (figure 4.1). Nous l'avons adaptée au convertisseur dimensionné au chapitre 3 et à une comparaison équitable avec quatre autres régulateurs ; chaque modification s'appuie sur une référence ou sur un calcul publié sur le dépôt du travail.

La section 4.2 justifie le remplacement du PID incrémental de l'article par le bloc PID commun aux cinq méthodes. Les sections 4.3 et 4.4 décrivent le réseau ELM et la loi d'adaptation des gains, la section 4.5 la mise en œuvre sous Simulink. La section 4.6 présente la mise en œuvre des trois méthodes de comparaison. Les gains de Ziegler-Nichols (ZN), point de départ commun, ont été calculés au chapitre 3.

[FIGURE À INSÉRER : REDACTION/chapitre4/figures/Fig4_1_boucle_ELM_PID.png]

Figure 4.1 : Structure de l'ELM-PID : boucle de régulation commune cadencée à *T*c = 1/220 000 s (bas) et boucle d'adaptation des gains, exécutée en fin de chaque fenêtre de 0,5 ms (haut).

## 4.2. Du PID incrémental de Lu au bloc PID commun

### 4.2.1. La loi incrémentale de Lu

Le régulateur de l'article est un PID incrémental, qui ajoute à chaque pas une correction à la commande précédente [Lu et al., 2021]. Transposé à notre convertisseur, avec une dérivée calculée sur l'erreur filtrée, il s'écrit :

*u*(*k*) = sat[ *u*(*k* − 1) + *K*p (*e*(*k*) − *e*(*k* − 1)) + *K*i *e*(*k*) + *K*d (*g*(*k*) − *g*(*k* − 1)) ],        (4.1)

où *u* est le rapport cyclique, borné par sat à [0,01 ; 0,99], *e* l'erreur entre la consigne et la tension mesurée, *g* la dérivée filtrée de l'erreur (même coefficient *N* = 64 122,9 rad/s que le bloc PID commun) et *K*p, *K*i, *K*d les gains de la forme incrémentale. Nous l'appelons « loi incrémentale de Lu ». Elle s'écarte déjà de l'article sur deux points : la commande est bornée dans la loi, alors que chez Lu c'est le modulateur qui borne, et les gains partent de ceux de Ziegler-Nichols au lieu de zéro.

### 4.2.2. Pourquoi l'option B

La loi (4.1) n'est pas le bloc PID parallèle (5.1) des quatre autres méthodes. Un écart de résultat pouvait donc venir de la loi autant que de l'adaptation. Un diagnostic du 8 octobre 2026 l'a mesuré : avec les mêmes gains fixes (ceux du PSO-PID), la loi incrémentale donne après 30 ms une IAE de 23,50 mV·s contre 16,54 pour le bloc parallèle sur l'essai de charge S4, 7,53 contre 5,46 sur S3 et 6,56 contre 2,04 sur S2. Elle fait mieux au démarrage.

La cause est mécanique. La forme incrémentale ne garde des actions proportionnelle et dérivée que leurs incréments ; en saturation, ces incréments sont perdus et la loi repart de la butée [Åström et Hägglund, 2006]. Sur S2, l'à-coup de dérivée dû au saut de consigne est tronqué par la saturation et jamais rendu. Les mêmes propriétés donnent un démarrage presque sans dépassement.

Le 8 octobre 2026, nous avons adopté l'option B : l'ELM n'agit plus sur une loi propre, il ajuste les gains *P*, *I*, *D* du bloc PID commun. Le réseau, la mise à jour en ligne, le gradient, la porte, les zones mortes, le critère d'admissibilité et la projection sont gardés avec les mêmes réglages. Ce choix a été fait en connaissant le diagnostic sur les onze essais de développement, dont S2 et S3 ; il porte sur la structure de la loi et non sur un réglage, mais il n'est pas aveugle à ces essais. La version à loi incrémentale reste entière sur le dépôt.

### 4.2.3. Comparaison des deux versions

Les essais de la comparaison ont été fixés avant le calcul : S4 pour juger, avec l'indice global de la section 5.2.3 séparé en une part « après 30 ms » et une part « démarrage » ; S2 et S1 pour montrer les deux mécanismes, quel que soit leur résultat. Trois prévisions étaient écrites : pour l'option B, une part après 30 ms inférieure à 0,747 (valeur de la loi incrémentale), une part de démarrage d'au moins 0,90, et une IAE sur S2 au plus égale à celle de Ziegler-Nichols. Le tableau 4.1 donne les résultats.

Tableau 4.1 : Loi incrémentale de Lu et option B (IAE en mV·s, banc Python).

| **Grandeur** | **Ziegler-Nichols** | **Loi incrémentale** | **Option B** |
| --- | --- | --- | --- |
| S4, IAE après 30 ms | 23,61 | 19,57 | 18,87 |
| S2, IAE après 30 ms | 2,84 | 5,61 | 2,41 |
| S2, écart maximal (V) | 2,01 | 5,34 | 2,01 |
| S1, IAE de 0 à 30 ms | 93,77 | 81,12 | 93,72 |
| S1, dépassement (%) | 14,0 | 2,4 | 14,0 |
| Indice global : après 30 ms / démarrage | 1 / 1 | 0,747 / 0,664 | 0,680 / 0,967 |

Les trois prévisions sont justes. Sur S4, l'option B fait 3,6 % de moins que la loi incrémentale ; sur S2, la loi incrémentale double presque l'IAE de Ziegler-Nichols, l'option B la réduit. Le prix est au démarrage : l'option B dépasse de 14 % comme Ziegler-Nichols, contre 2,4 % pour la loi incrémentale. Comme le démarrage pèse trois termes sur treize, l'indice global de l'option B (0,746) reste au-dessus de celui de la loi incrémentale (0,728). L'option B échange donc le démarrage contre le rejet des perturbations, à loi égale avec les autres méthodes.

## 4.3. Le réseau ELM

### 4.3.1. Structure

Le réseau prédit la moyenne de la tension mesurée sur une fenêtre de 0,5 ms, soit 110 périodes *T*c du régulateur. Ses cinq entrées sont celles de [Lu et al., 2021] : les moyennes ȳ(*n* − 1) et ȳ(*n* − 2) de la tension mesurée, et d̄(*n*), d̄(*n* − 1), d̄(*n* − 2) du rapport cyclique, où *n* est l'indice de la fenêtre. L'ordre 2 a été contrôlé par les quotients de Lipschitz [RÉF. À VÉRIFIER : He et Asada, 1993], selon une règle écrite avant le calcul.

C'est un réseau ELM avec liaisons directes entrée-sortie [Huang et al., 2006 ; Pao et al., 1994] : douze neurones logistiques, dont les poids et biais d'entrée sont tirés au hasard dans [−1 ; 1] puis fixés, plus une liaison directe de chaque entrée vers la sortie et un biais. La sortie s'écrit :

ŷ(*n*) = *σ*T [ Σ*j* *β*j *g*j(*n*) + Σ*i* *β*L,i *z*i(*n*) + *β*0 ] + *m*T,  avec *g*j(*n*) = 1 / (1 + exp(−Σ*i* *w*ij *z*i(*n*) − *b*j)),        (4.2)

où *z*i est la *i*-ème entrée, centrée et réduite par la moyenne et l'écart type des données d'apprentissage, *w*ij et *b*j les poids et biais tirés au hasard, *β*j, *β*L,i et *β*0 les poids de sortie des neurones, des liaisons directes et du biais, et *m*T, *σ*T la moyenne et l'écart type de la sortie d'apprentissage. Il y a dix-huit poids de sortie. La figure 4.2 représente le réseau.

[FIGURE À INSÉRER : REDACTION/chapitre4/figures/Fig4_2_reseau_ELM.png]

Figure 4.2 : Réseau ELM avec liaisons directes, modèle interne de l'ELM-PID (12 neurones logistiques, *C* = 0,1), et calcul de son jacobien *J*(*n*).

### 4.3.2. Apprentissage hors ligne

Le réseau est appris sur quatre enregistrements Simulink du convertisseur en boucle ouverte. En boucle fermée, la commande dépend de la sortie par la loi du régulateur, et une régression retrouverait le régulateur au lieu du convertisseur. Le rapport cyclique y est imposé par paliers de 0,5 à 20 ms ; la tension d'entrée varie de 150 à 240 V et la charge de 4 à 98 Ω, par rampes. Deux enregistrements de 1 s servent à l'apprentissage (4 000 fenêtres), deux de 0,5 s à la validation (2 000 fenêtres). Seuls les poids de sortie sont appris, par moindres carrés régularisés :

*β* = (*H*ᵀ*H* + *Λ*)⁻¹ *H*ᵀ *T*,  *Λ* = diag(1/*C*, …, 1/*C*, 10⁻⁸, …, 10⁻⁸),        (4.3)

où *H* a une ligne [*g*1 … *g*12, *z*1 … *z*5, 1] par fenêtre, *T* est le vecteur des sorties réduites et *C* = 0,1 le paramètre de régularisation. La pénalité 1/*C* = 10 ne porte que sur les douze poids des neurones ; les liaisons directes et le biais n'ont qu'une pénalité de 10⁻⁸.

La configuration a été choisie avant tout essai de régulation, parmi 12, 24 ou 48 neurones, *C* de 0,1 à 100 et vingt tirages aléatoires. Un tirage est éliminé si son jacobien est négatif, ou inférieur à la moitié du jacobien vrai, sur une seule fenêtre de contrôle. Ce jacobien vrai est calculé sur le banc : on repart de l'état exact du circuit au début de la fenêtre, on la refait avec d̄ ± 0,01, et on divise l'écart des tensions moyennes par 0,02. Il y a 4 615 fenêtres de contrôle, prises sur les enregistrements de validation et sur trois enregistrements à charge légère. Le 4 octobre 2026, la configuration à 12 neurones et *C* = 0,1 a été retenue (11 tirages sur 20 passent) et son tirage de graine 1 exporté. Le choix est fragile : avec les enregistrements à charge légère refaits, 8 tirages sur 20 seulement passent, et la règle « plus de la moitié » ne l'admettrait plus. Le tirage exporté passe toujours les deux critères et a été gardé. Le script d'apprentissage et de contrôle tourne en 14,8 s.

### 4.3.3. Mise à jour en ligne et jacobien

En ligne, les poids de sortie sont mis à jour par l'algorithme OS-ELM [Liang et al., 2006], des moindres carrés récursifs sans facteur d'oubli :

*Γ* ← *Γ* − *Γ* *h* *h*ᵀ *Γ* / (1 + *h*ᵀ *Γ* *h*),  *β* ← *β* + *Γ* *h* (ȳ(*n*) − ŷ(*n*)) / *σ*T,        (4.4)

où *h* est la ligne de *H* de la fenêtre *n* et *Γ* la matrice de covariance, initialisée à (*H*ᵀ*H* + *Λ*)⁻¹. La mise à jour n'a lieu que porte ouverte (section 4.4.2) et si l'erreur de prédiction |ȳ(*n*) − ŷ(*n*)| dépasse 0,1 V : cette zone morte d'estimation évite la dérive des paramètres sur des erreurs de l'ordre du bruit [Peterson et Narendra, 1982 ; Ioannou et Sun, 1996].

La loi d'adaptation utilise le jacobien du réseau, obtenu en dérivant (4.2) par rapport à d̄(*n*), troisième entrée :

*J*(*n*) = ∂ŷ(*n*)/∂d̄(*n*) = (*σ*T / *σ*3) [ Σ*j* *β*j *g*j(*n*) (1 − *g*j(*n*)) *w*3j + *β*L,3 ],        (4.5)

où *σ*3 est l'écart type de d̄ dans les données d'apprentissage et *β*L,3 la contribution de la liaison directe de d̄(*n*). *J* s'exprime en volts par unité de rapport cyclique.

## 4.4. La loi d'adaptation des gains

### 4.4.1. Fenêtres et gradient normalisé

L'adaptation suit la boucle par fenêtres de [Lu et al., 2021] (figure 4.1). À chaque période *T*c, l'adaptateur cumule l'erreur, la tension mesurée, le rapport cyclique et la sensibilité de la commande aux gains. En fin de fenêtre, il calcule les moyennes ē(*n*), ȳ(*n*), d̄(*n*), la prédiction et le jacobien, puis décide s'il change les gains.

Les gains sont exprimés en multiplicateurs de ceux de Ziegler-Nichols : *K* = *K*ZN ⊙ *x*, avec *K* = [*P*, *I*, *D*], *K*ZN = [0,093910 ; 301,089 ; 7,3227·10⁻⁶] et ⊙ le produit terme à terme. Avec *x* = (1, 1, 1), l'ELM-PID est exactement le PID de Ziegler-Nichols. La sensibilité de la commande aux gains est la dérivée exacte de la loi (5.1), prise depuis le début de la fenêtre :

∂*u*/∂*P* = *e*(*k*),  ∂*u*/∂*I* = *T*c Σ*j*<*k* *e*(*j*),  ∂*u*/∂*D* = *N* (*e*(*k*) − *ψ*(*k*)),  avec *ψ*(*k* + 1) = *ψ*(*k*) + *T*c *N* (*e*(*k*) − *ψ*(*k*)),        (4.6)

où la somme part du début de la fenêtre et *ψ* est un filtre remis à zéro à chaque fenêtre ; *s*(*n*) est le vecteur des moyennes de ces trois dérivées sur la fenêtre *n*. La saturation n'est pas dérivée, car une fenêtre saturée ferme la porte. En fin de fenêtre, le pas des multiplicateurs suit un gradient normalisé sur le critère ē(*n*)²/2 :

Δ*x*(*n*) = *η* ē(*n*) *φ*(*n*) / (*ε* + *φ*(*n*)·*φ*(*n*)) + *α* (*x*(*n*) − *x*(*n* − 1)),  avec *φ*(*n*) = *J*(*n*) (*s*(*n*) ⊙ *K*ZN),        (4.7)

où *φ* est la sensibilité de la tension moyenne aux multiplicateurs, *η* = 0,5 le pas, *ε* = 10⁻³ une constante de régularisation, *α* = 0,001 le coefficient d'inertie de Lu, et *x*(*n*) − *x*(*n* − 1) le dernier changement des multiplicateurs. La division par |*φ*|² rend la longueur du pas indépendante de l'échelle des sensibilités, comme dans un filtre LMS normalisé. Le produit par *K*ZN ramène les trois gains, de 10⁻⁶ à 10², à des multiplicateurs comparables. Les nouveaux gains servent dès la période suivante.

### 4.4.2. Porte et zone morte

Deux conditions sont testées avant le calcul de (4.7). La première est la porte. Une fenêtre est suspecte si le rapport cyclique touche une borne, 0,01 ou 0,99, à un seul de ses pas ; la porte n'est ouverte que si ni la fenêtre courante ni les deux précédentes ne sont suspectes. En saturation, le rapport cyclique ne dépend plus des gains, alors que (4.6) est calculée comme s'il en dépendait, et le gradient aurait une direction fausse. Les deux fenêtres précédentes comptent parce qu'elles fournissent les entrées du réseau. Après une butée dans la fenêtre *m*, la porte reste fermée pour les décisions de fin de *m*, *m* + 1 et *m* + 2, et se rouvre à la fin de *m* + 3 : 1,5 ms après la fin de la fenêtre saturée, soit 1,5 à 2 ms après l'événement qui a provoqué la butée.

La seconde condition est une zone morte de 0,1 V : les gains ne changent que si |ē(*n*)| > 0,1 V et *J*(*n*) > 0. En régime, l'erreur ne contient plus que des résidus que les gains ne peuvent pas corriger (ondulation de découpage d'environ 27 mV crête à crête, bruit, quantification). Adapter sur ces résidus fait dériver les paramètres ; la réponse classique est de n'adapter que si l'erreur dépasse une borne des résidus [Peterson et Narendra, 1982 ; Ioannou et Sun, 1996]. Le seuil vaut environ trois fois ces résidus et il est commun avec le PINN-PID. La figure 4.3 résume le fonctionnement des fenêtres, de la porte et de la zone morte.

[FIGURE À INSÉRER : REDACTION/chapitre4/figures/Fig4_3_chronogramme_fenetres.png]

Figure 4.3 : Chronogramme de l'adaptation (schéma de principe) : moyennes par fenêtre de 0,5 ms, porte fermée pendant trois fenêtres après une butée du rapport cyclique, zone morte de 0,1 V sur l'erreur moyenne (un trait pour 10 pas de *T*c).

La version de départ fermait aussi la porte quand l'erreur de prédiction dépassait 0,5 V. Cette erreur valant 1,4 V en moyenne, les gains ne changeaient sur aucun des trois cas de base. Ce seuil a été retiré : le gradient ne prend du réseau que le signe et l'ordre de grandeur de *J*, garantis par les critères de la section 4.3.2.

### 4.4.3. Ensemble admissible et projection

Un réglage est admissible si, aux neuf points nominaux (*R* = 4, 5 et 6 Ω ; *V*in = 160, 200 et 240 V), la boucle formée par le bloc PID et le modèle moyen du convertisseur, discrétisé avec un bloqueur d'ordre zéro à *T*c, garde une marge de phase au moins égale à celle du départ (24,93°) et une fréquence de coupure d'au plus *f*s/10 = 2,2 kHz. L'adaptation ne peut donc pas réduire la marge nominale sous celle du régulateur dont elle part ; à charge légère, elle doit trouver seule ses gains. L'ensemble est tabulé hors ligne sur une grille de multiplicateurs de 1/4 à 4, au pas de 2^(1/8) sur chaque gain (35 937 points), à l'aide de :

*γ*(*x*) = max( (*M*0 − *M*(*x*)) / *M*0 , (*f*c(*x*) − 2 200) / 2 200 ),        (4.8)

où *M*(*x*) est la plus petite marge de phase et *f*c(*x*) la plus haute fréquence de coupure (en Hz) aux neuf points, et *M*0 = 24,93°. Un réglage est admissible si *γ*(*x*) ≤ 0, ce que vérifient 12 663 points (35,2 %) ; entre les points, *γ* est interpolé linéairement en log₂ des multiplicateurs, et sur 3 000 points hors grille aucun n'est admis à tort. Le calcul prend 181 s.

Le départ (1, 1, 1) est sur la frontière de l'ensemble, qui y est localement non convexe. Le plus grand pavé admissible contenant le départ, utilisé dans la version de départ, en faisait un coin : *I* ne pouvait que baisser, alors qu'une hausse de *I* accompagnée d'une hausse de *D* est admissible. Après chaque pas, *x*(*n*) + Δ*x*(*n*) est donc projeté sur l'ensemble lui-même [Ioannou et Sun, 1996]. Si la cible en sort, on cherche le point de sortie sur le segment, on retire du reste du pas sa composante normale sortante, puis on revient sur la frontière le long de la normale, au plus dix fois et tant que le point se rapproche de la cible [RÉF. À VÉRIFIER : Rosen, 1961]. Le résultat est toujours admissible. Sans ce retour, le glissement était annulé dès le départ.

### 4.4.4. Réglages et variantes

Les réglages viennent de l'article ou des critères écrits avant le calcul : fenêtres de 0,5 ms, *η* = 0,5, *α* = 0,001, *ε* = 10⁻³, zones mortes de 0,1 V, multiplicateurs dans [1/4 ; 4]. Les essais de mise au point E1 à E4, distincts des onze essais de développement, ont servi à contrôler le code et n'ont conduit à changer aucun réglage.

Deux variantes mesurent le rôle du réseau (section 5.5.3). Dans la variante à jacobien constant, *J*(*n*) est remplacé par 11,07 V par unité, médiane du jacobien d'une régression linéaire d'ordre 2 apprise sur les mêmes données. Dans la variante sans OS-ELM, les poids de sortie restent ceux de l'apprentissage hors ligne. Deux variantes de la projection sont publiées sur le dépôt.

## 4.5. Mise en œuvre sous Simulink et validation

Sous Simulink, l'adaptateur est un bloc MATLAB System, `elm_pid_adaptatif.m`, exécuté en mode interprété. Il reçoit à chaque période *T*c, par trois bloqueurs d'ordre zéro, l'erreur *e*, la tension mesurée et la commande *u* du bloc PID, et il sort les gains *K* = [*P*, *I*, *D*] vers le bloc « PID Controller » du modèle commun, passé en gains externes. Sa sortie ne dépend que de son état : au pas *k*, le bloc PID calcule *u*(*k*) avec les gains déjà sortis, puis l'adaptateur lit *e*(*k*), la mesure et *u*(*k*), sans boucle algébrique. Le bloc est la copie ligne à ligne de la classe Python du banc.

Sur les onze essais de développement, Simulink et le banc font le même nombre de pas d'adaptation. Les IAE après 30 ms concordent à 0,1 % près, sauf sur l'essai à mesure quantifiée S7a (+2,5 %), où un arrondi suffit à changer une décision du convertisseur analogique-numérique. L'écart sur les gains est au plus de 0,13 % de S1 à S6, de 0,85 % sur S8b et de 4,2 % sur S7a, et les dépassements sont identiques (13,99 % sur S1). Le test qui compare le bloc et le banc pas à pas n'a pas encore été transmis ; cet accord le rend très probable sans le remplacer.

## 4.6. Mise en œuvre des méthodes de comparaison

Les trois méthodes avancées utilisent le même bloc PID, le même convertisseur et les mêmes essais. Chacune suit un article de référence ; chaque écart est déclaré.

### 4.6.1. PSO-PID

Le PSO-PID garde des gains fixes, réglés hors ligne par l'essaim particulaire de [Gaing, 2004], repris tel quel : population de 50, 100 itérations, coefficients d'accélération de 2, inertie décroissant de 0,9 à 0,4. La recherche porte sur les multiplicateurs des gains de Ziegler-Nichols, dans [0 ; 4].

Le coût de Gaing ne juge qu'une réponse à un échelon de consigne : il règle le suivi, pas le rejet des perturbations. Il a été remplacé par l'IAE sur quatre essais de réglage, distincts des onze essais de développement : E1, charge de 7 à 4,5 Ω ; E2, tension d'entrée de 210 V à 175 puis 235 V sous 15 Ω ; E3, échelon de consigne de 10 V à 60 Ω ; E4, bruit de mesure et quantification à 9 Ω. Les rapports d'IAE à Ziegler-Nichols y sont pondérés comme dans l'indice global, 3/13 pour le démarrage et 10/13 après 30 ms. La stabilité est imposée par une marge de phase d'au moins 30° et une coupure d'au plus 2,2 kHz à douze points de fonctionnement (*R* = 4, 5, 25 et 98 Ω ; *V*in = 160, 200 et 240 V), traitées par des règles de faisabilité sans pénalité [RÉF. À VÉRIFIER : Deb, 2000]. Ces essais reprennent les familles de perturbations de la comparaison sur d'autres points de fonctionnement : le PSO-PID optimise un cahier des charges connu, sur un modèle du même convertisseur.

Une évaluation prend 0,57 s ; la recherche a duré 35 minutes sur quatre cœurs pour cinq graines, et la graine au plus petit coût de réglage a été retenue, selon une règle écrite avant. Les gains valent *P* = 0,239585, *I* = 412,0556 et *D* = 1,913247·10⁻⁵, soit 2,551, 1,369 et 2,613 fois ceux de Ziegler-Nichols, avec une marge de 30,0° : la contrainte est active.

### 4.6.2. Fuzzy-PID

Le Fuzzy-PID applique l'ordonnancement flou des gains de [Zhao et al., 1993]. À chaque période, l'erreur et sa variation, normalisées, passent par sept ensembles flous, et les règles de l'article donnent *K*′p, *K*′d et un coefficient *α*F ∈ {2, 3, 4, 5}, d'où les gains :

*K*p = *K*p,min + (*K*p,max − *K*p,min) *K*′p,  *K*d = *K*d,min + (*K*d,max − *K*d,min) *K*′d,  *K*i = *K*p² / (*α*F *K*d),        (4.9)

où *K*p varie de 0,32 à 0,6 fois le gain critique *K*u et *K*d de 0,08 à 0,15 fois *K*u *T*u, *T*u étant la période critique. La méthode est appliquée telle que publiée, avec quatre écarts. Le chapitre 3 ayant écarté la méthode du point critique, on prend le *K*u et le *T*u qui redonnent exactement les gains de Ziegler-Nichols : *K*p va alors de 0,533 à 1 fois *P* et *K*d de 1,067 à 2 fois *D*. Les échelles de normalisation, que l'article ne chiffre pas, sont 100 V pour l'erreur et 0,37244 V par période pour sa variation (pente maximale de la réponse indicielle utilisée pour Ziegler-Nichols). Le régulateur est le bloc PID commun, avec un filtre de dérivée et une saturation absents de l'article. Enfin, la variation de l'erreur est prise nulle au premier pas. Rien n'est optimisé. Au repos, les règles donnent 0,991 fois *P*, 1,983 fois *D* et 0,661 fois *I* : le Fuzzy-PID ne revient pas à Ziegler-Nichols.

### 4.6.3. PINN-PID

Le PINN-PID suit [Ito et Wasa, 2025] : les gains du bloc PID commun sont optimisés en ligne sur un coût prédit par un réseau informé par la physique (PINN), à trois couches de 32 neurones tanh, appris sur les enregistrements Simulink de la section 4.3.2 avec un terme de résidu des équations du convertisseur. Seule la tension de sortie étant mesurée, un filtre de Kalman étendu estime l'état de départ de la prédiction, à charge nominale. Le coût, moyenné sur un horizon de 110 périodes, garde les rapports de pondération de l'article :

*E*(*x*) = moy[ ½ (*e*² + 10⁻⁵ *u*²) ] + 10⁻³ |*x*|²,        (4.10)

où *x* est le vecteur des multiplicateurs des gains de Ziegler-Nichols. L'article optimise à chaque pas jusqu'à convergence, avec des milliers d'itérations, ce qui est irréalisable en 4,5 µs. Nous avons retenu le principe de l'itération en temps réel [RÉF. À VÉRIFIER : Diehl et al., 2005] : à la fin de chaque fenêtre de 0,5 ms, cinq itérations de l'optimiseur Adam [Kingma et Ba, 2015] avec les réglages de l'article, départ à chaud des gains de la fenêtre précédente et moments remis à zéro.

Après chaque itération, *x* est ramené dans une boîte de gains : *P* et *D* de 1 à 2,378 fois, *I* de 0,25 à 1 fois ceux de Ziegler-Nichols. C'est le plus grand pavé contenant le départ qui satisfait le critère de marge de l'ELM-PID ; sa borne basse sur *I* vient de l'étendue de la grille, pas du critère. Son calcul prend 32 s.

L'optimisation n'a lieu que si l'erreur efficace de la fenêtre dépasse 0,1 V. Sans cette zone morte, le terme 10⁻³ |*x*|² décide seul en régime et ramène les gains au coin (1 ; 0,25 ; 1) de la boîte. Elle porte sur l'erreur efficace, et non sur la moyenne, parce que le coût (4.10) est quadratique ; le seuil et les références sont ceux de l'ELM-PID. Cette zone morte a été choisie après un premier calcul sans elle (indice global de 0,893 sur les onze essais), parmi trois corrections candidates testées sur les seuls essais de mise au point E1 à E4 ; la règle de choix était écrite avant, mais la valeur de cette correction sur les onze essais était déjà connue par une ablation du premier calcul. L'historique complet est sur le dépôt.

## 4.7. Conclusion

L'ELM-PID comparé au chapitre 5 est le bloc PID commun, dont les gains sont ajustés toutes les 0,5 ms par un gradient normalisé, guidé par le jacobien d'un réseau ELM avec liaisons directes, appris hors ligne et mis à jour par OS-ELM. La porte suspend l'adaptation pendant la saturation, la zone morte l'empêche de dériver sur les résidus, et la projection garde les gains dans l'ensemble admissible. L'option B a été préférée à la loi incrémentale de Lu pour comparer les méthodes à loi égale, au prix d'un démarrage moins bon.

Le PSO-PID, le Fuzzy-PID et le PINN-PID partagent ce bloc PID et ne diffèrent que par la façon d'en fixer les gains. Le chapitre 5 compare les cinq méthodes sur les scénarios retenus.

---

## Notes pour la relecture (à retirer)

### Chiffres et leur source

| Chiffre | Source |
| --- | --- |
| Loi (4.1), dérivée filtrée, départ u = 0,5, gains de départ ZN, *K*ZN incrémental [P, I *T*c, D/*T*c] | `ELM_PID_INCREMENTAL/banc_elm_pid.py`, en-tête lignes 20-24 et ligne 81 |
| Écarts à Lu : commande bornée dans la loi, gains de Lu partant de zéro | `ETAT_DE_REPRISE.md` §4bis |
| Diagnostic à gains PSO égaux : S4 23,50 / 16,54 ; S3 7,53 / 5,46 ; S2 6,56 / 2,04 ; démarrage meilleur (0,600 contre 0,855) | `COMPARAISON/diagnostic_lois/diagnostic_perturbations_sortie_console.txt`, lignes 5-6 ; `diagnostic_cout_J_sortie_console.txt` ; `ELM_PID/criteres_elm_pid.txt`, en-tête |
| Explication mécanique (incréments perdus en saturation, à-coup de dérivée sur S2) | `ELM_PID/criteres_elm_pid.txt` §4, M4 |
| Option B le 8 octobre 2026 ; reste de la boucle inchangé | `criteres_elm_pid.txt` §4 (« Inchangé ») ; `ETAT_DE_REPRISE.md`, journal du 8 oct. |
| Essais de la comparaison fixés avant le calcul (S4 ; S2 et S1 pour les mécanismes) ; prévisions Q3, Q4, Q5 | `criteres_elm_pid.txt` §7 (commit 1d16b45) ; en-tête de `COMPARAISON/elm_incremental_contre_B.py` |
| Tableau 4.1 (23,61 / 19,57 / 18,87 ; 2,84 / 5,61 / 2,41 ; 2,01 / 5,34 / 2,01 ; 93,77 / 81,12 / 93,72 ; 14,0 / 2,4 / 14,0 % ; 0,747 / 0,664 et 0,680 / 0,967) | `COMPARAISON/elm_incremental_contre_B_sortie_console.txt` et `.json` |
| 3,6 % : 1 − 18,87/19,57 = 0,036 ; indice global 0,746 contre 0,728 ; Q3, Q4, Q5 justes | calcul ; `criteres_elm_pid.txt` §8 |
| Fenêtre de 110 *T*c ; entrées ȳ(n−1), ȳ(n−2), d̄(n), d̄(n−1), d̄(n−2) ; ȳ = moyenne de la tension mesurée ; d̄ = moyenne de la sortie bornée du bloc | `ELM_PID/banc_elm_pid.py`, en-tête et `AdaptateurELM.mise_a_jour` |
| Ordre 2 par quotients de Lipschitz, règle q(n)/q(n+1) ≤ 1,1 (q(2)/q(3) = 1,078) | `entrainement_elm_sortie_console.txt`, étape 2 |
| RVFL : *h* = [*g*, *z*, 1], 12 + 5 + 1 = 18 poids, entrées centrées réduites, sortie remise à l'échelle, poids cachés uniformes dans [−1 ; 1] | `banc_elm_pid.py`, `AdaptateurELM.modele` ; `entrainement_elm.py`, `apprendre` (lignes 152-167 de la partie lue) ; `excitation_donnees_elm.py`, en-tête |
| *Λ* = diag(1/C × 12, 10⁻⁸ × 6), P0 = (HᵀH + Λ)⁻¹ | `entrainement_elm.py`, `apprendre` (lam, P0, beta) |
| Enregistrements en boucle ouverte : paliers 0,5 à 20 ms, *V*in 150 à 240 V, charge 4 à 98 Ω par rampes ; A1, A2 1 s (4 000 fenêtres), V1, V2 0,5 s (2 000) | `ELM_PID/excitation_donnees_elm.py`, en-tête ; `entrainement_elm_sortie_console.txt`, étape 1 |
| Raison de la boucle ouverte (régression qui retrouve le régulateur) | `excitation_donnees_elm.py`, « Pourquoi la boucle ouverte » |
| Candidats 12/24/48 neurones, *C* 0,1 à 100, 20 graines ; critères J > 0 et J ≥ J_vrai/2 ; J_vrai par d̄ ± 0,01 ; 4 615 fenêtres ; 11/20 le 4 oct., 8/20 avec les C98 refaits ; graine 1 gardée | `entrainement_elm.py`, en-tête ; console étapes 3 à 5 (1 212 + 625 + 40 + 2 738 = 4 615) ; `criteres_elm_pid.txt` §5 |
| 14,8 s | `ELM_PID/entrainement_elm_resultats.json`, `duree_s` (console : « 15 s ») |
| OS-ELM sans oubli (λ = 1 ; covariance notée *Γ* dans le texte, P dans le code), zone morte d'estimation 0,1 V, porte ouverte | `banc_elm_pid.py`, `fin_de_fenetre` (LAMBDA = 1, ZONE_MORTE_ESTIMATION = 0,1) |
| Jacobien (4.5), dérivée par rapport à l'entrée d'indice 2 (d̄(n)), terme de liaison directe | `banc_elm_pid.py`, `AdaptateurELM.modele` (dy[2]/XE[2]·TE) |
| Sensibilités (4.6), *φ* = *J* (*s* ⊙ *K*ZN), loi (4.7), *η* = 0,5, *ε* = 10⁻³, *α* = 0,001, *x* dans [1/4 ; 4] | `banc_elm_pid.py`, `REGLAGES` et `fin_de_fenetre` ; `criteres_elm_pid.txt` §2 et M4 |
| *K*ZN = [0,093910 ; 301,089 ; 7,3227·10⁻⁶] | `criteres_elm_pid.txt` §1 |
| Porte : butée à un pas (u ≤ 0,01 ou u ≥ 0,99), fenêtres n, n−1, n−2 ; réouverture 1,5 ms après la fin de la fenêtre saturée | `banc_elm_pid.py`, `mise_a_jour` et `fin_de_fenetre` ; `REDACTION/chapitre4/figures/LISEZMOI_SCHEMAS.txt` |
| Ancienne porte sur l'erreur de prédiction (0,5 V ; erreur moyenne 1,4 V) | `criteres_elm_pid.txt` §3, V1 |
| Résidus : ondulation 27 mV crête à crête ; seuil ≈ trois fois les résidus | `PINN_PID/criteres_pinn_pid.txt` §3, E4 |
| Ensemble admissible : 9 points, 24,93°, 2,2 kHz, grille 33³ = 35 937, 12 663 admissibles (35,2 %), 0 admis à tort sur 3 000, 181 s | `ELM_PID/ensemble_gains_elm.py`, en-tête ; `ensemble_gains_elm_sortie_console.txt` |
| Départ sur la frontière, non convexe, pavé en coin, hausse conjointe *I* × 1,2 et *D* × 1,3 admissible | `criteres_elm_pid.txt` §3 (V2, V3) ; console de l'ensemble, contrôle 2 |
| Projection : point de sortie (30 bissections), retrait de la composante sortante, restauration le long de la normale, au plus 10 fois | `criteres_elm_pid.txt` M3 ; `banc_elm_pid.py`, `projeter`, `restaurer` |
| E1 à E4 de mise au point, aucun réglage changé ensuite | `criteres_elm_pid.txt` §6 |
| Jacobien constant 11,0687 (médiane du jacobien de la régression linéaire d'ordre 2) ; sans OS-ELM (APPRENDRE = 0) ; deux variantes de projection (M2 seule, sans glissement) | `COMPARAISON/elm_incremental_contre_B_sortie_console.txt`, ligne 3 ; `banc_elm_pid.py` (J_REGRESSION) ; `criteres_elm_pid.txt` §7 |
| Bloc MATLAB System interprété, trois bloqueurs à *T*c, entrées e, mesure, u, sortie K, sans traversée directe | `ELM_PID/elm_pid_adaptatif.m`, en-tête |
| Validation : T0 2,3 mV ; mêmes pas d'adaptation ; IAE à 0,1 % sauf S7a (+2,5 %) ; gains 0,13 % (S1-S6), 0,85 % (S8b), 4,2 % (S7a) ; dépassement 13,99 % ; rejeu non transmis | `criteres_elm_pid.txt` §10 ; `ETAT_DE_REPRISE.md` §4.2 |
| PSO : population 50, 100 itérations, c1 = c2 = 2, inertie 0,9 à 0,4, multiplicateurs [0 ; 4], E1 à E4, coût 3/13 et 10/13, marge 30° et 2,2 kHz aux 12 points, 0,57 s, 35 min, quatre cœurs, cinq graines, graine 3 ; gains et 30,0° | `PSO_PID/criteres_pso_pid.txt` §1 à §6 |
| Fuzzy : sept ensembles, *α* de 2 à 5, (4.9), plages de l'article, *K*u et *T*u équivalents, 0,533-1 × P, 1,067-2 × D, E_M = 100 V, DE_M = 0,37244 V, gains de repos 0,991 / 1,983 / 0,661 | `FUZZY_PID/criteres_fuzzy_pid.txt` (« La méthode », « Les quatre écarts », « Valeurs au repos ») |
| PINN : 3 × 32 tanh, terme physique, filtre de Kalman étendu, coût (4.10) avec W_U = 10⁻⁵ et W_F = 10⁻³, horizon 110 *T*c, 5 itérations d'Adam, départ à chaud, moments à zéro, boîte 1-2,378 / 0,25-1 / 1-2,378, 32 s, zone morte efficace 0,1 V, coin (1 ; 0,25 ; 1), premier calcul 0,893, valeur de C1 connue d'avance | `PINN_PID/criteres_pinn_pid.txt` §2, §3 (E1, E3, E4), §5, §6 (« Déclaration ») ; `boite_gains_pinn_sortie_console.txt`, lignes 17 et 37 |

### Citations et statut

| Citation | Statut | Fichier |
| --- | --- | --- |
| [Lu et al., 2021] | avec réserve | `references_chapitre5.md` |
| [Åström et Hägglund, 2006] | vérifiée | `references_chapitre5.md` |
| [Huang et al., 2006] | avec réserve (était non vérifiée) | `references_chapitre4.md` |
| [Pao et al., 1994] | avec réserve | `references_chapitre4.md` |
| [Liang et al., 2006] | vérifiée | `references_chapitre5.md` |
| [Peterson et Narendra, 1982] | avec réserve | `references_chapitre5.md` |
| [Ioannou et Sun, 1996] | vérifiée (livre non consulté, pas de page) | `references_chapitre4.md` |
| [Gaing, 2004] | vérifiée | `references_chapitre5.md` |
| [Zhao et al., 1993] | avec réserve | `references_chapitre5.md` |
| [Ito et Wasa, 2025] | vérifiée (prépublication arXiv) | `references_chapitre5.md` |
| [Kingma et Ba, 2015] | vérifiée | `references_chapitre4.md` |
| He et Asada, 1993 ; Rosen, 1961 ; Deb, 2000 ; Diehl et al., 2005 | non vérifiées : repères jaunes seulement | `references_chapitre4.md` |

### Points à trancher et cohérence avec les chapitres 5 et 6

- Équation (5.4) : réglé le 10 octobre 2026. Elle écrivait *φ* = *J* *s* et omettait l'inertie ; elle est retirée du chapitre 5, dont la section 5.5.3 renvoie à la loi (4.7).
- Tension mesurée : réglé le 10 octobre 2026. Les chapitres 5 (5.5.3) et 6 (6.3.4) écrivent maintenant *J*(*n*) = ∂ŷ/∂d̄ et « tension mesurée », comme (4.5) et 4.3.1.
- Vocabulaire des essais : ce chapitre suit le chapitre 5 (« onze essais de développement », « essais de mise au point E1 à E4 », « essais de réglage » pour le PSO-PID). E1 à E4 sont les mêmes quatre essais pour l'ELM-PID, le PSO-PID et le PINN-PID. Le chapitre 1 doit définir ces catégories.
- Honnêteté sur l'option B : le diagnostic qui l'a motivée a été mesuré sur les onze essais (dont S2 et S3). Le texte le dit (4.2.2).
- Réouverture de la porte : réglé le 10 octobre 2026. Les chapitres 5 (5.3.2, 5.5.3) et 6 (6.3.2) disent « 1,5 ms après la fin de la fenêtre saturée, soit 1,5 à 2 ms après l'événement », comme 4.4.2 et la figure 4.3.
- Figures 4.1 à 4.3 : les chevauchements relevés au premier tirage ont été corrigés dans `schemas_chapitre4.py`. Le 10 octobre 2026, figure 4.3 : les étiquettes « fermée » ont un fond blanc (les hachures ne traversent plus le texte), et « réouverture 1,5 ms après la fin de *m* », « *d* en butée », « fenêtre *m* suspecte » et « points : *e*(*k*) ; traits : ē(*n*) » ont un fond blanc qui masque les pointillés.
- Ordre des figures : la figure 4.1 (structure de l'ELM-PID) venait après la figure 4.2 dans le texte. Elle est déplacée à la fin de 4.1, annoncée par « (figure 4.1) » dans le premier paragraphe ; le renvoi de 4.4.1 reste valable.
- Symboles : *α* (inertie de l'ELM-PID) et *α*F (Fuzzy-PID) sont distincts ; le coût du PINN-PID est noté *E*(*x*) en (4.10) pour ne pas le confondre avec l'inductance *L* ni avec le jacobien *J*.
- Milliers : espaces fines insécables dans Word.
