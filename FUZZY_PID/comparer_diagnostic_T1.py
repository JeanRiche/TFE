# =============================================================================
# comparer_diagnostic_T1.py
#
# OBJECTIF
#   Lire diagnostic_T1_fuzzy.mat (ecrit par Diagnostic_T1_Fuzzy.m : 20 ms de
#   S1 sous Simulink, Fuzzy-PID puis gains forces a Ziegler-Nichols) et
#   separer les deux causes possibles de l'ecart de l'auto-test T1 :
#   1. Le regulateur. On rejoue, pas par pas, la loi du banc (ordonnanceur
#      de Zhao et PID du bloc) avec l'erreur e vue par Simulink. Si la
#      commande et les gains rejoues sont ceux de Simulink a 1e-9 pres, le
#      bloc PID et l'ordonnanceur calculent exactement ce que suppose le
#      banc. Sinon, le premier pas different est donne.
#   2. Le circuit et la mesure. On compare e et Vout de Simulink a ceux du
#      banc (meme regulateur, circuit du banc) : instant ou l'ecart depasse
#      1 mV, 10 mV, 100 mV, et ecart au premier pas.
#
# COMMENT LANCER CE SCRIPT
#   python comparer_diagnostic_T1.py    (dans le dossier du banc, avec
#   diagnostic_T1_fuzzy.mat). Une demi-minute.
# =============================================================================

import os
import numpy as np
from scipy.io import loadmat

try:
    DOSSIER_FUZZY = os.path.dirname(os.path.abspath(__file__))
except NameError:
    DOSSIER_FUZZY = os.getcwd()
with open(os.path.join(DOSSIER_FUZZY, "banc_fuzzy_pid.py"), encoding="utf-8") as f:
    SOURCE = f.read()
exec(SOURCE[:SOURCE.index("# %% ETAPE 2")])   # banc commun, ordonnanceur de Zhao, FuzzyPID

D = loadmat(os.path.join(DOSSIER_FUZZY, "diagnostic_T1_fuzzy.mat"), squeeze_me=True, struct_as_record=False)
sc = ESSAIS["S1"]

for cas, fixes in (("zn", True), ("fuzzy", False)):
    d = D[cas]
    e_s, u_s, v_s = np.ravel(d.e), np.ravel(d.u), np.ravel(d.v)
    G_s = np.atleast_2d(d.G)
    if G_s.shape[1] != 3:
        G_s = G_s.T
    n = len(e_s)
    print(f"\n=== {cas} : {n} pas de Simulink ===")
    # 1. Le regulateur rejoue avec l'erreur de Simulink
    reg = FuzzyPID(gains_fixes=fixes)
    u_r = np.array([reg.pas(float(x)) for x in e_s])
    G_r = np.array(reg.K_pas)
    du = np.abs(u_r - u_s)
    dG = np.max(np.abs(G_r - G_s) / np.abs(G_r), axis=1)
    k_u = int(np.argmax(du > 1e-9)) if np.any(du > 1e-9) else None
    k_G = int(np.argmax(dG > 1e-9)) if np.any(dG > 1e-9) else None
    print(f"  Regulateur rejoue avec e de Simulink : ecart max sur u {du.max():.2e}, sur les gains {dG.max():.2e} (relatif)")
    if k_u is None and k_G is None:
        print("  -> identique : le bloc PID et l'ordonnanceur calculent exactement ce que suppose le banc.")
    else:
        for nom, k in (("u", k_u), ("gains", k_G)):
            if k is not None:
                print(f"  -> premier pas different sur {nom} : k = {k} (t = {k * TC * 1e3:.4f} ms) ; "
                      f"e = {e_s[k]:.6f} V, u Simulink {u_s[k]:.9f}, u banc {u_r[k]:.9f}, "
                      f"gains Simulink {G_s[k]}, gains banc {G_r[k]}")
    # 2. Circuit et mesure : trajectoire du banc avec le meme regulateur
    sc_n = {k: (v[:n] if isinstance(v, np.ndarray) else v) for k, v in sc.items()}
    sim = simuler(FuzzyPID(gains_fixes=fixes), sc_n)
    e_b = sim["consigne"] - sim["mesure"]
    de = np.abs(e_s - e_b[:n])
    print(f"  e Simulink - banc : premier pas {de[0]:.2e} V, a 0.1 ms {de[22]:.2e} V, max {de.max() * 1e3:.1f} mV "
          f"a {np.argmax(de) * TC * 1e3:.2f} ms")
    for seuil in (1e-3, 1e-2, 1e-1):
        k = np.argmax(de > seuil) if np.any(de > seuil) else None
        print(f"    depasse {seuil * 1e3:5.0f} mV pour la premiere fois a " +
              (f"{k * TC * 1e3:.3f} ms" if k is not None else "jamais"))
