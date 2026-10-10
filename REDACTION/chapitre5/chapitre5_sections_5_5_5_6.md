## 5.5. Bilan multicritère et discussion

### 5.5.1. Tableau récapitulatif multicritère

Le tableau 5.8 rassemble, pour chaque méthode, les grandeurs des sections 5.3 et 5.4. Les IAE y sont rapportées à celle de Ziegler-Nichols sur le même scénario.

Tableau 5.8 : Récapitulatif multicritère des cinq méthodes.

| **Grandeur** | **ZN** | **PSO-PID** | **Fuzzy-PID** | **ELM-PID** | **PINN-PID** |
| --- | --- | --- | --- | --- | --- |
| IAE/IAE_ZN, S1 | 1 | 0,935 | 1,183 | 0,999 | 0,982 |
| IAE/IAE_ZN, S2 | 1 | 0,719 | 0,856 | 0,847 | 0,858 |
| IAE/IAE_ZN, S3 | 1 | 0,630 | 0,916 | 0,739 | 0,739 |
| IAE/IAE_ZN, S8a | 1 | 0,204 | 0,341 | 0,246 | 0,245 |
| IAE/IAE_ZN, S10 | 1 | 0,056 | 0,130 | 0,122 | 0,094 |
| Dépassement au démarrage, S1 (%) | 13,99 | 7,06 | 27,34 | 13,99 | 13,20 |
| Erreur statique maximale en fin d'essai, cinq scénarios (mV) | 9,23 | 0,01 | 0,03 | 0,01 | 0,02 |
| Temps en butée, S10 de 100 ms à la fin (%) | 0,0 | 0,4 | 0,0 | 0,6 | 0,1 |
| Coût en ligne par appel, banc Python (µs) | 1,39 | 1,43 | 12,74 | 3,59 | 38,93 |
| Travail hors ligne | règle appliquée au modèle moyen, sans optimisation | essaim particulaire : 35 min sur quatre cœurs, cinq graines | règles de Zhao, plages tirées des gains de ZN, sans optimisation | réseau appris sur quatre enregistrements en boucle ouverte (14,8 s) ; ensemble de gains admissibles (181 s) | réseau appris sur des enregistrements Simulink (durée non relevée) ; boîte de gains (32 s) |

Le PSO-PID a le plus petit rapport d'IAE sur les cinq scénarios et le plus petit dépassement. L'ELM-PID et le PINN-PID sont proches l'un de l'autre partout, sauf sur S10. Le Fuzzy-PID et Ziegler-Nichols viennent derrière : le premier est le moins bon au démarrage, le second à charge légère. Sur le temps en butée, en revanche, le PSO-PID et l'ELM-PID sont les moins bons. Le tableau montre aussi ce que coûte chaque approche. Les deux méthodes à gains fixes déplacent tout leur travail hors ligne ; le PSO-PID en fait le plus, et c'est lui qui obtient les meilleurs résultats. Les deux méthodes adaptatives demandent un travail hors ligne plus court, centré sur l'apprentissage d'un réseau, puis un calcul en ligne plus lourd : 2,5 fois celui du PSO-PID pour l'ELM-PID, 27 fois pour le PINN-PID. Nous ne calculons pas d'indice global : le classement qui en sortirait dépendrait des poids donnés à chaque grandeur, pour la raison donnée à la section 5.2.3.

### 5.5.2. Hypothèses confrontées aux résultats

La proposition du travail annonçait des résultats avant tout calcul. Ses phrases ont été réécrites en hypothèses vérifiables le 8 octobre 2026, avant le calcul des résultats de ce chapitre ; l'indice global des versions de mise au point des méthodes (section 5.2.3) était alors déjà connu. Le tableau 5.9 confronte ces hypothèses aux résultats. Le « PID à gains fixes » de la première hypothèse est ici le PID de Ziegler-Nichols.

Tableau 5.9 : Hypothèses de la proposition et résultats.

