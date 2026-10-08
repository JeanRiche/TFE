# =============================================================================
# banc_elm_pid.py
#
# VERSION
#   5 (8 octobre 2026), option B2 : meme bloc PID parallele que l'option B,
#   gains mis a jour A CHAQUE PAS (comme Lu, eq. 16 et 18) au lieu d'une
#   fois par fenetre de 0.5 ms. Methode, modifications M1 a M5 et
#   previsions H1 a H6 : criteres_elm_pid.txt. L'option B (cadence par
#   fenetre) est dans le dossier ELM_PID et reste disponible ici comme
#   ablation (CADENCE_PAS = 0) ; la loi incrementale de Lu est dans
#   ELM_PID_INCREMENTAL.
#   Le bloc MATLAB elm_pid_adaptatif.m de ce dossier est encore celui de
#   l'option B (cadence par fenetre) : il devra etre porte avant toute
#   validation Simulink de B2.
#
# OBJECTIF
#   Faire tourner l'ELM-PID B2 sur le banc commun, sur les onze essais, a
#   cote des references (PID de Ziegler-Nichols, qui est aussi l'ELM-PID
#   sans adaptation, et meilleur PID fige sur grille), mesurer ce que chaque
#   piece apporte (ablations, jamais choisies : cadence par fenetre = option
#   B, sans zone morte par pas, jacobien constant), et verifier les
#   previsions H1 a H6.
#
# L'ELM-PID B2, TEL QU'IL EST CODE ICI
#   A chaque periode Tc = 1/220 000 s :
#   1. Le bloc PID de la base commune (Parallel, derivee filtree N =
#      64 122.9 rad/s, Forward Euler, sortie dans [0.01 ; 0.99], clamping,
#      integrateur a 0.5 et filtre a 0.01 au depart) calcule u a partir de
#      e = consigne - mesure, avec les gains P, I, D que lui donne
#      l'adaptateur (M4). Sans adaptation, c'est le PID de Ziegler-Nichols.
#   2. L'adaptateur recoit e, la mesure de Vout (jamais 100 - e) et u.
#      Sensibilites par pas de u aux gains (regle MIT, Astrom et
#      Wittenmark : derivees calculees comme si les gains etaient
#      constants, sur toute l'histoire) :
#        sP = e(k) ; sI = SI(k), SI(k+1) = SI(k) + Tc e(k) quand l'integrateur
#        du bloc integre (clamping), SI(0) = 0 ;
#        sD = N (e(k) - ef(k)), ef(k+1) = ef(k) + Tc N (e(k) - ef(k)), ef(0) = 0.
#   3. Pas des gains (M5), si u n'est pas en butee, |e(k)| > ZONE_MORTE_PAS
#      et J > 0 : multiplicateurs x = K / K_ZN,
#        phi = J (s .* K_ZN),
#        dx = ETA_PAS e(k) phi / (eps + phi.phi) + alpha (x - x_prec),
#      x + dx garde s'il est admissible (g_interp <= 0), sinon projection
#      M2-M3 sur l'ensemble admissible (ensemble_gains_elm.mat).
#   4. Sur des fenetres de 0.5 ms (110 x Tc), comme dans l'option B :
#      moyennes ybar, dbar ; l'ELM (elm_pid_modele.mat) predit ybar(n) a
#      partir de [ybar(n-1), ybar(n-2), dbar(n), dbar(n-1), dbar(n-2)] et
#      donne J = d ybar(n) / d dbar(n), garde jusqu'a la fenetre suivante ;
#      OS-ELM si la porte M1 est ouverte (aucune butee sur trois fenetres)
#      et |ybar - prediction| > ZONE_MORTE_ESTIMATION. La porte ne
#      concerne plus que l'apprentissage du modele, pas le pas des gains.
#   Les gains sortis par l'adaptateur ne dependent que de son etat : ceux
#   calcules au pas k servent a partir du pas k + 1.
#
# COMMENT LANCER CE SCRIPT
#   python banc_elm_pid.py      (quelques minutes : ablations et
#   sensibilite comprises)
#
# ORDRE D'EXECUTION
#   1. entrainement_elm.py ; 2. ensemble_gains_elm.py ; 3. ce script ;
#   4. Tester_ELM_PID_Rejeu.m ; 5. Construction_ELM_PID.m ;
#   6. verifier_modele_elm_pid.py ; 7. Simuler_ELM_PID.m.
# =============================================================================


# %% ETAPE 0 : bibliotheques, banc commun, modele, ensemble admissible

import os
import json
import time
import numpy as np
from scipy.io import loadmat, savemat
import matplotlib.pyplot as plt

try:
    DOSSIER_ELM = os.path.dirname(os.path.abspath(__file__))
except NameError:
    DOSSIER_ELM = os.getcwd()
with open(os.path.join(DOSSIER_ELM, "banc_commun.py"), encoding="utf-8") as f:
    SOURCE_BANC = f.read()
MARQUE = "# === FIN DES DEFINITIONS DU BANC COMMUN ==="
if MARQUE not in SOURCE_BANC or "iL_max_dem_A" not in SOURCE_BANC:
    raise RuntimeError("banc_commun.py n'est pas la version 2.1 (observation du courant) : prendre la version a jour.")
exec(SOURCE_BANC[:SOURCE_BANC.index(MARQUE)])

T_DEBUT = time.time()
ESSAIS = {sc["code"]: sc for sc in SCENARIOS}
CODES_IAE = ["S1", "S3", "S4", "S5", "S6", "S7a", "S7b", "S8a", "S8b", "S9"]
CODES_DEM = ["S1", "S8a", "S8b"]
K30 = int(round(0.03 / TC))
NF = 110
CODES_REJEU = ["S1", "S3", "S7b", "S8b", "S9"]
K_ZN = np.array([PID_P, PID_I, PID_D])   # Ziegler-Nichols, gains du bloc PID [P, I, D]

