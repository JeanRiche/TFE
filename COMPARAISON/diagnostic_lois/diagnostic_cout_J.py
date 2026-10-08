# Diagnostic du 8 octobre 2026 (COMPARAISON/diagnostic_lois) : pourquoi ELM-PID et PINN-PID
# rejettent moins bien les perturbations ; lois de Lu et PID parallele a gains figes.
# Lancer depuis ce dossier : python diagnostic_cout_J.py (le dossier ELM_PID doit etre a cote).
import os, json, numpy as np
_ICI = os.path.dirname(os.path.abspath(__file__)); __file__ = os.path.join(_ICI, "..", "..", "ELM_PID", "banc_elm_pid.py"); os.chdir(os.path.dirname(__file__))
src = open(__file__, encoding="utf-8").read(); exec(src[:src.index("# %% ETAPE 2 :")])
G = json.load(open(os.path.join(_ICI, "..", "..", "PSO_PID", "predictions_banc_pso_pid.json")))["gains"]
X_PSO = np.array([G["P"] / PID_P, G["I"] / PID_I, G["D"] / PID_D])

class LoiLuMesure(LoiLu):
    """Loi de Lu, derivee sur la mesure (-y) au lieu de l'erreur."""
    utilise_mesure = True
    def pas(self, e, mesure=None):
        y = -mesure
        if self.premier:
            self.e1, self.ef, self.g1, self.premier = e, y, 0.0, False
        g = TCN * (y - self.ef)
        brut = self.u + self.Kp * (e - self.e1) + self.Ki * e + self.Kd * (g - self.g1)
        u = min(max(brut, D_MIN), D_MAX)
        self.ef = self.ef + TCN * (y - self.ef)
        self.e1, self.g1, self.u = e, g, u
        return u

class PIDParMesure(PIDClassique):
    """PID parallele du bloc, derivee sur la mesure."""
    utilise_mesure = True
    def __init__(self, P, I, D):
        super().__init__(); self.P, self.I, self.D = P, I, D; self.init = False
    def pas(self, e, mesure=None):
        y = -mesure
        if not self.init:
            self.xF = PID_N * self.D * y * 0 + self.xF; self.init = True
        derivee = PID_N * (self.D * y - self.xF)
        u = self.P * e + self.xI + derivee
        u_sat = min(max(u, D_MIN), D_MAX)
        ei = self.I * e
        if not ((u != u_sat) and (np.sign(ei) == np.sign(u - u_sat))):
            self.xI += TC * ei
        self.xF += TC * derivee
        return u_sat

class PIDParallele(PIDClassique):
    def __init__(self, P, I, D):
        super().__init__(); self.P, self.I, self.D = P, I, D
    def pas(self, e):
        derivee = PID_N * (self.D * e - self.xF)
        u = self.P * e + self.xI + derivee
        u_sat = min(max(u, D_MIN), D_MAX)
        ei = self.I * e
        if not ((u != u_sat) and (np.sign(ei) == np.sign(u - u_sat))):
            self.xI += TC * ei
        self.xF += TC * derivee
        return u_sat
E = {sc["code"]: sc for sc in SCENARIOS}
def run(fab, codes):
    out = {}
    for c in codes:
        sim = simuler(fab(), E[c]); o = grandeurs(sim, E[c]); out[c] = (o["IAE"] * 1e3, max([ev["e_max_V"] for ev in o["evenements"]] or [0]))
    return out

class PIDParMesure2(PIDParallele):
    utilise_mesure = True
    def pas(self, e, mesure=None):
        y = -mesure
        if not hasattr(self, "yi"):
            self.xF = self.D * y; self.yi = True        # filtre initialise sur la mesure (pas de saut)
        derivee = PID_N * (self.D * y - self.xF)
        u = self.P * e + self.xI + derivee
        u_sat = min(max(u, D_MIN), D_MAX)
        ei = self.I * e
        if not ((u != u_sat) and (np.sign(ei) == np.sign(u - u_sat))):
            self.xI += TC * ei
        self.xF += TC * derivee
        return u_sat
CI = ["S1","S3","S4","S5","S6","S7a","S7b","S8a","S8b","S9"]; CD = ["S1","S8a","S8b"]; K30_ = int(round(0.03/TC))
def termes(fab):
    t1, t2, non = [], [], []
    for c in E:
        sim = simuler(fab(), E[c]); o = grandeurs(sim, E[c]); e = np.abs(sim["consigne"] - sim["v"])
        if c in CI: t1.append(o["IAE"])
        if c in CD: t2.append(float(np.sum(e[:K30_]) * TC))
        if not all(ev["revenu"] for ev in o["evenements"]): non.append(c)
    return np.array(t1 + t2), non
TZ, _ = termes(lambda: PIDClassique())
def J(nom, fab):
    t, non = termes(fab); r = t / TZ
    print(f"{nom:52s} J {r.mean():.3f}  apres30 {r[:10].mean():.3f}  dem {r[10:].mean():.3f}  non revenus {','.join(non) or '-'}", flush=True)
for gains, X in (("ZN", np.ones(3)), ("PSO", X_PSO)):
    P, I, D = PID_P * X[0], PID_I * X[1], PID_D * X[2]
    J(f"[{gains}] parallele (bloc, derivee sur e)", lambda: PIDParallele(P, I, D))
    J(f"[{gains}] parallele, derivee sur la mesure", lambda: PIDParMesure2(P, I, D))
    J(f"[{gains}] loi de Lu (derivee sur e)", lambda: LoiLu(K_ZN * X))
    J(f"[{gains}] loi de Lu, derivee sur la mesure", lambda: LoiLuMesure(K_ZN * X))
