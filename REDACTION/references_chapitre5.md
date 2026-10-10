# Références du chapitre 5 : vérification

*Établi le 10 octobre 2026. Document de travail, non commité.*

## 0. Comment la vérification a été faite, et sa limite

L'API Crossref (`api.crossref.org`), `doi.org` et les pages des éditeurs n'ont
pas pu être ouvertes directement depuis cette session : `curl` est refusé par
le proxy (403, refus de politique, non contourné) et l'outil de lecture de pages
échoue à la résolution DNS. La seule voie restante était le moteur de recherche,
souvent restreint au domaine de l'éditeur (`ieeexplore.ieee.org`,
`asmedigitalcollection.asme.org`, `link.springer.com`,
`onlinelibrary.wiley.com`, `pubs.acs.org`) ou à un catalogue de bibliothèque.

Trois statuts :

- **vérifiée** : notice de l'éditeur, résolution du DOI ou catalogue de
  bibliothèque trouvés par le moteur de recherche, avec auteurs, année, titre,
  revue, volume, pages et DOI (ou ISBN) concordants. Limite : la notice a été
  lue à travers le résumé du moteur, pas affichée en entier ;
- **vérifiée avec réserve** : la notice de l'éditeur a été trouvée, mais un
  champ (numéro, volume ou DOI) ne vient que de sources secondaires
  concordantes ;
- **non vérifiée** : notice de l'éditeur non atteinte, ou désaccord entre
  sources. Ce qui manque est indiqué.

Avant le dépôt du mémoire, il faut relire sur Crossref (depuis un poste qui y
a accès) les entrées « avec réserve » et « non vérifiées ». Une requête suffit
par DOI : `https://api.crossref.org/works/<DOI>`.

Étiquettes : règle de `REDACTION/guide_de_forme.md` §7 (deux auteurs reliés
par « et », trois et plus : « et al. »). Elle diffère de l'exemple
« [Ziegler J.G., 1942] » de la consigne ; à trancher avec Jean-Riche.

---

## 1. Le PDF fourni : note de F. Mudry

**Ce que c'est.** Une note d'application de cours, pas un article :
« Ajustage des Paramètres des Régulateurs PID », Prof. Freddy Mudry, Institut
d'Automatisation Industrielle (iAi), Laboratoire d'automatique, Département
d'électricité et informatique, eivd. 30 pages PDF (couverture, 2 pages de table
des matières, 26 pages numérotées). Dates : « avril 2002 » au pied de la
première page de table, « fmy / mars 2006 » au pied de toutes les autres ; le
fichier PDF a été produit en 2010. La version citée est donc celle de mars 2006.
Le sigle eivd désigne l'École d'ingénieurs du canton de Vaud (devenue HEIG-VD) :
c'est une connaissance générale, non vérifiée dans le document, qui n'écrit que
« eivd ». Une copie circule sur un forum (Futura-Sciences) ; aucune page
officielle de l'école n'a été trouvée.

Correspondance des pages : page imprimée *n* = page PDF *n* + 4.

**Passages utiles au chapitre 5**

| Page imprimée (PDF) | Contenu |
|---|---|
| p. 1 (PDF 5) | Ziegler et Nichols ont proposé en 1942 deux démarches ; Åström et al. ont cherché au début des années 1990 des règles « plus performantes que celles de Ziegler-Nichols ». Réserve explicite : les méthodes présentées « ne sont applicables qu'à des processus non oscillants » dont la phase franchit −180°. |
| p. 2 (PDF 6) | PID classique, éq. (1) à (3), forme « parallèle ou non-interactive » Kp(1 + 1/(sTi) + sTd). |
| p. 3 (PDF 7) | Filtre de la dérivée sTd/(1 + sTd/N), éq. (10), « généralement N entre 5 et 20 ». |
| p. 4 (PDF 8) | Emballement de l'intégrale en saturation et limitation du terme intégral (anti-emballement), sans détail d'algorithme. |
| p. 10 (PDF 14) | §5.1 : tableau 1, méthode de la réponse indicielle (Kp = 1.2/(aK0), Ti = 2L, Td = 0.5L) ; Kp de ZN « trop élevés », dépassement supérieur à 20 %, réduire Kp d'un facteur 2. §5.2 : méthode du point critique (gain critique Kcr, période Tcr), tableau 2 : PID Kp = 0.6Kcr, Ti = 0.5Tcr, Td = 0.125Tcr ; « temps de montée relativement court malheureusement assorti d'un dépassement élevé » ; Ti/Td = 4 pour les deux méthodes. |
| p. 11 (PDF 15) | Exemple numérique sur un processus d'ordre 3 ; « dépassement important ; par contre, la perturbation est corrigée rapidement ». |
| p. 12 (PDF 16) | Critère Ms (maximum de la fonction de sensibilité, 1.4 ou 2) défini par Åström pour comparer les réglages. |
| p. 17-18 (PDF 21-22) | Comparaison qualitative des réponses indicielles (dépassement, temps de réglage, rejet de perturbation) ; tableau 5 des paramètres. |
| p. 26 (PDF 30) | Liste de références. |

