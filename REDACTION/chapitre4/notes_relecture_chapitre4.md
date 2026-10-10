# Notes pour la relecture du chapitre 4

Notes retirées du fichier Word du chapitre 4.

## Source : `chapitre4_conception_elm_pid.md`

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
