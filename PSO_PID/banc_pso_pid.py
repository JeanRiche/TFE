# =============================================================================
# banc_pso_pid.py
#
# VERSION
#   1 (6 octobre 2026).
#
# OBJECTIF
#   Juger sur les onze essais communs le reglage trouve par
#   recherche_pso_pid.py (methode de Gaing, 2004), a cote de Ziegler-Nichols
#   (meme PID, gains de depart) et du meilleur PID fige (oracle), et ecrire
#   ce que Simulink doit retrouver :
#     - predictions_banc_pso_pid.json : gains retenus et resultats attendus
#       sur les onze essais (meme format que predictions_banc_pid_fige.json,
#       lu par Construction_PSO_PID.m et Simuler_PSO_PID.m) ;
#     - banc_pso_pid_resultats.json : tous les chiffres (dix recherches,
#       previsions) ;
#     - banc_pso_pid.png : S1, S8b et S9 ; pso_pid_convergence.png :
#       convergence des dix recherches (comme les fig. 4 et 14 de l'article).
#   Les onze essais n'ont servi a rien pendant la recherche.
#
# LE REGLAGE RETENU (criteres_pso_pid.txt, ecart 7)
#   Pour beta = 1.0, le gbest de plus petit W de reglage parmi les cinq
#   graines. Les neuf autres recherches sont jugees et publiees, jamais
#   choisies apres coup.
#
# FICHIERS NECESSAIRES
#   banc_commun.py (2.1), scenarios_communs.json, scenario_S*.mat,
#   predictions_banc_pid_fige.json, recherche_pso_pid.py et
#   recherche_pso_pid.json (dix recherches).
#   Facultatif : banc_elm_pid_resultats.json, banc_pinn_pid_resultats.json,
#   banc_fuzzy_pid_resultats.json (rappel de leur J, sans melange).
#
# COMMENT LANCER CE SCRIPT
#   python banc_pso_pid.py      (deux a trois minutes)
# =============================================================================


# %% ETAPE 0 : definitions (reprises de recherche_pso_pid.py) et recherches

import os
import json
import time
import numpy as np
import matplotlib.pyplot as plt

try:
    DOSSIER_PSO = os.path.dirname(os.path.abspath(__file__))
except NameError:
    DOSSIER_PSO = os.getcwd()
with open(os.path.join(DOSSIER_PSO, "recherche_pso_pid.py"), encoding="utf-8") as f:
    SOURCE_RECHERCHE = f.read()
exec(SOURCE_RECHERCHE[:SOURCE_RECHERCHE.index("# %% ETAPE 3")])   # banc commun, contraintes, W, essais de reglage

T_DEBUT = time.time()
ESSAIS = {sc["code"]: sc for sc in SCENARIOS}
CODES_IAE = ["S1", "S3", "S4", "S5", "S6", "S7a", "S7b", "S8a", "S8b", "S9"]
CODES_DEM = ["S1", "S8a", "S8b"]
K30_ESSAI = int(round(0.03 / TC))
with open(os.path.join(DOSSIER_PSO, "recherche_pso_pid.json"), encoding="utf-8") as f:
    RECH = json.load(f)["recherches"]
CLES = [f"beta={b:g},graine={g}" for b in BETAS for g in GRAINES]
manque = [c for c in CLES if c not in RECH]
if manque:
    raise RuntimeError("Recherches manquantes dans recherche_pso_pid.json : " + ", ".join(manque))
with open(os.path.join(DOSSIER_PSO, "predictions_banc_pid_fige.json"), encoding="utf-8") as f:
    GAINS_FIGE = json.load(f)["gains"]


def titre(texte):
    print("\n" + "=" * 78 + "\n " + texte + "\n" + "=" * 78)


# %% ETAPE 1 : le reglage retenu

titre("ETAPE 1 : les dix recherches et le reglage retenu")
print(f"  {'recherche':20s} {'W reglage':>10s} {'a (P)':>8s} {'b (I)':>8s} {'c (D)':>8s} {'marge':>7s} {'coupure':>8s} "
      f"{'Mp moy %':>9s} {'ts moy ms':>10s}")
for c in CLES:
    r = RECH[c]
    mp_ = np.mean([x["Mp_pct"] for x in r["reglage"]]) if r["reglage"] else float("nan")
    ts_ = np.mean([x["ts_ms"] for x in r["reglage"]]) if r["reglage"] else float("nan")
    print(f"  {c:20s} {r['W_gbest']:10.4f} {r['gbest'][0]:8.4f} {r['gbest'][1]:8.4f} {r['gbest'][2]:8.4f} "
          f"{r['marge_min']:6.1f}d {r['fc_max']:7.0f}Hz {mp_:9.2f} {ts_:10.3f}")
