# =============================================================================
# comparaison_methodes.py
#
# VERSION
#   1 (7 octobre 2026). Regle : criteres_comparaison.txt (ecrite avant).
#
# OBJECTIF
#   A partir des resultats du banc commun v2.1 de chaque methode (version
#   finale), classer les cinq methodes sur chaque essai, mesurer ce que
#   chaque essai revele de leurs differences, choisir LE scenario de la
#   comparaison du memoire par la regle ecrite avant, et classer les
#   methodes sur ce scenario.
#
# FICHIERS NECESSAIRES (dans ce dossier)
#   banc_pso_pid_resultats.json, banc_fuzzy_pid_resultats.json,
#   banc_elm_pid_resultats.json, banc_pinn_pid_resultats.json
#
# COMMENT LANCER CE SCRIPT
#   python comparaison_methodes.py      (quelques secondes)
# =============================================================================

import os
import json
import itertools
import numpy as np

try:
    DOSSIER = os.path.dirname(os.path.abspath(__file__))
except NameError:
    DOSSIER = os.getcwd()


def lire(nom):
    with open(os.path.join(DOSSIER, nom), encoding="utf-8") as f:
        return json.load(f)["references"]


SOURCES = {"PSO-PID": ("banc_pso_pid_resultats.json", "PSO-PID"),
           "Fuzzy-PID": ("banc_fuzzy_pid_resultats.json", "Fuzzy-PID"),
           "ELM-PID": ("banc_elm_pid_resultats.json", "ELM-PID"),
           "PINN-PID": ("banc_pinn_pid_resultats.json", "PINN-PID")}
REF = {n: lire(f) for n, (f, _) in SOURCES.items()}
DONNEES = {"Ziegler-Nichols": REF["PSO-PID"]["Ziegler-Nichols"]}
for n, (f, cle) in SOURCES.items():
    DONNEES[n] = REF[n][cle]
METHODES = list(DONNEES)                      # ZN, PSO, Fuzzy, ELM, PINN
CODES = ["S1", "S2", "S3", "S4", "S5", "S6", "S7a", "S7b", "S8a", "S8b", "S9"]
CODES_IAE = ["S1", "S3", "S4", "S5", "S6", "S7a", "S7b", "S8a", "S8b", "S9"]
CODES_DEM = ["S1", "S8a", "S8b"]
CANDIDATS = ["S2", "S3", "S4", "S5", "S6", "S7b", "S8a", "S8b", "S9"]
PHENOMENES = {"S2": {"consigne"}, "S3": {"charge"}, "S4": {"charge"}, "S5": {"Vin"}, "S6": {"consigne"},
              "S7b": {"bruit"}, "S8a": {"charge legere", "Vin"}, "S8b": {"charge legere", "Vin"},
              "S9": {"demarrage", "charge", "charge legere", "consigne", "Vin", "conduction discontinue"}}


def titre(t):
    print("\n" + "=" * 100 + "\n " + t + "\n" + "=" * 100)


# %% ETAPE 1 : controle et cout J recalcule

titre("ETAPE 1 : controle des donnees et cout J")
ecart_zn = 0.0
for n in SOURCES:
    for c in CODES:
        a, b = REF[n]["Ziegler-Nichols"][c], DONNEES["Ziegler-Nichols"][c]
        ecart_zn = max(ecart_zn, abs(a["grandeurs"]["IAE"] - b["grandeurs"]["IAE"]) / b["grandeurs"]["IAE"],
                       abs(a["IAE_dem"] - b["IAE_dem"]) / b["IAE_dem"])
print(f"  Ziegler-Nichols identique dans les quatre fichiers : ecart relatif maximal {ecart_zn:.1e}")
if ecart_zn > 1e-9:
    raise RuntimeError("Les quatre bancs n'ont pas les memes grandeurs pour Ziegler-Nichols.")


