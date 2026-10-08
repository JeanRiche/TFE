# =============================================================================
# banc_pinn_pid.py
#
# VERSION
#   1 (5 octobre 2026), PINN-PID sur la base commune v2 (banc commun 2.1),
#   etape 4.
#
# OBJECTIF
#   Faire tourner le PINN-PID sur le banc commun, sur les onze essais, a
#   cote des references (PID de Ziegler-Nichols, meilleur PID fige, version
#   R0), mesurer ce que chaque piece apporte (ablations, sensibilite) et
#   ecrire ce que MATLAB et Simulink doivent retrouver :
#     - predictions_banc_pinn_pid.json : resultats attendus du PINN-PID sur
#       les onze essais (meme format que les autres fichiers de predictions,
#       lu par Simuler_PINN_PID.m) ;
#     - pinn_pid_reglages.mat : tous les nombres du bloc MATLAB (boite,
#       reglages d'Adam, cout, observateur, table du modele), pour que le
#       bloc et ce banc ne puissent pas diverger ;
#     - reference_rejeu_pinn_pid.mat : erreur, mesure, commande et gains pas
#       par pas sur quatre essais, que Tester_PINN_PID_Rejeu.m rejoue dans le
#       bloc MATLAB.
#
# LE PINN-PID, TEL QU'IL EST CODE ICI ET DANS pinn_pid_adaptatif.m
#   A chaque periode Tc = 1/220 000 s, le regulateur recoit l'erreur
#   e = consigne - mesure et la mesure de Vout (sortie du capteur).
#   1. Loi de Lu a derivee filtree (la meme que l'ELM-PID et R0) :
#        g(k) = Tc N (e(k) - ef(k)),  ef(k+1) = ef(k) + Tc N (e(k) - ef(k)),
#        u(k) = sat( u(k-1) + Kp (e(k) - e(k-1)) + Ki e(k) + Kd (g(k) - g(k-1)) ),
#      sat = [0.01 ; 0.99], seule saturation du rapport cyclique ; depart
#      u = 0.5, premier pas sans a-coup ; gains de depart de Ziegler-Nichols
#      en forme incrementale, boite des gains de l'ELM-PID
#      (boite_gains_elm.json). Decision de Jean-Riche du 5 octobre 2026 :
#      meme loi, meme depart, meme boite que l'ELM-PID ; seule l'adaptation
#      change.
#   2. Observateur (consequence de l'etape 3, estimation_etat_pinn.py : la
#      charge n'est pas estimable a partir de Vout) : filtre de Kalman etendu
#      sur [Vout, iL, Vin_eff] avec la charge nominale G = 1/5 S. Vin_eff
#      est une tension d'entree "effective" : elle donne au modele nominal
#      le bon regime etabli au point de fonctionnement. Correction par la
#      mesure, puis prediction d'un pas avec la fraction de conduction
#      appliquee.
#   3. A la fin de chaque fenetre de 110 periodes (0.5 ms), si l'erreur
#      efficace mesuree sur la fenetre depasse SEUIL = 0.1 V : 5 iterations
#      d'Adam sur les gains normalises theta (0 au bord bas de la boite, 1 au
#      bord haut). Cout, sur un horizon de 110 pas a partir de l'etat estime,
#      la loi de Lu dans la boucle et la consigne courante :
#        J = moyenne de [ e^2 / (1 V)^2 + RHO (du / 0.01)^2 ] + MU |theta - theta_debut|^2.
#      Le predicteur de l'horizon est le PINN (pinn_pid_modele.mat) ; dans
#      la variante "plafond", c'est le modele physique moyen par tranche a
#      charge nominale (au mieux, le PINN l'egale).
#      Gradient : retropropagation dans le temps, ecrite a la main, a
#      travers la loi, la modulation (fraction de conduction continue
#      clip(u x 1200 - phase, 0, 120) / 120) et le predicteur. Saturation :
#      valeur exacte vers l'avant, pente de 0.01 vers l'arriere hors des
#      bornes.
#
# LES REGLAGES (fixes avant les essais, criteres_pinn_pid.txt)
#   SEUIL = 0.1 V (zone morte de l'ELM-PID) ; horizon 110 pas ; Adam :
#   ALPHA = 0.01, BETA1 = 0.9, BETA2 = 0.999, EPS = 1e-7 (Ito et Wasa),
#   5 iterations, moments remis a zero a chaque fenetre ; RHO = 0.01 ;
#   MU = 0.02. Observateur : bruit de mesure 14.1 mV, bruit d'etat 1 mV,
#   10 mA et 0.03 V par pas (etape 3).
#   Ecarts a Ito et Wasa (a ecrire) : du^2 au lieu de u^2 ; proximite au
#   lieu de |F|^2 ; declenchement a 0.1 V ; observateur (Ito et Wasa
#   mesurent tout l'etat) ; charge nominale (etape 3).
#
# CE QUE LE SCRIPT MESURE
#   Grandeurs de banc_commun.py pour chaque regulateur et chaque essai,
#   cout J du meilleur PID fige (13 rapports au PID de Ziegler-Nichols) et
#   retours dans la bande. Ablations : plafond (modele physique a la place
#   du PINN), sans seuil, sans Vin_eff, R0 aux gains finaux du PINN-PID sur
#   S8b (les gains seuls, sans adaptation), modele physique volontairement
#   faux (L et C x2, puis x0.5) a la place du PINN. Controle : sans
#   adaptation, le PINN-PID redonne R0 a l'identique. Sensibilite : L ou C
#   a +-0.1 %.
#   Marges de phase du modele moyen aux gains finaux.
#
# FICHIERS NECESSAIRES (dans le meme dossier que ce script)
#   banc_commun.py (version 2.1), scenarios_communs.json, scenario_S*.mat,
#   predictions_banc_pid_fige.json, boite_gains_elm.json,
#   pinn_pid_modele.mat (entrainement_pinn.py).
#
# CE QUE PRODUIT CE SCRIPT
#   predictions_banc_pinn_pid.json, pinn_pid_reglages.mat,
#   reference_rejeu_pinn_pid.mat, banc_pinn_pid_resultats.json,
#   banc_pinn_pid.png (tension, gains et courant sur S8b et S9).
#
# BIBLIOTHEQUES NECESSAIRES (pip install numpy scipy matplotlib)
#
# COMMENT LANCER CE SCRIPT
#   python banc_pinn_pid.py
#   Duree : une quinzaine de minutes.
#
# ORDRE D'EXECUTION (PINN-PID)
#   1. entrainement_pinn.py ; 2. estimation_etat_pinn.py ; 3. ce script ;
#   4. Tester_PINN_PID_Rejeu.m ; 5. Construction_PINN_PID.m ;
#   6. verifier_modele_pinn_pid.py ; 7. Simuler_PINN_PID.m ;
#   8. Construction_PINN_PID_Trois_Modeles.m ;
#   9. verifier_modeles_pinn_pid_trois.py ; 10. Simuler_PINN_PID_Trois_Modeles.m.
# =============================================================================


