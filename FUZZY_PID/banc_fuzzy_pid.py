# =============================================================================
# banc_fuzzy_pid.py
#
# VERSION
#   1 (6 octobre 2026), Fuzzy-PID sur la base commune v2 (banc commun 2.1).
#   Remplace entierement l'ancien dossier FUZZY (ancien circuit, increments
#   de gains sans fuite, facteurs d'echelle regles sur les essais).
#
# OBJECTIF
#   Faire tourner le Fuzzy-PID sur le banc commun, sur les onze essais, a cote
#   des references (PID de Ziegler-Nichols, meilleur PID fige, version R0),
#   mesurer ce que chaque piece apporte (ablations fixees dans
#   criteres_fuzzy_pid.txt) et ecrire ce que Simulink doit retrouver :
#     - predictions_banc_fuzzy_pid.json : resultats attendus du Fuzzy-PID
#       sur les onze essais, au format des autres fichiers de predictions
#       (lu par Simuler_Fuzzy_PID.m) ;
#     - fuzzy_pid_reglages.mat : les reglages du bloc MATLAB (boite, seuils,
#       tables), lus par fuzzy_pid_adaptatif.m, pour que le bloc et ce banc
#       utilisent les memes nombres ;
#     - reference_rejeu_fuzzy_pid.mat : erreur, commande et gains pas par pas
#       sur quatre essais, que Tester_Fuzzy_PID_Rejeu.m rejoue dans le bloc.
#
# LE FUZZY-PID, TEL QU'IL EST CODE ICI ET DANS fuzzy_pid_adaptatif.m
#   A chaque periode Tc = 1/220 000 s, le regulateur recoit l'erreur
#   e = consigne - mesure.
#   1. Loi PID incrementale de Lu et al. (eq. 13-14), terme derive sur
#      l'erreur filtree, exactement comme l'ELM-PID et R0 :
#        g(k) = Tc N (e(k) - ef(k)),   ef(k+1) = ef(k) + Tc N (e(k) - ef(k)),
#        u(k) = sat( u(k-1) + Kp (e(k) - e(k-1)) + Ki e(k) + Kd (g(k) - g(k-1)) ),
#      sat = [0.01 ; 0.99] ; depart u = 0.5 ; premier pas sans a-coup.
#   2. Fenetres de 0.5 ms (110 periodes Tc) : erreur moyenne ebar(n).
#   3. Fin de fenetre : E = ebar(n), dE = ebar(n) - ebar(n-1) (0 a la
#      premiere fenetre). Systeme flou (principe de Zhao, Tomizuka et Isaka,
#      1993) : cinq ensembles NG NP ZE PP PG par entree, points de cassure
#      0.1, 1 et 10 V ; 25 regles, ET = minimum ; conclusions en singletons
#      (0, 0.5, 1) ; moyenne ponderee. Il donne directement theta dans
#      [0 ; 1]^3, la position des gains dans la boite ; K = K_min + theta dK
#      sert pendant la fenetre suivante. Aucun integrateur sur les gains.
#   Detail, justification des seuils et des tables : criteres_fuzzy_pid.txt.
#
# CE QUE LE SCRIPT MESURE (memes grandeurs que Simulink, banc commun 2.1)
#   Pour chaque regulateur et chaque essai : grandeurs de banc_commun.py,
#   cout J du meilleur PID fige (13 rapports a Ziegler-Nichols) et
#   contrainte "tous les evenements reviennent dans la bande".
#
# FICHIERS NECESSAIRES (dans le meme dossier que ce script)
#   banc_commun.py (version 2.1), scenarios_communs.json, scenario_S*.mat,
#   predictions_banc_pid_fige.json, boite_gains_elm.json.
#   Facultatif : banc_elm_pid_resultats.json et banc_pinn_pid_resultats.json
#   (s'ils sont la, leur J est rappele dans la comparaison finale).
#
# CE QUE PRODUIT CE SCRIPT
#   predictions_banc_fuzzy_pid.json, fuzzy_pid_reglages.mat,
#   reference_rejeu_fuzzy_pid.mat, banc_fuzzy_pid_resultats.json,
#   banc_fuzzy_pid.png (tension, gains et courant sur S8b et S9),
#   fuzzy_pid_surfaces.png (les trois surfaces du systeme flou).
#
# BIBLIOTHEQUES NECESSAIRES (pip install numpy scipy matplotlib)
#
# COMMENT LANCER CE SCRIPT
#   python banc_fuzzy_pid.py      (trois a cinq minutes)
#
# ORDRE D'EXECUTION
#   1. ce script ; 2. Tester_Fuzzy_PID_Rejeu.m ; 3. Construction_Fuzzy_PID.m ;
#   4. verifier_modele_fuzzy_pid.py ; 5. Simuler_Fuzzy_PID.m.
# =============================================================================


# %% ETAPE 0 : bibliotheques, reglages et definitions du banc commun

import os                                     # chemins de fichiers
import json                                   # lecture et ecriture au format texte
import time                                   # duree d'execution
import numpy as np                            # calcul numerique
from scipy.io import savemat                  # fichiers .mat
import matplotlib.pyplot as plt               # figures