REGLAGES = {"ETA": 0.5, "ZONE_MORTE": 0.1, "ZONE_MORTE_ESTIMATION": 0.1, "ALPHA": 0.001, "EPS_PHI": 1e-3,
            "LAMBDA": 1.0, "APPRENDRE": 1.0, "GLISSEMENT": 1.0, "JACOBIEN_CONSTANT": float("nan"),
            "MULT_MIN": 0.25, "MULT_MAX": 4.0, "N_BISSECTIONS": 30.0, "H_GRADIENT": 1e-4,
            "RESTAURATION": 1.0, "N_PROJECTION": 10.0,
            # M5 (option B2) : cadence par pas. Regles ecrites avant tout calcul (criteres_elm_pid.txt, M5) :
            #   ETA_PAS = plus grande valeur 1, 2 ou 5 x 10^n sous Tc / (10 tau_cl), tau_cl = 0.932 ms
            #             (pole de boucle fermee le plus lent, modele moyen, gains de depart, 9 coins nominaux) ;
            #   ZONE_MORTE_PAS (R2 amendee apres E1-E4, amendement unique) = Ms x (q/2 + 3 sigma du capteur),
            #             Ms = 2.3165 : pic de la fonction de sensibilite de la boucle de depart (modele moyen,
            #             pire des 9 coins nominaux : 6 ohms, 160 V, 860 Hz) ; R2 d'origine : q/2 + 3 sigma = 54.41 mV.
            "CADENCE_PAS": 1.0, "ETA_PAS": 2e-4, "MS_DEPART": 2.3165,
            "ZONE_MORTE_PAS": 2.3165 * (2.5 / 4096 * 80 / 2 + 3 * 0.010)}

with open(os.path.join(DOSSIER_ELM, "predictions_banc_pid_fige.json"), encoding="utf-8") as f:
    GAINS_FIGE = json.load(f)["gains"]
with open(os.path.join(DOSSIER_ELM, "entrainement_elm_resultats.json"), encoding="utf-8") as f:
    APPR = json.load(f)
J_REGRESSION = float(APPR["references"]["regression lineaire, ordre 2"]["J_median"])   # constante

MODELE = loadmat(os.path.join(DOSSIER_ELM, "elm_pid_modele.mat"))
if int(MODELE["NF"].item()) != NF or int(MODELE["ORDRE"].item()) != 2:
    raise RuntimeError("elm_pid_modele.mat n'est pas le modele attendu (fenetres de 110 x Tc, ordre 2).")
ENS = loadmat(os.path.join(DOSSIER_ELM, "ensemble_gains_elm.mat"))
G_TABLE = ENS["G_TABLE"].astype(float)
LOG2_MIN, PAS_LOG2 = float(ENS["LOG2_MIN"].item()), float(ENS["PAS_LOG2"].item())
N_TABLE = G_TABLE.shape[0]
if np.max(np.abs(ENS["K_DEPART"].ravel() - K_ZN) / K_ZN) > 1e-12:
    raise RuntimeError("ensemble_gains_elm.mat n'a pas ete calcule avec les gains de Ziegler-Nichols de ce banc.")
print(f"ELM : {MODELE['W'].shape[1]} neurones, ordre {int(MODELE['ORDRE'].item())} ; ensemble admissible : "
      f"{N_TABLE}^3 points, {np.mean(G_TABLE <= 0):.1%} admissibles ; jacobien constant des ablations "
      f"{J_REGRESSION:.4f}.")


def titre(texte):
    print("\n" + "=" * 78 + "\n " + texte + "\n" + "=" * 78)


# %% ETAPE 1 : bloc PID, projection et adaptateur ELM (copie de elm_pid_adaptatif.m)

TCN = TC * PID_N


class BlocPID:
    """Le bloc "PID Controller" de la base commune (memes operations que
    PIDClassique du banc commun), gains P, I, D recus de l'exterieur a chaque
    pas (ports de gains externes du bloc Simulink, comme pour le Fuzzy-PID).
    Conditions initiales du bloc : integrateur 0.5, filtre 0.01."""

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


G_LISTE = G_TABLE.tolist()   # meme table, en listes Python (acces plus rapide, memes valeurs)


def g_interp(x):
    """g de l'ensemble admissible, interpole (trilineaire en log2 des
    multiplicateurs). Memes operations que g_interp du bloc MATLAB.
    Version 5 : memes operations dans le meme ordre que la version 4, en
    nombres Python au lieu de scalaires numpy (resultat identique au bit
    pres, environ 1.5 fois plus rapide ; la cadence par pas l'appelle a
    chaque pas adapte)."""
    u = (np.log2(x) - LOG2_MIN) / PAS_LOG2
    u = np.minimum(np.maximum(u, 0.0), N_TABLE - 1.0)
    i = np.minimum(np.floor(u), N_TABLE - 2.0).astype(int)
    f = (u - i).tolist()
    i0, i1, i2 = i.tolist()
    s = 0.0
    for di in (0, 1):
        wi = f[0] if di else 1.0 - f[0]
        Gi = G_LISTE[i0 + di]
        for dj in (0, 1):
            wj = f[1] if dj else 1.0 - f[1]
            Gij = Gi[i1 + dj]
            for dk in (0, 1):
                wk = f[2] if dk else 1.0 - f[2]
                s += wi * wj * wk * Gij[i2 + dk]
    return s


def gradient_g(x, h):
    """Gradient de g par differences centrees (normale a la frontiere)."""
    gr = np.zeros(3)
    for q in range(3):
        ep = np.zeros(3)
        ep[q] = h
        gr[q] = (g_interp(x + ep) - g_interp(x - ep)) / (2.0 * h)
    return gr


def restaurer(p, gr, r):
    """Restauration (M3) : depuis p (hors de l'ensemble), recul le long de
    -gr jusqu'a la frontiere (doublement puis bissection) ; None si un recul
    de 1 ne suffit pas."""
    lo_, hi_ = r["MULT_MIN"], r["MULT_MAX"]
    nh = gr / np.sqrt(gr @ gr)
    s_ok = 1e-6
    while g_interp(np.minimum(np.maximum(p - s_ok * nh, lo_), hi_)) > 0.0:
        s_ok *= 2.0
        if s_ok > 1.0:
            return None
    s_ko = 0.0 if s_ok == 1e-6 else 0.5 * s_ok
    for _ in range(int(r["N_BISSECTIONS"])):
        m = 0.5 * (s_ko + s_ok)
        if g_interp(np.minimum(np.maximum(p - m * nh, lo_), hi_)) <= 0.0:
            s_ok = m
        else:
            s_ko = m
    return np.minimum(np.maximum(p - s_ok * nh, lo_), hi_)


