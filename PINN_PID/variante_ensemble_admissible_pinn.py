# =============================================================================
# variante_ensemble_admissible_pinn.py
#
# VERSION
#   1 (7 octobre 2026). Section 6 de criteres_pinn_pid.txt.
#
# OBJECTIF
#   Mesurer, sans toucher au PINN-PID retenu (banc_pinn_pid.py, version
#   validee dans Simulink), ce que change la boite des gains. Le PINN-PID
#   projette ses gains sur la plus grande boite admissible contenant le
#   depart ; le depart y est un coin (Ki ne peut que baisser, Kp et Kd que
#   monter). La variante projette sur l'ensemble admissible lui-meme (meme
#   critere : marge nominale au moins celle du depart, coupure au plus
#   fs/10 ; ensemble_gains_pinn.mat), avec restauration vers la frontiere
#   (point admissible le plus proche, Rosen 1961), ou sans restauration.
#   Tout le reste est identique : PINN, observateur, seuil, Adam et son
#   echelle, cout.
#   Resultat attendu (calcul du 7 octobre, criteres_pinn_pid.txt) : J de la
#   variante 0.692, contre 0.684 pour le PINN-PID ; ecart plus petit que
#   celui que produit L ou C a +-0.1 %.
#
# FICHIERS NECESSAIRES
#   ceux de banc_pinn_pid.py, plus ensemble_gains_pinn.mat
#   (ensemble_gains_pinn.py).
#
# COMMENT LANCER CE SCRIPT
#   python variante_ensemble_admissible_pinn.py      (deux a trois minutes)
# =============================================================================

import os
import numpy as np
from scipy.io import loadmat

try:
    DOSSIER = os.path.dirname(os.path.abspath(__file__))
except NameError:
    DOSSIER = os.getcwd()
__file__ = os.path.join(DOSSIER, "banc_pinn_pid.py")
with open(__file__, encoding="utf-8") as f:
    _SRC = f.read()
exec(_SRC[:_SRC.index("# %% ETAPE 2 :")])   # le PINN-PID retenu, inchange

ENS = loadmat(os.path.join(DOSSIER, "ensemble_gains_pinn.mat"))
G_TABLE = ENS["G_TABLE"].astype(float)
LOG2_MIN, PAS_LOG2 = float(ENS["LOG2_MIN"].item()), float(ENS["PAS_LOG2"].item())
N_TABLE = G_TABLE.shape[0]
if np.max(np.abs(ENS["K_DEPART"].ravel() - K_ZN) / K_ZN) > 1e-12:
    raise RuntimeError("ensemble_gains_pinn.mat n'a pas ete calcule avec les gains de Ziegler-Nichols de ce banc.")
R_PROJ = {"RESTAURATION": 1.0, "MULT_MIN": 0.25, "MULT_MAX": 4.0, "N_BISSECTIONS": 30.0, "H_GRADIENT": 1e-4,
          "N_PROJECTION": 10.0}


def g_interp(x):
    """g de l'ensemble admissible (g <= 0 : admissible), interpolation
    trilineaire en log2 des multiplicateurs x = K / K_ZN (memes operations
    que g_interp du bloc MATLAB et de l'ELM-PID)."""
    u = (np.log2(x) - LOG2_MIN) / PAS_LOG2
    u = np.minimum(np.maximum(u, 0.0), N_TABLE - 1.0)
    i = np.minimum(np.floor(u), N_TABLE - 2.0).astype(int)
    f = u - i
    s = 0.0
    for di in (0, 1):
        wi = f[0] if di else 1.0 - f[0]
        for dj in (0, 1):
            wj = f[1] if dj else 1.0 - f[1]
            for dk in (0, 1):
                wk = f[2] if dk else 1.0 - f[2]
                s += wi * wj * wk * G_TABLE[i[0] + di, i[1] + dj, i[2] + dk]
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
    """Restauration (M2) : recul de p le long de -gr jusqu'a la frontiere
    (doublement puis bissection) ; None si un recul de 1 ne suffit pas."""
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
    """Pas dx depuis xc (admissible), projete sur l'ensemble admissible
    (M1) : point de sortie sur le segment, puis, si RESTAURATION (M2),
    projection du gradient de Rosen (1961) : composante sortante retiree,
    pas tangent, retour sur la frontiere le long de la normale, tant que le
    point se rapproche de la cible (N_PROJECTION fois au plus). Sans
    restauration : glissement tangent coupe par bissection. Meme code que
    l'ELM-PID (banc_elm_pid.py)."""
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


