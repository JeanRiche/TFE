# =============================================================================
# banc_pinn_pid.py
#
# VERSION
#   2 (8 octobre 2026), PINN-PID B : le bloc PID parallele de la base
#   commune, dont les gains sont optimises en ligne comme chez Ito et Wasa.
#   Methode, modifications, ecarts et previsions : criteres_pinn_pid.txt
#   de ce dossier. La version 1 (5 octobre, loi incrementale de Lu) est
#   dans le dossier PINN_PID.
#
# OBJECTIF
#   Faire tourner le PINN-PID B sur le banc commun, sur les onze essais, a
#   cote des references (PID de Ziegler-Nichols, qui est aussi le PINN-PID B
#   sans adaptation, et meilleur PID fige sur grille), mesurer ce que
#   quelques pieces apportent (ablations, rapportees, jamais choisies) et
#   juger les previsions de criteres_pinn_pid.txt.
#
# LE PINN-PID B, TEL QU'IL EST CODE ICI
#   A chaque periode Tc = 1/220 000 s :
#   1. Le bloc PID de la base commune (Parallel, derivee filtree N =
#      64 122.9 rad/s, Forward Euler, sortie dans [0.01 ; 0.99], clamping,
#      integrateur a 0.5 et filtre a 0.01 au depart) calcule u a partir de
#      e = consigne - mesure avec les gains K = K_ZN .* x que lui donne
#      l'adaptateur (x : multiplicateurs des gains de Ziegler-Nichols). Sans
#      adaptation, x = (1, 1, 1) : c'est le PID de Ziegler-Nichols.
#   2. Observateur (inchange, etape 3) : filtre de Kalman etendu sur
#      [Vout, iL, Vin_eff] a charge nominale ; correction par la mesure, puis
#      prediction d'un pas avec la fraction de conduction appliquee.
#   3. A la fin de CHAQUE fenetre de 110 periodes (0.5 ms), sans seuil :
#      5 iterations d'Adam (alpha = 1e-2, beta1 = 0.9, beta2 = 0.999,
#      eps = 1e-7, Ito et Wasa p. 5) sur x, depart a chaud (x de la fenetre
#      precedente), moments remis a zero, projection sur la boite
#      (boite_gains_pinn_b.json) apres chaque iteration (Algorithme 1,
#      ligne 8). Iteration en temps reel (Diehl, Bock et Schloder 2005) :
#      le probleme est celui d'Ito et Wasa, resolu progressivement le long
#      de la trajectoire au lieu d'etre resolu jusqu'a convergence a chaque
#      pas. Cout (eq. 13a-13b, rapports du cas masse-ressort, p. 10,
#      normalises par Q) :
#        J = moyenne sur l'horizon de 1/2 (e^2 + W_U u^2) + W_F |x|^2,
#        W_U = R/Q = 1e-5, W_F = mu/Q = 1e-3.
#      Horizon : 110 pas depuis l'etat estime, le bloc PID lui-meme dans la
#      boucle (integrateur, filtre de derivee, saturation, clamping), etats
#      initiaux = etats reels du bloc, consigne courante, predicteur = PINN
#      (pinn_pid_modele.mat) ; variante "plafond" : modele physique nominal.
#      Gradient : retropropagation dans le temps ecrite a la main (bloc,
#      modulation, predicteur) ; saturation : valeur exacte vers l'avant,
#      pente PENTE_SAT vers l'arriere hors des bornes (0.01, comme la
#      version 1) ; clamping : interrupteur fige pendant la derivation.
#   Les gains sortis par l'adaptateur ne dependent que de son etat : ceux
#   d'une fin de fenetre servent a partir du pas suivant.
#
# CONTROLES (avant tout calcul sur les onze essais)
#   - gradient de l'horizon contre differences finies, hors saturation
#     (pente de la version retenue) et en saturation avec clamping actif
#     (pente 0, derivee exacte) ;
#   - sans adaptation, ecart 0 sur d au PID de Ziegler-Nichols (S1, S8b).
#
# FICHIERS NECESSAIRES (dans le meme dossier que ce script)
#   banc_commun.py (version 2.1), scenarios_communs.json, scenario_S*.mat,
#   predictions_banc_pid_fige.json, boite_gains_pinn_b.json,
#   pinn_pid_modele.mat (entrainement_pinn.py).
#
# CE QUE PRODUIT CE SCRIPT
#   predictions_banc_pinn_pid.json, banc_pinn_pid_resultats.json,
#   banc_pinn_pid.png. Le bloc MATLAB (pinn_pid_adaptatif.m) et ses fichiers
#   (pinn_pid_reglages.mat, reference_rejeu_pinn_pid.mat) sont encore ceux
#   de la version 1 : ils ne sont ni lus ni ecrits ici.
#
# BIBLIOTHEQUES NECESSAIRES (pip install numpy scipy matplotlib)
#
# COMMENT LANCER CE SCRIPT
#   python banc_pinn_pid.py      (quatre processus ; cinq a dix minutes)
#
# ORDRE D'EXECUTION (PINN-PID B)
#   1. boite_gains_pinn_b.py ; 2. mise_au_point_pinn_pid_b.py ; 3. ce script.
# =============================================================================