def projeter(xc, dx, r):
    """Pas dx depuis xc (admissible), projete sur l'ensemble admissible.
    M3 (RESTAURATION = 1) : point admissible le plus proche de la cible
    z = xc + dx, par la methode de projection du gradient de Rosen (1961) :
    depuis le point de sortie, on retire la composante sortante de (z - y)
    le long de la normale, on avance dans le plan tangent, puis on revient
    sur la frontiere le long de la normale (restauration) ; on recommence
    tant que le point se rapproche de z (N_PROJECTION fois au plus).
    M2 seule (RESTAURATION = 0) : glissement puis bissection le long du pas
    tangent (version du calcul du 7 octobre, gardee pour l'ablation).
    Sans glissement : arret au point de sortie."""
    lo_, hi_ = r["MULT_MIN"], r["MULT_MAX"]
    nb = int(r["N_BISSECTIONS"])
    xn = np.minimum(np.maximum(xc + dx, lo_), hi_)
    if g_interp(xn) <= 0.0:
        return xn
    z = xn
    a, b = 0.0, 1.0
    for _ in range(nb):
        m = 0.5 * (a + b)
        if g_interp(np.minimum(np.maximum(xc + m * dx, lo_), hi_)) <= 0.0:
            a = m
        else:
            b = m
    xb = np.minimum(np.maximum(xc + a * dx, lo_), hi_)
    if not r["GLISSEMENT"]:
        return xb
    if r["RESTAURATION"]:
        y = xb
        for _ in range(int(r["N_PROJECTION"])):
            gr = gradient_g(y, r["H_GRADIENT"])
            if gr @ gr == 0.0:
                break
            d = z - y
            sortant = gr @ d
            if sortant > 0.0:
                d = d - sortant / (gr @ gr) * gr
            pt = np.minimum(np.maximum(y + d, lo_), hi_)
            if g_interp(pt) > 0.0:
                pt = restaurer(pt, gr, r)
                if pt is None:
                    break
            if np.sum((z - pt) ** 2) >= np.sum((z - y) ** 2):
                break
            y = pt
        return y
    gr = gradient_g(xb, r["H_GRADIENT"])
    reste = (1.0 - a) * dx
    sortant = gr @ reste
    if sortant > 0.0:
        reste = reste - sortant / (gr @ gr) * gr
    xn = np.minimum(np.maximum(xb + reste, lo_), hi_)
    if g_interp(xn) <= 0.0:
        return xn
    a, b = 0.0, 1.0
    for _ in range(nb):
        m = 0.5 * (a + b)
        if g_interp(np.minimum(np.maximum(xb + m * reste, lo_), hi_)) <= 0.0:
            a = m
        else:
            b = m
    return np.minimum(np.maximum(xb + a * reste, lo_), hi_)