La note ne définit ni l'IAE, ni l'ISE, ni l'ITAE, ni le temps de réglage à
2 %. Pour les critères de performance, elle ne sert donc qu'aux remarques
qualitatives sur le dépassement et le rejet de perturbation.

**Sources primaires citées par la note (p. 26)** : Ziegler et Nichols 1942
(Trans. ASME 64, pp. 759-768) ; Horowitz 1963 ; Åström et Hägglund 1995
(ISBN 1-55617-516-7) ; Åström, Hägglund, Hang, Ho 1993 (Control Engineering
Practice 1(4), 699-714) ; Åström et Hägglund 1984 (Automatica 20, 645-651).
Elle cite donc bien la source primaire, et c'est celle-ci qu'il faut citer
pour les tableaux de ZN.

**Remarque de fond pour le chapitre 5.** La réserve de la p. 1 touche
directement le sujet : un Buck en boucle ouverte est un second ordre LC peu
amorti, donc un processus oscillant, hors du domaine annoncé par la note. Les
gains ZN de la base commune ont bien le rapport Ti/Td = 4 de la p. 10
(P = 0.093910, I = 301.089, D = 7.3227e-6 donnent Ti = 3.119e-4 s,
Td = 7.797e-5 s). Le chapitre gagnera à dire que ZN sert de référence commune
et non de réglage « optimal » pour ce procédé, et à citer Mudry p. 10 pour le
fort dépassement attendu.

**Forme de citation proposée** (gabarit « livre/rapport » du guide) :

- Étiquette : [Mudry F., 2006]
- Entrée : Mudry F., 2006. *Ajustage des paramètres des régulateurs PID*.
  Note d'application, Institut d'Automatisation Industrielle, Laboratoire
  d'automatique, eivd, version de mars 2006 (première version avril 2002).
- Statut : vérifiée sur le document lui-même (auteur, titre, institution,
  dates lus dans le PDF). Document de cours non publié : à citer en
  complément, jamais à la place de [Ziegler J.G. et Nichols N.B., 1942].

---

## 2. Références de base du chapitre 5

### [Ziegler J.G. et Nichols N.B., 1942]
Ziegler J.G., Nichols N.B., 1942. *Optimum settings for automatic
controllers*. Transactions of the ASME, 64(8), 759-765.
doi:10.1115/1.4019264.
- **Statut : vérifiée.** Notice ASME Digital Collection :
  https://asmedigitalcollection.asme.org/fluidsengineering/article/64/8/759/1155342/Optimum-Settings-for-Automatic-Controllers
- Pages : l'article occupe 759-765. La plage 759-768 (Mudry, nombreux
  articles) inclut la discussion et la réponse des auteurs. Retenir 759-765.
- Appui : origine des règles du point critique (Kcr, Tcr) qui donnent les
  gains de la référence ZN.

### [Åström K.J. et Hägglund T., 1995]
Åström K.J., Hägglund T., 1995. *PID Controllers: Theory, Design, and
Tuning*. 2e éd., Instrument Society of America. ISBN 1-55617-516-7.
- **Statut : vérifiée** (ISBN, édition, année, éditeur). Notice de catalogue :
  https://kis.stuba.sk/arl-stu/en/detail-stu_us_cat-stu50665-PID-Controllers-Theory-Design-and-Tuning ;
  page de l'éditeur : https://www.isa.org/products/pid-controllers-theory-design-and-tuning-secon-1
  Ville non confirmée : ne pas l'ajouter sans vérification.
