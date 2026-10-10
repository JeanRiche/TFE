# Références du chapitre 4 : vérification

*Établi le 10 octobre 2026. Document de travail, non commité.*

## 0. Méthode et limite

Mêmes statuts que `references_chapitre5.md` §0. Depuis cette session,
`api.crossref.org`, `arxiv.org` et les pages des éditeurs ne s'ouvrent pas
(échec DNS de l'outil de lecture) ; la vérification passe par le moteur de
recherche, restreint quand c'est utile au domaine de l'éditeur ou à un
catalogue.

- **vérifiée** : notice de l'éditeur, page arXiv ou catalogue de
  bibliothèque atteints, champs concordants ;
- **avec réserve** : notice de l'éditeur (ou base bibliographique) atteinte,
  un champ seulement confirmé par des sources secondaires ;
- **non vérifiée** : notice de l'éditeur non atteinte, ou désaccord entre
  sources. Ne pas citer : repère jaune « [RÉF. À VÉRIFIER : ...] ».

Les références déjà contrôlées pour le chapitre 5 gardent leur statut
(`references_chapitre5.md`) : [Lu et al., 2021] avec réserve ; [Liang et
al., 2006] vérifiée ; [Gaing, 2004] vérifiée ; [Zhao et al., 1993] avec
réserve ; [Ito et Wasa, 2025] vérifiée (prépublication) ; [Peterson et
Narendra, 1982] avec réserve ; [Åström et Hägglund, 2006] vérifiée ;
[Ziegler et Nichols, 1942] vérifiée.

## 1. Références nouvelles ou revues pour le chapitre 4

### [Huang et al., 2006]
Huang G.-B., Zhu Q.-Y., Siew C.-K., 2006. *Extreme learning machine: theory
and applications*. Neurocomputing, vol. 70, n° 1-3, pp. 489-501.
doi:10.1016/j.neucom.2005.12.126.
- **Statut : avec réserve** (était « non vérifiée » au chapitre 5). La page
  ScienceDirect de l'article a été atteinte par le moteur de recherche
  (https://www.sciencedirect.com/science/article/abs/pii/S0925231206000385),
  avec le DOI. Volume 70 et pages 489-501 : copie de l'article
  (https://web.njit.edu/~usman/courses/cs675_fall20/ELM-NC-2006.pdf) et
  listes de références ; numéro 1-3 : sources secondaires seulement.
- Appui : principe de l'ELM (poids d'entrée tirés au hasard et fixés, poids
  de sortie par moindres carrés).

### [Pao et al., 1994]
Pao Y.-H., Park G.-H., Sobajic D.J., 1994. *Learning and generalization
characteristics of the random vector functional-link net*. Neurocomputing,
vol. 6, n° 2, pp. 163-180. doi:10.1016/0925-2312(94)90053-1.
- **Statut : avec réserve.** Notice DBLP de l'auteur (https://dblp.org/pid/98/95)
  et index TR Dizin concordants (volume, numéro, pages, DOI) ; page de
  l'éditeur non atteinte. Variante de titre sans « the » dans une liste de
  références.
- Appui : liaisons directes entre entrées et sortie (RVFL).

### [Ioannou et Sun, 1996]
Ioannou P.A., Sun J., 1996. *Robust Adaptive Control*. Prentice Hall, Upper
Saddle River (NJ). ISBN 0-13-439100-4.
- **Statut : vérifiée** (notices de catalogue : bibliothèque de l'université
  de Kyushu, https://catalog.lib.kyushu-u.ac.jp/ja/recordID/1000922167 ;
  catalogue UTB, https://vufind.katalog.k.utb.cz/Record/14743). Livre non
  consulté : aucune page citée.
- Appui : zone morte et opérateur de projection des paramètres sur un
  ensemble admissible (cités dans `ELM_PID/criteres_elm_pid.txt`, M1 et M2,
  et `PINN_PID/criteres_pinn_pid.txt`, E4).

### [Kingma et Ba, 2015]
Kingma D.P., Ba J., 2015. *Adam: a method for stochastic optimization*.
3rd International Conference on Learning Representations (ICLR), San Diego,
2015. arXiv:1412.6980.
- **Statut : vérifiée.** Page arXiv https://arxiv.org/abs/1412.6980 (champ
  « comments » : publiée à ICLR 2015, San Diego ; v1 du 22 décembre 2014,
  v9 du 30 janvier 2017).
- Appui : optimiseur Adam du PINN-PID (Ito et Wasa en reprennent les
  réglages).

### [Rosen, 1961]
Rosen J.B., 1961. *The gradient projection method for nonlinear
programming. Part II. Nonlinear constraints*. Journal of the Society for
Industrial and Applied Mathematics, vol. 9, n° 4, pp. 514-532 (ou 514-553).
- **Statut : non vérifiée.** Notice SIAM ou JSTOR non atteinte. Volume,
  numéro et première page concordants dans plusieurs listes de références,
  mais la dernière page diffère (532 ou 553). DOI probable
  10.1137/0109044, non confirmé : ne pas le reproduire. Le dépôt cite la
  partie II (1961), pas la partie I (1960) : c'est bien la partie II qui
  traite la restauration vers une frontière courbe.
- Usage au chapitre 4 : repère [RÉF. À VÉRIFIER : Rosen, 1961].

### [Diehl et al., 2005]
Diehl M., Bock H.G., Schlöder J.P., 2005. *A real-time iteration scheme for
nonlinear optimization in optimal feedback control*. SIAM Journal on Control
and Optimization, vol. 43, n° 5, pp. 1714-1736.
doi:10.1137/S0363012902400713.
- **Statut : non vérifiée** (inchangé). Notice Semantic Scholar et listes de
  références concordantes (https://www.semanticscholar.org/paper/05644bba98565e0c493b88eb80c35743e3dbd670) ;
  epubs.siam.org et la résolution du DOI non atteints.
- Usage au chapitre 4 : repère [RÉF. À VÉRIFIER : Diehl et al., 2005].

### [He et Asada, 1993]
He X., Asada H., 1993. *A new method for identifying orders of input-output
models for nonlinear dynamic systems*. Proceedings of the American Control
Conference, 1993.
- **Statut : non vérifiée.** Aucune notice IEEE Xplore ni catalogue trouvé ;
  pages et DOI inconnus.
- Usage : repère [RÉF. À VÉRIFIER : He et Asada, 1993] (choix de l'ordre du
  réseau par les quotients de Lipschitz).

### [Deb, 2000]
Deb K., 2000. *An efficient constraint handling method for genetic
algorithms*. Computer Methods in Applied Mechanics and Engineering, vol. 186,
pp. 311-338. doi:10.1016/S0045-7825(99)00389-8 (selon une liste de
références).
- **Statut : non vérifiée.** Page de l'éditeur non atteinte ; numéro
  discordant (2 ou 2-4).
- Usage : repère [RÉF. À VÉRIFIER : Deb, 2000] (règles de faisabilité du
  PSO-PID).

### Vérifications complémentaires sans changement de statut
- [Lu et al., 2021] : le numéro 7 n'a toujours pas été trouvé sur une notice
  de l'éditeur ; il reste hors de l'entrée.

## 2. Bilan

- Vérifiées : Ioannou et Sun (1996) ; Kingma et Ba (2015).
- Avec réserve : Huang et al. (2006) ; Pao et al. (1994).
- Non vérifiées (repères seulement) : Rosen (1961) ; Diehl et al. (2005) ;
  He et Asada (1993) ; Deb (2000).