try:                                          # dossier du script (ou dossier courant dans un notebook)
    DOSSIER_FUZZY = os.path.dirname(os.path.abspath(__file__))
except NameError:
    DOSSIER_FUZZY = os.getcwd()

with open(os.path.join(DOSSIER_FUZZY, "banc_commun.py"), encoding="utf-8") as f:
    SOURCE_BANC = f.read()
MARQUE = "# === FIN DES DEFINITIONS DU BANC COMMUN ==="
if MARQUE not in SOURCE_BANC or "iL_max_dem_A" not in SOURCE_BANC:
    raise RuntimeError("banc_commun.py n'est pas la version 2.1 (observation du courant) : prendre la version a jour.")
exec(SOURCE_BANC[:SOURCE_BANC.index(MARQUE)])  # constantes, essais, Circuit, simuler, grandeurs, PIDClassique

T_DEBUT = time.time()                         # pour la duree totale
ESSAIS = {sc["code"]: sc for sc in SCENARIOS}  # les onze essais, par code
CODES_IAE = ["S1", "S3", "S4", "S5", "S6", "S7a", "S7b", "S8a", "S8b", "S9"]   # IAE de 30 ms a la fin
CODES_DEM = ["S1", "S8a", "S8b"]              # IAE du demarrage (5, 25 et 98 ohms)
K30 = int(round(0.03 / TC))                   # instant 30 ms (numero de pas Tc)
NF = 110                                      # periodes Tc par fenetre de 0.5 ms
CODES_REJEU = ["S1", "S7b", "S8b", "S9"]      # essais rejoues dans le bloc MATLAB

# Boite des gains (boite_gains_elm.py, commune aux trois methodes)
with open(os.path.join(DOSSIER_FUZZY, "boite_gains_elm.json"), encoding="utf-8") as f:
    BOITE = json.load(f)
K_MIN = np.array(BOITE["K_min"])              # bord bas [Kp, Ki, Kd]
K_MAX = np.array(BOITE["K_max"])              # bord haut
K_ZN = np.array([PID_P, PID_I * TC, PID_D / TC])   # Ziegler-Nichols, forme incrementale
if np.max(np.abs(np.array(BOITE["K_depart"]) - K_ZN) / K_ZN) > 1e-12:
    raise RuntimeError("boite_gains_elm.json n'a pas ete calcule avec les gains de Ziegler-Nichols de ce banc.")

# Reglages du systeme flou (criteres_fuzzy_pid.txt, fixes avant le calcul)
SEUILS = np.array([0.1, 1.0, 10.0])           # points de cassure (V) : zone morte, bande, ecart d'evenement
Z, M, G = 0.0, 0.5, 1.0                       # singletons de sortie
# Lignes : E = NG NP ZE PP PG ; colonnes : dE = NG NP ZE PP PG
TABLE_P = np.array([[G, G, G, G, G],
                    [M, M, M, M, M],
                    [M, Z, Z, Z, M],
                    [M, M, M, M, M],
                    [G, G, G, G, G]])
TABLE_I = np.array([[G, G, G, M, Z],
                    [G, G, G, M, Z],
                    [G, G, G, G, G],
                    [Z, M, G, G, G],
                    [Z, M, G, G, G]])
TABLE_D = np.array([[Z, Z, Z, M, G],
                    [Z, Z, Z, M, G],
                    [M, Z, Z, Z, M],
                    [G, M, Z, Z, Z],
                    [G, M, Z, Z, Z]])
TABLES = np.stack([TABLE_P, TABLE_I, TABLE_D])   # 3 x 5 x 5
THETA_ZN = np.minimum(np.maximum((K_ZN - K_MIN) / (K_MAX - K_MIN), 0.0), 1.0)
if np.max(np.abs(TABLES[:, 2, 2] - THETA_ZN)) > 1e-12:
    raise RuntimeError("La regle (ZE, ZE) ne redonne pas Ziegler-Nichols : tables ou boite incoherentes.")

print(f"Boite : Kp de {K_MIN[0]:.6f} a {K_MAX[0]:.6f}, Ki de {K_MIN[1]:.4e} a {K_MAX[1]:.4e}, "
      f"Kd de {K_MIN[2]:.4f} a {K_MAX[2]:.4f} ; Ziegler-Nichols en theta = {THETA_ZN.tolist()}.")
print(f"Systeme flou : seuils {SEUILS.tolist()} V, 25 regles, ET minimum, singletons, moyenne ponderee.")

# Meilleur PID fige (deuxieme reference, oracle)
with open(os.path.join(DOSSIER_FUZZY, "predictions_banc_pid_fige.json"), encoding="utf-8") as f:
    GAINS_FIGE = json.load(f)["gains"]


def titre(texte):
    """Bandeau de titre dans la console."""
    print("\n" + "=" * 78 + "\n " + texte + "\n" + "=" * 78)


# %% ETAPE 1 : le systeme flou, la loi de Lu (R0) et le Fuzzy-PID (copie de fuzzy_pid_adaptatif.m)