| **Hypothèse (formulation du 8 octobre 2026)** | **Verdict** | **Éléments** |
| --- | --- | --- |
| H1 : l'ELM-PID « réduirait le dépassement et le temps de rétablissement par rapport au PID à gains fixes », et ses indices « se dégraderaient moins » quand *R* et *V*in varient. | En partie vérifiée | Dépassement identique (13,99 %). Retour dans ±1 V plus rapide sur S3 (0,87 ms contre 1,05 et 1,49 ms). Dégradation bien moindre à charge légère : IAE inférieure de 75 % (S8a) et de 88 % (S10). |
| H2 : l'ELM-PID obtiendrait « le meilleur compromis entre la précision, la rapidité et l'adaptabilité ». | Non vérifiée | Le PSO-PID a la plus petite IAE sur les cinq scénarios, le plus petit dépassement et l'établissement le plus rapide. |
| H3 : le Fuzzy-PID resterait « peu sensible aux perturbations ». | Non vérifiée | Dépassement de 27,34 % sur S1 ; derrière l'ELM-PID et le PINN-PID sur S3, S8a et S10 ; au niveau de l'ELM-PID et du PINN-PID sur S2 seulement. |
| H4 : le PSO-PID « pourrait atteindre des indices proches de ceux des autres méthodes, au prix d'un réglage plus coûteux ». | Non vérifiée pour la performance, vérifiée pour le coût | Il fait mieux que les autres, et pas seulement aussi bien. Son réglage coûte 35 minutes de calcul, mais hors ligne ; en ligne, il coûte autant que Ziegler-Nichols (1,43 contre 1,39 µs par appel). |

### 5.5.3. Rôle réel du réseau ELM et limites

Dans l'ELM-PID, le réseau sert au gradient de la boucle d'adaptation : il fournit le jacobien *J*(*n*) = ∂ŷ/∂d̄, sensibilité de la moyenne de la tension mesurée sur une fenêtre de 0,5 ms à la moyenne du rapport cyclique (équation (4.5)). Il est en outre mis à jour en ligne par l'algorithme OS-ELM [Liang et al., 2006]. Pour mesurer ce que ces deux éléments apportent, nous avons comparé l'ELM-PID à deux variantes déjà définies lors de sa mise au point (section 4.4.4) : l'une remplace le jacobien du réseau par une constante, l'autre supprime la mise à jour en ligne. Les critères et les prévisions ont été écrits avant le calcul, et le verdict suit la règle de séparation de la section 5.2.3.

Le jacobien constant augmente l'IAE de 1,09 % sur S2, de 1,82 % sur S3 et de 2,64 % sur S8a, et ces écarts sont séparés dans les trois cas. Sur S10, il fait au contraire mieux que le réseau au nominal (−9,76 %), mais l'écart n'est pas séparé : il va de −9,76 à +4,01 % selon la version du circuit. Pour comparaison, l'IAE de l'ELM-PID lui-même varie de 7,88 à 8,63 mV·s sur S10 avec ces variations de 0,1 % du circuit. Sans mise à jour en ligne, l'IAE est inchangée sur S2 et S3. Sur S8a, elle baisse de 0,04 % au nominal, écart séparé : sans OS-ELM, la méthode fait très légèrement mieux. Sur S10, l'écart nominal est de −0,90 %, non séparé.

Les prévisions sont justes pour la mise à jour en ligne : écart nul sur S2 et S3, inférieur à 0,1 % sur S8a, inférieur à 2 % sur S10. Sur S8a, cette borne de 0,1 % ne tient qu'au nominal : l'écart atteint −0,38 % dans une des versions du circuit. Elles sont justes aussi pour le jacobien constant sur S2, S3 et S8a (+1 à +3 %), dont la séparation avait été annoncée incertaine et s'est vérifiée dans les trois cas. Une prévision est fausse : sur S10, le jacobien constant fait mieux que le réseau au nominal, cas que les critères écrits avant le calcul classaient comme une prévision fausse.