class AdaptateurELM:
    """Copie Python de elm_pid_adaptatif.m (memes reglages, memes noms,
    meme ordre des operations : Tester_ELM_PID_Rejeu.m compare les deux pas
    par pas). Entrees a chaque pas : erreur e, mesure de Vout, commande u
    sortie du bloc PID. Sortie : gains [P I D] du bloc PID. Les gains sortis
    au pas k ne dependent que de l'etat (aucune traversee directe) : ils
    changent a chaque pas adapte (cadence par pas, M5, option B2) ou en fin
    de fenetre (CADENCE_PAS = 0, option B) et servent a partir du pas
    suivant. Les arguments servent aux ablations.
    Version 5 : la cadence par pas n'est pas encore portee dans
    elm_pid_adaptatif.m (seule la cadence par fenetre y est)."""

    def __init__(self, **modif):
        self.r = dict(REGLAGES, **modif)
        r = self.r
        self.eta, self.zm, self.zme = r["ETA"], r["ZONE_MORTE"], r["ZONE_MORTE_ESTIMATION"]
        self.alpha, self.eps, self.lam = r["ALPHA"], r["EPS_PHI"], r["LAMBDA"]
        self.apprendre, self.Jc = bool(r["APPRENDRE"]), r["JACOBIEN_CONSTANT"]
        self.adapter = r.get("ADAPTER", True)
        self.W = MODELE["W"].astype(float)
        self.B = MODELE["B"].astype(float).ravel()
        self.BETA = MODELE["BETA"].astype(float).ravel().copy()
        self.P = MODELE["P0"].astype(float).copy()
        self.XM = MODELE["X_MOY"].astype(float).ravel()
        self.XE = MODELE["X_EC"].astype(float).ravel()
        self.TM = float(MODELE["T_MOY"].item())
        self.TE_ = float(MODELE["T_EC"].item())
        self.n = self.W.shape[1]
        self.x = np.ones(3)                   # multiplicateurs de Ziegler-Nichols
        self.x_prec = self.x.copy()
        self.K = K_ZN * self.x
        self.cpt, self.sy, self.sd, self.se, self.hors = 0, 0.0, 0.0, 0.0, False
        self.SE, self.phiD = 0.0, 0.0          # somme des erreurs et filtre de sensibilite, remis a zero par fenetre
        self.sS1 = self.sS2 = self.sS3 = 0.0
        self.yb1 = self.yb2 = self.db1 = self.db2 = 0.0
        self.sus1 = self.sus2 = True
        self.nfen = 0
        self.journal = []
        # M5 (option B2) : cadence par pas
        self.cadence_pas = bool(r["CADENCE_PAS"])
        self.eta_pas, self.zm_pas = r["ETA_PAS"], r["ZONE_MORTE_PAS"]
        self.SI, self.ef = 0.0, 0.0            # sensibilites par pas (toute l'histoire, regle MIT), nulles au depart
        self.J_pas = float("nan")              # jacobien de la derniere fin de fenetre, garde entre deux fenetres
        self.k = 0                             # numero du pas
        self.pas_changes = []                  # pas k ou les gains ont change (cadence par pas)
        self.n_maj_pas = self.n_proj_pas = 0   # pas de gradient calcules, projections
        self.maj_fen = self.change_fen = 0     # pas adaptes et pas changes dans la fenetre en cours

    def modele(self, x):
        xn = (x - self.XM) / self.XE
        gg = 1.0 / (1.0 + np.exp(-(xn @ self.W + self.B)))
        h = np.concatenate([gg, xn, [1.0]])
        y = (h @ self.BETA) * self.TE_ + self.TM
        dy = ((gg * (1.0 - gg)) * self.BETA[:self.n]) @ self.W.T + self.BETA[self.n:self.n + 5]
        return y, dy[2] / self.XE[2] * self.TE_, h

    def pas_des_gains(self, e, u):
        """M5 (option B2) : un pas de gradient a chaque periode Tc (Lu, eq. 16
        et 18), sur les multiplicateurs x = K / K_ZN.
        Sensibilites de u(k) aux gains, regle MIT (Astrom et Wittenmark) :
        derivees de la loi du bloc calculees comme si les gains etaient
        constants depuis le depart (les gains varient lentement devant la
        boucle, c'est la condition de la regle et l'objet de la regle de
        ETA_PAS) :
          du/dP = e(k) ;
          du/dI = SI(k), SI(k+1) = SI(k) + Tc e(k) si l'integrateur du bloc
                  integre (clamping : pas d'integration si u est en butee
                  haute avec e > 0 ou en butee basse avec e < 0) ;
          du/dD = N (e(k) - ef(k)), ef(k+1) = ef(k) + Tc N (e(k) - ef(k)) :
                  ef est l'erreur passee dans le filtre de derivee du bloc
                  (xF = D ef quand D est constant) ; SI(0) = ef(0) = 0 car
                  les conditions initiales du bloc ne dependent pas des gains.
        Pas calcule si u n'est pas en butee (la sortie ne depend alors plus
        des gains), |e(k)| > ZONE_MORTE_PAS et J > 0."""
        sP, sI, sD = e, self.SI, PID_N * (e - self.ef)
        haut, bas = u >= D_MAX, u <= D_MIN
        if not ((haut and e > 0.0) or (bas and e < 0.0)):
            self.SI += TC * e
        self.ef += TCN * (e - self.ef)
        J = self.J_pas
        if self.adapter and not (haut or bas) and abs(e) > self.zm_pas and J > 0.0:
            phi = J * (np.array([sP, sI, sD]) * K_ZN)
            dx = (self.eta_pas * e / (self.eps + phi @ phi)) * phi + self.alpha * (self.x - self.x_prec)
            xn = np.minimum(np.maximum(self.x + dx, self.r["MULT_MIN"]), self.r["MULT_MAX"])
            if g_interp(xn) > 0.0:             # hors de l'ensemble admissible : projection M2-M3
                xn = projeter(self.x, dx, self.r)
                self.n_proj_pas += 1
            self.n_maj_pas += 1
            self.maj_fen += 1
            self.x_prec = self.x
            if np.any(xn != self.x):
                self.x = xn
                self.K = K_ZN * self.x
                self.pas_changes.append(self.k)
                self.change_fen += 1
        else:
            self.x_prec = self.x               # pas sans mise a jour : increment precedent nul (inertie de Lu)

    def mise_a_jour(self, e, mesure, u):
        if self.cadence_pas:
            self.pas_des_gains(e, u)
        self.k += 1
        # Sensibilite de u(k) a un changement des gains au debut de la fenetre
        # (derivee exacte de la loi du bloc, hors clamping) :
        #   du/dP = e(k) ; du/dI = Tc x (somme des e de la fenetre avant k) ;
        #   du/dD = N (e(k) - phiD(k)), phiD(k+1) = phiD(k) + Tc N (e(k) - phiD(k)), phiD = 0 au debut.
        self.sS1 += e
        self.sS2 += TC * self.SE
        self.sS3 += PID_N * (e - self.phiD)
        self.SE += e
        self.phiD += TCN * (e - self.phiD)
        self.sy, self.sd, self.se = self.sy + mesure, self.sd + u, self.se + e
        if u <= D_MIN or u >= D_MAX:          # sortie du bloc en butee : la fenetre est suspecte
            self.hors = True
        self.cpt += 1
        if self.cpt >= NF:
            self.fin_de_fenetre()

    def fin_de_fenetre(self):
        yb, db, eb = self.sy / NF, self.sd / NF, self.se / NF
        s = np.array([self.sS1, self.sS2, self.sS3]) / NF
        sus, porte, err, J, adapte, appris, change = self.hors, False, float("nan"), float("nan"), False, False, False
        if self.nfen >= 2:
            xin = np.array([self.yb1, self.yb2, db, self.db1, self.db2])
            yhat, J, h = self.modele(xin)
            if not np.isnan(self.Jc):
                J = self.Jc
            self.J_pas = J                     # cadence par pas : jacobien garde jusqu'a la fin de fenetre suivante
            err = yb - yhat
            porte = (not sus) and (not self.sus1) and (not self.sus2)
            if porte:
                if self.apprendre and abs(err) > self.zme:          # a. OS-ELM, zone morte d'estimation
                    Ph = self.P @ h
                    gain = Ph / (self.lam + h @ Ph)
                    self.BETA = self.BETA + gain * (err / self.TE_)
                    self.P = (self.P - np.outer(gain, Ph)) / self.lam
                    appris = True
                if not self.cadence_pas:                             # b. gains, cadence par fenetre (option B)
                    ancien = self.x.copy()
                    if self.adapter and abs(eb) > self.zm and J > 0:
                        phi = J * (s * K_ZN)
                        dx = self.eta * eb * phi / (self.eps + phi @ phi) + self.alpha * (self.x - self.x_prec)
                        self.x = projeter(self.x, dx, self.r)
                        adapte = True
                        change = bool(np.any(self.x != ancien))
                    self.x_prec = ancien
                    self.K = K_ZN * self.x
        if self.cadence_pas:                   # cadence par pas : bilan des pas de la fenetre
            adapte, change = self.maj_fen > 0, self.change_fen > 0
            self.maj_fen = self.change_fen = 0
        self.journal.append({"ybar": yb, "dbar": db, "ebar": eb, "err": err, "J": J, "porte": porte,
                             "adapte": adapte, "appris": appris, "change": change, "x": self.x.copy(),
                             "K": self.K.copy(), "s": s})
        self.yb2, self.yb1 = self.yb1, yb
        self.db2, self.db1 = self.db1, db
        self.sus2, self.sus1 = self.sus1, sus
        self.nfen += 1
        self.cpt, self.sy, self.sd, self.se, self.hors = 0, 0.0, 0.0, 0.0, False
        self.SE, self.phiD = 0.0, 0.0
        self.sS1 = self.sS2 = self.sS3 = 0.0


class ELMPID:
    """Le montage Simulink de l'option B : adaptateur ELM -> gains -> bloc
    PID de la base commune -> u, et u renvoye a l'adaptateur."""
    utilise_mesure = True

    def __init__(self, **modif):
        self.adapt = AdaptateurELM(**modif)
        self.bloc = BlocPID()
        self.journal = self.adapt.journal
        self.K_pas = []

    @property
    def K(self):
        return self.adapt.K

    def pas(self, e, mesure):
        K = self.adapt.K                       # sortie de l'adaptateur (son etat seulement)
        self.K_pas.append(K)
        u = self.bloc.pas(e, K)
        self.adapt.mise_a_jour(e, mesure, u)
        return u