# %% ETAPE 0 : bibliotheques, reglages et definitions du banc commun

import os                                     # chemins de fichiers
import json                                   # lecture et ecriture au format texte
import time                                   # duree d'execution
import numpy as np                            # calcul numerique
from scipy.io import loadmat, savemat         # fichiers .mat
from scipy.linalg import expm                 # table du modele physique
from scipy.signal import cont2discrete        # marges du modele moyen
import matplotlib
matplotlib.use("Agg")                         # figure ecrite dans un fichier, sans fenetre
import matplotlib.pyplot as plt               # figure

try:                                          # dossier du script (ou dossier courant dans une console)
    DOSSIER_PINN = os.path.dirname(os.path.abspath(__file__))
except NameError:
    DOSSIER_PINN = os.getcwd()

with open(os.path.join(DOSSIER_PINN, "banc_commun.py"), encoding="utf-8") as f:
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
TCN = TC * PID_N                              # Tc x N du filtre de derivee (meme produit dans le bloc MATLAB)
L_MOD, C_MOD = L_BOB, C_CONV                  # L et C du modele du regulateur (le circuit peut etre perturbe a part)

# Boite des gains (la meme que l'ELM-PID)
with open(os.path.join(DOSSIER_PINN, "boite_gains_elm.json"), encoding="utf-8") as f:
    BOITE = json.load(f)
K_MIN = np.array(BOITE["K_min"])              # bord bas [Kp, Ki, Kd]
K_MAX = np.array(BOITE["K_max"])              # bord haut
DK = K_MAX - K_MIN                            # largeur de la boite
K_ZN = np.array([PID_P, PID_I * TC, PID_D / TC])   # Ziegler-Nichols, forme incrementale
if np.max(np.abs(np.array(BOITE["K_depart"]) - K_ZN) / K_ZN) > 1e-12:
    raise RuntimeError("boite_gains_elm.json n'a pas ete calcule avec les gains de Ziegler-Nichols de ce banc.")

# Reglages du PINN-PID (voir l'en-tete)
REGLAGES = {"SEUIL": 0.1, "NH": float(NF), "ALPHA": 0.01, "BETA1": 0.9, "BETA2": 0.999, "EPS_ADAM": 1e-7,
            "N_ADAM": 5.0, "MU": 0.02, "RHO": 0.01, "DU_ECHELLE": 0.01, "PENTE_SAT": 0.01,
            "G_NOM": 0.2, "VIN_DEPART": 200.0, "SIG_Y": (200.0 / 4096.0) / np.sqrt(12.0),
            "SIG_V": 1e-3, "SIG_I": 1e-2, "SIG_VIN": 0.03, "P0_I": 1.0, "P0_VIN": 30.0 ** 2}

# Meilleur PID fige (deuxieme reference, oracle)
with open(os.path.join(DOSSIER_PINN, "predictions_banc_pid_fige.json"), encoding="utf-8") as f:
    GAINS_FIGE = json.load(f)["gains"]

# Modele PINN de l'etape 2
MODELE = loadmat(os.path.join(DOSSIER_PINN, "pinn_pid_modele.mat"))
COUCHES = []
l = 1
while f"W{l}" in MODELE:
    COUCHES.append((MODELE[f"W{l}"].astype(float), MODELE[f"b{l}"].astype(float).ravel()))
    l += 1
if abs(float(MODELE["TC"].item()) - TC) > 1e-18:
    raise RuntimeError("pinn_pid_modele.mat n'a pas ete appris avec la periode Tc de ce banc.")
SV_P, SI_P = float(MODELE["SV"].item()), float(MODELE["SI"].item())          # echelles de sortie du PINN
G_C, G_E = float(MODELE["G_CENTRE"].item()), float(MODELE["G_ECHELLE"].item())   # normalisation de G
print(f"Boite : Kp de {K_MIN[0]:.6f} a {K_MAX[0]:.6f}, Ki de {K_MIN[1]:.4e} a {K_MAX[1]:.4e}, "
      f"Kd de {K_MIN[2]:.4f} a {K_MAX[2]:.4f} ; depart a Ziegler-Nichols.")
print(f"PINN : {len(COUCHES) - 1} couches cachees de {COUCHES[0][0].shape[1]} neurones "
      f"(candidat {str(MODELE['CANDIDAT'][0])}, plage {str(MODELE['PLAGE'][0])}).")


def titre(texte):
    """Bandeau de titre dans la console."""
    print("\n" + "=" * 78 + "\n " + texte + "\n" + "=" * 78)


# %% ETAPE 1 : predicteurs, observateur, horizon et regulateurs

