# =============================================================================
# recherche_pso_pid.py
#
# VERSION
#   1 (6 octobre 2026). Remplace l'ancien pso_pid_buck.py (ancien circuit,
#   modele lineaire de Tustin, cout ITAE sur le seul echelon nominal).
#
# OBJECTIF
#   Regler hors ligne les gains P, I, D du bloc "PID Controller" de
#   Ziegler-Nichols par la methode de Gaing (2004) : essaim de particules,
#   cout W(K) de l'article, sur six demarrages qui ne font pas partie des
#   onze essais communs. Les onze essais ne servent qu'a juger le resultat
#   (banc_pso_pid.py). Methode, ecarts declares et previsions :
#   criteres_pso_pid.txt.
#
# LA METHODE, TELLE QU'ELLE EST CODEE ICI
#   Individu = multiplicateurs (a, b, c) des gains de Ziegler-Nichols
#   (P = a P_ZN, I = b I_ZN, D = c D_ZN), chacun dans [0 ; 4] (amendement 1
#   de criteres_pso_pid.txt : [0 ; 16] ne contenait que 0.05 % de points
#   admissibles). Population 50, 100 iterations, w de 0.9 a 0.4 (eq. 12),
#   c1 = c2 = 2, |v| <= 2 (moitie de la plage), positions ramenees dans
#   [0 ; 4] (eq. 15).
#   Cout d'un individu : si la marge de phase minimale aux 12 coins est sous
#   30 degres ou la coupure maximale au-dessus de fs/10, W = 1e6 ; sinon,
#   moyenne des six W(K) = (1 - exp(-beta)) (Mp + Ess) + exp(-beta) (ts - tr),
#   Mp et Ess en %, ts et tr en unites de tau1 = 1.7280 ms. Pendant ces six
#   demarrages, le PID part de l'etat nul (amendement 2 : reponse indicielle
#   de l'article ; la premiere version partait de l'integrateur precharge a
#   0.5, ce qui poussait Ki a zero).
#   Deux valeurs de beta (1.0 retenu, 1.5 publie) et cinq graines chacune.
#
# DEUX FACONS DE LE LANCER
#   RECALCULER = False (reglage fourni) : les recherches deja presentes dans
#   recherche_pso_pid.json sont reprises ; le script recalcule seulement le
#   cout de chaque gbest et s'arrete s'il differe (controle du fichier sur
#   ta machine). Une minute environ.
#   RECALCULER = True : les dix recherches sont refaites (une a trois heures
#   selon la machine et le nombre de coeurs). Sur une autre machine, les
#   arrondis peuvent faire diverger l'essaim apres quelques iterations : le
#   gbest peut alors differer un peu, c'est la nature de la methode.
#
# CE QUE PRODUIT CE SCRIPT
#   recherche_pso_pid.json : pour chaque (beta, graine) : gbest, son cout et
#   ses grandeurs sur les six demarrages, l'historique du gbest et de la
#   moyenne et de l'ecart type de f = 1/W dans la population (comme la fig.
#   14 de l'article).
#
# BIBLIOTHEQUES NECESSAIRES (pip install numpy scipy matplotlib)
#
# COMMENT LANCER CE SCRIPT
#   python recherche_pso_pid.py
#
# ORDRE D'EXECUTION
#   1. ce script ; 2. banc_pso_pid.py ; 3. Construction_PSO_PID.m ;
#   4. verifier_pso_pid.py ; 5. Simuler_PSO_PID.m.
# =============================================================================


# %% ETAPE 0 : bibliotheques, reglages et definitions du banc commun

import os                                     # chemins de fichiers
import json                                   # lecture et ecriture au format texte
import math                                   # exponentielle
import time                                   # duree d'execution
import multiprocessing as mp                  # evaluation en parallele des individus
import numpy as np                            # calcul numerique
from scipy.signal import cont2discrete        # modele moyen discretise (marges)

RECALCULER = False                            # True : refaire les dix recherches

try:                                          # dossier du script (ou dossier courant dans un notebook)
    DOSSIER_PSO = os.path.dirname(os.path.abspath(__file__))
except NameError:
    DOSSIER_PSO = os.getcwd()
with open(os.path.join(DOSSIER_PSO, "banc_commun.py"), encoding="utf-8") as f:
    SOURCE_BANC = f.read()
MARQUE = "# === FIN DES DEFINITIONS DU BANC COMMUN ==="
if MARQUE not in SOURCE_BANC or "iL_max_dem_A" not in SOURCE_BANC:
    raise RuntimeError("banc_commun.py n'est pas la version 2.1 (observation du courant) : prendre la version a jour.")
