# =============================================================================
# mise_au_point_elm_pid.py
#
# VERSION
#   3 (8 octobre 2026), option B2 (bloc PID parallele a gains externes,
#   gains mis a jour a chaque pas, M5). Version 2 : option B (cadence par
#   fenetre, dossier ELM_PID) ; version 1 : loi incrementale (dossier
#   ELM_PID_INCREMENTAL).
#
# OBJECTIF
#   Verifier le mecanisme de l'ELM-PID AVANT de le juger sur les onze essais
#   communs (criteres_elm_pid.txt), sur des essais qui n'en font pas partie :
#     1. test geometrique de la projection : 500 pas aleatoires depuis le
#        depart (gains de Ziegler-Nichols, sur la frontiere de l'ensemble
#        admissible) ;
#     2. quatre essais de mise au point E1 a E4 (points R, Vin absents des
#        onze essais) : Ziegler-Nichols (point de depart), option B
#        (cadence par fenetre), option B2 (cadence par pas) et les variantes
#        des ablations de B2 ; IAE du demarrage et apres 30 ms, pas ou les
#        gains changent, gains finaux, changement des gains dans les 5 ms
#        qui suivent l'evenement de 40 ms, derive apres 30 ms sur E4 ;
#     3. controle : sans adaptation, l'ELM-PID redonne le PID de
#        Ziegler-Nichols a l'identique (ecart 0 sur d).
#   Rien n'est regle sur ces essais : ils montrent seulement que chaque
#   piece fait ce qu'elle doit faire. Le banc des onze essais
#   (banc_elm_pid.py) n'est execute ici que jusqu'a son etape 1
#   (definitions) : aucun des onze essais n'est simule.
#
# COMMENT LANCER CE SCRIPT
#   python mise_au_point_elm_pid.py      (quelques minutes)
# =============================================================================

import os
import time
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
print(f"  B2 : ETA_PAS = {REGLAGES['ETA_PAS']:g}, ZONE_MORTE_PAS = {REGLAGES['ZONE_MORTE_PAS'] * 1e3:.2f} mV "
      f"(regles R1 et R2 amendee de criteres_elm_pid.txt, M5 ; R2 d'origine : 54.41 mV, gardee en variante).")
VARIANTES = (("Ziegler-Nichols", lambda: PIDClassique()),
             ("B (par fenetre)", lambda: ELMPID(CADENCE_PAS=0.0)),
             ("B2 (par pas)", lambda: ELMPID()),
             ("B2 sans zone morte", lambda: ELMPID(ZONE_MORTE_PAS=0.0)),
             ("B2 zone morte R2 d'origine", lambda: ELMPID(ZONE_MORTE_PAS=2.5 / 4096 * 80 / 2 + 3 * 0.010)),
             ("B2 jacobien const.", lambda: ELMPID(JACOBIEN_CONSTANT=J_REGRESSION)))
K40, K45 = int(round(0.040 / TC)), int(round(0.045 / TC))
RESULTATS = {}
for sc in E:
    print(f"  {sc['code']} (R = {sc['R0']:g} ohms, Vin = {sc['vin'][0]:g} V)")
    for nom, fab in VARIANTES:
        reg = fab()
        t0 = time.time()
        sim = simuler(reg, sc)
        duree = time.time() - t0
        e = np.abs(sim["consigne"] - sim["v"])
        dem, apres = np.sum(e[:K30]) * TC * 1e3, np.sum(e[K30:]) * TC * 1e3
        RESULTATS[(sc["code"], nom)] = (dem, apres)
        ligne = f"    {nom:27s} demarrage {dem:6.2f}, apres 30 ms {apres:6.2f}"
        if hasattr(reg, "journal"):
            Kp = np.array(reg.K_pas) / K_ZN
            Kf = Kp[-1]
            if reg.adapt.cadence_pas:
                ch = reg.adapt.pas_changes
                prem = ch[0] * TC * 1e3 if ch else float("nan")
                ligne += (f" ; gains changes sur {len(ch):5d} pas (premier a {prem:5.2f} ms ; projections "
                          f"{reg.adapt.n_proj_pas:4d})")
            else:
                ch = [i for i, x in enumerate(reg.journal) if x["change"]]
                ligne += (f" ; gains changes sur {len(ch):5d} fenetres (premiere a "
                          f"{(ch[0] + 1) * 0.5 if ch else float('nan'):5.2f} ms)")
            ligne += f", finaux x({Kf[0]:.3f}, {Kf[1]:.3f}, {Kf[2]:.3f})"
            if sc["evenements"]:
                d45 = np.max(np.abs(Kp[min(K45, len(Kp) - 1)] - Kp[K40]))
                ligne += f" ; |dx| de 40 a 45 ms {d45:.4f}"
            else:
                derive = np.max(np.abs(Kp[K30:] - Kp[K30]))
                ligne += f" ; derive apres 30 ms (max |x(t) - x(30 ms)|) {derive:.4f}"
        if sc["evenements"]:
            o = grandeurs(sim, sc)
            ligne += " ; " + ("revenu" if all(ev["revenu"] for ev in o["evenements"]) else "PAS REVENU")
        ligne += f" ; {duree:4.1f} s"
        print(ligne)

titre("ETAPE 3 : controle, ELM-PID sans adaptation contre Ziegler-Nichols (E1 a E4)")
ecart = 0.0
for sc in E:
    a = simuler(PIDClassique(), sc)["d"]
    b = simuler(ELMPID(ADAPTER=False), sc)["d"]
    ecart = max(ecart, float(np.max(np.abs(a - b))))
print(f"  ecart maximal sur d : {ecart:.1e}")
if ecart != 0.0:
    raise RuntimeError("Sans adaptation, l'ELM-PID ne redonne pas le PID de Ziegler-Nichols a l'identique.")