CLE_RETENUE = min((c for c in CLES if c.startswith("beta=1,")), key=lambda c: RECH[c]["W_gbest"])
RET = RECH[CLE_RETENUE]
if not RET["admissible"]:
    raise RuntimeError("Le reglage retenu ne respecte pas les contraintes.")
P_R, I_R, D_R = RET["gains"]["P"], RET["gains"]["I"], RET["gains"]["D"]
print(f"\n  Retenu : {CLE_RETENUE} ; P = {P_R:.6f}, I = {I_R:.4f}, D = {D_R:.6e} "
      f"(x ZN : {RET['gbest'][0]:.4f}, {RET['gbest'][1]:.4f}, {RET['gbest'][2]:.4f}).")
print("  Sur les six demarrages de reglage :")
for x in RET["reglage"]:
    print(f"    {x['essai']:10s} Mp {x['Mp_pct']:6.2f} %, Ess {x['Ess_pct']:.3f} %, tr {x['tr_ms']:.3f} ms, "
          f"ts {x['ts_ms']:.3f} ms, W {x['W']:.3f}")


# %% ETAPE 2 : jugement sur les onze essais

def evaluer_essais(P, I, D):
    """Grandeurs du banc commun sur les onze essais, IAE du demarrage, retours."""
    res = {}
    for code, sc in ESSAIS.items():
        sim = simuler(PIDParallele(P, I, D), sc)
        o = grandeurs(sim, sc)
        e = sim["consigne"] - sim["v"]
        res[code] = {"o": o, "IAE_dem": float(np.sum(np.abs(e[:K30_ESSAI])) * TC),
                     "revenus": bool(all(ev["revenu"] for ev in o["evenements"])), "sim": sim}
    return res


def termes(res):
    return np.array([res[c]["o"]["IAE"] for c in CODES_IAE] + [res[c]["IAE_dem"] for c in CODES_DEM])


titre("ETAPE 2 : jugement sur les onze essais communs")
TOUS = {"Ziegler-Nichols": evaluer_essais(PID_P, PID_I, PID_D),
        "meilleur PID fige": evaluer_essais(GAINS_FIGE["P"], GAINS_FIGE["I"], GAINS_FIGE["D"]),
        "PSO-PID": evaluer_essais(P_R, I_R, D_R)}
T_ZN = termes(TOUS["Ziegler-Nichols"])
J_TOUS = {n: float(np.mean(termes(r) / T_ZN)) for n, r in TOUS.items()}
print("  " + " " * 28 + "".join(f"{n:>20s}" for n in TOUS))
print("  " + f"{'cout J':28s}" + "".join(f"{J_TOUS[n]:20.3f}" for n in TOUS))
print("  " + f"{'evenements non revenus':28s}" + "".join(
    f"{(','.join(c for c in CODES_IAE if not TOUS[n][c]['revenus']) or '-'):>20s}" for n in TOUS))
for code in ESSAIS:
    for cle, etiquette, fmt, k in (("depassement_pct", "depassement %", "{:.1f}", 1.0), ("IAE", "IAE mV.s", "{:.2f}", 1e3),
                                   ("e_eff_V", "ecart efficace mV", "{:.1f}", 1e3), ("iL_max_dem_A", "iL crete dem. A", "{:.1f}", 1.0)):
        if cle == "depassement_pct" and code not in ("S1", "S8a", "S8b"):
            continue
        if cle == "iL_max_dem_A" and code not in ("S1", "S8b"):
            continue
        print("  " + f"{code + ' ' + etiquette:28s}" + "".join(f"{fmt.format(TOUS[n][code]['o'][cle] * k):>20s}" for n in TOUS))
print("  " + f"{'activite |dd| (S1)':28s}" + "".join(f"{TOUS[n]['S1']['o']['dd_moyen']:20.4f}" for n in TOUS))
DECOMP = {}
print("\n  Decomposition de J (10 IAE apres 30 ms ; 3 IAE de demarrage) :")
for n in TOUS:
    r = termes(TOUS[n]) / T_ZN
    DECOMP[n] = (float(np.mean(r[:10])), float(np.mean(r[10:])))
    print(f"    {n:20s} apres 30 ms {DECOMP[n][0]:.3f} ; demarrage {DECOMP[n][1]:.3f}")

print("\n  Les dix recherches jugees sur les onze essais (aucune n'est choisie apres coup) :")
JUGEMENT = {}
for c in CLES:
    r = RECH[c]
    if not r["admissible"]:
        JUGEMENT[c] = None
        print(f"    {c:20s} aucun individu admissible")
        continue
    res = TOUS["PSO-PID"] if c == CLE_RETENUE else evaluer_essais(r["gains"]["P"], r["gains"]["I"], r["gains"]["D"])
    Jc = float(np.mean(termes(res) / T_ZN))
    non = [k for k in CODES_IAE if not res[k]["revenus"]]
    JUGEMENT[c] = {"J": Jc, "non_revenus": non, "S1_depassement_pct": res["S1"]["o"]["depassement_pct"]}
    print(f"    {c:20s} J = {Jc:.3f} ; {'tous revenus' if not non else 'pas revenus : ' + ','.join(non)} ; "
          f"depassement S1 {res['S1']['o']['depassement_pct']:.1f} %{'   <- retenu' if c == CLE_RETENUE else ''}")