essai = ELMPID()
ecart_y = max(abs(essai.adapt.modele(MODELE["X_TEST"][i].astype(float))[0] - MODELE["Y_TEST"][i, 0])
              for i in range(MODELE["X_TEST"].shape[0]))
ecart_J = max(abs(essai.adapt.modele(MODELE["X_TEST"][i].astype(float))[1] - MODELE["J_TEST"][i, 0])
              for i in range(MODELE["X_TEST"].shape[0]))
print(f"Vecteurs de test du modele : ecart {ecart_y:.1e} V sur ybar, {ecart_J:.1e} sur le jacobien.")
if ecart_y > 1e-9 or ecart_J > 1e-9:
    raise RuntimeError("elm_pid_modele.mat ne redonne pas ses vecteurs de test.")
if g_interp(np.ones(3)) > 0.0:
    raise RuntimeError("Le depart (gains de Ziegler-Nichols) n'est pas admissible dans la table.")


# %% ETAPE 2 : evaluation et references

def evaluer(fabrique, codes=None, essais=None):
    essais = essais or ESSAIS
    res = {}
    for code in (codes or list(essais)):
        reg = fabrique()
        sim = simuler(reg, essais[code])
        o = grandeurs(sim, essais[code])
        e = sim["consigne"] - sim["v"]
        res[code] = {"o": o, "IAE_dem": float(np.sum(np.abs(e[:K30])) * TC),
                     "revenus": bool(all(ev["revenu"] for ev in o["evenements"])), "reg": reg, "sim": sim}
    return res


def termes(res):
    return np.array([res[c]["o"]["IAE"] for c in CODES_IAE] + [res[c]["IAE_dem"] for c in CODES_DEM])


class PIDParallele(PIDClassique):
    """PID du bloc Simulink (forme Parallel, clamping) avec d'autres gains."""

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


def fenetres_adaptees(reg):
    """Fenetres ou un pas de gradient a ete calcule (porte ouverte, |ebar| > zone morte, J > 0)."""
    return [i for i, x in enumerate(reg.journal) if x["adapte"]]


def fenetres_changees(reg):
    """Fenetres ou les gains ont effectivement change apres projection."""
    return [i for i, x in enumerate(reg.journal) if x["change"]]


def bilan(nom, res):
    J = float(np.mean(termes(res) / T_ZN))
    non = [c for c in CODES_IAE if not res[c]["revenus"]]
    print(f"\n  {nom} : J = {J:.3f} ; {'tous les evenements reviennent' if not non else 'pas revenus : ' + ', '.join(non)}")
    for code, r in res.items():
        o = r["o"]
        ligne = (f"    {code:4s} depassement {o['depassement_pct']:5.1f} %, IAE {o['IAE'] * 1e3:7.2f} mV.s, "
                 f"efficace {o['e_eff_V'] * 1e3:7.1f} mV, |dd| {o['dd_moyen']:.4f}")
        if hasattr(r["reg"], "journal"):
            jr = r["reg"].journal
            Kf = r["reg"].K / K_ZN
            ad = fenetres_adaptees(r["reg"])
            ch = fenetres_changees(r["reg"])
            if r["reg"].adapt.cadence_pas:
                pc = r["reg"].adapt.pas_changes
                ligne += (f" ; pas adaptes {r['reg'].adapt.n_maj_pas:5d}, gains changes sur {len(pc):5d} pas (dont "
                          f"{sum(1 for k in pc if k >= K30):5d} apres 30 ms), projections {r['reg'].adapt.n_proj_pas:4d}, "
                          f"finaux x({Kf[0]:.3f}, {Kf[1]:.3f}, {Kf[2]:.3f})")
            else:
                ligne += (f" ; porte {100 * np.mean([x['porte'] for x in jr]):3.0f} %, pas calcules {len(ad):2d}, gains "
                          f"changes {len(ch):2d} (dont {sum(1 for i in ch if (i + 1) * NF > K30):2d} apres 30 ms), finaux "
                          f"x({Kf[0]:.3f}, {Kf[1]:.3f}, {Kf[2]:.3f})")
        print(ligne)
    return J


titre("ETAPE 2 : les references")
REF = {"Ziegler-Nichols": evaluer(lambda: PIDClassique()),
       "meilleur PID fige": evaluer(lambda: PIDParallele(GAINS_FIGE["P"], GAINS_FIGE["I"], GAINS_FIGE["D"]))}
T_ZN = termes(REF["Ziegler-Nichols"])
J_FIGE = float(np.mean(termes(REF["meilleur PID fige"]) / T_ZN))
print(f"  Meilleur PID fige sur grille : J = {J_FIGE:.3f}.")




# %% ETAPE 3 : ELM-PID B2 sur les onze essais

def x_pas(reg):
    """Multiplicateurs de Ziegler-Nichols appliques a chaque pas."""
    return np.array(reg.K_pas) / K_ZN


def k_de(t):
    return int(round(t / TC))


titre("ETAPE 3 : ELM-PID B2, cadence par pas (le point de depart, gains figes, est le PID de Ziegler-Nichols)")
ELM = evaluer(lambda: ELMPID())
J_ELM = bilan("ELM-PID B2", ELM)
fige = evaluer(lambda: ELMPID(ADAPTER=False))
ecart_zn = max(float(np.max(np.abs(fige[c]["sim"]["d"] - REF["Ziegler-Nichols"][c]["sim"]["d"]))) for c in fige)
print(f"\n  Controle : ELM-PID sans adaptation contre le PID de Ziegler-Nichols, onze essais, ecart maximal sur d : {ecart_zn:.1e}.")
if ecart_zn != 0.0:
    raise RuntimeError("Sans adaptation, l'ELM-PID ne redonne pas le PID de Ziegler-Nichols a l'identique.")
for code in ("S1", "S2", "S3"):
    X = x_pas(ELM[code]["reg"])
    print(f"  {code} : x a 2, 5, 30, 50, 55, 70 ms et final : " + " ; ".join(
        f"({X[min(k_de(t), len(X) - 1)][0]:.3f}, {X[min(k_de(t), len(X) - 1)][1]:.3f}, {X[min(k_de(t), len(X) - 1)][2]:.3f})"
        for t in (0.002, 0.005, 0.030, 0.050, 0.055, 0.070, 1.0)))
admis = [g_interp(x) <= 0.0 for c in ELM for x in np.unique(x_pas(ELM[c]["reg"]), axis=0)]
print(f"  Controle : gains admissibles a tous les pas des onze essais : {'oui' if all(admis) else 'NON'}.")


# %% ETAPE 4 : ablations