class PINNPIDEnsemble(PINNPID):
    """PINN-PID dont chaque iteration d'Adam est suivie de la projection sur
    l'ensemble admissible au lieu de la boite."""

    def __init__(self, restauration=True):
        super().__init__("pinn")
        self.r_proj = dict(R_PROJ, RESTAURATION=float(restauration))

    def optimiser(self, r):
        R = REGLAGES
        x0 = (float(self.obs.x[0]), float(self.obs.x[1])); vin = float(self.obs.x[2])
        ctrl = (self.u, self.e1, self.ef, self.g1)
        th0 = self.theta.copy(); th = th0.copy()
        m = np.zeros(3); vv = np.zeros(3)
        b1t, b2t = 1.0, 1.0
        for it in range(1, self.n_adam + 1):
            b1t *= R["BETA1"]; b2t *= R["BETA2"]
            J, gK = horizon(K_MIN + th * DK, x0, ctrl, r, self.k, vin, self.pas_pred, self.NH, R["RHO"])
            gth = gK * DK + 2 * R["MU"] * (th - th0)
            m = R["BETA1"] * m + (1 - R["BETA1"]) * gth
            vv = R["BETA2"] * vv + (1 - R["BETA2"]) * gth * gth
            th_prec = th
            th = th - R["ALPHA"] * (m / (1 - b1t)) / (np.sqrt(vv / (1 - b2t)) + R["EPS_ADAM"])
            xc = (K_MIN + th_prec * DK) / K_ZN       # seule difference avec PINNPID.optimiser
            xn = projeter(xc, (K_MIN + th * DK) / K_ZN - xc, self.r_proj)
            th = (xn * K_ZN - K_MIN) / DK
        self.theta = th
        self.K = K_MIN + th * DK


def evaluer(fabrique):
    res = {}
    for code, sc in ESSAIS.items():
        reg = fabrique()
        sim = simuler(reg, sc)
        o = grandeurs(sim, sc)
        e = sim["consigne"] - sim["v"]
        res[code] = {"o": o, "IAE_dem": float(np.sum(np.abs(e[:K30])) * TC),
                     "revenus": all(ev["revenu"] for ev in o["evenements"]), "reg": reg}
    return res


CODES_IAE = ["S1", "S3", "S4", "S5", "S6", "S7a", "S7b", "S8a", "S8b", "S9"]
CODES_DEM = ["S1", "S8a", "S8b"]


def termes(res):
    return np.array([res[c]["o"]["IAE"] for c in CODES_IAE] + [res[c]["IAE_dem"] for c in CODES_DEM])


T_ZN = termes(evaluer(lambda: PIDClassique()))
VARIANTES = {"PINN-PID (boite, retenu)": lambda: PINNPID("pinn"),
             "variante : ensemble admissible et restauration": lambda: PINNPIDEnsemble(True),
             "variante : ensemble admissible sans restauration": lambda: PINNPIDEnsemble(False)}
print(f"\n  {'version':50s} {'J':>6s}  {'non revenus':12s} {'Ki max (x ZN)':>14s} {'R0 aux gains finaux S8b':>24s}")
for nom, fab in VARIANTES.items():
    res = evaluer(fab)
    J = float(np.mean(termes(res) / T_ZN))
    non = [c for c in CODES_IAE if not res[c]["revenus"]]
    ki = max(max(x["K"][1] for x in res[c]["reg"].journal) for c in res) / K_ZN[1]
    K8 = res["S8b"]["reg"].journal[-1]["K"].copy()
    J_r0 = float(np.mean(termes(evaluer(lambda: LoiLu(K8))) / T_ZN))
    print(f"  {nom:50s} {J:6.3f}  {(','.join(non) or '-'):12s} {ki:14.3f} {J_r0:12.3f} x({K8[0] / K_ZN[0]:.2f}, "
          f"{K8[1] / K_ZN[1]:.2f}, {K8[2] / K_ZN[2]:.2f})", flush=True)