AUTRES = {}
for nom, fichier in (("ELM-PID", "banc_elm_pid_resultats.json"), ("PINN-PID", "banc_pinn_pid_resultats.json"),
                     ("Fuzzy-PID", "banc_fuzzy_pid_resultats.json")):
    chemin = os.path.join(DOSSIER_PSO, fichier)
    if os.path.isfile(chemin):
        with open(chemin, encoding="utf-8") as f:
            AUTRES[nom] = json.load(f).get("J", {}).get(nom)
if AUTRES:
    print("\n  Rappel des autres methodes (J sur les memes onze essais) : " +
          " ; ".join(f"{n} {j:.3f}" for n, j in AUTRES.items() if j is not None))


# %% ETAPE 3 : previsions

titre("ETAPE 3 : previsions de criteres_pso_pid.txt")
PSO = TOUS["PSO-PID"]
au_bord = sum(1 for x in RET["gbest"] if x <= K_MIN + 1e-9 or x >= K_MAX - 1e-9)
b1 = [RECH[c] for c in CLES if c.startswith("beta=1,") and RECH[c]["admissible"]]
Wb1 = [r["W_gbest"] for r in b1]
G1 = np.array([r["gbest"] for r in b1])
ret15 = min((RECH[c] for c in CLES if c.startswith("beta=1.5,") and RECH[c]["admissible"]),
            key=lambda r: r["W_gbest"])
mp10, ts10 = np.mean([x["Mp_pct"] for x in RET["reglage"]]), np.mean([x["ts_ms"] for x in RET["reglage"]])
mp15, ts15 = np.mean([x["Mp_pct"] for x in ret15["reglage"]]), np.mean([x["ts_ms"] for x in ret15["reglage"]])
P = {"P1": RET["admissible"] and au_bord <= 1,
     "P2": PSO["S1"]["o"]["depassement_pct"] < TOUS["Ziegler-Nichols"]["S1"]["o"]["depassement_pct"],
     "P3": 0.74 <= J_TOUS["PSO-PID"] <= 0.95,
     "P4": all(PSO[c]["revenus"] for c in CODES_IAE),
     "P5": DECOMP["PSO-PID"][0] > DECOMP["meilleur PID fige"][0],
     "P6": (max(Wb1) / min(Wb1) - 1 <= 0.02) and bool(np.any(G1.max(axis=0) / np.maximum(G1.min(axis=0), 1e-12) - 1 > 0.2)),
     "P7": mp15 < mp10 and ts15 > ts10}
TEXTE = {"P1": f"admissible, {au_bord} gain(s) au bord de [0 ; 4]",
         "P2": f"depassement S1 {PSO['S1']['o']['depassement_pct']:.2f} % (ZN 13.99 %)",
         "P3": f"J entre 0.74 et 0.95 : {J_TOUS['PSO-PID']:.3f}",
         "P4": "tous les evenements reviennent" if P["P4"] else "pas revenus : " + ",".join(
             c for c in CODES_IAE if not PSO[c]["revenus"]),
         "P5": f"apres 30 ms {DECOMP['PSO-PID'][0]:.3f} (PID fige {DECOMP['meilleur PID fige'][0]:.3f})",
         "P6": f"W des cinq graines (beta = 1) de {min(Wb1):.4f} a {max(Wb1):.4f} ; gains x ZN de "
               f"{np.round(G1.min(axis=0), 3).tolist()} a {np.round(G1.max(axis=0), 3).tolist()}",
         "P7": f"beta = 1.5 : Mp moyen {mp15:.2f} % (beta = 1 : {mp10:.2f}), ts moyen {ts15:.3f} ms ({ts10:.3f})"}
for k in P:
    print(f"  {k} {'juste' if P[k] else 'FAUSSE'} : {TEXTE[k]}")


# %% ETAPE 4 : fichiers pour Simulink, resultats et figures

titre("ETAPE 4 : fichiers pour Simulink, resultats et figures")
pas_1ms = int(round(1e-3 / TC))
predictions = {"version": 2, "Te": TC,
               "regulateur": f"PSO-PID (Gaing 2004, {CLE_RETENUE} ; P = {P_R:.6f}, I = {I_R:.4f}, D = {D_R:.6e}, N = {PID_N})",
               "gains": {"P": P_R, "I": I_R, "D": D_R, "N": PID_N, "multiplicateurs": RET["gbest"]},
               "critere": {"W_reglage": RET["W_gbest"], "J_essais": J_TOUS["PSO-PID"], "marge_min_deg": RET["marge_min"],
                           "fc_max_Hz": RET["fc_max"]},
               "controle": {}, "essais": {}}
