# =============================================================================
# simulations_scenario.py
#
# VERSION
#   1 (7 octobre 2026).
#
# OBJECTIF
#   Rejouer le scenario retenu par comparaison_methodes.py (S4, charge
#   +-20 %) avec les cinq methodes, chacune prise dans son propre dossier
#   (son banc, ses fichiers, sa version finale), pour :
#     1. verifier que l'IAE retrouve celle des fichiers de resultats ;
#     2. mesurer la robustesse du classement : circuit avec L ou C a
#        +-0.1 % (le regulateur, lui, n'est pas change) ;
#     3. enregistrer les signaux a pleine resolution (scenario_retenu.npz)
#        et tracer la figure de comparaison (comparaison_S4.png).
#
# DOSSIERS NECESSAIRES (a cote de ce dossier)
#   ../PSO_PID, ../FUZZY_PID, ../ELM_PID, ../PINN_PID (dossiers complets)
#
# COMMENT LANCER CE SCRIPT
#   python simulations_scenario.py [S4|S8a|...]   (trois a cinq minutes ; S4 par defaut)
# =============================================================================

import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    DOSSIER = os.path.dirname(os.path.abspath(__file__))
except NameError:
    DOSSIER = os.getcwd()
RACINE = os.path.dirname(DOSSIER)
import sys
CODE = sys.argv[1] if len(sys.argv) > 1 else "S4"   # scenario a rejouer (par defaut S4)
DESCRIPTION = {"S4": "charge +-20 %", "S8a": "charge legere 25 ohms, echelons de charge"}.get(CODE, "")


def charger(dossier, fichier, marque):
    """Execute les definitions d'un banc (jusqu'a la marque) dans un espace
    de noms propre a la methode."""
    chemin = os.path.join(RACINE, dossier, fichier)
    ns = {"__file__": chemin, "__name__": "definitions"}
    with open(chemin, encoding="utf-8") as f:
        src = f.read()
    exec(src[:src.index(marque)], ns)
    return ns


NS = {"Ziegler-Nichols": charger("ELM_PID", "banc_elm_pid.py", "# %% ETAPE 2 :"),
      "PSO-PID": charger("PSO_PID", "recherche_pso_pid.py", "\n# %% ETAPE 3 :"),
      "Fuzzy-PID": charger("FUZZY_PID", "banc_fuzzy_pid.py", "# %% ETAPE 2 :"),
      "ELM-PID": None, "PINN-PID": charger("PINN_PID", "banc_pinn_pid.py", "# %% ETAPE 2 :")}
NS["ELM-PID"] = NS["Ziegler-Nichols"]
with open(os.path.join(RACINE, "PSO_PID", "predictions_banc_pso_pid.json"), encoding="utf-8") as f:
    G_PSO = json.load(f)["gains"]
FABRIQUES = {"Ziegler-Nichols": lambda ns: ns["PIDClassique"](),
             "PSO-PID": lambda ns: ns["PIDParallele"](G_PSO["P"], G_PSO["I"], G_PSO["D"]),
             "Fuzzy-PID": lambda ns: ns["FuzzyPID"](),
             "ELM-PID": lambda ns: ns["ELMPID"](),
             "PINN-PID": lambda ns: ns["PINNPID"]()}
with open(os.path.join(DOSSIER, "comparaison_resultats.json"), encoding="utf-8") as f:
    ATTENDU = json.load(f)["essais"][CODE]["IAE_mVs"]


def lancer(m, fl=1.0, fc=1.0):
    ns = NS[m]
    L0, C0 = ns["L_BOB"], ns["C_CONV"]
    ns["L_BOB"], ns["C_CONV"] = L0 * fl, C0 * fc       # le circuit seul change
    try:
        sc = {s["code"]: s for s in ns["SCENARIOS"]}[CODE]
        reg = FABRIQUES[m](ns)
        sim = ns["simuler"](reg, sc)
        o = ns["grandeurs"](sim, sc)
    finally:
        ns["L_BOB"], ns["C_CONV"] = L0, C0
    return o, sim, reg


print(f"Scenario {CODE} : nominal, puis L ou C a +-0.1 % (IAE de 30 ms a la fin, mV.s)")
VARIANTES = (("nominal", 1.0, 1.0), ("L - 0.1 %", 0.999, 1.0), ("L + 0.1 %", 1.001, 1.0),
             ("C - 0.1 %", 1.0, 0.999), ("C + 0.1 %", 1.0, 1.001))