TCN = TC * PID_N                              # Tc x N du filtre de derivee (meme produit dans le bloc MATLAB)


def appartenances(x, s):
    """Degres d'appartenance de x aux cinq ensembles [NG, NP, ZE, PP, PG],
    points de cassure s = [a, b, c] (memes formules, meme ordre que
    appartenances dans fuzzy_pid_adaptatif.m)."""
    a, b, c = s
    ax = abs(x)
    if ax <= a:
        ze, p, gr = 1.0, 0.0, 0.0
    elif ax < b:
        ze = (b - ax) / (b - a)
        p, gr = (ax - a) / (b - a), 0.0
    elif ax < c:
        ze = 0.0
        p, gr = (c - ax) / (c - b), (ax - b) / (c - b)
    else:
        ze, p, gr = 0.0, 0.0, 1.0
    if x >= 0:
        return [0.0, 0.0, ze, p, gr]
    return [gr, p, ze, 0.0, 0.0]


def inference(E, dE, tables, s):
    """theta = sortie du systeme flou pour (E, dE) : ET minimum sur les 25
    regles, moyenne ponderee des singletons (regles parcourues ligne par
    ligne, comme dans le bloc MATLAB)."""
    mE, mD = appartenances(E, s), appartenances(dE, s)
    num = np.zeros(3)
    den = 0.0
    for i in range(5):
        for j in range(5):
            w = min(mE[i], mD[j])
            if w > 0.0:
                num = num + w * tables[:, i, j]
                den = den + w
    return num / den


class LoiLu:
    """Loi incrementale de Lu a derivee filtree, gains figes (version R0).
    Memes operations, dans le meme ordre, que l'etape 1 du Fuzzy-PID."""

    def __init__(self, K):
        self.Kp, self.Ki, self.Kd = (float(x) for x in K)   # gains figes
        self.u = 0.5                          # commande de depart
        self.premier = True                   # premier pas : sans a-coup

    def pas(self, e):
        if self.premier:
            self.e1, self.ef, self.g1, self.premier = e, e, 0.0, False
        g = TCN * (e - self.ef)                           # derivee filtree (x Tc)
        brut = self.u + self.Kp * (e - self.e1) + self.Ki * e + self.Kd * (g - self.g1)
        u = min(max(brut, D_MIN), D_MAX)                  # seule saturation du rapport cyclique
        self.ef = self.ef + TCN * (e - self.ef)           # filtre, Forward Euler
        self.e1, self.g1, self.u = e, g, u
        return u


class FuzzyPID:
    """Copie Python de fuzzy_pid_adaptatif.m (memes reglages, memes noms,
    meme ordre des operations : Tester_Fuzzy_PID_Rejeu.m compare les deux pas
    par pas). Les arguments servent aux ablations ; leurs valeurs par defaut
    sont celles du bloc."""

    def __init__(self, tables=TABLES, echelle=1.0, sans_dE=False):
        self.tables = np.array(tables, dtype=float)
        self.s = SEUILS * echelle
        self.sans_dE = sans_dE
        self.dK = K_MAX - K_MIN
        self.theta = THETA_ZN.copy()          # depart a Ziegler-Nichols
        self.K = K_MIN + self.theta * self.dK
        self.u, self.premier = 0.5, True
        self.cpt, self.se, self.eb1, self.nfen = 0, 0.0, 0.0, 0
        self.journal = []                     # une ligne par fenetre
        self.K_pas = []                       # gains utilises a chaque pas

    def pas(self, e):
        self.K_pas.append(self.K)             # gains utilises pour ce pas
        if self.premier:
            self.e1, self.ef, self.g1, self.premier = e, e, 0.0, False
        g = TCN * (e - self.ef)
        brut = self.u + self.K[0] * (e - self.e1) + self.K[1] * e + self.K[2] * (g - self.g1)
        u = min(max(brut, D_MIN), D_MAX)
        self.ef = self.ef + TCN * (e - self.ef)
        self.e1, self.g1, self.u = e, g, u
        self.se += e
        self.cpt += 1
        if self.cpt >= NF:
            self.fin_de_fenetre()
        return u

    def fin_de_fenetre(self):
        eb = self.se / NF                     # erreur moyenne de la fenetre
        dE = 0.0 if (self.nfen == 0 or self.sans_dE) else eb - self.eb1
        self.theta = inference(eb, dE, self.tables, self.s)
        self.K = K_MIN + self.theta * self.dK
        self.journal.append({"E": eb, "dE": dE, "theta": self.theta.copy(), "K": self.K.copy(),
                             "hors_ZN": bool(np.max(np.abs(self.theta - THETA_ZN)) > 0.0)})
        self.eb1 = eb
        self.nfen += 1
        self.cpt, self.se = 0, 0.0


# Controle 1 : quelques points du systeme flou calcules a la main
for (E, dE, attendu) in ((0.0, 0.0, [0, 1, 0]), (0.05, -0.08, [0, 1, 0]), (20.0, 0.0, [1, 1, 0]),
                         (20.0, -20.0, [1, 0, 1]), (-20.0, 20.0, [1, 0, 1]), (0.0, 20.0, [0.5, 1, 0.5]),
                         (0.55, 0.0, [0.25, 1, 0])):
    th = inference(E, dE, TABLES, SEUILS)
    if np.max(np.abs(th - np.array(attendu, float))) > 1e-12:
        raise RuntimeError(f"Systeme flou : ({E}, {dE}) donne {th}, attendu {attendu}.")