# Table du modele physique moyen par tranche a charge nominale, pour les
# 121 fractions de conduction possibles s = j/120 : sur une tranche,
#   x(fin) = PHI(s) x(debut) + GAM(s) (s Vin - (1 - s) Vf) / L,
# avec PHI = exp(A Tc) et GAM = (integrale de 0 a Tc de exp(A t) dt) [0 ; 1].
NS = NREG
PHI = np.zeros((NS + 1, 2, 2)); GAM = np.zeros((NS + 1, 2))
for j in range(NS + 1):
    s = j / NS
    req = s * RON + (1 - s) * RDIODE          # resistance moyenne vue par la bobine
    A = np.array([[-REGLAGES["G_NOM"] / C_MOD, 1 / C_MOD], [-1 / L_MOD, -req / L_MOD]])
    M = np.zeros((4, 4)); M[:2, :2] = A * TC; M[:2, 2:] = np.eye(2) * TC
    E = expm(M)                               # [[exp(A Tc), integrale], [0, I]]
    PHI[j] = E[:2, :2]; GAM[j] = E[:2, 3]


def modele_pas(v, i, s, vin):
    """Un pas Tc du modele physique nominal (interpolation lineaire de la
    table en s). Renvoie v', iL', la matrice d(v', iL')/d(v, iL), les
    derivees de v' et iL' par rapport a s, puis par rapport a Vin."""
    x = s * NS
    j = min(int(x), NS - 1); f = x - j       # segment de la table et position dans le segment
    P = PHI[j] + f * (PHI[j + 1] - PHI[j]); dP = (PHI[j + 1] - PHI[j]) * NS
    g = GAM[j] + f * (GAM[j + 1] - GAM[j]); dg = (GAM[j + 1] - GAM[j]) * NS
    src = (s * vin - (1 - s) * VF) / L_MOD; dsrc = (vin + VF) / L_MOD   # source moyenne vue par la bobine
    vn = P[0, 0] * v + P[0, 1] * i + g[0] * src
    inn = P[1, 0] * v + P[1, 1] * i + g[1] * src
    dvs = dP[0, 0] * v + dP[0, 1] * i + dg[0] * src + g[0] * dsrc
    dis = dP[1, 0] * v + dP[1, 1] * i + dg[1] * src + g[1] * dsrc
    return vn, inn, P, dvs, dis, g[0] * s / L_MOD, g[1] * s / L_MOD


def pinn_pas(v, i, s, vin):
    """Un pas Tc du PINN (tau = Tc) a charge nominale, avec la matrice
    d(v', iL')/d(v, iL) et les derivees par rapport a s, calculees en mode
    direct (trois directions : v, iL, s)."""
    z = np.array([1.0, (v - 100.0) / 60.0, (i - 12.0) / 10.0, 2 * s - 1, (vin - 195.0) / 45.0,
                  (REGLAGES["G_NOM"] - G_C) / G_E])
    T = np.zeros((3, 6)); T[0, 1] = 1 / 60.0; T[1, 2] = 1 / 10.0; T[2, 3] = 2.0   # dz / d(v, iL, s)
    h = z
    for W, b in COUCHES[:-1]:
        h = np.tanh(h @ W + b)
        T = (T @ W) * (1 - h * h)
    W, b = COUCHES[-1]
    N = h @ W + b; TN = T @ W
    vn = v + SV_P * N[0]; inn = i + SI_P * N[1]
    P = np.array([[1 + SV_P * TN[0, 0], SV_P * TN[1, 0]], [SI_P * TN[0, 1], 1 + SI_P * TN[1, 1]]])
    return vn, inn, P, SV_P * TN[2, 0], SI_P * TN[2, 1], 0.0, 0.0


def predicteur_modele_faux(fl, fc):
    """Ablation : le modele physique nominal avec L multiplie par fl et C
    par fc (modele volontairement faux), meme forme que modele_pas. Sert a
    mesurer si la precision du predicteur compte pour le regulateur."""
    Lf, Cf = L_MOD * fl, C_MOD * fc
    PH = np.zeros((NS + 1, 2, 2)); GA = np.zeros((NS + 1, 2))
    for jj in range(NS + 1):
        sj = jj / NS
        rq = sj * RON + (1 - sj) * RDIODE    # resistance moyenne vue par la bobine
        Af = np.array([[-REGLAGES["G_NOM"] / Cf, 1 / Cf], [-1 / Lf, -rq / Lf]])
        Mf = np.zeros((4, 4)); Mf[:2, :2] = Af * TC; Mf[:2, 2:] = np.eye(2) * TC
        Ef = expm(Mf)
        PH[jj] = Ef[:2, :2]; GA[jj] = Ef[:2, 3]

    def pas(v, i, s, vin):
        x = s * NS
        j = min(int(x), NS - 1); f = x - j
        P = PH[j] + f * (PH[j + 1] - PH[j]); dP = (PH[j + 1] - PH[j]) * NS
        g = GA[j] + f * (GA[j + 1] - GA[j]); dg = (GA[j + 1] - GA[j]) * NS
        src = (s * vin - (1 - s) * VF) / Lf; dsrc = (vin + VF) / Lf
        vn = P[0, 0] * v + P[0, 1] * i + g[0] * src
        inn = P[1, 0] * v + P[1, 1] * i + g[1] * src
        dvs = dP[0, 0] * v + dP[0, 1] * i + dg[0] * src + g[0] * dsrc
        dis = dP[1, 0] * v + dP[1, 1] * i + dg[1] * src + g[1] * dsrc
        return vn, inn, P, dvs, dis, 0.0, 0.0
    return pas


# Controle : le PINN relu redonne ses vecteurs de test (un pas et ses derivees)
ECART_TEST = 0.0
for q, (v0, i0, s0, vin0, G0) in enumerate(MODELE["X_TEST"]):
    vn, inn, P, dvs, dis, _, _ = pinn_pas(v0, i0, s0, vin0)
    D = np.array([[P[0, 0] - 1, P[1, 0]], [P[0, 1], P[1, 1] - 1], [dvs, dis]])
    ECART_TEST = max(ECART_TEST, abs(vn - MODELE["Y_TEST"][q, 0]), abs(inn - MODELE["Y_TEST"][q, 1]),
                     float(np.max(np.abs(D - MODELE["D_TEST"][q].reshape(3, 2)))))
print(f"Vecteurs de test du PINN : ecart maximal {ECART_TEST:.1e}.")
if ECART_TEST > 1e-12:
    raise RuntimeError("pinn_pid_modele.mat ne redonne pas ses vecteurs de test.")


