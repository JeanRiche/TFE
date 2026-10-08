# =============================================================================
# mise_au_point_elm_pid.py
#
# VERSION
#   1 (7 octobre 2026).
#
# OBJECTIF
#   Verifier le mecanisme de l'ELM-PID AVANT de le juger sur les onze essais
#   communs (criteres_elm_pid.txt), sur des essais qui n'en font pas partie :
#     1. test geometrique de la projection : 500 pas aleatoires depuis le
#        depart (gains de Ziegler-Nichols, sur la frontiere de l'ensemble
#        admissible) ;
#     2. quatre essais de mise au point E1 a E4 (points R, Vin absents des
#        onze essais) : R0 (gains figes), ELM-PID, et les variantes des
#        ablations ; IAE du demarrage et apres 30 ms, fenetres ou les gains
#        changent, gains finaux.
#   Rien n'est regle sur ces essais : ils montrent seulement que chaque
#   piece fait ce qu'elle doit faire.
#
# COMMENT LANCER CE SCRIPT
#   python mise_au_point_elm_pid.py      (une minute)
# =============================================================================

import os
import numpy as np

try:
    DOSSIER_ELM = os.path.dirname(os.path.abspath(__file__))
except NameError:
    DOSSIER_ELM = os.getcwd()
__file__ = os.path.join(DOSSIER_ELM, "banc_elm_pid.py")
with open(__file__, encoding="utf-8") as f:
    _SRC = f.read()
exec(_SRC[:_SRC.index("# %% ETAPE 2 :")])   # banc commun, modele, ensemble admissible, ELMPID


# %% ETAPE 1 : test geometrique de la projection

titre("ETAPE 1 : projection depuis le depart (500 pas aleatoires)")
rng = np.random.default_rng(1)
x0 = np.ones(3)
print(f"  g au depart : {g_interp(x0):.2e} (0 : le depart est sur la frontiere de l'ensemble admissible)")
VARIANTES_P = {"M3 (restauration)": dict(REGLAGES), "M2 seule (glissement)": dict(REGLAGES, RESTAURATION=0.0),
               "sans glissement": dict(REGLAGES, GLISSEMENT=0.0)}
res_p = {n: [] for n in VARIANTES_P}
for _ in range(500):
    dx = rng.normal(size=3) * 0.1
    for n, r in VARIANTES_P.items():
        res_p[n].append((dx, projeter(x0, dx, r)))
for n, liste in res_p.items():
    ch = sum(bool(np.any(x != x0)) for _, x in liste)
    hors = sum(g_interp(x) > 0.0 for _, x in liste)
    dist = np.mean([np.linalg.norm(np.clip(x0 + dx, REGLAGES["MULT_MIN"], REGLAGES["MULT_MAX"]) - x) for dx, x in liste])
    print(f"  {n:24s} gains changes {ch:3d} / 500 ; resultats hors de l'ensemble {hors} ; distance moyenne a la cible {dist:.4f}")


# %% ETAPE 2 : essais de mise au point E1 a E4

def essai_mise_au_point(code, R0, vin0, duree, evenements=(), gx=None, vin=None, dvref=None, bruit=False, q=1e-9):
    n = int(round(duree / TC)) + 1
    t = np.arange(n) * TC

    def palier(base, morceaux):
        y = np.full(n, base, dtype=float)
        for t0, t1, val in morceaux:
            y[(t >= t0 - 1e-12) & (t < t1 - 1e-12)] = val
        return y

    sc = {"code": code, "nom": code, "duree": duree, "R0": R0, "q": q, "evenements": list(evenements), "t": t,
          "dvref": palier(0.0, dvref or []), "vin": palier(vin0, vin or []), "gx": palier(0.0, gx or []),
          "bruit": np.zeros(n)}
    if bruit:                                  # meme nature que S7b (10 mV, 10 kHz), autre graine (7)
        blanc = np.random.default_rng(7).standard_normal(n)
        a = np.exp(-2.0 * np.pi * 10e3 * TC)
        y, etat = np.zeros(n), 0.0
        for k in range(n):
            etat = a * etat + (1.0 - a) * blanc[k]
            y[k] = etat
        sc["bruit"] = 0.01 * y / np.std(y)
    return sc


E = [essai_mise_au_point("E1", 7.0, 190.0, 0.090, (0.040, 0.065), gx=[(0.040, 0.065, 1 / 4.5 - 1 / 7.0)]),
     essai_mise_au_point("E2", 15.0, 210.0, 0.090, (0.040, 0.065), vin=[(0.040, 0.065, 175.0), (0.065, 1.0, 235.0)]),
     essai_mise_au_point("E3", 60.0, 220.0, 0.090, (0.040, 0.065), dvref=[(0.040, 0.065, 10.0)]),
     essai_mise_au_point("E4", 9.0, 200.0, 0.060, (), bruit=True, q=2.5 / 4096 * 80)]
for sc in E:                                   # aucun point de mise au point n'est un point des onze essais
    for s_ in SCENARIOS:
        if abs(s_["R0"] - sc["R0"]) < 1e-9 and np.any(np.abs(s_["vin"] - sc["vin"][0]) < 1e-9):
            raise RuntimeError(f"Le point {sc['code']} apparait dans l'essai {s_['code']}.")

titre("ETAPE 2 : essais de mise au point E1 a E4 (IAE en mV.s)")
VARIANTES = (("R0 (gains figes)", lambda: LoiLu(K_ZN)), ("ELM-PID", lambda: ELMPID()),
             ("M2 seule", lambda: ELMPID(RESTAURATION=0.0)),
             ("jacobien constant", lambda: ELMPID(JACOBIEN_CONSTANT=J_REGRESSION)))
for sc in E:
    print(f"  {sc['code']} (R = {sc['R0']:g} ohms, Vin = {sc['vin'][0]:g} V)")
    for nom, fab in VARIANTES:
        reg = fab()
        sim = simuler(reg, sc)
        e = np.abs(sim["consigne"] - sim["v"])
        ligne = f"    {nom:18s} demarrage {np.sum(e[:K30]) * TC * 1e3:6.2f}, apres 30 ms {np.sum(e[K30:]) * TC * 1e3:6.2f}"
        if hasattr(reg, "journal"):
            ch = [i for i, x in enumerate(reg.journal) if x["change"]]
            Kf = reg.journal[-1]["K"] / K_ZN
            ligne += (f" ; gains changes sur {len(ch):2d} fenetres (premiere a "
                      f"{(ch[0] + 1) * 0.5 if ch else float('nan'):4.1f} ms), finaux x({Kf[0]:.3f}, {Kf[1]:.3f}, {Kf[2]:.3f})")
        print(ligne)