# %% ETAPE 0 : bibliotheques, reglages et definitions du banc commun

import os                                     # chemins de fichiers
import json                                   # lecture et ecriture au format texte
import time                                   # duree d'execution
import types                                  # resultats legers renvoyes par les processus
import multiprocessing as mp                  # essais en parallele (un processus par essai)
import numpy as np                            # calcul numerique
from scipy.io import loadmat                  # fichiers .mat
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
TCN = TC * PID_N                              # Tc x N du filtre de derivee
L_MOD, C_MOD = L_BOB, C_CONV                  # L et C du modele du regulateur (le circuit peut etre perturbe a part)
K_ZN = np.array([PID_P, PID_I, PID_D])       # Ziegler-Nichols, gains du bloc PID [P, I, D]

# Boite des gains (boite_gains_pinn_b.py : meme critere que la version 1, loi du bloc parallele)
with open(os.path.join(DOSSIER_PINN, "boite_gains_pinn_b.json"), encoding="utf-8") as f:
    BOITE = json.load(f)
if np.max(np.abs(np.array(BOITE["K_depart"]) - K_ZN) / K_ZN) > 1e-12:
    raise RuntimeError("boite_gains_pinn_b.json n'a pas ete calcule avec les gains de Ziegler-Nichols de ce banc.")
X_MIN = np.array(BOITE["multiplicateurs_min"])   # bornes de la boite en multiplicateurs de ZN
X_MAX = np.array(BOITE["multiplicateurs_max"])

