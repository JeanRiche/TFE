# =============================================================================
# mise_au_point_pinn_pid.py
#
# VERSION
#   1 (7 octobre 2026).
#
# OBJECTIF
#   Verifier le mecanisme du PINN-PID AVANT de le juger sur les onze essais
#   communs (criteres_pinn_pid.txt), sur des essais qui n'en font pas
#   partie : quatre essais de mise au point E1 a E4 (les memes que pour
#   l'ELM-PID ; points R, Vin absents des onze essais). Variantes : R0
#   (gains figes), version de depart (boite), PINN-PID (ensemble admissible
#   et restauration, M1-M2), M1 sans restauration. IAE du demarrage et apres
#   30 ms, fenetres ou les gains changent, gains extremes et finaux.
#   Rien n'est regle sur ces essais.
#
# COMMENT LANCER CE SCRIPT
#   python mise_au_point_pinn_pid.py      (trois a cinq minutes)
# =============================================================================

import os
import numpy as np

try:
    DOSSIER = os.path.dirname(os.path.abspath(__file__))
except NameError:
    DOSSIER = os.getcwd()
__file__ = os.path.join(DOSSIER, "banc_pinn_pid.py")
with open(__file__, encoding="utf-8") as f:
    _SRC = f.read()
exec(_SRC[:_SRC.index("# %% ETAPE 2 :")])   # banc commun, PINN, observateur, horizon, PINNPID


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
for sc in E:
    for s_ in SCENARIOS:
        if abs(s_["R0"] - sc["R0"]) < 1e-9 and np.any(np.abs(s_["vin"] - sc["vin"][0]) < 1e-9):
            raise RuntimeError(f"Le point {sc['code']} apparait dans l'essai {s_['code']}.")

titre("Essais de mise au point E1 a E4 (IAE en mV.s ; gains en multiples de Ziegler-Nichols)")
VARIANTES = (("R0 (gains figes)", lambda: LoiLu(K_ZN)), ("boite (depart)", lambda: PINNPID("pinn", projection=0.0)),
             ("PINN-PID (M1-M2)", lambda: PINNPID("pinn")),
             ("M1 sans restauration", lambda: PINNPID("pinn", restauration=0.0)))
for sc in E:
    print(f"  {sc['code']} (R = {sc['R0']:g} ohms, Vin = {sc['vin'][0]:g} V)")
    for nom, fab in VARIANTES:
        reg = fab()
        sim = simuler(reg, sc)
        e = np.abs(sim["consigne"] - sim["v"])
        ligne = f"    {nom:22s} demarrage {np.sum(e[:K30]) * TC * 1e3:6.2f}, apres 30 ms {np.sum(e[K30:]) * TC * 1e3:6.2f}"
        if hasattr(reg, "journal"):
            G = np.array([x["K"] for x in reg.journal]) / K_ZN
            ch = int(np.sum(np.any(np.abs(np.diff(np.vstack([np.ones(3), G]), axis=0)) > 1e-12, axis=1)))
            ligne += (f" ; gains changes {ch:2d} fenetres ; Ki de {G[:, 1].min():.3f} a {G[:, 1].max():.3f} ; "
                      f"finaux x({G[-1, 0]:.3f}, {G[-1, 1]:.3f}, {G[-1, 2]:.3f})")
        print(ligne, flush=True)