titre("ETAPE 4 : ce que chaque piece apporte (ablations, jamais choisies)")
R2_ORIGINE = 2.5 / 4096 * 80 / 2 + 3 * 0.010
ABLATIONS = {"Cadence par fenetre (option B)": {"CADENCE_PAS": 0.0},
             "Sans zone morte par pas": {"ZONE_MORTE_PAS": 0.0},
             "Zone morte R2 d'origine": {"ZONE_MORTE_PAS": R2_ORIGINE},
             "Jacobien constant": {"JACOBIEN_CONSTANT": J_REGRESSION}}
RES_ABL, J_ABL = {}, {}
for nom, modif in ABLATIONS.items():
    RES_ABL[nom] = evaluer(lambda: ELMPID(**modif))
    J_ABL[nom] = float(np.mean(termes(RES_ABL[nom]) / T_ZN))
print(f"\n  {'variante':31s} {'J':>6s}  {'non revenus':12s} {'S1 dem':>7s} {'S2':>6s} {'S3':>6s} {'S5':>6s} "
      f"{'S8b':>7s} {'S9':>8s}")
print("  (IAE en mV.s : demarrage pour S1 dem, de 30 ms a la fin pour les autres)")
for nom, res, J in ([("ELM-PID B2", ELM, J_ELM)] + [(n, RES_ABL[n], J_ABL[n]) for n in ABLATIONS]):
    non = [c for c in CODES_IAE if not res[c]["revenus"]]
    print(f"  {nom:31s} {J:6.3f}  {(','.join(non) or '-'):12s} {res['S1']['IAE_dem'] * 1e3:7.2f} "
          f"{res['S2']['o']['IAE'] * 1e3:6.2f} {res['S3']['o']['IAE'] * 1e3:6.2f} {res['S5']['o']['IAE'] * 1e3:6.2f} "
          f"{res['S8b']['o']['IAE'] * 1e3:7.2f} {res['S9']['o']['IAE'] * 1e3:8.2f}")
B_OPT = RES_ABL["Cadence par fenetre (option B)"]
J_B = J_ABL["Cadence par fenetre (option B)"]
print(f"\n  Controle : la cadence par fenetre doit redonner l'option B publiee (J = 0.746) : J = {J_B:.4f} "
      f"({'oui' if abs(J_B - 0.7463) < 0.0005 else 'NON'}).")


# %% ETAPE 4b : sensibilite a de tres petits ecarts du circuit

titre("ETAPE 4b : sensibilite (L ou C a +-0.1 %)")
L_NOM, C_NOM = L_BOB, C_CONV
SENSIBILITE = []
for nom_p, fl, fc in (("nominal", 1.0, 1.0), ("L - 0.1 %", 0.999, 1.0), ("L + 0.1 %", 1.001, 1.0),
                      ("C - 0.1 %", 1.0, 0.999), ("C + 0.1 %", 1.0, 1.001)):
    L_BOB, C_CONV = L_NOM * fl, C_NOM * fc
    r_e = ELM if nom_p == "nominal" else evaluer(lambda: ELMPID())
    J_e = float(np.mean(termes(r_e) / T_ZN))
    rev = all(r_e[c]["revenus"] for c in CODES_IAE)
    nb = sum(len(r_e[c]["reg"].adapt.pas_changes) for c in r_e)
    SENSIBILITE.append({"circuit": nom_p, "J": J_e, "tous_revenus": rev, "pas_gains_changes": nb})
    print(f"  {nom_p:12s} J = {J_e:.3f} ; gains changes sur {nb} pas ; {'tous revenus' if rev else 'PAS TOUS REVENUS'}")
L_BOB, C_CONV = L_NOM, C_NOM


# %% ETAPE 5 : comparaison et previsions H1 a H6 (criteres_elm_pid.txt, section 7)

titre("ETAPE 5 : ELM-PID B2 face aux references, previsions H1 a H6 de criteres_elm_pid.txt")
TOUS = {"Ziegler-Nichols": REF["Ziegler-Nichols"], "meilleur PID fige": REF["meilleur PID fige"],
        "ELM-PID B": B_OPT, "ELM-PID B2": ELM}
J_TOUS = {n: float(np.mean(termes(r) / T_ZN)) for n, r in TOUS.items()}
print("  " + " " * 28 + "".join(f"{n:>20s}" for n in TOUS))
print("  " + f"{'cout J':28s}" + "".join(f"{J_TOUS[n]:20.3f}" for n in TOUS))
print("  " + f"{'evenements non revenus':28s}" + "".join(
    f"{(','.join(c for c in CODES_IAE if not TOUS[n][c]['revenus']) or '-'):>20s}" for n in TOUS))
for code in ESSAIS:
    print("  " + f"{code + ' IAE dem. mV.s':28s}" + "".join(f"{TOUS[n][code]['IAE_dem'] * 1e3:20.2f}" for n in TOUS))
    for cle, etiquette, fmt, k in (("depassement_pct", "depassement %", "{:.1f}", 1.0), ("IAE", "IAE mV.s", "{:.2f}", 1e3),
                                   ("e_max_V", "ecart maximal V", "{:.2f}", 1.0), ("e_eff_V", "ecart efficace mV", "{:.1f}", 1e3),
                                   ("iL_max_dem_A", "iL crete dem. A", "{:.1f}", 1.0)):
        if cle == "depassement_pct" and code not in ("S1", "S8a", "S8b"):
            continue
        if cle == "iL_max_dem_A" and code not in ("S1", "S8b"):
            continue
        if cle == "e_max_V" and code not in ("S2", "S3"):
            continue
        print("  " + f"{code + ' ' + etiquette:28s}" + "".join(f"{fmt.format(TOUS[n][code]['o'][cle] * k):>20s}" for n in TOUS))
DECOMP = {}
for n in TOUS:
    r = termes(TOUS[n]) / T_ZN
    DECOMP[n] = (float(np.mean(r[:10])), float(np.mean(r[10:])))
print("  Decomposition de J (apres 30 ms ; demarrage) : " +
      " ; ".join(f"{n} {DECOMP[n][0]:.3f} / {DECOMP[n][1]:.3f}" for n in TOUS))

ZN = REF["Ziegler-Nichols"]
# H1 : les gains changent pendant F1 (S2) et F2 (S3), entre 50 et 55 ms
H1_D = {}
for c in ("S2", "S3"):
    X = x_pas(ELM[c]["reg"])
    pc = [k for k in ELM[c]["reg"].adapt.pas_changes if k_de(0.050) <= k < k_de(0.055)]
    H1_D[c] = (len(pc), float(np.max(np.abs(X[k_de(0.055)] - X[k_de(0.050)]))))