exec(SOURCE_BANC[:SOURCE_BANC.index(MARQUE)])  # constantes, Circuit, simuler, PIDClassique

FICHIER = os.path.join(DOSSIER_PSO, "recherche_pso_pid.json")

# Methode de l'article
N_POP, N_ITER = 50, 100                       # population, iterations
W_MAX, W_MIN = 0.9, 0.4                       # inertie (eq. 12)
C1 = C2 = 2.0                                 # constantes d'acceleration
K_MIN, K_MAX = 0.0, 4.0                       # bornes des multiplicateurs (ecart 1, amendement 1 : 16 -> 4)
V_MAX = K_MAX / 2.0                           # vitesse maximale (moitie de la plage)
W_PENALITE = 1e6                              # W "tres grand" d'un individu refuse
BETAS = (1.0, 1.5)                            # 1.0 retenu, 1.5 publie (ecart 6)
GRAINES = (1, 2, 3, 4, 5)                     # ecart 7
# Ecarts 3 et 4 : unites et definitions
TAU1 = 1.7280e-3                              # constante de temps dominante du Buck (s)
T_FIN = 0.050                                 # duree d'un demarrage de reglage (s)
K30 = int(round(0.030 / TC))                  # debut de la fenetre de Ess (30 ms)
# Ecart 5 : essais de reglage
POINTS_REGLAGE = [(R, V) for R in (4.5, 10.0, 50.0) for V in (180.0, 220.0)]
# Amendement 2 : pendant le reglage, le PID part de l'etat nul (reponse indicielle de l'article) ;
# le jugement et Simulink gardent les conditions initiales du bloc (PID_CI_INTEGRATEUR, PID_CI_FILTRE).
CI_REGLAGE = (0.0, 0.0)                       # (integrateur, filtre) pendant le reglage
# Ecart 2 : contraintes du meilleur PID fige
MARGE_MINI = 30.0                             # degres
FC_MAXI = FSW / 10.0                          # Hz


def essai_reglage(R, V):
    """Demarrage 0 -> 100 V de 50 ms, charge R, entree V, sans bruit,
    quantification ni evenement (meme format que les essais communs)."""
    n = int(round(T_FIN / TC)) + 1
    return {"code": f"R{R:g}_V{V:g}", "nom": f"reglage {R:g} ohms, {V:g} V", "duree": T_FIN, "R0": R, "q": 1e-9,
            "evenements": [], "t": np.arange(n) * TC, "dvref": np.zeros(n), "vin": np.full(n, V),
            "gx": np.zeros(n), "bruit": np.zeros(n)}


REGLAGE = [essai_reglage(R, V) for R, V in POINTS_REGLAGE]
for sc in REGLAGE:                            # aucun point de reglage ne doit etre un point des onze essais
    for s in SCENARIOS:
        if abs(s["R0"] - sc["R0"]) < 1e-9 and np.any(np.abs(s["vin"] - sc["vin"][0]) < 1e-9):
            raise RuntimeError(f"Le point de reglage {sc['code']} apparait dans l'essai {s['code']}.")


class PIDParallele:
    """Bloc "PID Controller" de Simulink (forme Parallel, Forward Euler,
    clamping, sortie [0.01 ; 0.99]) avec des gains P, I, D donnes ; memes
    operations que PIDClassique du banc commun."""

    def __init__(self, P, I, D, ci=None):
        self.P, self.I, self.D = P, I, D
        self.xI, self.xF = (PID_CI_INTEGRATEUR, PID_CI_FILTRE) if ci is None else ci

    def pas(self, e):
        derivee = PID_N * (self.D * e - self.xF)
        u = self.P * e + self.xI + derivee
        u_sat = min(max(u, D_MIN), D_MAX)
        entree_I = self.I * e
        if not ((u != u_sat) and (np.sign(entree_I) == np.sign(u - u_sat))):
            self.xI += TC * entree_I
        self.xF += TC * derivee
        return u_sat


# %% ETAPE 1 : contraintes (marge et coupure aux 12 coins, comme recherche_pid_fige.py)

W_PULS = np.logspace(np.log10(2 * np.pi * 20.0), np.log10(np.pi / TC * 0.999), 60000)   # pulsations (rad/s)
Z_CERCLE = np.exp(1j * W_PULS * TC)
COINS = [(R, V) for R in (4.0, 5.0, 25.0, 98.0) for V in (160.0, 200.0, 240.0)]
REPONSES = {}
for R, V in COINS:
    num_d, den_d, _ = cont2discrete(([V], [L_BOB * C_CONV, L_BOB / R, 1.0]), TC, method="zoh")
    REPONSES[(R, V)] = np.polyval(np.squeeze(num_d), Z_CERCLE) / np.polyval(den_d, Z_CERCLE)