RES, SIG = {}, {}
for m in FABRIQUES:
    RES[m] = {}
    for nom, fl, fc in VARIANTES:
        o, sim, reg = lancer(m, fl, fc)
        RES[m][nom] = o["IAE"] * 1e3
        if nom == "nominal":
            SIG[m] = {"t": sim["t"], "v": sim["v"], "iL": sim["iL"], "d": sim["d"], "consigne": sim["consigne"]}
            if hasattr(reg, "K_pas"):
                SIG[m]["K"] = np.array(reg.K_pas)
    ecart = abs(RES[m]["nominal"] - ATTENDU[m]) / ATTENDU[m]
    print(f"  {m:16s} " + "  ".join(f"{n} {RES[m][n]:6.2f}" for n, _, _ in VARIANTES) +
          f"   (fichier {ATTENDU[m]:.2f}, ecart {ecart:.1e})", flush=True)
    if ecart > 1e-6:
        raise RuntimeError(f"{m} : l'IAE rejouee ne retrouve pas le fichier de resultats.")

print("\nClassement dans chaque variante du circuit :")
ORDRES = {}
for nom, _, _ in VARIANTES:
    o = sorted(FABRIQUES, key=lambda m: RES[m][nom])
    ORDRES[nom] = o
    v = [RES[m][nom] for m in o]
    print(f"  {nom:10s} " + " > ".join(o) + "   (ecart minimal entre voisins "
          f"{100 * min(b / a - 1 for a, b in zip(v, v[1:])):.1f} %)")
stable = all(ORDRES[n] == ORDRES["nominal"] for n in ORDRES)
print(f"  Classement {'identique dans les cinq variantes' if stable else 'CHANGE avec le circuit'}.")

np.savez_compressed(os.path.join(DOSSIER, f"scenario_{CODE}.npz"),
                    **{f"{m}__{k}": v for m in SIG for k, v in SIG[m].items()})
with open(os.path.join(DOSSIER, f"robustesse_{CODE}.json"), "w", encoding="utf-8") as f:
    json.dump({"scenario": CODE, "IAE_mVs": RES, "ordres": ORDRES, "stable": stable}, f, indent=1)

# Figure : demarrage et trois premiers evenements (S4 : 50 et 100 ms charge forte, 70 ms retour)
COUL = {"Ziegler-Nichols": "0.5", "PSO-PID": "tab:orange", "Fuzzy-PID": "tab:green", "ELM-PID": "tab:blue",
        "PINN-PID": "tab:red"}
fig, ax = plt.subplots(3, 4, figsize=(20, 10), sharex="col", gridspec_kw={"height_ratios": [2, 1, 1]})
for col, (t0, t1) in enumerate(((0.0, 8.0), (49.0, 56.0), (69.0, 76.0), (99.0, 106.0))):
    for m in FABRIQUES:
        s = SIG[m]
        k = (s["t"] * 1e3 >= t0) & (s["t"] * 1e3 <= t1)
        ax[0, col].plot(s["t"][k] * 1e3, s["v"][k], color=COUL[m], lw=1.0, label=f"{m} (IAE {RES[m]['nominal']:.1f} mV.s)")
        ax[1, col].plot(s["t"][k] * 1e3, s["iL"][k], color=COUL[m], lw=0.6)
        ax[2, col].plot(s["t"][k] * 1e3, s["d"][k], color=COUL[m], lw=0.6)
    ax[0, col].plot(SIG["PSO-PID"]["t"][k] * 1e3, SIG["PSO-PID"]["consigne"][k], "k--", lw=0.6)
    TITRES = (["demarrage (5 ohms)", "50 ms : 5 -> 4 ohms", "70 ms : 4 -> 5 ohms", "100 ms : 5 -> 6 ohms"]
              if CODE == "S4" else ["demarrage", "evenement a 50 ms", "evenement a 70 ms", "evenement a 100 ms"])
    ax[0, col].set_title(TITRES[col], fontsize=10, loc="left")
    if col:
        ax[0, col].set_ylim(*((87, 113) if CODE == "S4" else (97.5, 102.5)))
    ax[2, col].set_xlabel("temps (ms)")
    for a in ax[:, col]:
        a.grid(alpha=0.3)
ax[0, 0].set_ylabel("Vout (V)")
ax[1, 0].set_ylabel("iL (A)")
ax[2, 0].set_ylabel("rapport cyclique")
ax[0, 1].legend(fontsize=8, loc="lower right")
fig.suptitle(f"{CODE} ({DESCRIPTION}) : les cinq methodes sur le banc commun v2.1", fontsize=12)
fig.tight_layout()
fig.savefig(os.path.join(DOSSIER, f"comparaison_{CODE}.png"), dpi=110)
plt.close(fig)
print(f"\nscenario_{CODE}.npz, robustesse_{CODE}.json et comparaison_{CODE}.png ecrits.")