class Observateur:
    """Filtre de Kalman etendu sur [Vout, iL, Vin_eff], charge nominale."""

    def __init__(self, v0, svin):
        r = REGLAGES
        self.x = np.array([v0, 0.0, r["VIN_DEPART"]])          # depart : premiere mesure, repos, 200 V
        self.P = np.diag([r["SIG_Y"] * r["SIG_Y"], r["P0_I"], r["P0_VIN"] if svin > 0 else 0.0])
        self.Q = np.diag([r["SIG_V"] * r["SIG_V"], r["SIG_I"] * r["SIG_I"], svin * svin])
        self.R = r["SIG_Y"] * r["SIG_Y"]

    def mise_a_jour(self, y):
        """Correction par la mesure de Vout."""
        P = self.P
        S = P[0, 0] + self.R
        K = P[:, 0] / S
        self.x = self.x + K * (y - self.x[0])
        self.P = P - np.outer(K, P[0, :])

    def prediction(self, s):
        """Prediction d'un pas avec la fraction de conduction appliquee s."""
        v, i, vin = self.x
        vn, inn, Pm, _, _, dv_vin, di_vin = modele_pas(v, i, s, vin)
        F = np.array([[Pm[0, 0], Pm[0, 1], dv_vin], [Pm[1, 0], Pm[1, 1], di_vin], [0.0, 0.0, 1.0]])
        self.x = np.array([vn, inn, vin])
        self.P = F @ self.P @ F.T + self.Q


def s_continu(u, ph):
    """Fraction de conduction continue de la tranche de phase ph pour la
    commande u, et sa derivee par rapport a u (dans l'horizon)."""
    y = u * NPER - ph
    if y <= 0.0:
        return 0.0, 0.0
    if y >= NREG:
        return 1.0, 0.0
    return y / NREG, NPER / NREG


def horizon(K, x0, ctrl, r, k1, vin, pas_pred, NH, RHO, grad=True):
    """Simule NH pas a partir de l'etat x0 (instant k1) avec la loi de Lu de
    gains K et le predicteur pas_pred ; renvoie le cout (sans la proximite)
    et son gradient par rapport a K (retropropagation dans le temps)."""
    Kp, Ki, Kd = K
    u_p, e_p, ef, g_p = ctrl                  # etat de la loi a la fin du pas courant
    v, i = x0
    pile = []                                 # valeurs gardees pour la retropropagation
    J = 0.0
    for j in range(NH):
        e = r - v                             # erreur predite
        g = TCN * (e - ef)                    # derivee filtree
        b = u_p + Kp * (e - e_p) + Ki * e + Kd * (g - g_p)
        if b < D_MIN:
            u, du = D_MIN, REGLAGES["PENTE_SAT"]
        elif b > D_MAX:
            u, du = D_MAX, REGLAGES["PENTE_SAT"]
        else:
            u, du = b, 1.0
        ph = ((k1 + j) * NREG) % NPER         # phase de la porteuse
        s, ds = s_continu(u, ph)
        vn, inn, Pm, dvs, dis, _, _ = pas_pred(v, i, s, vin)
        t_u = (u - u_p) / REGLAGES["DU_ECHELLE"]   # variation de commande rapportee a 0.01
        J += e * e + RHO * (t_u * t_u)
        pile.append((e, e_p, g, g_p, u, u_p, du, ds, Pm, dvs, dis))
        ef = ef + TCN * (e - ef)
        u_p, e_p, g_p = u, e, g
        v, i = vn, inn
    J /= NH
    if not grad:
        return J, None
    gK = np.zeros(3)
    cu = 2 * RHO / (REGLAGES["DU_ECHELLE"] * REGLAGES["DU_ECHELLE"]) / NH   # derivee du terme de commande, a (u - u_p) pres
    lv = li = lu = le = lef = lg = 0.0        # adjoints de v, iL, u(k-1), e(k-1), ef, g(k-1)
    for j in range(NH - 1, -1, -1):
        e, e_p, g, g_p, u, u_p, du, ds, Pm, dvs, dis = pile[j]
        dJu = lu + cu * (u - u_p) + (lv * dvs + li * dis) * ds
        db = dJu * du
        gK[0] += db * (e - e_p); gK[1] += db * e; gK[2] += db * (g - g_p)
        dJg = lg + db * Kd
        dJe = 2 * e / NH + db * (Kp + Ki) + dJg * TCN + lef * TCN + le
        dJup = db - cu * (u - u_p)
        dJep = -db * Kp
        dJgp = -db * Kd
        dJef = -TCN * dJg + lef * (1 - TCN)
        lv_new = Pm[0, 0] * lv + Pm[1, 0] * li - dJe
        li_new = Pm[0, 1] * lv + Pm[1, 1] * li
        lv, li, lu, le, lef, lg = lv_new, li_new, dJup, dJep, dJef, dJgp
    return J, gK


class LoiLu:
    """Loi de Lu a derivee filtree, gains figes (version R0)."""

    def __init__(self, K):
        self.Kp, self.Ki, self.Kd = (float(x) for x in K)
        self.u = 0.5
        self.premier = True

    def pas(self, e):
        if self.premier:
            self.e1, self.ef, self.g1, self.premier = e, e, 0.0, False
        g = TCN * (e - self.ef)
        brut = self.u + self.Kp * (e - self.e1) + self.Ki * e + self.Kd * (g - self.g1)
        u = min(max(brut, D_MIN), D_MAX)
        self.ef = self.ef + TCN * (e - self.ef)
        self.e1, self.g1, self.u = e, g, u
        return u