Ces résultats s'accordent avec ce que l'on sait du réseau. Sur 4 615 fenêtres de contrôle, le jacobien vrai du convertisseur, calculé sur le banc (section 4.3.2), varie avec la charge, de 11,2 V par unité de rapport cyclique (médiane, 4 à 6 Ω) à 15,8 V (50 à 99 Ω). Celui du réseau reste autour de 11 V (médianes de 11,06 à 11,44 V selon la classe de charge), et la corrélation entre les logarithmes du jacobien du réseau et du jacobien vrai est de −0,04. Le réseau ne reçoit que des moyennes par fenêtre : celles de la tension mesurée sur les deux fenêtres précédentes, celles du rapport cyclique sur la fenêtre courante et les deux précédentes. Avec ces seules entrées, la charge n'est pas observable à l'échelle d'une fenêtre de 0,5 ms. Le réseau agit donc comme un identificateur qui donne à la boucle le signe et l'ordre de grandeur de ∂ŷ/∂d̄ ; ce n'est pas un estimateur de l'état du convertisseur.

La forme de la loi d'adaptation explique pourquoi un jacobien aussi peu précis suffit. À la fin de chaque fenêtre, les multiplicateurs des gains suivent le gradient normalisé de la loi (4.7), repris de [Lu et al., 2021]. Dans cette loi, la sensibilité *φ* de la tension moyenne aux multiplicateurs est le produit du jacobien *J* par le vecteur *s* ⊙ *K*ZN, qui ne dépend que de l'erreur, et le pas est divisé par *ε* + |*φ*|², avec *ε* = 10⁻³. Quand *ε* est négligeable, le terme de gradient vaut à peu près *η* ē (*s* ⊙ *K*ZN) / (*J* |*s* ⊙ *K*ZN|²) : le jacobien n'en fixe que le signe et la longueur. Une erreur de 30 % sur *J* change la longueur du pas, pas sa direction. Le terme d'inertie de (4.7), de coefficient *α* = 0,001, ne fait que prolonger le pas précédent.

Le résultat de l'ELM-PID tient donc surtout à sa boucle d'adaptation, reprise de [Lu et al., 2021] et modifiée : gradient normalisé, porte fermée pendant la saturation de la commande, projection des gains sur un ensemble admissible. Près du point nominal, le jacobien du réseau apporte 1 à 3 %, de façon reproductible ; sa mise à jour en ligne n'apporte rien de mesurable. Sur S10, ni l'un ni l'autre ne se distingue de la sensibilité de la méthode aux variations du circuit.

Plusieurs limites encadrent ces conclusions. L'adaptation est bloquée tant que la commande est saturée, donc pendant toute la montée en tension. Sa boucle, par fenêtres de 0,5 ms, est trop lente pour agir pendant une perturbation brève : la porte se rouvre 1,5 à 2 ms après l'événement, quand le PID a déjà ramené l'erreur moyenne sous la zone morte. Tout repose sur la simulation d'un seul convertisseur, sans essai sur montage réel. La règle de séparation dit si un ordre est reproductible sous des variations de 0,1 % de *L* et de *C* ; ce n'est pas une étude de tolérance des composants. Les temps de calcul sont ceux de Python interprété. S2 s'écarte de l'article de Lu et al. en appliquant F1 à la consigne. Enfin, le PSO-PID a été réglé sur un modèle du même convertisseur, sur d'autres points de fonctionnement mais avec les mêmes familles de perturbations ; son avance suppose que ce modèle soit disponible et juste.

## 5.6. Conclusion

Ce chapitre a comparé en simulation, sur un même convertisseur Buck et un même bloc PID, l'ELM-PID au PID de Ziegler-Nichols dont il part, puis au PSO-PID, au Fuzzy-PID et au PINN-PID, sur cinq scénarios et selon des critères fixés avant le calcul.

Face à Ziegler-Nichols, l'ELM-PID ne fait jamais moins bien. Son avantage est nul au démarrage, de 15 à 26 % près du point nominal, et de 75 à 88 % à charge légère, là où le réglage de Ziegler-Nichols ne convient plus. Une grande part de cet avantage vient d'un seul ajustement des gains à la fin du démarrage ; l'adaptation poursuivie réduit encore l'IAE de 41 % sur S10. Face aux méthodes avancées, le PSO-PID, à gains fixes réglés hors ligne, a la meilleure IAE sur les cinq scénarios. L'ELM-PID fait jeu égal avec le PINN-PID sauf sur S10, pour un calcul environ dix fois moins coûteux, et devance le Fuzzy-PID sauf sur S2, où ils sont au même niveau.