def termes(m):
    d = DONNEES[m]
    return np.array([d[c]["grandeurs"]["IAE"] for c in CODES_IAE] + [d[c]["IAE_dem"] for c in CODES_DEM])


T_ZN = termes("Ziegler-Nichols")
J = {m: float(np.mean(termes(m) / T_ZN)) for m in METHODES}
ORDRE_J = sorted(METHODES, key=lambda m: J[m])
print("  Cout J (13 termes) : " + " ; ".join(f"{m} {J[m]:.3f}" for m in ORDRE_J))


# %% ETAPE 2 : chaque essai

def iae(m, c):
    return DONNEES[m][c]["grandeurs"]["IAE"]


def revenus(m, c):
    return DONNEES[m][c]["revenus"]


def kendall(o1, o2):
    """Tau de Kendall entre deux ordres des memes elements."""
    r1 = {m: i for i, m in enumerate(o1)}
    r2 = {m: i for i, m in enumerate(o2)}
    conc = disc = 0
    for a, b in itertools.combinations(o1, 2):
        s = (r1[a] - r1[b]) * (r2[a] - r2[b])
        conc += s > 0
        disc += s < 0
    return (conc - disc) / (conc + disc), disc


def ordre_essai(c):
    """Evenements revenus d'abord, puis IAE croissante."""
    return sorted(METHODES, key=lambda m: (not revenus(m, c), iae(m, c)))


titre("ETAPE 2 : IAE de 30 ms a la fin (mV.s) par essai et par methode ; classement ; criteres")
print(f"  {'essai':5s}" + "".join(f"{m:>16s}" for m in METHODES) + f"{'C3 sep.':>9s}{'C1 ecart':>10s}{'C2 tau':>8s}  classement")
TABLE = {}
for c in CODES:
    o = ordre_essai(c)
    v = np.array([iae(m, c) for m in o])
    ecarts = v[1:] / v[:-1] - 1.0
    tau, disc = kendall(o, ORDRE_J)
    sep = float(np.std(np.log([iae(m, c) for m in METHODES])))
    TABLE[c] = {"ordre": o, "IAE_mVs": {m: iae(m, c) * 1e3 for m in METHODES},
                "revenus": {m: revenus(m, c) for m in METHODES}, "C1_ecart_min": float(ecarts.min()),
                "C2_tau": tau, "C2_paires_inversees": disc, "C3_separation": sep}
    ligne = f"  {c:5s}" + "".join(f"{iae(m, c) * 1e3:15.2f}{'' if revenus(m, c) else '*'}{' ' if revenus(m, c) else ''}"
                                   for m in METHODES)
    print(ligne + f"{sep:9.3f}{100 * ecarts.min():9.1f}%{tau:8.2f}  " + " > ".join(o))
print("  (* : un evenement au moins ne revient pas dans +-1 V ; classement : meilleur a gauche)")
print("\n  Demarrage (IAE de 0 a 30 ms, mV.s) :")
for c in CODES_DEM:
    print(f"    {c:4s}" + "".join(f"  {m} {DONNEES[m][c]['IAE_dem'] * 1e3:6.2f}" for m in METHODES))


# %% ETAPE 3 : choix du scenario (regle de criteres_comparaison.txt)

titre("ETAPE 3 : choix du scenario")
for c in CANDIDATS:
    t = TABLE[c]
    ok1, ok2 = t["C1_ecart_min"] >= 0.05, t["C2_tau"] >= 0.6
    print(f"  {c:4s} C1 {'oui' if ok1 else 'non'} ({100 * t['C1_ecart_min']:5.1f} %) ; C2 {'oui' if ok2 else 'non'} "
          f"(tau {t['C2_tau']:.2f}, {t['C2_paires_inversees']} paire(s) inversee(s)) ; C3 {t['C3_separation']:.3f} ; "
          f"C4 {len(PHENOMENES[c])} phenomene(s)")