class PINNPID:
    """Copie Python de pinn_pid_adaptatif.m (memes reglages, meme ordre des
    operations : Tester_PINN_PID_Rejeu.m compare les deux pas par pas). Les
    arguments servent aux variantes ; leurs valeurs par defaut sont celles du
    bloc."""
    utilise_mesure = True                     # le banc commun passe aussi la mesure

    def __init__(self, predicteur="pinn", adapter=True, seuil=None, svin=None):
        r = REGLAGES
        if predicteur == "pinn":
            self.pas_pred = pinn_pas          # le PINN de l'etape 2
        elif predicteur == "modele":
            self.pas_pred = modele_pas        # plafond : le modele physique nominal
        else:
            self.pas_pred = predicteur        # ablation : un autre predicteur (fonction de meme forme)
        self.adapter = adapter
        self.seuil = r["SEUIL"] if seuil is None else seuil
        self.svin = r["SIG_VIN"] if svin is None else svin
        self.NH, self.n_adam = int(r["NH"]), int(r["N_ADAM"])
        self.theta = np.minimum(np.maximum((K_ZN - K_MIN) / DK, 0.0), 1.0)   # depart dans la boite
        self.K = K_MIN + self.theta * DK
        self.u, self.premier = 0.5, True
        self.obs = None
        self.k = 0                            # numero de la periode Tc
        self.cpt, self.se2 = 0, 0.0           # fenetre courante
        self.journal = []                     # une ligne par fenetre
        self.K_pas = []                       # gains utilises a chaque pas

    def pas(self, e, mesure):
        self.K_pas.append(self.K)
        k = self.k
        if self.obs is None:
            self.obs = Observateur(mesure, self.svin)
        self.obs.mise_a_jour(mesure)          # 1. correction de l'observateur
        r = e + mesure                        # consigne courante
        if self.premier:
            self.e1, self.ef, self.g1, self.premier = e, e, 0.0, False
        g = TCN * (e - self.ef)               # 2. loi de Lu
        brut = self.u + self.K[0] * (e - self.e1) + self.K[1] * e + self.K[2] * (g - self.g1)
        u = min(max(brut, D_MIN), D_MAX)
        self.ef = self.ef + TCN * (e - self.ef)
        self.e1, self.g1, self.u = e, g, u
        ph = (k * NREG) % NPER                # 3. prediction de l'observateur avec la fraction appliquee
        s_app = min(max(int(np.ceil(u * NPER)) - ph, 0), NREG) / NREG
        self.obs.prediction(s_app)
        self.se2 += e * e                     # 4. fenetre
        self.cpt += 1
        self.k += 1
        if self.cpt >= NF:
            eff = np.sqrt(self.se2 / NF)
            adapte = False
            if self.adapter and eff > self.seuil:
                self.optimiser(r)
                adapte = True
            self.journal.append({"k": k, "eff": float(eff), "adapte": adapte, "K": self.K.copy(),
                                 "vin_eff": float(self.obs.x[2]), "iL": float(self.obs.x[1])})
            self.cpt, self.se2 = 0, 0.0
        return u

    def optimiser(self, r):
        """5 iterations d'Adam sur theta, horizon depuis l'etat estime."""
        R = REGLAGES
        x0 = (float(self.obs.x[0]), float(self.obs.x[1])); vin = float(self.obs.x[2])
        ctrl = (self.u, self.e1, self.ef, self.g1)
        th0 = self.theta.copy(); th = th0.copy()
        m = np.zeros(3); vv = np.zeros(3)     # moments d'Adam, remis a zero
        b1t, b2t = 1.0, 1.0                   # BETA1^it et BETA2^it, par produits (memes nombres dans MATLAB)
        for it in range(1, self.n_adam + 1):
            b1t *= R["BETA1"]; b2t *= R["BETA2"]
            J, gK = horizon(K_MIN + th * DK, x0, ctrl, r, self.k, vin, self.pas_pred, self.NH, R["RHO"])
            gth = gK * DK + 2 * R["MU"] * (th - th0)
            m = R["BETA1"] * m + (1 - R["BETA1"]) * gth
            vv = R["BETA2"] * vv + (1 - R["BETA2"]) * gth * gth
            th = th - R["ALPHA"] * (m / (1 - b1t)) / (np.sqrt(vv / (1 - b2t)) + R["EPS_ADAM"])
            th = np.minimum(np.maximum(th, 0.0), 1.0)          # projection sur la boite
        self.theta = th
        self.K = K_MIN + th * DK


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


# Controle du gradient de l'horizon (differences finies, hors saturation)
ctrl_t = (0.5, 0.5, 0.4, 0.01)
_, g_a = horizon(K_ZN, (99.5, 20.0), ctrl_t, 100.0, 7, 200.0, pinn_pas, NF, REGLAGES["RHO"])
ECART_GRAD = 0.0
for m_ in range(3):
    h_ = K_ZN[m_] * 1e-6
    Kp_, Km_ = K_ZN.copy(), K_ZN.copy(); Kp_[m_] += h_; Km_[m_] -= h_
    fd = (horizon(Kp_, (99.5, 20.0), ctrl_t, 100.0, 7, 200.0, pinn_pas, NF, REGLAGES["RHO"], grad=False)[0]
          - horizon(Km_, (99.5, 20.0), ctrl_t, 100.0, 7, 200.0, pinn_pas, NF, REGLAGES["RHO"], grad=False)[0]) / (2 * h_)
    ECART_GRAD = max(ECART_GRAD, abs(fd - g_a[m_]) / abs(fd))
print(f"Gradient de l'horizon contre differences finies : ecart relatif maximal {ECART_GRAD:.1e}.")
if ECART_GRAD > 1e-4:
    raise RuntimeError("Le gradient de l'horizon ne correspond pas aux differences finies.")


# %% ETAPE 2 : evaluation sur les onze essais et references

def evaluer(fabrique, codes=None):
    """Simule un nouveau regulateur (fabrique()) sur chaque essai."""
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


def non_revenus(res):
    return [c for c in CODES_IAE if not res[c]["revenus"]]


titre("ETAPE 2 : les references")
REF = {"Ziegler-Nichols": evaluer(lambda: PIDClassique()),
       "meilleur PID fige": evaluer(lambda: PIDParallele(GAINS_FIGE["P"], GAINS_FIGE["I"], GAINS_FIGE["D"])),
       "R0": evaluer(lambda: LoiLu(K_ZN))}