print("Controle du systeme flou : sept points calcules a la main retrouves.")


# %% ETAPE 2 : evaluation d'un regulateur sur les onze essais

def evaluer(fabrique, codes=None):
    """Simule un nouveau regulateur (fabrique()) sur chaque essai et renvoie,
    par essai : grandeurs du banc commun, IAE du demarrage, retours, et le
    regulateur (pour son journal)."""
    res = {}
    for code in (codes or list(ESSAIS)):
        reg = fabrique()
        sim = simuler(reg, ESSAIS[code])
        o = grandeurs(sim, ESSAIS[code])
        e = sim["consigne"] - sim["v"]
        res[code] = {"o": o, "IAE_dem": float(np.sum(np.abs(e[:K30])) * TC),
                     "revenus": bool(all(ev["revenu"] for ev in o["evenements"])), "reg": reg, "sim": sim}
    return res


def termes(res):
    """Les 13 termes du cout du meilleur PID fige."""
    return np.array([res[c]["o"]["IAE"] for c in CODES_IAE] + [res[c]["IAE_dem"] for c in CODES_DEM])


class PIDParallele(PIDClassique):
    """PID du bloc Simulink (forme Parallel, clamping) avec d'autres gains P, I, D."""

    def __init__(self, P, I, D):
        super().__init__()
        self.P, self.I, self.D = P, I, D

    def pas(self, e):
        derivee = PID_N * (self.D * e - self.xF)
        u = self.P * e + self.xI + derivee
        u_sat = min(max(u, D_MIN), D_MAX)
        entree_I = self.I * e
        if not ((u != u_sat) and (np.sign(entree_I) == np.sign(u - u_sat))):
            self.xI += TC * entree_I
        self.xF += TC * derivee
        return u_sat


titre("ETAPE 2 : les references")
REF = {}
REF["Ziegler-Nichols"] = evaluer(lambda: PIDClassique())
REF["meilleur PID fige"] = evaluer(lambda: PIDParallele(GAINS_FIGE["P"], GAINS_FIGE["I"], GAINS_FIGE["D"]))
T_ZN = termes(REF["Ziegler-Nichols"])
J_FIGE = float(np.mean(termes(REF["meilleur PID fige"]) / T_ZN))
print(f"  Meilleur PID fige : J = {J_FIGE:.3f} (recherche_pid_fige.py : 0.738).")


# %% ETAPE 3 : version R0 et Fuzzy-PID sur les onze essais

titre("ETAPE 3 : version R0 (gains de Ziegler-Nichols figes) et Fuzzy-PID")


def bilan(nom, res):
    """Cout J, retours et une ligne par essai."""
    J = float(np.mean(termes(res) / T_ZN))
    non = [c for c in CODES_IAE if not res[c]["revenus"]]
    print(f"\n  {nom} : J = {J:.3f} ; {'tous les evenements reviennent' if not non else 'pas revenus : ' + ', '.join(non)}")
    for code, r in res.items():
        o = r["o"]
        ligne = (f"    {code:4s} depassement {o['depassement_pct']:5.1f} %, IAE {o['IAE'] * 1e3:7.2f} mV.s, "
                 f"efficace {o['e_eff_V'] * 1e3:7.1f} mV, |dd| {o['dd_moyen']:.4f}, iL crete {o['iL_max_dem_A']:5.1f} A")
        if hasattr(r["reg"], "journal"):
            jr = r["reg"].journal
            Kf = jr[-1]["K"] / K_ZN
            ligne += (f" ; hors ZN sur {sum(x['hors_ZN'] for x in jr):3d} fenetres sur {len(jr)}, "
                      f"gains finaux x({Kf[0]:.2f}, {Kf[1]:.2f}, {Kf[2]:.2f})")
        print(ligne)
    return J


R0 = evaluer(lambda: LoiLu(K_ZN))
J_R0 = bilan("R0", R0)
FZ = evaluer(lambda: FuzzyPID())
J_FZ = bilan("Fuzzy-PID", FZ)

# Controle 2 : avec la regle (ZE, ZE) partout, le Fuzzy-PID redonne exactement R0
TABLES_ZN = np.broadcast_to(THETA_ZN[:, None, None], (3, 5, 5)).copy()
fige = evaluer(lambda: FuzzyPID(tables=TABLES_ZN), ["S1", "S8b"])
ecart_r0 = max(float(np.max(np.abs(fige[c]["sim"]["d"] - R0[c]["sim"]["d"]))) for c in fige)
print(f"\n  Controle : Fuzzy-PID a tables Ziegler-Nichols contre R0, ecart maximal sur d : {ecart_r0:.1e}.")
if ecart_r0 > 1e-12:
    raise RuntimeError("Avec des tables Ziegler-Nichols, le Fuzzy-PID ne redonne pas la loi R0.")