for code, r in PSO.items():
    sim = r["sim"]
    predictions["essais"][code] = {"grandeurs": r["o"],
                                   "v_toutes_les_ms": sim["v"][::pas_1ms].tolist(),
                                   "iL_toutes_les_ms": sim["iL"][::pas_1ms].tolist(),
                                   "d_moyen_par_ms": [float(np.mean(sim["d"][i:i + pas_1ms]))
                                                      for i in range(0, len(sim["d"]) - pas_1ms + 1, pas_1ms)]}
with open(os.path.join(DOSSIER_PSO, "predictions_banc_pso_pid.json"), "w", encoding="utf-8") as f:
    json.dump(predictions, f, indent=1, allow_nan=False)
print("  predictions_banc_pso_pid.json ecrit.")

sortie = {"version": 1, "retenu": CLE_RETENUE, "gains": predictions["gains"], "J": J_TOUS, "decomposition": DECOMP,
          "jugement_dix_recherches": JUGEMENT, "autres_methodes_J": AUTRES,
          "previsions": {k: {"juste": bool(P[k]), "detail": TEXTE[k]} for k in P},
          "references": {n: {c: {"grandeurs": TOUS[n][c]["o"], "IAE_dem": TOUS[n][c]["IAE_dem"],
                                 "revenus": TOUS[n][c]["revenus"]} for c in ESSAIS} for n in TOUS},
          "duree_s": round(time.time() - T_DEBUT, 1)}
with open(os.path.join(DOSSIER_PSO, "banc_pso_pid_resultats.json"), "w", encoding="utf-8") as f:
    json.dump(sortie, f, indent=1, allow_nan=False, default=lambda x: None)
print("  banc_pso_pid_resultats.json ecrit.")

fig, axes = plt.subplots(2, 3, figsize=(16, 7.5), sharex="col")
for col, (code, xlim) in enumerate((("S1", (0, 15)), ("S8b", None), ("S9", None))):
    for nom, couleur in (("Ziegler-Nichols", "0.55"), ("meilleur PID fige", "tab:green"), ("PSO-PID", "tab:red")):
        sim = TOUS[nom][code]["sim"]
        axes[0, col].plot(sim["t"] * 1e3, sim["v"], lw=0.6, color=couleur, label=nom)
        axes[1, col].plot(sim["t"] * 1e3, sim["iL"], lw=0.4, color=couleur)
    axes[0, col].plot(sim["t"] * 1e3, sim["consigne"], "k--", lw=0.6)
    axes[0, col].set_ylim(30, 200)
    axes[0, col].set_title(f"{code} : tension de sortie", fontsize=9, loc="left")
    axes[1, col].set_title(f"{code} : courant de la bobine (observe)", fontsize=9, loc="left")
    axes[1, col].set_xlabel("temps (ms)")
    if xlim:
        axes[1, col].set_xlim(*xlim)
    for ax in axes[:, col]:
        ax.grid(alpha=0.3)
axes[0, 0].legend(fontsize=7)
axes[0, 0].set_ylabel("V")
axes[1, 0].set_ylabel("A")
fig.tight_layout()
fig.savefig(os.path.join(DOSSIER_PSO, "banc_pso_pid.png"), dpi=110)
plt.close(fig)

fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
for c in CLES:
    h = RECH[c]["historique"]
    style = "-" if c.startswith("beta=1,") else "--"
    axes[0].plot([x["iter"] for x in h], [1.0 / x["W_gbest"] for x in h], style, lw=1.0, label=c)
    axes[1].plot([x["iter"] for x in h], [x["f_moy"] for x in h], style, lw=0.8)
    axes[2].plot([x["iter"] for x in h], [x["f_ect"] for x in h], style, lw=0.8)
axes[0].set_title("f = 1/W du gbest (fig. 4 de l'article)", fontsize=9, loc="left")
axes[1].set_title("moyenne de f dans la population (fig. 14)", fontsize=9, loc="left")
axes[2].set_title("ecart type de f dans la population (fig. 14)", fontsize=9, loc="left")
for ax in axes:
    ax.set_xlabel("iteration")
    ax.grid(alpha=0.3)
axes[0].legend(fontsize=6)
fig.tight_layout()
fig.savefig(os.path.join(DOSSIER_PSO, "pso_pid_convergence.png"), dpi=110)
plt.close(fig)
print(f"  banc_pso_pid.png et pso_pid_convergence.png ecrits. Duree totale : {time.time() - T_DEBUT:.0f} s.")