L'ELM-PID peut donc revendiquer d'améliorer toujours son point de départ, d'égaler le PINN-PID à moindre coût, et de se passer d'un réglage hors ligne des gains, au prix d'un réseau appris hors ligne. Il ne peut pas revendiquer de battre un PID fixe bien réglé, ni attribuer ses résultats à son réseau : ils viennent surtout de sa boucle d'adaptation.

Plusieurs questions restent ouvertes : la tenue des méthodes face aux tolérances réelles des composants, leur temps d'exécution sur une cible embarquée, une adaptation assez rapide pour agir pendant les perturbations. Le chapitre 6 les reprend.

---

## Notes pour la relecture (à retirer)

### Chiffres et leur source

| Chiffre | Source |
| --- | --- |
| Rapports IAE/IAE_ZN du tableau 5.8 | calculés sur les IAE nominales de `COMPARAISON/separation/separation_resultats.json` (identiques à `metriques_banc.csv` à 2,7e-10 près) |
| Dépassements S1 ; erreur statique en fin d'essai (maximum des cinq valeurs « 10 dernières ms », moyenne absolue) ; temps en butée sur S10 ; coût par appel | `COMPARAISON/metriques/metriques_banc.md` (résumé, tableaux S1 et S10, tableaux d'erreur en régime permanent, coût de calcul) |
| PSO hors ligne : 35 minutes, cinq graines, quatre cœurs ; population 50, 100 itérations | `PSO_PID/criteres_pso_pid.txt` §2 et §6 |
| ELM hors ligne : apprentissage 14,8 s ; ensemble admissible 181 s ; quatre enregistrements Simulink en boucle ouverte ; moindres carrés régularisés C = 0,1 | `ELM_PID/entrainement_elm_resultats.json` (`duree_s`) ; `ensemble_gains_elm_sortie_console.txt` (dernière ligne) ; `criteres_elm_pid.txt` §2 ; `entrainement_elm.py`, lignes 284-285 |
| PINN hors ligne : réseau tanh appris sur des enregistrements Simulink (durée non relevée) ; boîte de gains 32 s | `PINN_PID/criteres_pinn_pid.txt` §2.4 et 2.5 ; `boite_gains_pinn_sortie_console.txt`, ligne 37 |
| Fuzzy : règles de Zhao, plages de 0,533 à 1 fois P et de 1,067 à 2 fois D tirées des gains de ZN | `FUZZY_PID/criteres_fuzzy_pid.txt`, écart 1 |
| Hypothèses H1 à H4 (citations) | `REDACTION/proposition_resultats_en_hypotheses.md` §1.1 à 1.3 ; commit 4cb68ec du 8 octobre 2026 à 05:25, avant ceux de S10 (09:42) et des métriques (13:23) |
| S3, retours 0,87 / 1,05 et 1,49 ms | `metriques_banc.md`, S3 par événement |
| Ablations : +1,09 / +1,82 / +2,64 % ; S10 −9,76 (−9,76 à +4,01) ; sans OS-ELM 0 / 0 / −0,04 (−0,38 à −0,04) / −0,90 (−9,46 à +8,81) ; ELM 7,88 à 8,63 ; prévisions justes et fausses | `COMPARAISON/ablation_S10/criteres_ablation.txt` §3 et §5 ; `ablation_sortie_console.txt` |
| Jacobien : 4 615 fenêtres ; vrai 11,2 (4-6 Ω) à 15,8 (50-99 Ω) ; réseau 11,06 à 11,44 (médianes) ; corrélation de ln *J* (réseau) et ln *J* vrai −0,043 ; entrées du réseau ȳ(n−1), ȳ(n−2), d̄(n), d̄(n−1), d̄(n−2) (moyennes par fenêtre, `criteres_elm_pid.txt` §2) ; charge non observable | `ELM_PID/criteres_elm_pid.txt` §5 ; `ELM_PID/entrainement_elm_sortie_console.txt`, étape 5 (lignes 65 à 69) |
| Gradient normalisé (NLMS), porte de saturation (M1), projection (M2, M3) ; loi (4.7) du chapitre 4 (l'ancienne équation (5.4) est retirée), *η* = 0,5, *ε* = 1e-3, *α* = 0,001, *φ* = *J* (*s* .* *K*_ZN) ; *J* = ∂ŷ/∂d̄, équation (4.5) | `criteres_elm_pid.txt` §2, §4 (M4) ; explication du rôle de *J* (30 %) : `ELM_PID_INCREMENTAL/criteres_elm_pid.txt` §9, point 3 (même loi de gradient, gardée telle quelle en option B) |
| Facteurs 2,5 et 27 par rapport au PSO-PID : 3,59/1,43 = 2,51 et 38,93/1,43 = 27,2 (l'ancienne version donnait 2,6 et 28, qui sont les rapports à Ziegler-Nichols : 3,59/1,39 = 2,58 et 38,93/1,39 = 28,0) | `metriques_banc.md`, coût de calcul |
| Porte rouverte 1,5 à 2 ms après l'événement (1,5 ms après la fin de la fenêtre saturée) | chapitre 4, section 4.4.2 et figure 4.3 ; `banc_elm_pid.py`, en-tête point 4 (porte sur n, n−1, n−2) ; `criteres_elm_pid.txt` §8 et §9, point 3 (« 1.5 ms plus tard », « rattrapée en 1.5 ms ») |
| « 15 à 26 % », « 75 à 88 % », « 41 % », « dix fois » | sections 5.3 et 5.4 (`metriques_banc.md`, `resultats_S10.json`) |

### Citations

- [Liang et al., 2006] : vérifiée. [Lu et al., 2021] : vérifiée avec réserve.

### Corrections et précisions par rapport à la commande

- Plage du jacobien du réseau « 9,6 à 13,9 V par unité » : ce chiffre se trouve seulement dans `ELM_PID_INCREMENTAL/criteres_elm_pid.txt` (ligne 283), mesuré avec la version incrémentale, pas avec l'option B. Il n'est pas repris. Le texte utilise les médianes du réseau par classe de charge (11,06 à 11,44 V), tirées de l'entraînement, qui ne dépendent pas de la version. Les valeurs 11,2 à 15,8 et la corrélation −0,04 sont confirmées.
- Datation des hypothèses : la réécriture date du 8 octobre 2026, avant les résultats de ce chapitre, mais l'indice global (J dans le dépôt) des versions de mise au point (dont le PSO-PID à 0,714) était déjà connu. Le texte le dit.
- H2 : le PSO-PID ne domine pas sur toutes les grandeurs du tableau 5.8. Il est moins bon que Ziegler-Nichols et le Fuzzy-PID sur le temps en butée de S10 (0,4 % contre 0,0 %), et l'ELM-PID a la même erreur statique maximale que lui. Le verdict « non vérifiée » vaut pour les grandeurs de l'hypothèse elle-même (précision, rapidité, adaptabilité).
- H3 : sur S2, le Fuzzy-PID est au niveau de l'ELM-PID et du PINN-PID, et il devance Ziegler-Nichols partout sauf sur S1. Le verdict « non vérifiée » est relatif aux autres méthodes avancées.
- H4 : la proposition prévoyait de mesurer le coût par le nombre de simulations ; seul le temps total (35 minutes) est publié. La population (50) et le nombre d'itérations (100) sont connus, mais le nombre exact de simulations n'est pas relevé dans le dépôt.
- 5.6 : « ils viennent surtout de sa boucle d'adaptation » est une conclusion de 5.5.3 (jacobien : 1 à 3 % ; OS-ELM : rien de mesurable).

### Repères

- Aucune figure. Tableaux 5.8 et 5.9. Aucune équation dans 5.5 depuis le 10 octobre : l'ancienne (5.4) est remplacée par un renvoi à la loi (4.7). Le chapitre 5 garde les équations (5.1) à (5.3).

### Harmonisation du 10 octobre 2026 (cohérence chapitres 5 et 6)

- Notations : le dépassement n'a plus de symbole (*D* reste le gain dérivé) ; l'indice global de mise au point n'est plus noté J (5.2.3, 5.5.2), pour ne pas le confondre avec le jacobien *J* de (4.5). Dans le dépôt, il s'appelle toujours J.
- Anti-emballement : « intégration conditionnelle (blocage de l'intégrateur en butée) » en 5.2.1, puis « intégration conditionnelle », comme au chapitre 6. Le code (`banc_commun.py`) parle de « clamping ».
- PINN-PID : « boîte de gains » partout (5.4.1 disait « ensemble de gains admissibles ») ; « ensemble admissible » est réservé à l'ELM-PID.
- « Porte » définie à sa première occurrence (5.3.1).
- 5.5.1 : « facteur 2,6 et 28 par rapport au PSO-PID » remplacé par « 2,5 fois et 27 fois celui du PSO-PID » (3,59/1,43 = 2,51 ; 38,93/1,43 = 27,2 ; 2,6 et 28 étaient les rapports à Ziegler-Nichols, 1,39 µs).
- Tableau 5.6 : réductions arrondies à l'unité, 41 % et 61 % (`resultats_S10.json`, `gain_adaptation` = 0,4089 et 0,6146 ; la console affiche +40,9 et +61,5 %), comme dans le texte des chapitres 5 et 6.
- 5.5.3 : entrées exactes du réseau (`criteres_elm_pid.txt` §2 : ȳ(n−1), ȳ(n−2), d̄(n), d̄(n−1), d̄(n−2), moyennes par fenêtre) ; −0,04 est la corrélation de ln *J* du réseau et ln *J* vrai (`entrainement_elm_sortie_console.txt`, étape 5 : −0,043). Même formulation en 6.3.4.

### Alignement sur le chapitre 4 (10 octobre 2026)

- Équation (5.4) retirée : elle écrivait *φ* = *J* *s* et omettait l'inertie. 5.5.3 renvoie à la loi (4.7) (*φ*(*n*) = *J*(*n*) (*s*(*n*) ⊙ *K*ZN), terme *α* (*x*(*n*) − *x*(*n* − 1)), *α* = 0,001) et n'en garde que l'argument sur le signe et la longueur du pas. (5.4) était la dernière équation du chapitre : aucune renumérotation. La phrase « change la longueur du pas de 30 % » devient « change la longueur du pas » : avec *J* au dénominateur, une erreur de 30 % change la longueur d'un facteur 1/1,3 à 1/0,7, pas de 30 % exactement.
- Tension mesurée : « ∂*v*o/∂*d* » et « moyennes de la tension de sortie » remplacés par *J*(*n*) = ∂ŷ/∂d̄ (équation (4.5)) et « tension mesurée » (5.5.3) ; « sensibilité vraie » devient « jacobien vrai » (section 4.3.2).
- Réouverture de la porte : 1,5 ms après la fin de la fenêtre saturée, soit 1,5 à 2 ms après l'événement (5.3.2 et 5.5.3). 5.5.3 disait « une perturbation brève, que le PID rattrape en environ 1,5 ms » ; le retour dans ±1 V sur S3 prend 0,87 ms (ELM-PID), la phrase parle maintenant de la réouverture de la porte.
- Tableau 5.8 : apprentissage du réseau 14,8 s (au lieu de 15 s), comme au chapitre 4 (`entrainement_elm_resultats.json`, `duree_s`).
- 5.4.1 : premier essai de réglage du PSO-PID « échelon de charge de 7 à 4,5 Ω » (E1 du chapitre 4, `criteres_pso_pid.txt`), au lieu de « à 7 Ω ».
- Renvois précis ajoutés : porte (section 4.4.2) en 5.3.1 ; variantes d'ablation (section 4.4.4) en 5.5.3.
