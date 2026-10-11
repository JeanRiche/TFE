# Notes pour la relecture du chapitre 3

Notes retirées du fichier Word du chapitre 3.

## Source : `chapitre3_modelisation_base_commune.md`

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