def frequentiel(a, b, c):
    """Plus petite marge de phase (degres) et plus haute frequence de coupure
    (Hz) aux 12 coins (meme calcul que recherche_pid_fige.py)."""
    P, I, D = PID_P * a, PID_I * b, PID_D * c
    Cz = P + I * TC / (Z_CERCLE - 1) + D * PID_N / (1 + PID_N * TC / (Z_CERCLE - 1))
    pire, fc = 180.0, 0.0
    for G in REPONSES.values():
        boucle = Cz * G
        module = np.abs(boucle)
        phase = np.degrees(np.unwrap(np.angle(boucle)))
        croisements = np.where(np.diff(np.sign(module - 1.0)))[0]
        for j in croisements:
            pire = min(pire, (phase[j] + 360.0) % 360.0 - 180.0)
            fc = max(fc, W_PULS[j] / (2 * np.pi))
    return float(pire), float(fc)


# %% ETAPE 2 : le cout W(K) de l'article

def grandeurs_W(v):
    """Mp (%), Ess (%), tr et ts (s) d'un demarrage (ecart 4)."""
    e = VREF - v
    Mp = max(0.0, (float(v.max()) - VREF) / VREF * 100.0)
    k10 = np.where(v >= 10.0)[0]
    k90 = np.where(v >= 90.0)[0]
    tr = float((k90[0] - k10[0]) * TC) if len(k10) and len(k90) else T_FIN
    hors = np.where(np.abs(e) > BANDE)[0]
    ts = float((hors[-1] + 1) * TC) if len(hors) else 0.0
    Ess = abs(float(np.mean(e[K30:]))) / VREF * 100.0
    return Mp, Ess, tr, ts


def W_de(g, beta):
    """Cout de l'eq. 9 pour les grandeurs g = (Mp, Ess, tr, ts) (ecart 3)."""
    Mp, Ess, tr, ts = g
    return (1.0 - math.exp(-beta)) * (Mp + Ess) + math.exp(-beta) * (ts - tr) / TAU1


def evaluer(x):
    """Grandeurs d'un individu x = (a, b, c) : contraintes, puis, s'il les
    respecte, les six demarrages. Ne depend pas de beta : le cout se calcule
    ensuite pour chaque beta."""
    a, b, c = (float(t) for t in x)
    marge, fc = frequentiel(a, b, c)
    res = {"a": a, "b": b, "c": c, "marge_min": marge, "fc_max": fc,
           "admissible": bool(marge >= MARGE_MINI and fc <= FC_MAXI)}
    if res["admissible"]:
        res["essais"] = []
        for sc in REGLAGE:
            sim = simuler(PIDParallele(PID_P * a, PID_I * b, PID_D * c, ci=CI_REGLAGE), sc)   # amendement 2
            res["essais"].append(grandeurs_W(sim["v"]))
    return res


def cout(res, beta):
    """W moyen sur les six demarrages, ou W_PENALITE si l'individu est refuse."""
    if not res["admissible"]:
        return W_PENALITE
    return float(np.mean([W_de(g, beta) for g in res["essais"]]))


# %% ETAPE 3 : l'essaim (article, etapes 1 a 9)