# H2 : B2 fait mieux que Ziegler-Nichols sur les trois cas de base, et S1 a S3 reviennent
H2_D = {"S1 dem": (ELM["S1"]["IAE_dem"], ZN["S1"]["IAE_dem"]), "S2": (ELM["S2"]["o"]["IAE"], ZN["S2"]["o"]["IAE"]),
        "S3": (ELM["S3"]["o"]["IAE"], ZN["S3"]["o"]["IAE"])}
# H3 : B2 fait mieux que B sur les memes trois grandeurs
H3_D = {"S1 dem": (ELM["S1"]["IAE_dem"], B_OPT["S1"]["IAE_dem"]), "S2": (ELM["S2"]["o"]["IAE"], B_OPT["S2"]["o"]["IAE"]),
        "S3": (ELM["S3"]["o"]["IAE"], B_OPT["S3"]["o"]["IAE"])}
# H4 : pas de derive sur S7a et S7b
H4_D = {}
for c in ("S7a", "S7b"):
    X = x_pas(ELM[c]["reg"])
    n_apres = sum(1 for k in ELM[c]["reg"].adapt.pas_changes if k >= K30)
    H4_D[c] = (float(np.max(np.abs(X[K30:] - X[K30]))), n_apres, len(X) - K30)
NON_B2 = [c for c in CODES_IAE if not ELM[c]["revenus"]]
J_SENS = [x["J"] for x in SENSIBILITE]
P = {"H1": all(n >= 1 and d >= 0.005 for n, d in H1_D.values()),
     "H2": all(a < b for a, b in H2_D.values()) and all(ELM[c]["revenus"] for c in ("S1", "S2", "S3")),
     "H3": all(a < b for a, b in H3_D.values()),
     "H4": all(d <= 0.02 and n <= 0.01 * tot for d, n, tot in H4_D.values()),
     "H5a": 0.81 <= J_ELM <= 0.93,
     "H5b": 0.77 <= DECOMP["ELM-PID B2"][0] <= 0.89 and 0.97 <= DECOMP["ELM-PID B2"][1] <= 1.00,
     "H5c": ("S8b" in NON_B2) or ("S9" in NON_B2),
     "H6": max(abs(j - J_ELM) for j in J_SENS) <= 0.02}
# Ce qui a ete prevu pour chaque enonce (section 7) : H3 est l'hypothese de l'etudiant, prevue fausse.
PREVU = {"H1": True, "H2": True, "H3": False, "H4": True, "H5a": True, "H5b": True, "H5c": True, "H6": True}
TEXTE = {"H1": " ; ".join(f"{c} : {n} pas changes entre 50 et 55 ms, max |x(55 ms) - x(50 ms)| = {d:.4f}"
                          for c, (n, d) in H1_D.items()),
         "H2": " ; ".join(f"{c} {a * 1e3:.2f} contre {b * 1e3:.2f} mV.s" for c, (a, b) in H2_D.items())
               + " ; S1 a S3 " + ("reviennent" if all(ELM[c]["revenus"] for c in ("S1", "S2", "S3")) else "NE REVIENNENT PAS TOUS"),
         "H3": " ; ".join(f"{c} B2 {a * 1e3:.2f} contre B {b * 1e3:.2f} mV.s" for c, (a, b) in H3_D.items()),
         "H4": " ; ".join(f"{c} : variation max apres 30 ms {d:.4f}, pas changes apres 30 ms {n} sur {tot}"
                          for c, (d, n, tot) in H4_D.items()),
         "H5a": f"J = {J_ELM:.3f} (fourchette 0.81 a 0.93)",
         "H5b": f"apres 30 ms {DECOMP['ELM-PID B2'][0]:.3f} (0.77 a 0.89), demarrage {DECOMP['ELM-PID B2'][1]:.3f} (0.97 a 1.00)",
         "H5c": "non revenus : " + (", ".join(NON_B2) or "aucun"),
         "H6": f"J de {min(J_SENS):.3f} a {max(J_SENS):.3f} (nominal {J_ELM:.3f})"}
for k in P:
    print(f"  {k} enonce {'vrai' if P[k] else 'FAUX'} ; prevu {'vrai' if PREVU[k] else 'faux'} -> prevision "
          f"{'juste' if P[k] == PREVU[k] else 'FAUSSE'} : {TEXTE[k]}")


# %% ETAPE 6 : fichiers, resultats et figure

titre("ETAPE 6 : fichiers")
pas_1ms = int(round(1e-3 / TC))
REGL_JSON = {k: (None if (isinstance(v, float) and np.isnan(v)) else v) for k, v in REGLAGES.items()}
predictions = {"version": 2, "Te": TC,              # format de la base commune v2 (lu par Simuler_ELM_PID.m)
               "regulateur": "ELM-PID option B2 (bloc PID de la base commune a gains externes, gains mis a jour a "
                             "chaque pas, ELM de Lu, projection M2-M3)",
               "avertissement": "elm_pid_adaptatif.m n'est pas encore porte a la cadence par pas : pas de "
                                "comparaison Simulink possible avant ce portage",
               "reglages": REGL_JSON, "K_depart": K_ZN.tolist(),
               "controle": {"ecart_vecteurs_test_V": ecart_y, "ecart_sans_adaptation_ZN": ecart_zn},
               "essais": {}}
for code, r in ELM.items():
    Kp = np.array(r["reg"].K_pas)
    predictions["essais"][code] = {"grandeurs": r["o"],
                                   "v_toutes_les_ms": r["sim"]["v"][::pas_1ms].tolist(),
                                   "iL_toutes_les_ms": r["sim"]["iL"][::pas_1ms].tolist(),
                                   "d_moyen_par_ms": [float(np.mean(r["sim"]["d"][i:i + pas_1ms]))
                                                      for i in range(0, len(r["sim"]["d"]) - pas_1ms + 1, pas_1ms)],
                                   "K_toutes_les_ms": Kp[::pas_1ms].tolist(),
                                   "pas_adaptes": r["reg"].adapt.n_maj_pas,
                                   "pas_gains_changes": len(r["reg"].adapt.pas_changes),
                                   "K_final": r["reg"].K.tolist()}
with open(os.path.join(DOSSIER_ELM, "predictions_banc_elm_pid.json"), "w", encoding="utf-8") as f:
    json.dump(predictions, f, indent=1, allow_nan=False)
print("  predictions_banc_elm_pid.json ecrit.")

