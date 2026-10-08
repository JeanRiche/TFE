# Diagnostic du 8 octobre 2026 (COMPARAISON/diagnostic_lois) : pourquoi ELM-PID et PINN-PID
# rejettent moins bien les perturbations ; lois de Lu et PID parallele a gains figes.
# Lancer depuis ce dossier : python diagnostic_perturbations.py (le dossier ELM_PID doit etre a cote).
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
codes = ["S2", "S3", "S4", "S5", "S6", "S9"]
V = {"ZN parallele (bloc)": lambda: PIDClassique(),
     "R0 = loi de Lu, gains ZN": lambda: LoiLu(K_ZN),
     "R0, derivee sur la mesure": lambda: LoiLuMesure(K_ZN),
     "PSO parallele (bloc)": lambda: PIDParallele(G["P"], G["I"], G["D"]),
     "loi de Lu, gains PSO": lambda: LoiLu(K_ZN * X_PSO),
     "loi de Lu, gains PSO, derivee mesure": lambda: LoiLuMesure(K_ZN * X_PSO),
     "ELM-PID (retenu)": lambda: ELMPID()}
print(f"{'variante':40s}" + "".join(f"{c:>15s}" for c in codes) + "   (IAE apres 30 ms mV.s / ecart max V)")
for n, f in V.items():
    r = run(f, codes)
    print(f"{n:40s}" + "".join(f"{r[c][0]:8.2f}/{r[c][1]:5.2f}" for c in codes), flush=True)
print("\nGains PSO x ZN :", np.round(X_PSO, 3), " g de l'ensemble admissible ELM :", round(float(g_interp(X_PSO)), 4),
      "(<= 0 : admissible)")
reg = ELMPID(); sim = simuler(reg, E["S4"])
for i, x in enumerate(reg.journal):
    t = (i + 1) * 0.5
    if x["adapte"] and t > 30:
        print(f"  S4 ELM fenetre finissant a {t:5.1f} ms : ebar {x['ebar']:+.3f} V -> x({x['x'][0]:.3f}, {x['x'][1]:.3f}, {x['x'][2]:.3f})")