print("\n  Evenements du Fuzzy-PID sur S3, S4, S5, S8a, S8b et S9 :")
for code in ("S3", "S4", "S5", "S8a", "S8b", "S9"):
    for ev, ev0 in zip(FZ[code]["o"]["evenements"], R0[code]["o"]["evenements"]):
        etat = ("reste dans la bande" if ev["reste_dans_bande"] else
                f"retour en {ev['t_retour_ms']:.2f} ms" if ev["revenu"] else "PAS REVENU")
        print(f"    {code:4s} a {ev['t_ms']:6.1f} ms : ecart max {ev['e_max_V']:6.2f} V (R0 {ev0['e_max_V']:6.2f}), "
              f"IAE {ev['IAE'] * 1e3:7.2f} mV.s (R0 {ev0['IAE'] * 1e3:7.2f}), crete a crete en fin "
              f"{ev['e_crete_a_crete_fin_V']:5.2f} V (R0 {ev0['e_crete_a_crete_fin_V']:5.2f}), {etat}")


# %% ETAPE 4 : ablations (liste fixee dans criteres_fuzzy_pid.txt)

titre("ETAPE 4 : ce que chaque piece apporte (ablations)")
TABLES_KP = TABLES.copy()
TABLES_KP[1], TABLES_KP[2] = THETA_ZN[1], THETA_ZN[2]   # Ki et Kd figes a Ziegler-Nichols
ABLATIONS = {"Kp seul": {"tables": TABLES_KP},
             "Sans dE": {"sans_dE": True},
             "Univers x0.5": {"echelle": 0.5},
             "Univers x2": {"echelle": 2.0}}
RES_ABL, J_ABL = {}, {}
for nom, modif in ABLATIONS.items():
    RES_ABL[nom] = evaluer(lambda: FuzzyPID(**modif))
    J_ABL[nom] = float(np.mean(termes(RES_ABL[nom]) / T_ZN))
print(f"\n  {'variante':28s} {'J':>6s}  {'non revenus':12s} {'S8a':>7s} {'S8b':>7s} {'S9':>8s} {'S7b eff':>8s} "
      f"{'hors ZN':>8s}")
for nom, res, J in ([("Fuzzy-PID (reglages fixes)", FZ, J_FZ), ("R0", R0, J_R0)]
                    + [(n, RES_ABL[n], J_ABL[n]) for n in ABLATIONS]):
    non = [c for c in CODES_IAE if not res[c]["revenus"]]
    nb = sum(sum(x["hors_ZN"] for x in res[c]["reg"].journal) for c in res) if hasattr(res["S1"]["reg"], "journal") else 0
    print(f"  {nom:28s} {J:6.3f}  {(','.join(non) or '-'):12s} {res['S8a']['o']['IAE'] * 1e3:7.2f} "
          f"{res['S8b']['o']['IAE'] * 1e3:7.2f} {res['S9']['o']['IAE'] * 1e3:8.2f} {res['S7b']['o']['e_eff_V'] * 1e3:8.1f} "
          f"{nb:8d}")
print("  (IAE de 30 ms a la fin en mV.s ; ecart efficace en mV ; hors ZN : total des fenetres sur les onze essais)")


# %% ETAPE 4b : sensibilite a de tres petits ecarts du circuit

titre("ETAPE 4b : sensibilite a de tres petits ecarts du circuit (L ou C a +-0.1 %)")
L_NOM, C_NOM = L_BOB, C_CONV                  # valeurs nominales, retablies a la fin
SENSIBILITE = []
print(f"  {'circuit':12s} {'J Fuzzy-PID':>11s} {'S8b IAE':>8s} {'S8b c-c fin':>12s} {'tous revenus':>13s}")
for nom_p, fl, fc in (("nominal", 1.0, 1.0), ("L - 0.1 %", 0.999, 1.0), ("L + 0.1 %", 1.001, 1.0),
                      ("C - 0.1 %", 1.0, 0.999), ("C + 0.1 %", 1.0, 1.001)):
    L_BOB, C_CONV = L_NOM * fl, C_NOM * fc   # le banc lit ces constantes a chaque nouveau circuit
    r_f = FZ if nom_p == "nominal" else evaluer(lambda: FuzzyPID())
    J_f = float(np.mean(termes(r_f) / T_ZN))
    cc = max(ev["e_crete_a_crete_fin_V"] for ev in r_f["S8b"]["o"]["evenements"])
    rev = all(r_f[c]["revenus"] for c in CODES_IAE)
    SENSIBILITE.append({"circuit": nom_p, "J_fuzzy": J_f, "S8b_IAE": r_f["S8b"]["o"]["IAE"],
                        "S8b_crete_a_crete_fin_max_V": cc, "tous_revenus": rev})
    print(f"  {nom_p:12s} {J_f:11.3f} {r_f['S8b']['o']['IAE'] * 1e3:8.2f} {cc:12.2f} {'oui' if rev else 'NON':>13s}")