T_ZN = termes(REF["Ziegler-Nichols"])
J_REF = {n: float(np.mean(termes(r) / T_ZN)) for n, r in REF.items()}
print(f"  Meilleur PID fige : J = {J_REF['meilleur PID fige']:.3f} (recherche_pid_fige.py : 0.738) ; R0 : "
      f"J = {J_REF['R0']:.3f}.")


# %% ETAPE 3 : PINN-PID et plafond sur les onze essais

titre("ETAPE 3 : PINN-PID et plafond (modele physique a la place du PINN)")


def bilan(nom, res):
    """Cout J, retours et une ligne par essai."""
    J = float(np.mean(termes(res) / T_ZN))
    non = non_revenus(res)
    print(f"\n  {nom} : J = {J:.3f} ; {'tous les evenements reviennent' if not non else 'pas revenus : ' + ', '.join(non)}")
    for code, r in res.items():
        o = r["o"]; jr = r["reg"].journal
        Kf = jr[-1]["K"] / K_ZN
        print(f"    {code:4s} depassement {o['depassement_pct']:5.1f} %, IAE {o['IAE'] * 1e3:7.2f} mV.s, efficace "
              f"{o['e_eff_V'] * 1e3:7.1f} mV, |dd| {o['dd_moyen']:.4f} ; fenetres adaptees "
              f"{sum(x['adapte'] for x in jr):3d}/{len(jr)}, gains finaux x({Kf[0]:.2f}, {Kf[1]:.2f}, {Kf[2]:.2f})")
    return J


t0 = time.time()
PINN = evaluer(lambda: PINNPID("pinn"))
J_PINN = bilan("PINN-PID", PINN)
print(f"  ({time.time() - t0:.0f} s)")
PLAFOND = evaluer(lambda: PINNPID("modele"))
J_PLAFOND = bilan("Plafond (modele physique nominal a la place du PINN)", PLAFOND)

fige = evaluer(lambda: PINNPID("pinn", adapter=False), ["S1", "S8b"])
ECART_R0 = max(float(np.max(np.abs(fige[c]["sim"]["d"] - REF["R0"][c]["sim"]["d"]))) for c in fige)
print(f"\n  Controle : PINN-PID sans adaptation contre R0, ecart maximal sur d : {ECART_R0:.1e}.")
if ECART_R0 > 1e-12:
    raise RuntimeError("Sans adaptation, le PINN-PID ne redonne pas la loi R0.")


# %% ETAPE 4 : ablations, sensibilite et marges

titre("ETAPE 4 : ce que chaque piece apporte (ablations)")
K_FIN_S8B = PINN["S8b"]["reg"].journal[-1]["K"].copy()
# Les deux dernieres ablations (modele physique volontairement faux) ont ete
# ajoutees apres avoir vu que le PINN et le modele physique donnaient le
# meme J : elles mesurent si la precision du predicteur compte. Ce sont des
# ablations, pas des choix du regulateur.
PRED_FAUX_2 = predicteur_modele_faux(2.0, 2.0)
PRED_FAUX_05 = predicteur_modele_faux(0.5, 0.5)
ABLATIONS = {"Sans seuil (adaptation a chaque fenetre)": lambda: PINNPID("pinn", seuil=0.0),
             "Sans Vin_eff (Vin fixee a 200 V)": lambda: PINNPID("pinn", svin=0.0),
             "R0 aux gains finaux du PINN-PID sur S8b": lambda: LoiLu(K_FIN_S8B),
             "Modele physique faux (L et C x2)": lambda: PINNPID(PRED_FAUX_2),
             "Modele physique faux (L et C x0.5)": lambda: PINNPID(PRED_FAUX_05)}
RES_ABL = {n: evaluer(f) for n, f in ABLATIONS.items()}
J_ABL = {n: float(np.mean(termes(r) / T_ZN)) for n, r in RES_ABL.items()}
print(f"\n  {'variante':44s} {'J':>6s}  {'non revenus':12s} {'S8a':>7s} {'S8b':>7s} {'S9':>8s} {'S7b eff':>8s}")
for nom, res, J in ([("PINN-PID", PINN, J_PINN), ("Plafond (modele physique)", PLAFOND, J_PLAFOND),
                     ("R0", REF["R0"], J_REF["R0"])] + [(n, RES_ABL[n], J_ABL[n]) for n in ABLATIONS]):
    print(f"  {nom:44s} {J:6.3f}  {(','.join(non_revenus(res)) or '-'):12s} {res['S8a']['o']['IAE'] * 1e3:7.2f} "
          f"{res['S8b']['o']['IAE'] * 1e3:7.2f} {res['S9']['o']['IAE'] * 1e3:8.2f} {res['S7b']['o']['e_eff_V'] * 1e3:8.1f}")
print(f"  (IAE de 30 ms a la fin en mV.s ; ecart efficace en mV ; gains finaux S8b x"
      f"({K_FIN_S8B[0] / K_ZN[0]:.2f}, {K_FIN_S8B[1] / K_ZN[1]:.2f}, {K_FIN_S8B[2] / K_ZN[2]:.2f}))")

titre("ETAPE 4b : sensibilite a de tres petits ecarts du circuit (L ou C a +-0.1 %)")
L_NOM, C_NOM = L_BOB, C_CONV                  # valeurs nominales du circuit, retablies a la fin
SENSIBILITE = []
for nom_p, fl, fc in (("L - 0.1 %", 0.999, 1.0), ("L + 0.1 %", 1.001, 1.0), ("C - 0.1 %", 1.0, 0.999),
                      ("C + 0.1 %", 1.0, 1.001)):
    L_BOB, C_CONV = L_NOM * fl, C_NOM * fc   # seul le circuit change ; le modele du regulateur reste nominal
    t_zn = termes(evaluer(lambda: PIDClassique()))
    r_p = evaluer(lambda: PINNPID("pinn"))
    J_p = float(np.mean(termes(r_p) / t_zn))
    SENSIBILITE.append({"circuit": nom_p, "J": J_p, "non_revenus": non_revenus(r_p),
                        "S8b_IAE": r_p["S8b"]["o"]["IAE"], "S8b_K_final_sur_ZN": (r_p["S8b"]["reg"].journal[-1]["K"] / K_ZN).tolist()})
    print(f"  {nom_p:10s} J = {J_p:.3f} ; non revenus : {','.join(non_revenus(r_p)) or '-'} ; S8b IAE "
          f"{r_p['S8b']['o']['IAE'] * 1e3:.2f} mV.s")