savemat(os.path.join(DOSSIER_ELM, "elm_pid_reglages.mat"),
        {"K_DEPART": K_ZN.reshape(1, 3), "ETA": REGLAGES["ETA"], "ZONE_MORTE": REGLAGES["ZONE_MORTE"],
         "ZONE_MORTE_ESTIMATION": REGLAGES["ZONE_MORTE_ESTIMATION"], "ALPHA": REGLAGES["ALPHA"],
         "EPS_PHI": REGLAGES["EPS_PHI"], "LAMBDA": REGLAGES["LAMBDA"], "APPRENDRE": REGLAGES["APPRENDRE"],
         "GLISSEMENT": REGLAGES["GLISSEMENT"], "JACOBIEN_CONSTANT": REGLAGES["JACOBIEN_CONSTANT"],
         "MULT_MIN": REGLAGES["MULT_MIN"], "MULT_MAX": REGLAGES["MULT_MAX"],
         "N_BISSECTIONS": REGLAGES["N_BISSECTIONS"], "H_GRADIENT": REGLAGES["H_GRADIENT"],
         "RESTAURATION": REGLAGES["RESTAURATION"], "N_PROJECTION": REGLAGES["N_PROJECTION"],
         "CADENCE_PAS": REGLAGES["CADENCE_PAS"], "ETA_PAS": REGLAGES["ETA_PAS"],
         "ZONE_MORTE_PAS": REGLAGES["ZONE_MORTE_PAS"], "MS_DEPART": REGLAGES["MS_DEPART"],
         "NF": float(NF), "TC": TC, "N_FILTRE": PID_N, "D_MIN": D_MIN, "D_MAX": D_MAX, "VERSION": 5.0})
print("  elm_pid_reglages.mat ecrit (cadence par pas : a porter dans elm_pid_adaptatif.m).")

rejeu = {}
for code in CODES_REJEU:
    r = ELM[code]
    rejeu[code] = {"e": (r["sim"]["consigne"] - r["sim"]["mesure"]).reshape(-1, 1),
                   "mesure": r["sim"]["mesure"].reshape(-1, 1), "u": r["sim"]["d"].reshape(-1, 1),
                   "K": np.array(r["reg"].K_pas),
                   "pas_changes": np.array(r["reg"].adapt.pas_changes, float).reshape(-1, 1)}
savemat(os.path.join(DOSSIER_ELM, "reference_rejeu_elm_pid.mat"), rejeu, do_compression=True)
print(f"  reference_rejeu_elm_pid.mat ecrit ({', '.join(CODES_REJEU)}).")


def resume_essais(res):
    return {c: {"grandeurs": res[c]["o"], "IAE_dem": res[c]["IAE_dem"], "revenus": res[c]["revenus"]} for c in res}


sortie = {"version": 5, "reglages": REGL_JSON, "J": J_TOUS, "decomposition": DECOMP, "J_ablations": J_ABL,
          "J_regression": J_REGRESSION, "sensibilite": SENSIBILITE,
          "previsions": {k: {"enonce_vrai": bool(P[k]), "prevu_vrai": PREVU[k], "prevision_juste": bool(P[k] == PREVU[k]),
                             "detail": TEXTE[k]} for k in P},
          "references": {n: resume_essais(TOUS[n]) for n in TOUS},
          "ablations": {n: resume_essais(RES_ABL[n]) for n in RES_ABL},
          "x_toutes_les_ms": {c: x_pas(ELM[c]["reg"])[::pas_1ms].tolist() for c in ELM},
          "pas_gains_changes": {c: len(ELM[c]["reg"].adapt.pas_changes) for c in ELM},
          "pas_adaptes": {c: ELM[c]["reg"].adapt.n_maj_pas for c in ELM},
          "projections": {c: ELM[c]["reg"].adapt.n_proj_pas for c in ELM},
          "duree_s": round(time.time() - T_DEBUT, 1)}
with open(os.path.join(DOSSIER_ELM, "banc_elm_pid_resultats.json"), "w", encoding="utf-8") as f:
    json.dump(sortie, f, indent=1, allow_nan=False, default=lambda x: None)
print("  banc_elm_pid_resultats.json ecrit.")

fig, axes = plt.subplots(3, 4, figsize=(20, 9.5), sharex="col")
for col, (code, xlim) in enumerate((("S1", (0, 30)), ("S2", (40, 90)), ("S3", (40, 90)), ("S8b", None))):
    for nom, couleur in (("Ziegler-Nichols", "0.6"), ("meilleur PID fige", "tab:green"),
                         ("ELM-PID B", "tab:orange"), ("ELM-PID B2", "tab:blue")):
        sim = TOUS[nom][code]["sim"]
        axes[0, col].plot(sim["t"] * 1e3, sim["v"], lw=0.6, color=couleur, label=nom)
        axes[2, col].plot(sim["t"] * 1e3, sim["iL"], lw=0.4, color=couleur)
    axes[0, col].plot(sim["t"] * 1e3, sim["consigne"], "k--", lw=0.6)
    t_ms = ELM[code]["sim"]["t"] * 1e3
    for nom_opt, res_opt, style in (("B2", ELM, "-"), ("B", B_OPT, ":")):
        Kx = x_pas(res_opt[code]["reg"])
        for i, nom in enumerate(("Kp", "Ki", "Kd")):
            axes[1, col].plot(t_ms, Kx[:, i], style, lw=1.0, color=("tab:red", "tab:purple", "tab:brown")[i],
                              label=f"{nom} ({nom_opt})")
    axes[0, col].set_ylim((85, 115) if code in ("S2", "S3") else (30, 200))
    axes[0, col].set_title(f"{code} : tension de sortie", fontsize=9, loc="left")
    axes[1, col].set_title(f"{code} : gains de l'ELM-PID (multiples de ZN)", fontsize=9, loc="left")
    axes[2, col].set_title(f"{code} : courant de la bobine (observe)", fontsize=9, loc="left")
    axes[2, col].set_xlabel("temps (ms)")
    if xlim:
        axes[2, col].set_xlim(*xlim)
    for ax in axes[:, col]:
        ax.grid(alpha=0.3)
axes[0, 0].legend(fontsize=7)
axes[1, 0].legend(fontsize=7, ncol=2)
fig.tight_layout()
fig.savefig(os.path.join(DOSSIER_ELM, "banc_elm_pid.png"), dpi=110)
plt.close(fig)
print(f"  banc_elm_pid.png ecrit. Duree totale : {time.time() - T_DEBUT:.0f} s.")