eligibles = [c for c in CANDIDATS if TABLE[c]["C1_ecart_min"] >= 0.05 and TABLE[c]["C2_tau"] >= 0.6]
if eligibles:
    RETENU = max(eligibles, key=lambda c: (TABLE[c]["C3_separation"], len(PHENOMENES[c])))
    print(f"\n  Essais qui passent C1 et C2 : {', '.join(eligibles)}. Retenu (plus grand C3) : {RETENU}.")
else:
    passe1 = [c for c in CANDIDATS if TABLE[c]["C1_ecart_min"] >= 0.05]
    RETENU = max(passe1, key=lambda c: TABLE[c]["C3_separation"])
    print(f"\n  Aucun essai ne passe C1 et C2. Retenu parmi ceux qui passent C1 (plus grand C3) : {RETENU}.")


# %% ETAPE 4 : classement sur le scenario retenu

titre(f"ETAPE 4 : classement des cinq methodes sur {RETENU}")
o = TABLE[RETENU]["ordre"]
for rang, m in enumerate(o, 1):
    g = DONNEES[m][RETENU]["grandeurs"]
    ev = g["evenements"]
    print(f"  {rang}. {m:16s} IAE {g['IAE'] * 1e3:8.2f} mV.s ; demarrage {DONNEES[m][RETENU]['IAE_dem'] * 1e3:7.2f} mV.s ; "
          f"depassement {g['depassement_pct']:5.1f} % ; ecart max {g['e_max_V']:6.2f} V ; activite |dd| {g['dd_moyen']:.4f} ; "
          f"{'tous les evenements reviennent' if revenus(m, RETENU) else 'evenement(s) non revenu(s)'}")
    for e in ev:
        print(f"       evenement a {e['t_ms']:6.1f} ms : IAE {e['IAE'] * 1e3:7.2f} mV.s, ecart max {e['e_max_V']:6.2f} V, "
              f"retour {('%.2f ms' % e['t_retour_ms']) if e.get('t_retour_ms') is not None else ('dans la bande' if e['revenu'] else 'NON')}")
tau, disc = kendall(o, ORDRE_J)
print(f"\n  Accord avec le classement par J : tau {tau:.2f} ({disc} paire(s) inversee(s)) ; ordre par J : {' > '.join(ORDRE_J)}")

with open(os.path.join(DOSSIER, "comparaison_resultats.json"), "w", encoding="utf-8") as f:
    json.dump({"version": 1, "J": J, "ordre_J": ORDRE_J, "essais": TABLE, "retenu": RETENU,
               "classement_retenu": o}, f, indent=1)
print("\n  comparaison_resultats.json ecrit.")


# %% ETAPE 5 : figure d'annexe (IAE rapportee a Ziegler-Nichols, essai par essai)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

M = np.array([[iae(m, c) / iae("Ziegler-Nichols", c) for c in CODES] for m in METHODES])
fig, ax = plt.subplots(figsize=(13, 3.8))
im = ax.imshow(np.log2(M), cmap="RdYlGn_r", vmin=-2, vmax=2, aspect="auto")
ax.set_xticks(range(len(CODES)))
ax.set_xticklabels([c + (" (retenu)" if c == RETENU else "") for c in CODES], fontsize=9)
ax.set_yticks(range(len(METHODES)))
ax.set_yticklabels(METHODES, fontsize=9)
for i, m in enumerate(METHODES):
    for j, c in enumerate(CODES):
        rang = TABLE[c]["ordre"].index(m) + 1
        ax.text(j, i, f"{M[i, j]:.2f}\n({rang})", ha="center", va="center", fontsize=7.5)
ax.set_title("IAE de 30 ms a la fin rapportee a Ziegler-Nichols (rang dans l'essai entre parentheses ; "
             "vert : meilleur que ZN)", fontsize=10, loc="left")
fig.colorbar(im, ax=ax, label="log2 du rapport")
fig.tight_layout()
fig.savefig(os.path.join(DOSSIER, "classement_par_essai.png"), dpi=110)
plt.close(fig)
print("  classement_par_essai.png ecrit.")