# Reglages du PINN-PID B (fixes avant les essais, criteres_pinn_pid.txt)
REGLAGES = {"NH": float(NF), "ALPHA": 0.01, "BETA1": 0.9, "BETA2": 0.999, "EPS_ADAM": 1e-7, "N_ADAM": 5.0,
            "W_U": 1e-5, "W_F": 1e-3, "PENTE_SAT": 0.01,
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
print(f"Boite (multiplicateurs de ZN) : P de {X_MIN[0]:.3f} a {X_MAX[0]:.3f}, I de {X_MIN[1]:.3f} a {X_MAX[1]:.3f}, "
      f"D de {X_MIN[2]:.3f} a {X_MAX[2]:.3f} ; depart a Ziegler-Nichols (1, 1, 1).")
print(f"PINN : {len(COUCHES) - 1} couches cachees de {COUCHES[0][0].shape[1]} neurones "
      f"(candidat {str(MODELE['CANDIDAT'][0])}, plage {str(MODELE['PLAGE'][0])}).")


def titre(texte):
    """Bandeau de titre dans la console."""
    print("\n" + "=" * 78 + "\n " + texte + "\n" + "=" * 78, flush=True)


# %% ETAPE 1 : predicteurs, observateur, horizon et regulateur

# Table du modele physique moyen par tranche a charge nominale (inchangee) :
#   x(fin) = PHI(s) x(debut) + GAM(s) (s Vin - (1 - s) Vf) / L.
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
    """Filtre de Kalman etendu sur [Vout, iL, Vin_eff], charge nominale (inchange)."""

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


def horizon(x, x0, bloc0, r, k1, vin, pas_pred, NH, pente=None, grad=True):
    """Simule NH pas a partir de l'etat x0 = (v, iL) (instant k1) avec le
    bloc PID parallele de gains K = K_ZN .* x, partant des etats du bloc
    bloc0 = (xI, xF), et le predicteur pas_pred. Renvoie le cout
      J = moyenne de 1/2 (e^2 + W_U u^2) + W_F |x|^2
    et son gradient par rapport a x (retropropagation dans le temps)."""
    R = REGLAGES
    pente = R["PENTE_SAT"] if pente is None else pente
    WU = R["W_U"]
    P, I, D = K_ZN * x
    xI, xF = bloc0
    v, i = x0
    pile = []                                 # valeurs gardees pour la retropropagation
    J = 0.0
    for j in range(NH):
        e = r - v                             # erreur predite
        derivee = PID_N * (D * e - xF)        # bloc PID : memes operations que BlocPID
        b = P * e + xI + derivee
        if b < D_MIN:
            u, du = D_MIN, pente
        elif b > D_MAX:
            u, du = D_MAX, pente
        else:
            u, du = b, 1.0
        entree_I = I * e
        integre = not ((b != u) and (np.sign(entree_I) == np.sign(b - u)))   # clamping
        ph = ((k1 + j) * NREG) % NPER         # phase de la porteuse
        s, ds = s_continu(u, ph)
        vn, inn, Pm, dvs, dis, _, _ = pas_pred(v, i, s, vin)
        J += 0.5 * (e * e + WU * u * u)
        pile.append((e, u, du, ds, integre, Pm, dvs, dis))
        if integre:
            xI = xI + TC * entree_I
        xF = xF + TC * derivee
        v, i = vn, inn
    J = J / NH + R["W_F"] * float(x @ x)
    if not grad:
        return J, None
    gK = np.zeros(3)                          # gradient par rapport a [P, I, D]
    lv = li = lxI = lxF = 0.0                 # adjoints de v, iL, xI, xF (etat suivant)
    for j in range(NH - 1, -1, -1):
        e, u, du, ds, integre, Pm, dvs, dis = pile[j]
        gu = WU * u / NH + (lv * dvs + li * dis) * ds
        gb = gu * du
        gder = gb + lxF * TC                  # derivee entre dans u et dans xF'
        gK[0] += gb * e
        gK[2] += gder * PID_N * e
        ge = e / NH + gb * P + gder * PID_N * D
        if integre:
            gK[1] += lxI * TC * e
            ge += lxI * TC * I
        gxI = gb + lxI
        gxF = lxF - gder * PID_N
        lv_new = Pm[0, 0] * lv + Pm[1, 0] * li - ge
        li_new = Pm[0, 1] * lv + Pm[1, 1] * li
        lv, li, lxI, lxF = lv_new, li_new, gxI, gxF
    return J, gK * K_ZN + 2 * R["W_F"] * x


class BlocPID:
    """Le bloc "PID Controller" de la base commune (memes operations que
    PIDClassique du banc commun), gains P, I, D recus de l'exterieur a chaque
    pas. Conditions initiales : integrateur 0.5, filtre 0.01."""

    def __init__(self):
        self.xI = PID_CI_INTEGRATEUR
        self.xF = PID_CI_FILTRE

    def pas(self, e, K):
        P, I, D = K
        derivee = PID_N * (D * e - self.xF)
        u = P * e + self.xI + derivee
        u_sat = min(max(u, D_MIN), D_MAX)
        entree_I = I * e
        if not ((u != u_sat) and (np.sign(entree_I) == np.sign(u - u_sat))):
            self.xI += TC * entree_I
        self.xF += TC * derivee
        return u_sat


class AdaptateurPINN:
    """Observateur et optimisation des gains. Entrees a chaque pas : erreur
    e, mesure de Vout, commande u et etats (xI, xF) du bloc apres le pas.
    Sortie : gains K = K_ZN .* x du bloc PID, qui ne dependent que de l'etat
    (changes en fin de fenetre, utilises a partir du pas suivant). Les
    arguments servent aux variantes ; leurs valeurs par defaut sont celles
    de la methode."""

    def __init__(self, predicteur="pinn", adapter=True, seuil=None, svin=None):
        r = REGLAGES
        if predicteur == "pinn":
            self.pas_pred = pinn_pas          # le PINN de l'etape 2
        elif predicteur == "modele":
            self.pas_pred = modele_pas        # plafond : le modele physique nominal
        else:
            raise ValueError(predicteur)
        self.adapter = adapter
        self.seuil = seuil                    # None : optimisation a chaque fenetre (la methode)
        self.svin = r["SIG_VIN"] if svin is None else svin
        self.NH, self.n_adam = int(r["NH"]), int(r["N_ADAM"])
        self.x = np.ones(3)                   # multiplicateurs de Ziegler-Nichols
        self.K = K_ZN * self.x
        self.obs = None
        self.k = 0                            # numero de la periode Tc
        self.cpt, self.se2 = 0, 0.0           # fenetre courante
        self.journal = []                     # une ligne par fenetre

    def mise_a_jour(self, e, mesure, u, xI, xF):
        k = self.k
        if self.obs is None:
            self.obs = Observateur(mesure, self.svin)
        self.obs.mise_a_jour(mesure)          # 1. correction de l'observateur
        r = e + mesure                        # consigne courante
        ph = (k * NREG) % NPER                # 2. prediction de l'observateur avec la fraction appliquee
        s_app = min(max(int(np.ceil(u * NPER)) - ph, 0), NREG) / NREG
        self.obs.prediction(s_app)
        self.se2 += e * e                     # 3. fenetre
        self.cpt += 1
        self.k += 1
        if self.cpt >= NF:
            eff = np.sqrt(self.se2 / NF)
            ancien = self.x.copy()
            adapte, Jfin = False, float("nan")
            if self.adapter and (self.seuil is None or eff > self.seuil):
                Jfin = self.optimiser(r, xI, xF)
                adapte = True
            self.journal.append({"k": k, "eff": float(eff), "adapte": adapte, "J": Jfin,
                                 "change": bool(np.any(self.x != ancien)), "x": self.x.copy(), "K": self.K.copy(),
                                 "vin_eff": float(self.obs.x[2]), "iL": float(self.obs.x[1])})
            self.cpt, self.se2 = 0, 0.0

    def optimiser(self, r, xI, xF):
        """5 iterations d'Adam sur x depuis x courant (depart a chaud),
        horizon depuis l'etat estime et l'etat du bloc, projection sur la
        boite apres chaque iteration."""
        R = REGLAGES
        x0 = (float(self.obs.x[0]), float(self.obs.x[1])); vin = float(self.obs.x[2])
        th = self.x.copy()
        m = np.zeros(3); vv = np.zeros(3)     # moments d'Adam, remis a zero (Ito et Wasa, p. 5)
        b1t, b2t = 1.0, 1.0
        J = float("nan")
        for it in range(1, self.n_adam + 1):
            b1t *= R["BETA1"]; b2t *= R["BETA2"]
            J, g = horizon(th, x0, (xI, xF), r, self.k, vin, self.pas_pred, self.NH)
            m = R["BETA1"] * m + (1 - R["BETA1"]) * g
            vv = R["BETA2"] * vv + (1 - R["BETA2"]) * g * g
            th = th - R["ALPHA"] * (m / (1 - b1t)) / (np.sqrt(vv / (1 - b2t)) + R["EPS_ADAM"])
            th = np.minimum(np.maximum(th, X_MIN), X_MAX)       # projection sur la boite (Algorithme 1, ligne 8)
        self.x = th
        self.K = K_ZN * th
        return float(J)


class PINNPIDB:
    """Montage : adaptateur -> gains -> bloc PID de la base commune -> u, et
    u (avec les etats du bloc) renvoye a l'adaptateur."""
    utilise_mesure = True

    def __init__(self, **options):
        self.adapt = AdaptateurPINN(**options)
        self.bloc = BlocPID()
        self.journal = self.adapt.journal
        self.K_pas = []

    def pas(self, e, mesure):
        K = self.adapt.K                       # sortie de l'adaptateur (son etat seulement)
        self.K_pas.append(K)
        u = self.bloc.pas(e, K)
        self.adapt.mise_a_jour(e, mesure, u, self.bloc.xI, self.bloc.xF)
        return u


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


# Controle 1 du gradient : hors saturation, pente de la methode
def ecart_gradient(x, x0, bloc0, r, k1, vin, pente, h_rel=1e-6):
    _, g_a = horizon(x, x0, bloc0, r, k1, vin, pinn_pas, NF, pente=pente)
    ecart = 0.0
    for m_ in range(3):
        h_ = x[m_] * h_rel
        xp, xm = x.copy(), x.copy(); xp[m_] += h_; xm[m_] -= h_
        fd = (horizon(xp, x0, bloc0, r, k1, vin, pinn_pas, NF, pente=pente, grad=False)[0]
              - horizon(xm, x0, bloc0, r, k1, vin, pinn_pas, NF, pente=pente, grad=False)[0]) / (2 * h_)
        ecart = max(ecart, abs(fd - g_a[m_]) / abs(fd))
    return ecart


X_ESSAI = np.array([1.3, 0.7, 1.6])           # un point interieur de la boite
ECART_GRAD = ecart_gradient(X_ESSAI, (99.5, 20.0), (0.5, 7.3227e-6 * 0.5), 100.0, 7, 200.0, None)


def pas_en_butee(x, x0, bloc0, r, k1, vin):
    """Nombre de pas de l'horizon ou la sortie du bloc est en butee (et ou le clamping coupe l'integrateur)."""
    P_, I_, D_ = K_ZN * x
    xI, xF = bloc0; v, i = x0; n_sat = n_cl = 0
    for j in range(NF):
        e = r - v; der = PID_N * (D_ * e - xF); b = P_ * e + xI + der; u = min(max(b, D_MIN), D_MAX)
        integre = not ((b != u) and (np.sign(I_ * e) == np.sign(b - u)))
        n_sat += int(b != u); n_cl += int(not integre)
        s, _ = s_continu(u, ((k1 + j) * NREG) % NPER)
        v, i, *_ = pinn_pas(v, i, s, vin)
        if integre:
            xI += TC * I_ * e
        xF += TC * der
    return n_sat, n_cl


# Controle 2 : horizons ou la sortie passe une partie du temps en butee (haute puis basse), clamping actif,
# pente 0 (derivee exacte de la loi saturee)
CAS_SAT = [((99.0, 22.0), (0.55, 7.3227e-6)), ((102.0, 22.0), (0.5, -2 * 7.3227e-6))]
ECART_GRAD_SAT = max(ecart_gradient(X_ESSAI, x0_, b0_, 100.0, 7, 200.0, 0.0) for x0_, b0_ in CAS_SAT)
BUTEES = [pas_en_butee(X_ESSAI, x0_, b0_, 100.0, 7, 200.0) for x0_, b0_ in CAS_SAT]
print(f"Gradient de l'horizon contre differences finies : ecart relatif maximal {ECART_GRAD:.1e} (hors saturation), "
      f"{ECART_GRAD_SAT:.1e} (pente 0 ; pas en butee / pas sous clamping sur 110 : "
      + ", ".join(f"{a} / {b}" for a, b in BUTEES) + ").")
if ECART_GRAD > 1e-4 or ECART_GRAD_SAT > 1e-4:
    raise RuntimeError("Le gradient de l'horizon ne correspond pas aux differences finies.")


# Evaluation d'un regulateur sur des essais, un processus par essai
_FABRIQUE, _ESSAIS_EVAL = None, None


def _un_essai(code):
    reg = _FABRIQUE()
    sc = _ESSAIS_EVAL[code]
    sim = simuler(reg, sc)
    o = grandeurs(sim, sc)
    e = sim["consigne"] - sim["v"]
    leger = types.SimpleNamespace(journal=getattr(reg, "journal", None),
                                  K_pas=np.array(reg.K_pas) if hasattr(reg, "K_pas") else None)
    return code, {"o": o, "IAE_dem": float(np.sum(np.abs(e[:K30])) * TC),
                  "revenus": bool(all(ev["revenu"] for ev in o["evenements"])), "reg": leger, "sim": sim}


def evaluer(fabrique, codes=None, essais=None, processus=4):
    """Simule un nouveau regulateur (fabrique()) sur chaque essai."""
    global _FABRIQUE, _ESSAIS_EVAL
    _FABRIQUE, _ESSAIS_EVAL = fabrique, (essais or ESSAIS)
    codes = codes or list(_ESSAIS_EVAL)
    if processus > 1 and len(codes) > 1:
        with mp.get_context("fork").Pool(min(processus, len(codes))) as pool:
            res = dict(pool.map(_un_essai, codes, chunksize=1))
    else:
        res = dict(_un_essai(c) for c in codes)
    return {c: res[c] for c in codes}


# %% ETAPE 2 : references

def termes(res):
    """Les 13 termes du cout (10 IAE apres 30 ms, 3 IAE de demarrage)."""
    return np.array([res[c]["o"]["IAE"] for c in CODES_IAE] + [res[c]["IAE_dem"] for c in CODES_DEM])


def non_revenus(res):
    return [c for c in res if not res[c]["revenus"]]


def multiplicateurs(res, code):
    """Multiplicateurs de ZN a la fin de chaque fenetre (une ligne par fenetre)."""
    return np.array([x["x"] for x in res[code]["reg"].journal])


if __name__ == "__main__":
    titre("ETAPE 2 : les references")
    REF = {"Ziegler-Nichols": evaluer(lambda: PIDClassique()),
           "meilleur PID fige": evaluer(lambda: PIDParallele(GAINS_FIGE["P"], GAINS_FIGE["I"], GAINS_FIGE["D"]))}
    T_ZN = termes(REF["Ziegler-Nichols"])
    J_FIGE = float(np.mean(termes(REF["meilleur PID fige"]) / T_ZN))
    print(f"  Meilleur PID fige sur grille : J = {J_FIGE:.3f} (0.738 attendu).")

    # %% ETAPE 3 : PINN-PID B sur les onze essais, controle d'identite

    titre("ETAPE 3 : PINN-PID B (sans adaptation : le PID de Ziegler-Nichols lui-meme)")
    fige = evaluer(lambda: PINNPIDB(adapter=False), ["S1", "S8b"])
    ECART_ZN = max(float(np.max(np.abs(fige[c]["sim"]["d"] - REF["Ziegler-Nichols"][c]["sim"]["d"]))) for c in fige)
    print(f"  Controle : PINN-PID B sans adaptation contre Ziegler-Nichols (S1, S8b), ecart maximal sur d : {ECART_ZN:.1e}.")
    if ECART_ZN != 0.0:
        raise RuntimeError("Sans adaptation, le PINN-PID B ne redonne pas le PID de Ziegler-Nichols a l'identique.")

    def bilan(nom, res):
        r_ = termes(res) / T_ZN
        J = float(np.mean(r_))
        non = non_revenus(res)
        print(f"\n  {nom} : J = {J:.3f} (apres 30 ms {np.mean(r_[:10]):.3f}, demarrage {np.mean(r_[10:]):.3f}) ; "
              f"{'tous les evenements reviennent' if not non else 'pas revenus : ' + ', '.join(non)}")
        for code, r in res.items():
            o = r["o"]; X = multiplicateurs(res, code)
            print(f"    {code:4s} depassement {o['depassement_pct']:5.1f} %, IAE {o['IAE'] * 1e3:7.2f} mV.s, dem. "
                  f"{r['IAE_dem'] * 1e3:7.2f} mV.s, efficace {o['e_eff_V'] * 1e3:6.1f} mV ; x final "
                  f"({X[-1, 0]:.3f}, {X[-1, 1]:.3f}, {X[-1, 2]:.3f}), x apres 30 ms de ({X[59:, 0].min():.2f}, "
                  f"{X[59:, 1].min():.2f}, {X[59:, 2].min():.2f}) a ({X[59:, 0].max():.2f}, {X[59:, 1].max():.2f}, "
                  f"{X[59:, 2].max():.2f})", flush=True)
        return J

    t0 = time.time()
    PINN = evaluer(lambda: PINNPIDB())
    J_PINN = bilan("PINN-PID B", PINN)
    print(f"  ({time.time() - t0:.0f} s)")

    # %% ETAPE 4 : ablations (rapportees, jamais choisies) et sensibilite

    titre("ETAPE 4 : ablations (rapportees, jamais choisies)")
    X_FIN_S8B = multiplicateurs(PINN, "S8b")[-1]
    ABLATIONS = {"Plafond (modele physique nominal a la place du PINN)": lambda: PINNPIDB(predicteur="modele"),
                 "Declenchement a 0.1 V (version 1)": lambda: PINNPIDB(seuil=0.1),
                 "PID fige aux gains finaux du PINN-PID B sur S8b": lambda: PIDParallele(*(K_ZN * X_FIN_S8B))}
    RES_ABL, J_ABL = {}, {}
    for nom, fab in ABLATIONS.items():
        t0 = time.time()
        RES_ABL[nom] = evaluer(fab)
        r_ = termes(RES_ABL[nom]) / T_ZN
        J_ABL[nom] = float(np.mean(r_))
        print(f"  {nom:52s} J = {J_ABL[nom]:.3f} ({np.mean(r_[:10]):.3f} / {np.mean(r_[10:]):.3f}) ; non revenus : "
              f"{','.join(non_revenus(RES_ABL[nom])) or '-'} ({time.time() - t0:.0f} s)", flush=True)
    print(f"  (gains finaux S8b x({X_FIN_S8B[0]:.3f}, {X_FIN_S8B[1]:.3f}, {X_FIN_S8B[2]:.3f}))")

    titre("ETAPE 4b : sensibilite (L ou C a +-0.1 %)")
    L_NOM, C_NOM = L_BOB, C_CONV
    SENSIBILITE = []
    for nom_p, fl, fc in (("L - 0.1 %", 0.999, 1.0), ("L + 0.1 %", 1.001, 1.0), ("C - 0.1 %", 1.0, 0.999),
                          ("C + 0.1 %", 1.0, 1.001)):
        L_BOB, C_CONV = L_NOM * fl, C_NOM * fc   # seul le circuit change ; le modele du regulateur reste nominal
        t_zn = termes(evaluer(lambda: PIDClassique()))
        r_p = evaluer(lambda: PINNPIDB())
        J_p = float(np.mean(termes(r_p) / t_zn))
        SENSIBILITE.append({"circuit": nom_p, "J": J_p, "non_revenus": non_revenus(r_p)})
        print(f"  {nom_p:10s} J = {J_p:.3f} ; non revenus : {','.join(non_revenus(r_p)) or '-'}", flush=True)
    L_BOB, C_CONV = L_NOM, C_NOM

    titre("ETAPE 4c : marges de phase du modele moyen aux gains finaux")
    W_F = np.logspace(np.log10(2 * np.pi * 20.0), np.log10(np.pi / TC * 0.999), 8000)
    Z_F = np.exp(1j * W_F * TC)

    def marge(K, R, V):
        """Marge de phase (degres) du bloc parallele de gains K sur le modele
        moyen sans pertes au coin (R, V) (memes formules que boite_gains_pinn_b.py)."""
        num, den, _ = cont2discrete(([V], [L_BOB * C_CONV, L_BOB / R, 1.0]), TC, method="zoh")
        G = np.polyval(np.squeeze(num), Z_F) / np.polyval(den, Z_F)
        Cz = K[0] + K[1] * TC / (Z_F - 1.0) + K[2] * PID_N * (Z_F - 1.0) / (Z_F - 1.0 + TC * PID_N)
        boucle = Cz * G
        lm = np.log(np.abs(boucle)); ph = np.unwrap(np.angle(boucle))
        j = np.where(np.diff(np.sign(lm)) != 0)[0]
        if len(j) == 0:
            return 180.0
        f = lm[j] / (lm[j] - lm[j + 1])
        phase = ph[j] + f * (ph[j + 1] - ph[j])
        return float(((np.degrees(phase) + 360.0) % 360.0 - 180.0).min())

    MARGES = {}
    for nom, x_ in [("depart (Ziegler-Nichols)", np.ones(3))] + [(f"final {c}", multiplicateurs(PINN, c)[-1])
                                                                for c in ("S1", "S3", "S8a", "S8b", "S9")]:
        nominal = min(marge(K_ZN * x_, R, V) for R in (4.0, 5.0, 6.0) for V in (160.0, 200.0, 240.0))
        leger = min(marge(K_ZN * x_, R, V) for R in (25.0, 98.0) for V in (160.0, 200.0, 240.0))
        MARGES[nom] = {"x": x_.tolist(), "marge_nominale_deg": nominal, "marge_legere_deg": leger}
        print(f"  {nom:26s} x({x_[0]:.3f}, {x_[1]:.3f}, {x_[2]:.3f}) : marge minimale {nominal:5.1f} deg (4 a 6 ohms), "
              f"{leger:5.1f} deg (25 et 98 ohms)")

    # %% ETAPE 5 : comparaison et previsions

    titre("ETAPE 5 : PINN-PID B face aux references ; previsions de criteres_pinn_pid.txt")
    TOUS = {"Ziegler-Nichols": REF["Ziegler-Nichols"], "meilleur PID fige": REF["meilleur PID fige"], "PINN-PID B": PINN}
    J_TOUS = {n: float(np.mean(termes(r) / T_ZN)) for n, r in TOUS.items()}
    DECOMP = {n: (float(np.mean((termes(r) / T_ZN)[:10])), float(np.mean((termes(r) / T_ZN)[10:]))) for n, r in TOUS.items()}
    print("  " + " " * 28 + "".join(f"{n:>20s}" for n in TOUS))
    print("  " + f"{'cout J':28s}" + "".join(f"{J_TOUS[n]:20.3f}" for n in TOUS))
    print("  " + f"{'apres 30 ms / demarrage':28s}" + "".join(f"{DECOMP[n][0]:13.3f} /{DECOMP[n][1]:5.3f}" for n in TOUS))
    print("  " + f"{'evenements non revenus':28s}" + "".join(f"{(','.join(non_revenus(TOUS[n])) or '-'):>20s}" for n in TOUS))
    for code in ESSAIS:
        print("  " + f"{code + ' IAE mV.s':28s}" + "".join(f"{TOUS[n][code]['o']['IAE'] * 1e3:20.2f}" for n in TOUS))
    print("  " + f"{'S1 demarrage mV.s':28s}" + "".join(f"{TOUS[n]['S1']['IAE_dem'] * 1e3:20.2f}" for n in TOUS))

    PREV = json.load(open(os.path.join(DOSSIER_PINN, "previsions_pinn_pid_b.json"), encoding="utf-8"))

    def change_pendant(code, t0_, t1_):
        """Plus grand ecart d'un multiplicateur, sur les fenetres finies dans ]t0, t1], a sa valeur a t0."""
        X = multiplicateurs(PINN, code)
        n0, n1 = int(round(t0_ / 0.5e-3)), int(round(t1_ / 0.5e-3))
        return float(np.max(np.abs(X[n0:n1] - X[n0 - 1])))

    X_S1 = multiplicateurs(PINN, "S1")
    derive = {c: float(np.max(np.abs(multiplicateurs(PINN, c)[59:] - X_S1[59:]))) for c in ("S7a", "S7b")}
    eff_S7b = (PINN["S7b"]["o"]["e_eff_V"], REF["Ziegler-Nichols"]["S7b"]["o"]["e_eff_V"])
    iae = {c: PINN[c]["o"]["IAE"] * 1e3 for c in ESSAIS}
    s1dem = PINN["S1"]["IAE_dem"] * 1e3
    dF1, dF2 = change_pendant("S2", 0.050, 0.055), change_pendant("S3", 0.050, 0.055)
    P = PREV["bornes"]
    VERDICT = {
        "P1": (P["P1"][0] <= J_PINN <= P["P1"][1], f"J = {J_PINN:.3f}"),
        "P2": (P["P2"][0] <= DECOMP["PINN-PID B"][0] <= P["P2"][1], f"apres 30 ms {DECOMP['PINN-PID B'][0]:.3f}"),
        "P3": (P["P3"][0] <= DECOMP["PINN-PID B"][1] <= P["P3"][1], f"demarrage {DECOMP['PINN-PID B'][1]:.3f}"),
        "P4": (P["P4"][0] <= s1dem <= P["P4"][1], f"S1 demarrage {s1dem:.2f} mV.s (ZN 93.77)"),
        "P5": (P["P5"][0] <= iae["S2"] <= P["P5"][1], f"S2 {iae['S2']:.2f} mV.s (ZN 2.84)"),
        "P6": (P["P6"][0] <= iae["S3"] <= P["P6"][1], f"S3 {iae['S3']:.2f} mV.s (ZN 8.67)"),
        "P7": (P["P7"][0] <= iae["S8a"] <= P["P7"][1], f"S8a {iae['S8a']:.2f} mV.s (ZN 12.07)"),
        "P8": (len(non_revenus(PINN)) == 0, "non revenus : " + (",".join(non_revenus(PINN)) or "aucun")),
        "P9": (min(dF1, dF2) >= P["P9"], f"variation maximale d'un multiplicateur de 50 a 55 ms : S2 {dF1:.3f}, S3 {dF2:.3f}"),
        "P10": (max(derive.values()) <= P["P10"][0] and eff_S7b[0] <= P["P10"][1] * eff_S7b[1],
                f"ecart maximal a S1 apres 30 ms : S7a {derive['S7a']:.3f}, S7b {derive['S7b']:.3f} ; efficace S7b "
                f"{eff_S7b[0] * 1e3:.1f} mV (ZN {eff_S7b[1] * 1e3:.1f})"),
    }
    for k_, (ok, txt) in VERDICT.items():
        print(f"  {k_:3s} {'juste' if ok else 'FAUSSE'} : {txt}")
    AUTRES = {"PSO-PID": (87.62, 2.04, 5.46, 2.46), "ELM-PID B": (93.72, 2.41, 6.41, 2.96),
              "Fuzzy-PID": (110.91, 2.43, 7.94, 4.12), "Ziegler-Nichols": (93.77, 2.84, 8.67, 12.07)}
    mien = (s1dem, iae["S2"], iae["S3"], iae["S8a"])
    CLASSEMENT = {}
    for q_, nom_q in enumerate(("S1 demarrage", "S2", "S3", "S8a")):
        liste = sorted([(v[q_], n) for n, v in AUTRES.items()] + [(mien[q_], "PINN-PID B")])
        CLASSEMENT[nom_q] = [f"{n} {v:.2f}" for v, n in liste]
        print(f"  Classement {nom_q:13s} : " + " < ".join(CLASSEMENT[nom_q]))

    # %% ETAPE 6 : fichiers, resultats et figure

    titre("ETAPE 6 : fichiers")
    pas_1ms = int(round(1e-3 / TC))
    predictions = {"version": 2, "Te": TC,
                   "regulateur": "PINN-PID B (bloc PID de la base commune a gains externes, gains optimises par Adam "
                                 "a chaque fenetre, iteration en temps reel, boite boite_gains_pinn_b.json)",
                   "reglages": REGLAGES, "boite": {"x_min": X_MIN.tolist(), "x_max": X_MAX.tolist()},
                   "K_depart": K_ZN.tolist(),
                   "controle": {"ecart_vecteurs_test": ECART_TEST, "ecart_sans_adaptation_ZN": ECART_ZN,
                                "ecart_gradient": ECART_GRAD, "ecart_gradient_saturation": ECART_GRAD_SAT},
                   "essais": {}}
    for code, r in PINN.items():
        Kp = r["reg"].K_pas
        predictions["essais"][code] = {"grandeurs": r["o"],
                                       "v_toutes_les_ms": r["sim"]["v"][::pas_1ms].tolist(),
                                       "iL_toutes_les_ms": r["sim"]["iL"][::pas_1ms].tolist(),
                                       "d_moyen_par_ms": [float(np.mean(r["sim"]["d"][i:i + pas_1ms]))
                                                          for i in range(0, len(r["sim"]["d"]) - pas_1ms + 1, pas_1ms)],
                                       "K_toutes_les_ms": Kp[::pas_1ms].tolist(),
                                       "K_final": r["reg"].journal[-1]["K"].tolist()}
    with open(os.path.join(DOSSIER_PINN, "predictions_banc_pinn_pid.json"), "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=1, allow_nan=False)
    print("  predictions_banc_pinn_pid.json ecrit.")

    def resume_essais(res):
        return {c: {"grandeurs": res[c]["o"], "IAE_dem": res[c]["IAE_dem"], "revenus": res[c]["revenus"]} for c in res}

    sortie = {"version": 2, "reglages": REGLAGES, "boite": predictions["boite"], "J": J_TOUS, "decomposition": DECOMP,
              "J_ablations": J_ABL, "sensibilite": SENSIBILITE, "marges": MARGES,
              "previsions": {k_: {"juste": bool(v[0]), "detail": v[1]} for k_, v in VERDICT.items()},
              "classement": CLASSEMENT,
              "references": {n: resume_essais(TOUS[n]) for n in TOUS},
              "ablations": {n: resume_essais(RES_ABL[n]) for n in RES_ABL},
              "multiplicateurs_par_fenetre": {c: multiplicateurs(PINN, c).tolist() for c in PINN},
              "duree_s": round(time.time() - T_DEBUT, 1)}
    with open(os.path.join(DOSSIER_PINN, "banc_pinn_pid_resultats.json"), "w", encoding="utf-8") as f:
        json.dump(sortie, f, indent=1, allow_nan=False, default=lambda x: None)
    print("  banc_pinn_pid_resultats.json ecrit.")

    fig, axes = plt.subplots(3, 4, figsize=(20, 9.5), sharex="col")
    for col, (code, xlim) in enumerate((("S1", (0, 30)), ("S2", (40, 90)), ("S3", (40, 90)), ("S8b", None))):
        for nom, couleur in (("Ziegler-Nichols", "0.6"), ("meilleur PID fige", "tab:green"), ("PINN-PID B", "tab:blue")):
            sim = TOUS[nom][code]["sim"]
            axes[0, col].plot(sim["t"] * 1e3, sim["v"], lw=0.6, color=couleur, label=nom)
            axes[2, col].plot(sim["t"] * 1e3, sim["iL"], lw=0.4, color=couleur)
        axes[0, col].plot(sim["t"] * 1e3, sim["consigne"], "k--", lw=0.6)
        Kx = PINN[code]["reg"].K_pas / K_ZN
        t_ms = PINN[code]["sim"]["t"] * 1e3
        for i, nom in enumerate(("P", "I", "D")):
            axes[1, col].plot(t_ms, Kx[:, i], lw=1.0, label=nom)
        axes[0, col].set_ylim((85, 115) if code in ("S2", "S3") else (30, 200))
        axes[0, col].set_title(f"{code} : tension de sortie", fontsize=9, loc="left")
        axes[1, col].set_title(f"{code} : gains du PINN-PID B (multiples de ZN)", fontsize=9, loc="left")
        axes[2, col].set_title(f"{code} : courant de la bobine", fontsize=9, loc="left")
        axes[2, col].set_xlabel("temps (ms)")
        if xlim:
            axes[2, col].set_xlim(*xlim)
        for ax in axes[:, col]:
            ax.grid(alpha=0.3)
    axes[0, 0].legend(fontsize=7)
    axes[1, 0].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(DOSSIER_PINN, "banc_pinn_pid.png"), dpi=110)
    plt.close(fig)
    print(f"  banc_pinn_pid.png ecrit. Duree totale : {time.time() - T_DEBUT:.0f} s.")