- Appui : forme parallèle du PID, filtre de la dérivée (N), anti-emballement,
  critères intégraux IAE/ISE. Livre non consulté : citer des pages
  seulement après lecture.

### [Åström K.J. et Hägglund T., 2006]
Åström K.J., Hägglund T., 2006. *Advanced PID Control*. ISA – The
Instrumentation, Systems, and Automation Society. ISBN 978-1-55617-942-6.
- **Statut : vérifiée.** Lund University Publications :
  https://lup.lub.lu.se/record/535630 ; WorldCat OCLC 60557376 :
  https://search.worldcat.org/title/advanced-pid-control/oclc/60557376
- Appui : même usage que l'édition 1995 (anti-emballement par intégration
  conditionnelle, filtre de la dérivée, IAE). Déjà cité dans
  `ELM_PID/criteres_elm_pid.txt` [13].

### [Graham D. et Lathrop R.C., 1953]
Graham D., Lathrop R.C., 1953. *The synthesis of "optimum" transient
response: criteria and standard forms*. Transactions of the American
Institute of Electrical Engineers, Part II: Applications and Industry, 72,
273-288.
- **Statut : vérifiée avec réserve.** Notice IEEE Xplore (titre, pp. 273-288,
  novembre 1953, résumé : l'ITAE « clairement supérieur » parmi huit
  critères) : https://ieeexplore.ieee.org/document/6371346. Le volume 72 et
  le DOI 10.1109/TAI.1953.6371346 ne viennent que de Semantic Scholar ; le
  DOI n'est donc pas reproduit dans l'entrée. Prénom du premier auteur :
  « Dunstan » selon Semantic Scholar, mais un résumé du rapport WADC
  TR 53-66 (DTIC) donne « Frank D. » ; l'initiale D. reste sûre.
- Appui : définition et origine du critère ITAE.

### [Ogata K., 2010]
Ogata K., 2010. *Modern Control Engineering*. 5e éd., Prentice Hall, Boston.
ISBN 978-0-13-615673-4.
- **Statut : vérifiée.** Notice de la bibliothèque universitaire de Paderborn :
  https://ce.visuallibrary.net/ubpb/content/titleinfo/1253651 (ne pas
  confondre avec l'édition internationale, ISBN 978-0-13-713337-6).
- Appui : définitions du dépassement, du temps de montée, du temps de réglage
  (bande de 2 %) et de l'erreur statique. Pages à relever sur l'ouvrage.

### [Dorf R.C. et Bishop R.H., 2017]
Dorf R.C., Bishop R.H. *Modern Control Systems*. 13e éd., Pearson.
ISBN 978-0-13-440762-3.
- **Statut : non vérifiée.** L'ISBN correspond bien à la 13e édition, mais
  l'année varie selon les notices (2016 ou 2017) ; seules des notices de
  libraires ont été trouvées. Alternative à Ogata, inutile si Ogata est
  retenu.

### [Erickson R.W. et Maksimović D., 2020]
Erickson R.W., Maksimović D., 2020. *Fundamentals of Power Electronics*.
3e éd., Springer. ISBN 978-3-030-43879-1 (relié), 978-3-030-43881-4
(livre électronique). doi:10.1007/978-3-030-43881-4.
- **Statut : vérifiée.** Springer : https://link.springer.com/10.1007/978-3-030-43881-4
  et https://www.springer.com/us/book/9783030438791. Ville (Cham) non
  confirmée.
- Appui : convertisseur Buck, conduction continue, modèle moyen.

### Critère normalisé par une référence (moyenne des rapports d'IAE à ZN)

Aucune référence standard n'a été trouvée qui définisse un coût comme la
moyenne des rapports IAE(méthode)/IAE(ZN). Le coût J du chapitre 5 doit donc
être présenté comme une définition propre au travail. Deux références
vérifiées portent le principe d'un indice en rapport à une référence ; elles
peuvent être citées pour ce principe, sans laisser croire qu'elles
définissent J :

#### [Harris T.J., 1989]
Harris T.J., 1989. *Assessment of control loop performance*. The Canadian
Journal of Chemical Engineering, 67(5), 856-861. doi:10.1002/cjce.5450670519.
- **Statut : vérifiée.** Wiley : https://onlinelibrary.wiley.com/doi/abs/10.1002/cjce.5450670519
- Appui : indice de performance défini comme un rapport (variance observée
  sur variance minimale), origine de l'évaluation des boucles par rapport à
  une référence. Référence = régulateur à variance minimale, pas un PID.

