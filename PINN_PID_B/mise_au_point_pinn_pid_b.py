# =============================================================================
# mise_au_point_pinn_pid_b.py
#
# VERSION
#   1 (8 octobre 2026), PINN-PID B (bloc PID parallele a gains externes).
#   Memes essais E1 a E4 que mise_au_point_elm_pid.py (dossier ELM_PID).
#
# OBJECTIF
#   Verifier le mecanisme du PINN-PID B AVANT de le juger sur les onze essais
#   communs (criteres_pinn_pid.txt), sur des essais qui n'en font pas partie :
#     1. controles (gradient de l'horizon, faits au chargement du banc) et
#        identite : sans adaptation, ecart 0 sur d au PID de Ziegler-Nichols
#        sur E1 a E4 ;
#     2. quatre essais de mise au point E1 a E4 (points R, Vin absents des
#        onze essais) : Ziegler-Nichols (point de depart), PINN-PID B, et deux
#        variantes des ablations (plafond : modele physique nominal ;
#        declenchement a 0.1 V de la version 1) ; IAE du demarrage et apres
#        30 ms, fenetres ou les gains changent, gains finaux.
#   Rien n'est regle sur ces essais : ils montrent seulement que chaque
#   piece fait ce qu'elle doit faire.
#
# COMMENT LANCER CE SCRIPT
#   python mise_au_point_pinn_pid_b.py      (quelques minutes)
# =============================================================================

import os
import numpy as np

try:
    DOSSIER_PINN = os.path.dirname(os.path.abspath(__file__))
except NameError:
    DOSSIER_PINN = os.getcwd()
__file__ = os.path.join(DOSSIER_PINN, "banc_pinn_pid.py")
with open(__file__, encoding="utf-8") as f:
    _SRC = f.read()
exec(_SRC[:_SRC.index("# %% ETAPE 2 :")])   # banc commun, PINN, observateur, horizon, PINNPIDB, controles du gradient


# %% ETAPE 1 : essais de mise au point E1 a E4 (definitions de mise_au_point_elm_pid.py)

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
ESSAIS_E = {sc["code"]: sc for sc in E}

titre("ETAPE 1 : identite sans adaptation (E1 a E4)")
zn = evaluer(lambda: PIDClassique(), essais=ESSAIS_E)
fige = evaluer(lambda: PINNPIDB(adapter=False), essais=ESSAIS_E)
ecart = max(float(np.max(np.abs(fige[c]["sim"]["d"] - zn[c]["sim"]["d"]))) for c in ESSAIS_E)
print(f"  PINN-PID B sans adaptation contre Ziegler-Nichols, ecart maximal sur d : {ecart:.1e}")
if ecart != 0.0:
    raise RuntimeError("Sans adaptation, le PINN-PID B ne redonne pas le PID de Ziegler-Nichols.")

titre("ETAPE 2 : essais de mise au point E1 a E4 (IAE en mV.s)")
VARIANTES = (("PINN-PID B", lambda: PINNPIDB()),
             ("plafond (modele)", lambda: PINNPIDB(predicteur="modele")),
             ("declenchement 0.1 V", lambda: PINNPIDB(seuil=0.1)))
RES = {"Ziegler-Nichols": zn}
for nom, fab in VARIANTES:
    RES[nom] = evaluer(fab, essais=ESSAIS_E)
for sc in E:
    c = sc["code"]
    print(f"  {c} (R = {sc['R0']:g} ohms, Vin = {sc['vin'][0]:g} V)")
    for nom, res in RES.items():
        r = res[c]
        e = np.abs(r["sim"]["consigne"] - r["sim"]["v"])
        ligne = f"    {nom:20s} demarrage {np.sum(e[:K30]) * TC * 1e3:6.2f}, apres 30 ms {np.sum(e[K30:]) * TC * 1e3:6.2f}"
        jr = r["reg"].journal
        if jr:
            X = np.array([x["x"] for x in jr])
            ch = [i for i, x in enumerate(jr) if x["change"]]
            ligne += (f" ; gains changes sur {len(ch):3d}/{len(jr)} fenetres (premiere a "
                      f"{(ch[0] + 1) * 0.5 if ch else float('nan'):4.1f} ms), finaux x({X[-1, 0]:.3f}, {X[-1, 1]:.3f}, "
                      f"{X[-1, 2]:.3f}), apres 30 ms P {X[59:, 0].min():.2f}-{X[59:, 0].max():.2f}, I "
                      f"{X[59:, 1].min():.2f}-{X[59:, 1].max():.2f}, D {X[59:, 2].min():.2f}-{X[59:, 2].max():.2f}")
        print(ligne, flush=True)