L_BOB, C_CONV = L_NOM, C_NOM                  # circuit nominal retabli

titre("ETAPE 4c : marges de phase du modele moyen aux gains finaux")
W_F = np.logspace(np.log10(2 * np.pi * 20.0), np.log10(np.pi / TC * 0.999), 8000)   # pulsations (rad/s)
Z_F = np.exp(1j * W_F * TC)


def marge(K, R, V):
    """Marge de phase (degres) et frequence de coupure (Hz) de la loi de Lu
    de gains K sur le modele moyen sans pertes au coin (R, V), discretise
    avec un bloqueur d'ordre zero (memes formules que boite_gains_elm.py)."""
    num, den, _ = cont2discrete(([V], [L_BOB * C_CONV, L_BOB / R, 1.0]), TC, method="zoh")
    G = np.polyval(np.squeeze(num), Z_F) / np.polyval(den, Z_F)
    Cz = K[0] + K[1] * Z_F / (Z_F - 1.0) + K[2] * TC * PID_N * (Z_F - 1.0) / (Z_F - 1.0 + TC * PID_N)
    boucle = Cz * G
    lm = np.log(np.abs(boucle)); ph = np.unwrap(np.angle(boucle))
    j = np.where(np.diff(np.sign(lm)) != 0)[0]
    if len(j) == 0:
        return 180.0, 0.0
    f = lm[j] / (lm[j] - lm[j + 1])
    phase = ph[j] + f * (ph[j + 1] - ph[j])
    wc = W_F[j] * (W_F[j + 1] / W_F[j]) ** f
    marges = (np.degrees(phase) + 360.0) % 360.0 - 180.0
    return float(marges.min()), float(wc.max() / (2 * np.pi))


COINS = [(R, V) for R in (4.0, 5.0, 25.0, 98.0) for V in (160.0, 200.0, 240.0)]
MARGES = {}
for nom, K in [("depart (Ziegler-Nichols)", K_ZN)] + [(f"final {c}", PINN[c]["reg"].journal[-1]["K"]) for c in ("S5", "S8a", "S8b", "S9")]:
    mg = [marge(K, R, V) for R, V in COINS]
    nominal = [m for (R, V), m in zip(COINS, mg) if R <= 5.0]
    leger = [m for (R, V), m in zip(COINS, mg) if R > 5.0]
    MARGES[nom] = {"K_sur_ZN": (K / K_ZN).tolist(), "marge_min_nominale_deg": min(m[0] for m in nominal),
                   "marge_min_charge_legere_deg": min(m[0] for m in leger), "coupure_max_Hz": max(m[1] for m in mg)}
    print(f"  {nom:26s} x({K[0] / K_ZN[0]:.2f}, {K[1] / K_ZN[1]:.2f}, {K[2] / K_ZN[2]:.2f}) : marge minimale "
          f"{MARGES[nom]['marge_min_nominale_deg']:5.1f} deg (4 et 5 ohms), {MARGES[nom]['marge_min_charge_legere_deg']:5.1f} "
          f"deg (25 et 98 ohms) ; coupure maximale {MARGES[nom]['coupure_max_Hz']:.0f} Hz")


# %% ETAPE 5 : comparaison avec les references

titre("ETAPE 5 : PINN-PID face aux references")
TOUS = {"Ziegler-Nichols": REF["Ziegler-Nichols"], "meilleur PID fige": REF["meilleur PID fige"], "R0": REF["R0"],
        "Plafond": PLAFOND, "PINN-PID": PINN}
J_TOUS = {nom: float(np.mean(termes(res) / T_ZN)) for nom, res in TOUS.items()}
print("  " + " " * 28 + "".join(f"{nom:>18s}" for nom in TOUS))
print("  " + f"{'cout J':28s}" + "".join(f"{J_TOUS[n]:18.3f}" for n in TOUS))
print("  " + f"{'evenements non revenus':28s}" + "".join(f"{(','.join(non_revenus(TOUS[n])) or '-'):>18s}" for n in TOUS))
for code in ESSAIS:
    for cle, etiquette, fmt, k in (("depassement_pct", "depassement %", "{:.1f}", 1.0), ("IAE", "IAE mV.s", "{:.2f}", 1e3),
                                   ("e_eff_V", "ecart efficace mV", "{:.1f}", 1e3), ("iL_max_dem_A", "iL crete dem. A", "{:.1f}", 1.0)):
        if cle == "depassement_pct" and code not in ("S1", "S8a", "S8b"):
            continue
        if cle == "iL_max_dem_A" and code not in ("S1", "S8b"):
            continue
        print("  " + f"{code + ' ' + etiquette:28s}" + "".join(f"{fmt.format(TOUS[n][code]['o'][cle] * k):>18s}" for n in TOUS))
print("  " + f"{'activite |dd| (S1)':28s}" + "".join(f"{TOUS[n]['S1']['o']['dd_moyen']:18.4f}" for n in TOUS))


# %% ETAPE 6 : fichiers pour Simulink et MATLAB, resultats et figure

titre("ETAPE 6 : fichiers pour Simulink et MATLAB")
pas_1ms = int(round(1e-3 / TC))               # 220 periodes Tc
predictions = {"version": 2, "Te": TC,
               "regulateur": "PINN-PID (loi de Lu a derivee filtree, PINN de l'etape 2, observateur a charge nominale, "
                             "boite boite_gains_elm.json)",
               "reglages": REGLAGES,
               "boite": {"K_min": K_MIN.tolist(), "K_max": K_MAX.tolist(), "K_depart": K_ZN.tolist()},
               "controle": {"ecart_vecteurs_test": ECART_TEST, "ecart_sans_adaptation_R0": ECART_R0,
                            "ecart_gradient": ECART_GRAD},
               "essais": {}}