#### [Huang H.-P. et Jeng J.-C., 2002]
Huang H.-P., Jeng J.-C., 2002. *Monitoring and assessment of control
performance for single loop systems*. Industrial & Engineering Chemistry
Research, 41(5), 1297-1309. doi:10.1021/ie0101285.
- **Statut : vérifiée avec réserve.** ACS : https://pubs.acs.org/doi/10.1021/ie0101285
  (volume, pages, DOI) ; le numéro 5 vient d'une source secondaire.
- Appui : indice qui compare l'IAE courant d'une boucle à un IAE de référence
  (optimal) après un échelon de consigne.

Non retrouvée : Swanda A.P., Seborg D.E., 1999 (IAE adimensionnel, American
Control Conference) : **non vérifiée**, aucune notice trouvée ; ne pas citer
en l'état.

---

## 3. Références des méthodes

### [Liang N.-Y. et al., 2006]
Liang N.-Y., Huang G.-B., Saratchandran P., Sundararajan N., 2006. *A fast
and accurate online sequential learning algorithm for feedforward networks*.
IEEE Transactions on Neural Networks, 17(6), 1411-1423.
doi:10.1109/TNN.2006.880583.
- **Statut : vérifiée.** Résolution du DOI (https://doi.org/10.1109/tnn.2006.880583)
  et notice IEEE Xplore https://ieeexplore.ieee.org/document/4012031/
- Appui : OS-ELM, mise à jour en ligne des poids de sortie de l'ELM-PID.

### [Huang G.-B. et al., 2006]
Huang G.-B., Zhu Q.-Y., Siew C.-K., 2006. *Extreme learning machine: theory
and applications*. Neurocomputing, 70(1-3), 489-501.
doi:10.1016/j.neucom.2005.12.126.
- **Statut : non vérifiée.** La page ScienceDirect n'a pas été atteinte. Les
  données concordent dans la copie de l'article (https://web.njit.edu/~usman/courses/cs675_fall20/ELM-NC-2006.pdf),
  sur Semantic Scholar et dans de nombreuses listes de références. Manque :
  la notice de l'éditeur ou Crossref.
- Appui : principe de l'ELM (poids d'entrée aléatoires, poids de sortie par
  pseudo-inverse).