def recherche(beta, graine, pool):
    """Une recherche complete pour (beta, graine) ; renvoie son compte rendu."""
    rng = np.random.default_rng(graine)
    x = rng.uniform(K_MIN, K_MAX, (N_POP, 3))                 # etape 1 : positions
    v = rng.uniform(-V_MAX, V_MAX, (N_POP, 3))                # et vitesses
    res = pool.map(evaluer, [tuple(r) for r in x])            # etape 2
    W = np.array([cout(r, beta) for r in res])
    pbest, W_pbest, res_pbest = x.copy(), W.copy(), list(res)
    g = int(np.argmin(W_pbest))                               # etape 4 : gbest
    histo = [{"iter": 0, "W_gbest": float(W_pbest[g]), "f_moy": float(np.mean(1 / W)), "f_ect": float(np.std(1 / W)),
              "gbest": pbest[g].tolist()}]
    for it in range(1, N_ITER + 1):
        w = W_MAX - (W_MAX - W_MIN) / N_ITER * it              # eq. 12
        r1 = rng.random((N_POP, 3))                           # rand()
        r2 = rng.random((N_POP, 3))                           # Rand()
        v = w * v + C1 * r1 * (pbest - x) + C2 * r2 * (pbest[g] - x)   # etape 5, eq. 14
        v = np.clip(v, -V_MAX, V_MAX)                         # etape 6
        x = np.clip(x + v, K_MIN, K_MAX)                      # etape 7, eq. 15
        res = pool.map(evaluer, [tuple(r) for r in x])        # etapes 2 et 3
        W = np.array([cout(r, beta) for r in res])
        mieux = W < W_pbest                                   # etape 4
        pbest[mieux], W_pbest[mieux] = x[mieux], W[mieux]
        for i in np.where(mieux)[0]:
            res_pbest[i] = res[i]
        g = int(np.argmin(W_pbest))
        histo.append({"iter": it, "W_gbest": float(W_pbest[g]), "f_moy": float(np.mean(1 / W)),
                      "f_ect": float(np.std(1 / W)), "gbest": pbest[g].tolist()})
    rg = res_pbest[g]
    return {"beta": beta, "graine": graine, "gbest": pbest[g].tolist(), "W_gbest": float(W_pbest[g]),
            "gains": {"P": PID_P * pbest[g][0], "I": PID_I * pbest[g][1], "D": PID_D * pbest[g][2]},
            "marge_min": rg["marge_min"], "fc_max": rg["fc_max"],
            "admissible": rg["admissible"],
            "reglage": [{"essai": sc["code"], "Mp_pct": e[0], "Ess_pct": e[1], "tr_ms": e[2] * 1e3, "ts_ms": e[3] * 1e3,
                         "W": W_de(e, beta)} for sc, e in zip(REGLAGE, rg.get("essais", []))],
            "historique": histo}


# %% ETAPE 4 : les dix recherches (ou leur controle)

if __name__ == "__main__":
    T0 = time.time()
    print(f"Points de reglage : {', '.join(sc['code'] for sc in REGLAGE)} ; tau1 = {TAU1 * 1e3:.4f} ms.")
    ZN = evaluer((1.0, 1.0, 1.0))
    print(f"Ziegler-Nichols : marge minimale {ZN['marge_min']:.1f} degres, coupure {ZN['fc_max']:.0f} Hz, "
          f"{'admissible' if ZN['admissible'] else 'REFUSE par les contraintes'}.")
    if ZN["admissible"]:
        for beta in BETAS:
            print(f"  W de Ziegler-Nichols (beta = {beta}) : {cout(ZN, beta):.4f}")
    resultats = {}
    if os.path.isfile(FICHIER) and not RECALCULER:
        with open(FICHIER, encoding="utf-8") as f:
            resultats = json.load(f)["recherches"]
        print(f"{len(resultats)} recherche(s) reprise(s) de recherche_pso_pid.json.")
    with mp.Pool(min(4, os.cpu_count() or 1)) as pool:
        for beta in BETAS:
            for graine in GRAINES:
                cle = f"beta={beta:g},graine={graine}"
                if cle in resultats:                          # controle du point repris
                    r = resultats[cle]
                    W_recalc = cout(evaluer(tuple(r["gbest"])), beta)
                    ecart = abs(W_recalc - r["W_gbest"]) / r["W_gbest"]
                    print(f"  {cle} : repris, W du gbest {r['W_gbest']:.6f}, recalcule {W_recalc:.6f} "
                          f"(ecart relatif {ecart:.1e})")
                    if ecart > 1e-9:
                        raise RuntimeError(f"{cle} : le cout recalcule differe du fichier.")
                    continue
                t = time.time()
                r = recherche(beta, graine, pool)
                resultats[cle] = r
                with open(FICHIER, "w", encoding="utf-8") as f:   # sauvegarde apres chaque recherche
                    json.dump({"version": 2, "methode": "Gaing 2004, criteres_pso_pid.txt (amendements 1 et 2)",
                               "recherches": resultats},
                              f, indent=1, allow_nan=False)
                print(f"  {cle} : {'' if r['admissible'] else 'AUCUN INDIVIDU ADMISSIBLE ; '}W = {r['W_gbest']:.5f}, gains x ZN ({r['gbest'][0]:.4f}, {r['gbest'][1]:.4f}, "
                      f"{r['gbest'][2]:.4f}), marge {r['marge_min']:.1f} degres, coupure {r['fc_max']:.0f} Hz "
                      f"({time.time() - t:.0f} s)", flush=True)
    print(f"Duree totale : {time.time() - T0:.0f} s.")