L_BOB, C_CONV = L_NOM, C_NOM                  # circuit nominal retabli
J_F_SENS = [x["J_fuzzy"] for x in SENSIBILITE]
print(f"\n  J du Fuzzy-PID entre {min(J_F_SENS):.3f} et {max(J_F_SENS):.3f} selon L ou C a +-0.1 %.")


# %% ETAPE 5 : comparaison avec les references et les previsions

titre("ETAPE 5 : Fuzzy-PID face aux references")
TOUS = {"Ziegler-Nichols": REF["Ziegler-Nichols"], "meilleur PID fige": REF["meilleur PID fige"], "R0": R0,
        "Fuzzy-PID": FZ}
J_TOUS = {nom: float(np.mean(termes(res) / T_ZN)) for nom, res in TOUS.items()}
print("  " + " " * 28 + "".join(f"{nom:>20s}" for nom in TOUS))
print("  " + f"{'cout J':28s}" + "".join(f"{J_TOUS[n]:20.3f}" for n in TOUS))
print("  " + f"{'evenements non revenus':28s}" + "".join(
    f"{(','.join(c for c in CODES_IAE if not TOUS[n][c]['revenus']) or '-'):>20s}" for n in TOUS))
for code in ESSAIS:
    for cle, etiquette, fmt, k in (("depassement_pct", "depassement %", "{:.1f}", 1.0), ("IAE", "IAE mV.s", "{:.2f}", 1e3),
                                   ("e_eff_V", "ecart efficace mV", "{:.1f}", 1e3), ("iL_max_dem_A", "iL crete dem. A", "{:.1f}", 1.0)):
        if cle == "depassement_pct" and code not in ("S1", "S8a", "S8b"):
            continue
        if cle == "iL_max_dem_A" and code not in ("S1", "S8b"):
            continue
        print("  " + f"{code + ' ' + etiquette:28s}" + "".join(f"{fmt.format(TOUS[n][code]['o'][cle] * k):>20s}" for n in TOUS))
print("  " + f"{'activite |dd| (S1)':28s}" + "".join(f"{TOUS[n]['S1']['o']['dd_moyen']:20.4f}" for n in TOUS))
print("  " + f"{'S2 ecart maximal V':28s}" + "".join(f"{TOUS[n]['S2']['o']['e_max_V']:20.2f}" for n in TOUS))

AUTRES = {}                                   # J des autres methodes, si leurs resultats sont dans le dossier
for nom, fichier in (("ELM-PID", "banc_elm_pid_resultats.json"), ("PINN-PID", "banc_pinn_pid_resultats.json")):
    chemin = os.path.join(DOSSIER_FUZZY, fichier)
    if os.path.isfile(chemin):
        with open(chemin, encoding="utf-8") as f:
            AUTRES[nom] = json.load(f).get("J", {})
if AUTRES:
    print("  Rappel des autres methodes (fichiers de resultats presents) : " +
          " ; ".join(f"{n} {', '.join(f'{k} {v:.3f}' for k, v in j.items() if isinstance(v, float))}" for n, j in AUTRES.items()))

# Decomposition du cout : demarrage seul, et sans le demarrage
def decomposition(res):
    r = termes(res) / T_ZN
    return float(np.mean(r[:len(CODES_IAE)])), float(np.mean(r[len(CODES_IAE):]))


print("\n  Decomposition de J (moyenne des 10 IAE apres 30 ms ; moyenne des 3 IAE de demarrage) :")
DECOMP = {}
for nom in TOUS:
    DECOMP[nom] = decomposition(TOUS[nom])
    print(f"    {nom:20s} apres 30 ms {DECOMP[nom][0]:.3f} ; demarrage {DECOMP[nom][1]:.3f}")

print("\n  Previsions de criteres_fuzzy_pid.txt :")
P = {}
P["P1"] = all(abs(FZ[c]["o"]["e_eff_V"] / R0[c]["o"]["e_eff_V"] - 1.0) <= 0.01 for c in ("S7a", "S7b"))
P["P2"] = FZ["S1"]["o"]["depassement_pct"] <= R0["S1"]["o"]["depassement_pct"] + 1e-9
P["P3"] = all(ev["e_max_V"] >= 0.9 * ev0["e_max_V"] for c in ("S3", "S4", "S5")
              for ev, ev0 in zip(FZ[c]["o"]["evenements"], R0[c]["o"]["evenements"]))
cc_s8b = max(ev["e_crete_a_crete_fin_V"] for ev in FZ["S8b"]["o"]["evenements"])
P["P4"] = 0.2 <= cc_s8b <= 2.0
P["P5"] = 0.80 <= J_FZ <= 0.92
P["P6"] = (abs(J_ABL["Kp seul"] - J_FZ) < 0.02 and
           min(abs(J_ABL["Univers x0.5"] - J_FZ), abs(J_ABL["Univers x2"] - J_FZ)) > (max(J_F_SENS) - min(J_F_SENS)))