### [Lu Y. et al., 2021]
Lu Y., Yu W., Wang J., Jiang D., Li R., 2021. *Design of PID controller
based on ELM and its implementation for Buck converters*. International
Journal of Control, Automation and Systems, 19, 2479-2490.
doi:10.1007/s12555-019-0989-1.
- **Statut : vérifiée avec réserve.** Springer : https://link.springer.com/article/10.1007/s12555-019-0989-1
  et IJCAS : https://www.ijcas.org/journal/view.html?pn=related&uid=3243&vmd=Full
  Le numéro 7 (dépôt) n'apparaît pas dans les résultats obtenus : à confirmer
  avant de l'ajouter. Date de publication : 1er mai 2021 selon Springer,
  1er juillet 2021 selon IJCAS (en ligne contre papier, sans incidence sur
  l'année).
- Appui : article de référence de l'ELM-PID (Buck, modèle moyen en CCM).

### [Ito J. et Wasa Y., 2025]
Ito J., Wasa Y., 2025. *Data-driven adaptive PID control based on
physics-informed neural networks*. Prépublication arXiv:2510.04591 (v1 du
6 octobre 2025, v2 du 8 octobre 2025).
- **Statut : vérifiée** comme prépublication (pages arXiv
  https://arxiv.org/abs/2510.04591v1 et https://arxiv.org/html/2510.04591v2).
  Les auteurs l'annoncent soumise à IEEE Transactions on Control Systems
  Technology ; aucune version publiée trouvée à ce jour. Citer la version
  arXiv utilisée (v1 ou v2) et le dire. DOI arXiv non relevé : ne pas
  l'ajouter.
- Appui : coût et optimisation des gains du PINN-PID.

### [Zhao Z.-Y. et al., 1993]
Zhao Z.-Y., Tomizuka M., Isaka S., 1993. *Fuzzy gain scheduling of PID
controllers*. IEEE Transactions on Systems, Man, and Cybernetics, 23(5),
1392-1398.
- **Statut : vérifiée avec réserve.** La notice IEEE Xplore existe
  (https://ieeexplore.ieee.org/document/260670/, titre et résumé, qui
  compare d'ailleurs la méthode à Ziegler-Nichols). Volume, numéro, pages et
  DOI 10.1109/21.260670 ne viennent que de ResearchGate et de listes de
  références ; DOI non reproduit dans l'entrée. Deux notices IEEE Xplore
  portent le même titre (260670 et 269762) : à éclaircir.
- Appui : méthode du Fuzzy-PID (ordonnancement flou des gains).

### [Gaing Z.-L., 2004]
Gaing Z.-L., 2004. *A particle swarm optimization approach for optimum
design of PID controller in AVR system*. IEEE Transactions on Energy
Conversion, 19(2), 384-391. doi:10.1109/TEC.2003.821821.
- **Statut : vérifiée.** IEEE Xplore : https://ieeexplore.ieee.org/abstract/document/1300705/
- Appui : essaim particulaire du PSO-PID (le coût W d'origine a été remplacé,
  voir `PSO_PID/criteres_pso_pid.txt`).

### [Diehl M. et al., 2005]
Diehl M., Bock H.G., Schlöder J.P., 2005. *A real-time iteration scheme for
nonlinear optimization in optimal feedback control*. SIAM Journal on Control
and Optimization, 43(5), 1714-1736. doi:10.1137/S0363012902400713.
- **Statut : non vérifiée.** Crossref et epubs.siam.org inaccessibles depuis
  cette session. Données concordantes sur la copie KU Leuven
  (https://lirias.kuleuven.be/retrieve/80044), Semantic Scholar et des
  listes de références. Le dépôt notait déjà « notice doi.org non
  consultée ». Manque : Crossref.
- Appui : itération en temps réel (une itération d'optimisation par pas) du
  PINN-PID.

### [Peterson B.B. et Narendra K.S., 1982]
Peterson B.B., Narendra K.S., 1982. *Bounded error adaptive control*. IEEE
Transactions on Automatic Control, 27(6), 1161-1168.
doi:10.1109/TAC.1982.1103112.
- **Statut : vérifiée avec réserve.** Notice IEEE Xplore (titre, résumé :
  loi adaptative à zone morte, signaux bornés) :
  https://ieeexplore.ieee.org/document/1103112/ ; volume, numéro et pages
  dans les listes de références Elsevier et Springer ; DOI dans une liste de
  références Wiley (Cheng, 1991, qui donne aussi 1161-1167, plage isolée).
  Manque : Crossref.
- Appui : zone morte commune de l'ELM-PID et du PINN-PID.

---

## 4. Références déjà présentes dans le dépôt (lecture seule)

Statut « dépôt » = ce qui est écrit dans le fichier ; statut « ici » = ce
contrôle.

| Référence (forme du dépôt) | Fichier | Statut dans le dépôt | Ici |
|---|---|---|---|
| Lu et al., IJCAS 19(7), 2479-2490, 2021, doi:10.1007/s12555-019-0989-1 | ELM [1] | texte intégral lu | avec réserve (n° 7) |
| Huang, Zhu, Siew, Neurocomputing 70(1-3), 489-501, 2006 | ELM [2] | tiré du document de la méthode | non vérifiée |
| Liang et al., IEEE TNN 17(6), 1411-1423, 2006 | ELM [3] | tiré du document de la méthode | vérifiée |
| Pao, Park, Sobajic, Neurocomputing 6(2), 163-180, 1994 | ELM [4] | tiré du document de la méthode | non contrôlée |
| Peterson, Narendra, IEEE TAC 27(6), 1161-1168, 1982 | ELM [5], PINN [3] | tiré du document de la méthode | avec réserve |
| Egardt, Stability of Adaptive Controllers, LNCIS 20, Springer, 1979 | ELM [6] | notice vérifiée | non contrôlée |
| Ioannou, Sun, Robust Adaptive Control, Prentice Hall, 1996 | ELM [7], PINN [4] | tiré du document de la méthode | non contrôlée |
| Goodwin, Sin, Adaptive Filtering, Prediction and Control, 1984 | ELM [8], PINN [7] | notice vérifiée | non contrôlée |
| He, Asada, ACC 1993 | ELM [9] | notice vérifiée | non contrôlée |
| Bomberger, Seborg, J. Process Control 8(5-6), 1998 | ELM [10] | notice vérifiée (pages absentes) | non contrôlée |
| Haykin, Adaptive Filter Theory, 4e éd., 2002 | ELM [11] | tiré du document de la méthode | non contrôlée |
| Narendra, Parthasarathy, IEEE TNN 1(1), 4-27, 1990 | ELM [12] | tiré du document de la méthode | non contrôlée |
| Åström, Hägglund, Advanced PID Control, ISA, 2006 | ELM [13] | tiré du document de la méthode | vérifiée |
| Rosen, J. SIAM 9(4), 1961 | ELM [14], PINN [8] | notice vérifiée (pages absentes) | non contrôlée |
| Visioli, Practical PID Control, Springer, 2006 | ELM [15] | cité sans consultation, « à vérifier » | non contrôlée |
| Åström, Wittenmark, Adaptive Control, 2e éd., 1995 | ELM [16] | cité sans consultation, « à vérifier » | non contrôlée |
| Ito, Wasa, arXiv:2510.04591, 2025 | PINN [1] | texte lu (pages du preprint) | vérifiée (preprint) |
| Diehl, Bock, Schlöder, SICON 43(5), 1714-1736, 2005 | PINN [2] | lu sur la copie KU Leuven, doi.org non consulté | non vérifiée |
| Tikhonov, Arsenin, 1977 | PINN [5] | non précisé | non contrôlée |
| Ioannou, Kokotovic, Automatica, 1984, doi:10.1016/0005-1098(84)90009-8 | PINN [6] | volume et pages non confirmés | non contrôlée |
| Kingma, Ba, Adam, ICLR 2015 | PINN [9] | non précisé | non contrôlée |
| Gaing, IEEE TEC 19(2), 384-391, 2004, doi:10.1109/TEC.2003.821821 | PSO [1] | lu en entier | vérifiée |
| Åström, Panagopoulos, Hägglund, Automatica 34(5), 585-601, 1998 | PSO [2] | notice vérifiée | non contrôlée |
| Panagopoulos, Åström, Hägglund, IEE Proc. CTA 149(1), 32-40, 2002 | PSO [3] | notice vérifiée | non contrôlée |
| Krohling, Rey, IEEE TEC (Evol. Comput.) 5(1), 2001 | PSO [4] | notice vérifiée (pages absentes) | non contrôlée |
| Alipoor, ICIS 2009 | PSO [5] | notice vérifiée | non contrôlée |
| Deb, CMAME 186(2-4), 311-338, 2000 | PSO [6] | notice vérifiée | non contrôlée |
| Toscano Pulido, Coello Coello, CEC 2004 | PSO [7] | notice vérifiée | non contrôlée |
| Kim, Maruta, Sugie, Automatica 44(4), 1104-1110, 2008 | PSO [8] | notice vérifiée | non contrôlée |
| Clerc, Kennedy, IEEE TEC 6(1), 58-73, 2002 | PSO [9] | notice vérifiée | non contrôlée |
| Zhao, Tomizuka, Isaka, IEEE SMC 23(5), 1392-1398, 1993 | FUZZY | article suivi, statut de notice non indiqué | avec réserve |

« Non contrôlée » : hors du périmètre de cette vérification (références des
modifications, pas des articles principaux ni des besoins du chapitre 5).
Celles qui seront citées au chapitre 4 devront passer le même contrôle.

---

## 5. Bilan

- Vérifiées : 10 (Mudry, vérifiée sur le document lui-même ; Ziegler et
  Nichols ; Åström et Hägglund 1995 et 2006 ; Ogata ; Erickson et
  Maksimović ; Harris ; Liang et al. ; Ito et Wasa, comme prépublication ;
  Gaing).
- Vérifiées avec réserve : 5 (Graham et Lathrop, Huang et Jeng, Lu et al.,
  Zhao et al., Peterson et Narendra).
- Non vérifiées : 4 (Dorf et Bishop, Huang et al. 2006, Diehl et al.,
  Swanda et Seborg).
- Écarts trouvés : pages de Ziegler et Nichols (759-765 pour l'article,
  759-768 avec la discussion) ; prénom de Graham ; double notice IEEE de
  Zhao et al. ; numéro 7 de Lu et al. non confirmé.