for code, r in PINN.items():
    Kp = np.array(r["reg"].K_pas)
    predictions["essais"][code] = {"grandeurs": r["o"],
                                   "v_toutes_les_ms": r["sim"]["v"][::pas_1ms].tolist(),
                                   "iL_toutes_les_ms": r["sim"]["iL"][::pas_1ms].tolist(),
                                   "d_moyen_par_ms": [float(np.mean(r["sim"]["d"][i:i + pas_1ms]))
                                                      for i in range(0, len(r["sim"]["d"]) - pas_1ms + 1, pas_1ms)],
                                   "K_toutes_les_ms": Kp[::pas_1ms].tolist()}
with open(os.path.join(DOSSIER_PINN, "predictions_banc_pinn_pid.json"), "w", encoding="utf-8") as f:
    json.dump(predictions, f, indent=1, allow_nan=False)
print("  predictions_banc_pinn_pid.json ecrit.")

reglages_mat = {k: float(v) for k, v in REGLAGES.items()}
reglages_mat.update({"K_MIN": K_MIN.reshape(1, 3), "K_MAX": K_MAX.reshape(1, 3), "K_DEPART": K_ZN.reshape(1, 3),
                     "NF": float(NF), "TC": TC, "N_FILTRE": PID_N, "D_MIN": D_MIN, "D_MAX": D_MAX, "U_DEPART": 0.5,
                     "NPER": float(NPER), "NREG": float(NREG), "L_MOD": L_MOD, "VF": VF,
                     "PHI": PHI.reshape(NS + 1, 4), "GAM": GAM, "PREDICTEUR_PINN": 1.0, "VERSION": 1.0})
savemat(os.path.join(DOSSIER_PINN, "pinn_pid_reglages.mat"), reglages_mat)
print("  pinn_pid_reglages.mat ecrit (reglages du bloc ; PHI range ligne par ligne : [p11 p12 p21 p22]).")

rejeu = {}
for code in CODES_REJEU:
    r = PINN[code]
    jr = r["reg"].journal
    rejeu[code] = {"e": (r["sim"]["consigne"] - r["sim"]["mesure"]).reshape(-1, 1),
                   "mesure": r["sim"]["mesure"].reshape(-1, 1), "u": r["sim"]["d"].reshape(-1, 1),
                   "K": np.array(r["reg"].K_pas), "adapte": np.array([x["adapte"] for x in jr], float).reshape(-1, 1),
                   "vin_eff": np.array([x["vin_eff"] for x in jr]).reshape(-1, 1),
                   "iL_obs": np.array([x["iL"] for x in jr]).reshape(-1, 1)}
savemat(os.path.join(DOSSIER_PINN, "reference_rejeu_pinn_pid.mat"), rejeu, do_compression=True)
print(f"  reference_rejeu_pinn_pid.mat ecrit ({', '.join(CODES_REJEU)}).")


def resume_essais(res):
    return {c: {"grandeurs": res[c]["o"], "IAE_dem": res[c]["IAE_dem"], "revenus": res[c]["revenus"]} for c in res}


sortie = {"version": 1, "reglages": REGLAGES, "boite": predictions["boite"], "J": J_TOUS, "J_ablations": J_ABL,
          "sensibilite": SENSIBILITE, "marges": MARGES,
          "references": {n: resume_essais(TOUS[n]) for n in TOUS},
          "ablations": {n: resume_essais(RES_ABL[n]) for n in RES_ABL},
          "gains_pinn_pid": {c: [x["K"].tolist() for x in PINN[c]["reg"].journal] for c in PINN},
          "fenetres_adaptees": {c: int(sum(x["adapte"] for x in PINN[c]["reg"].journal)) for c in PINN},
          "duree_s": round(time.time() - T_DEBUT, 1)}
with open(os.path.join(DOSSIER_PINN, "banc_pinn_pid_resultats.json"), "w", encoding="utf-8") as f:
    json.dump(sortie, f, indent=1, allow_nan=False, default=lambda x: None)
print("  banc_pinn_pid_resultats.json ecrit.")

fig, axes = plt.subplots(3, 2, figsize=(13, 9), sharex="col")
for col, code in enumerate(("S8b", "S9")):
    for nom, couleur in (("Ziegler-Nichols", "0.6"), ("R0", "tab:orange"), ("meilleur PID fige", "tab:green"),
                         ("Plafond", "tab:purple"), ("PINN-PID", "tab:blue")):
        sim = TOUS[nom][code]["sim"]
        axes[0, col].plot(sim["t"] * 1e3, sim["v"], lw=0.6, color=couleur, label=nom)
        axes[2, col].plot(sim["t"] * 1e3, sim["iL"], lw=0.4, color=couleur)
    axes[0, col].plot(sim["t"] * 1e3, sim["consigne"], "k--", lw=0.6)
    Kp = np.array(PINN[code]["reg"].K_pas) / K_ZN
    t_ms = PINN[code]["sim"]["t"] * 1e3
    for i, nom in enumerate(("Kp", "Ki", "Kd")):
        axes[1, col].plot(t_ms, Kp[:, i], lw=1.0, label=nom)
    axes[0, col].set_ylim(30, 200)
    axes[0, col].set_title(f"{code} : tension de sortie", fontsize=9, loc="left")
    axes[1, col].set_title(f"{code} : gains du PINN-PID (multiples de Ziegler-Nichols)", fontsize=9, loc="left")
    axes[2, col].set_title(f"{code} : courant de la bobine (observe)", fontsize=9, loc="left")
    axes[2, col].set_xlabel("temps (ms)")
    for ax in axes[:, col]:
        ax.grid(alpha=0.3)
axes[0, 0].legend(fontsize=7)
axes[1, 0].legend(fontsize=7)
axes[0, 0].set_ylabel("V")
axes[2, 0].set_ylabel("A")
fig.tight_layout()
fig.savefig(os.path.join(DOSSIER_PINN, "banc_pinn_pid.png"), dpi=110)
plt.close(fig)
print(f"  banc_pinn_pid.png ecrit. Duree totale : {time.time() - T_DEBUT:.0f} s.")