TEXTE_P = {"P1": f"S7a, S7b a 1 % de R0 : {FZ['S7a']['o']['e_eff_V'] * 1e3:.1f} et {FZ['S7b']['o']['e_eff_V'] * 1e3:.1f} mV",
           "P2": f"depassement S1 {FZ['S1']['o']['depassement_pct']:.2f} % (R0 {R0['S1']['o']['depassement_pct']:.2f} %)",
           "P3": "ecart maximal de S3, S4, S5 a moins de 10 % sous R0",
           "P4": f"S8b crete a crete de fin entre 0.2 et 2 V : {cc_s8b:.2f} V",
           "P5": f"J entre 0.80 et 0.92 : {J_FZ:.3f}",
           "P6": f"Kp seul {J_ABL['Kp seul']:.3f}, univers x0.5 {J_ABL['Univers x0.5']:.3f}, x2 {J_ABL['Univers x2']:.3f}"}
for k in P:
    print(f"    {k} {'juste' if P[k] else 'FAUSSE'} : {TEXTE_P[k]}")


# %% ETAPE 6 : fichiers pour Simulink et MATLAB, resultats et figures

titre("ETAPE 6 : fichiers pour Simulink et MATLAB")
pas_1ms = int(round(1e-3 / TC))               # 220 periodes Tc
# 1. Resultats attendus du Fuzzy-PID (format des autres fichiers de predictions)
predictions = {"version": 2, "Te": TC,
               "regulateur": "Fuzzy-PID (loi de Lu a derivee filtree, systeme flou de criteres_fuzzy_pid.txt, "
                             "boite boite_gains_elm.json)",
               "reglages": {"SEUILS": SEUILS.tolist(), "TABLE_P": TABLE_P.tolist(), "TABLE_I": TABLE_I.tolist(),
                            "TABLE_D": TABLE_D.tolist(), "NF": NF},
               "boite": {"K_min": K_MIN.tolist(), "K_max": K_MAX.tolist(), "K_depart": K_ZN.tolist()},
               "controle": {"ecart_tables_ZN_R0": ecart_r0},
               "essais": {}}
for code, r in FZ.items():
    Kp = np.array(r["reg"].K_pas)             # gains utilises a chaque pas
    predictions["essais"][code] = {"grandeurs": r["o"],
                                   "v_toutes_les_ms": r["sim"]["v"][::pas_1ms].tolist(),
                                   "iL_toutes_les_ms": r["sim"]["iL"][::pas_1ms].tolist(),
                                   "d_moyen_par_ms": [float(np.mean(r["sim"]["d"][i:i + pas_1ms]))
                                                      for i in range(0, len(r["sim"]["d"]) - pas_1ms + 1, pas_1ms)],
                                   "K_toutes_les_ms": Kp[::pas_1ms].tolist()}
with open(os.path.join(DOSSIER_FUZZY, "predictions_banc_fuzzy_pid.json"), "w", encoding="utf-8") as f:
    json.dump(predictions, f, indent=1, allow_nan=False)
print("  predictions_banc_fuzzy_pid.json ecrit.")

# 2. Reglages du bloc MATLAB
savemat(os.path.join(DOSSIER_FUZZY, "fuzzy_pid_reglages.mat"),
        {"K_MIN": K_MIN.reshape(1, 3), "K_MAX": K_MAX.reshape(1, 3), "K_DEPART": K_ZN.reshape(1, 3),
         "SEUILS": SEUILS.reshape(1, 3), "TABLE_P": TABLE_P, "TABLE_I": TABLE_I, "TABLE_D": TABLE_D,
         "NF": float(NF), "TC": TC, "N_FILTRE": PID_N, "D_MIN": D_MIN, "D_MAX": D_MAX, "U_DEPART": 0.5,
         "VERSION": 1.0})
print("  fuzzy_pid_reglages.mat ecrit (reglages du bloc).")

# 3. Reference du test de rejeu MATLAB
rejeu = {}
for code in CODES_REJEU:
    r = FZ[code]
    jr = r["reg"].journal
    rejeu[code] = {"e": (r["sim"]["consigne"] - r["sim"]["mesure"]).reshape(-1, 1),
                   "u": r["sim"]["d"].reshape(-1, 1), "K": np.array(r["reg"].K_pas),
                   "theta": np.array([x["theta"] for x in jr]),
                   "E": np.array([x["E"] for x in jr]).reshape(-1, 1),
                   "dE": np.array([x["dE"] for x in jr]).reshape(-1, 1)}
# Points de controle du systeme flou seul (grille de E et dE, dont les points de cassure)
grille = np.array([-30, -10, -5.5, -1, -0.55, -0.1, -0.05, 0, 0.05, 0.1, 0.55, 1, 5.5, 10, 30], float)
pts = np.array([[a, b] for a in grille for b in grille])
rejeu["FIS_ENTREES"] = pts
rejeu["FIS_SORTIES"] = np.array([inference(a, b, TABLES, SEUILS) for a, b in pts])
savemat(os.path.join(DOSSIER_FUZZY, "reference_rejeu_fuzzy_pid.mat"), rejeu, do_compression=True)
print(f"  reference_rejeu_fuzzy_pid.mat ecrit ({', '.join(CODES_REJEU)}, et {len(pts)} points du systeme flou).")


# 4. Resultats pour le memoire
def resume_essais(res):
    return {c: {"grandeurs": res[c]["o"], "IAE_dem": res[c]["IAE_dem"], "revenus": res[c]["revenus"]} for c in res}


sortie = {"version": 1, "reglages": predictions["reglages"], "boite": predictions["boite"],
          "J": J_TOUS, "J_ablations": J_ABL, "sensibilite": SENSIBILITE, "decomposition": DECOMP,
          "previsions": {k: {"juste": bool(P[k]), "detail": TEXTE_P[k]} for k in P},
          "references": {n: resume_essais(TOUS[n]) for n in TOUS},
          "ablations": {n: resume_essais(RES_ABL[n]) for n in RES_ABL},
          "gains_fuzzy": {c: [x["K"].tolist() for x in FZ[c]["reg"].journal] for c in FZ},
          "fenetres_hors_ZN": {c: int(sum(x["hors_ZN"] for x in FZ[c]["reg"].journal)) for c in FZ},
          "duree_s": round(time.time() - T_DEBUT, 1)}
with open(os.path.join(DOSSIER_FUZZY, "banc_fuzzy_pid_resultats.json"), "w", encoding="utf-8") as f:
    json.dump(sortie, f, indent=1, allow_nan=False, default=lambda x: None)
print("  banc_fuzzy_pid_resultats.json ecrit.")

# 5. Figure : tension, gains et courant sur S8b et S9
fig, axes = plt.subplots(3, 2, figsize=(13, 9), sharex="col")
for col, code in enumerate(("S8b", "S9")):
    for nom, couleur in (("Ziegler-Nichols", "0.6"), ("R0", "tab:orange"), ("meilleur PID fige", "tab:green"),
                         ("Fuzzy-PID", "tab:purple")):
        sim = TOUS[nom][code]["sim"]
        axes[0, col].plot(sim["t"] * 1e3, sim["v"], lw=0.6, color=couleur, label=nom)
        axes[2, col].plot(sim["t"] * 1e3, sim["iL"], lw=0.4, color=couleur)
    axes[0, col].plot(sim["t"] * 1e3, sim["consigne"], "k--", lw=0.6)
    Kp = np.array(FZ[code]["reg"].K_pas) / K_ZN
    t_ms = FZ[code]["sim"]["t"] * 1e3
    for i, nom in enumerate(("Kp", "Ki", "Kd")):
        axes[1, col].plot(t_ms, Kp[:, i], lw=1.0, label=nom)
    axes[0, col].set_ylim(30, 200)
    axes[0, col].set_title(f"{code} : tension de sortie", fontsize=9, loc="left")
    axes[1, col].set_title(f"{code} : gains du Fuzzy-PID (multiples de Ziegler-Nichols)", fontsize=9, loc="left")
    axes[2, col].set_title(f"{code} : courant de la bobine (observe)", fontsize=9, loc="left")
    axes[2, col].set_xlabel("temps (ms)")
    for ax in axes[:, col]:
        ax.grid(alpha=0.3)
axes[0, 0].legend(fontsize=7)
axes[1, 0].legend(fontsize=7)
axes[0, 0].set_ylabel("V")
axes[2, 0].set_ylabel("A")
fig.tight_layout()
fig.savefig(os.path.join(DOSSIER_FUZZY, "banc_fuzzy_pid.png"), dpi=110)
plt.close(fig)
print("  banc_fuzzy_pid.png ecrit.")

# 6. Figure : les trois surfaces du systeme flou (pour le memoire)
ax_v = np.concatenate([-np.logspace(np.log10(30), -2, 120), [0.0], np.logspace(-2, np.log10(30), 120)])
EE, DD = np.meshgrid(ax_v, ax_v, indexing="ij")
TH = np.array([[inference(a, b, TABLES, SEUILS) for b in ax_v] for a in ax_v])   # 241 x 241 x 3
fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
for i, (nom, ax) in enumerate(zip(("theta_p (Kp)", "theta_i (Ki)", "theta_d (Kd)"), axes)):
    im = ax.pcolormesh(np.arange(len(ax_v)), np.arange(len(ax_v)), TH[:, :, i].T, vmin=0, vmax=1, cmap="viridis",
                       shading="nearest")
    ticks = [np.argmin(np.abs(ax_v - x)) for x in (-10, -1, -0.1, 0, 0.1, 1, 10)]
    ax.set_xticks(ticks)
    ax.set_xticklabels(["-10", "-1", "-0.1", "0", "0.1", "1", "10"], fontsize=7)
    ax.set_yticks(ticks)
    ax.set_yticklabels(["-10", "-1", "-0.1", "0", "0.1", "1", "10"], fontsize=7)
    ax.set_xlabel("E = erreur moyenne de la fenetre (V)")
    ax.set_ylabel("dE (V par fenetre)")
    ax.set_title(nom, fontsize=9, loc="left")
    fig.colorbar(im, ax=ax, fraction=0.046)
fig.tight_layout()
fig.savefig(os.path.join(DOSSIER_FUZZY, "fuzzy_pid_surfaces.png"), dpi=110)
plt.close(fig)
print(f"  fuzzy_pid_surfaces.png ecrit. Duree totale : {time.time() - T_DEBUT:.0f} s.")
