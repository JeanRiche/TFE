# =============================================================================
# estimation_etat_pinn.py
#
# VERSION
#   1 (5 octobre 2026), PINN-PID sur la base commune v2 (banc commun 2.1),
#   etape 3.
#
# OBJECTIF
#   Repondre, avant de construire le regulateur, a une question : le
#   PINN-PID peut-il connaitre l'etat du convertisseur (Vout, iL), sa charge
#   et sa tension d'entree a partir de ce qu'il mesure ? Le PINN a besoin de
#   ces quatre grandeurs au debut de chaque prediction. Le regulateur ne
#   mesure que Vout (sortie du capteur, bruitee ou quantifiee selon l'essai)
#   et connait le rapport cyclique qu'il applique. Les autres methodes n'ont
#   rien de plus : le PINN-PID n'aura rien de plus (pas de mesure de iL, de
#   la charge ou de Vin).
#
# LA METHODE
#   Filtre de Kalman etendu (EKF) a chaque periode Tc = 1/220 000 s, sur
#   l'etat [Vout, iL, ln G, Vin] (G : conductance de charge, 1/R). Il utilise
#   le modele physique exact (moyen par tranche Tc), le meme que la mesure
#   de reference de l'etape 2 : c'est le meilleur cas. Si l'estimation
#   echoue avec ce modele, elle echouera avec le PINN.
#   Modele d'une tranche Tc : pendant la tranche, le MOSFET conduit une
#   fraction s du temps (s se deduit du rapport cyclique et de la phase de
#   la porteuse, comme dans le banc commun). Le modele moyen sur la tranche
#   est lineaire :
#     C dv/dt = iL - G v,
#     L diL/dt = s Vin - v - (1 - s) Vf - (s Ron + (1 - s) Rd) iL,
#   integre exactement sur Tc (exponentielle de matrice). Si le courant
#   passe sous zero pendant une tranche ou le MOSFET ne conduit pas tout le
#   temps, la diode se bloque : le courant reste a zero et le condensateur
#   se decharge dans la charge (approximation lineaire de l'instant du
#   blocage).
#
# CE QUE LA PHYSIQUE PERMET D'ATTENDRE
#   En regime etabli, le couple (Vout, d) ne donne qu'une equation :
#     d Vin = Vout + Req iL + (1 - d) Vf,  iL = G Vout,  Req = d Ron + (1 - d) Rd.
#   La charge n'y entre que par la chute Req iL (1 V environ a 5 ohms) : en
#   regime etabli, un changement de charge et quelques volts de Vin
#   produisent le meme effet. La charge ne se voit que pendant les
#   transitoires, par l'amortissement du filtre LC.
#
# LES DONNEES
#   Reglage du filtre : ELM_A1 et ELM_A2 (enregistrements Simulink en boucle
#   ouverte de l'ELM-PID, distincts des essais), mesure quantifiee au pas de
#   S7a (200/4096 V), le cas le plus dur.
#   Evaluation : les onze essais du banc commun en boucle fermee avec R0
#   (loi de Lu a derivee filtree, gains de Ziegler-Nichols figes). Le filtre
#   recoit la mesure telle que le regulateur la recoit et le rapport
#   cyclique applique.
#
# LES CRITERES (fixes avant le calcul, criteres_etape3_estimation.txt)
#   De 30 ms a la fin de chaque essai :
#     E1 : |Vin estimee - Vin| <= 5 V pendant au moins 95 % du temps ;
#     E2 : |ln(G estimee / G)| <= ln 2 (charge a un facteur 2 pres)
#          pendant au moins 90 % du temps ;
#     E3 : prediction de la fenetre suivante (0.5 ms) par le modele physique,
#          a partir de l'etat et des parametres estimes, avec le rapport
#          cyclique applique : erreur efficace mediane <= 20 mV et centile 99
#          <= 100 mV (pour comparaison, la meme prediction depuis l'etat vrai).
#   Decision ecrite avant le calcul : si E2 echoue, la charge n'est pas
#   estimable ; le PINN-PID utilise la charge nominale (5 ohms).
#   Reglage : grille sg (marche aleatoire de ln G par pas) dans {1e-4, 3e-4,
#   1e-3, 3e-3} et sv (marche aleatoire de Vin par pas, en V) dans {0.01,
#   0.03, 0.1, 0.3}. Regle fixee avant le calcul : mediane de |ln(G^/G)| la
#   plus faible parmi les reglages dont la mediane de |Vin^ - Vin| est au
#   plus 2 V. Amendement 1 (declare apres le reglage, avant l'evaluation) :
#   aucun reglage ne passait la condition sur Vin (5.2 V au mieux) ; on
#   retient la plus faible mediane de |ln(G^/G)| sans condition sur Vin.
#
# CE QUE LE SCRIPT AFFICHE ET ECRIT
#   Le tableau du reglage, le diagnostic (filtre avec G et Vin vrais imposes
#   contre filtre libre, sur 0.5 s de ELM_A1), les criteres E1 a E3 essai
#   par essai et la decision. Fichier ecrit : estimation_etat_pinn.json.
#
# RESULTAT OBTENU LE 5 OCTOBRE 2026 (a retrouver a l'identique)
#   Reglage retenu (amendement 1) : sg = 1e-3, sv = 0.03 V. Le filtre ne
#   passe que sur S1, S2 et S6 (charge vraie egale a celle du depart, Vin
#   constante). Decision : charge nominale et Vin nominale pour le PINN-PID ;
#   l'etat initial des predictions vient d'un observateur a charge nominale
#   (banc_pinn_pid.py).
#
# FICHIERS NECESSAIRES (dans le meme dossier que ce script)
#   banc_commun.py (version 2.1), scenarios_communs.json, scenario_S*.mat,
#   donnees_elm_ELM_A1.mat, donnees_elm_ELM_A2.mat, scenario_ELM_A1.mat,
#   scenario_ELM_A2.mat.
#
# BIBLIOTHEQUES NECESSAIRES (pip install numpy scipy)
#
# COMMENT LANCER CE SCRIPT
#   python estimation_etat_pinn.py
#   Duree : une dizaine de minutes (le filtre tourne a chaque pas Tc sur
#   2 s d'enregistrements pour le reglage et 2.42 s d'essais).
#
# ORDRE D'EXECUTION (PINN-PID)
#   1. entrainement_pinn.py ; 2. ce script ; 3. banc_pinn_pid.py ;
#   4. Tester_PINN_PID_Rejeu.m ; 5. Construction_PINN_PID.m ;
#   6. verifier_modele_pinn_pid.py ; 7. Simuler_PINN_PID.m ;
#   8. Construction_PINN_PID_Trois_Modeles.m ;
#   9. verifier_modeles_pinn_pid_trois.py ; 10. Simuler_PINN_PID_Trois_Modeles.m.
# =============================================================================


# %% ETAPE 0 : bibliotheques et definitions du banc commun

import os                                     # chemins de fichiers
import json                                   # fichier de resultats
import time                                   # duree d'execution
import numpy as np                            # calcul numerique
from scipy.io import loadmat                  # lecture des fichiers .mat
from scipy.linalg import expm                 # exponentielle de matrice (integration exacte sur Tc)

try:                                          # dossier du script (ou dossier courant dans une console)
    DOSSIER_PINN = os.path.dirname(os.path.abspath(__file__))
except NameError:
    DOSSIER_PINN = os.getcwd()

# Le banc commun est execute jusqu'a sa marque de fin des definitions :
# constantes du circuit, essais, Circuit, simuler, grandeurs, PIDClassique.
with open(os.path.join(DOSSIER_PINN, "banc_commun.py"), encoding="utf-8") as f:
    SOURCE_BANC = f.read()
MARQUE = "# === FIN DES DEFINITIONS DU BANC COMMUN ==="
if MARQUE not in SOURCE_BANC or "iL_max_dem_A" not in SOURCE_BANC:
    raise RuntimeError("banc_commun.py n'est pas la version 2.1 : prendre la version a jour.")
exec(SOURCE_BANC[:SOURCE_BANC.index(MARQUE)])

T_DEBUT = time.time()                         # pour la duree totale
NF = 110                                      # periodes Tc par fenetre de 0.5 ms
K30 = int(round(0.03 / TC))                   # instant 30 ms (numero de pas Tc)
K10 = int(round(0.010 / TC))                  # instant 10 ms (debut du jugement du reglage)
Q_CAN = 200.0 / 4096.0                        # pas du CAN de S7a (V)
SIG_Y = Q_CAN / np.sqrt(12.0)                 # ecart type de l'erreur de quantification (14.1 mV)
G_MIN, G_MAX = 1.0 / 200.0, 1.0 / 2.0         # bornes de la conductance estimee (S)
VIN_MIN, VIN_MAX = 100.0, 300.0               # bornes de Vin estimee (V)
K_ZN = np.array([PID_P, PID_I * TC, PID_D / TC])   # Ziegler-Nichols, forme incrementale
TCN = TC * PID_N                              # Tc x N du filtre de derivee


def titre(texte):
    """Bandeau de titre dans la console."""
    print("\n" + "=" * 78 + "\n " + texte + "\n" + "=" * 78)


# %% ETAPE 1 : modele physique d'une tranche Tc et filtre de Kalman etendu

def frac_tranche(d, k):
    """Fraction de la tranche [k Tc, (k+1) Tc] pendant laquelle le MOSFET
    conduit, pour le rapport cyclique d : memes conventions que le banc
    commun (porteuse de 1 200 pas, 120 pas par tranche)."""
    n_on = np.ceil(np.asarray(d) * NPER).astype(int)            # pas de phase passants dans la periode
    ph0 = (np.asarray(k) * NREG) % NPER                         # phase de la porteuse au debut de la tranche
    return np.clip(n_on - ph0, 0, NREG) / NREG                  # part passante de la tranche


def pas_modele(v, i, s, G, vin):
    """Un pas Tc du modele moyen par tranche, pour B etats a la fois
    (tableaux de taille B). Integration exacte (exponentielle de matrice) en
    conduction continue ; blocage de la diode approche si le courant passe
    sous zero. Renvoie v, iL a la fin de la tranche et la matrice
    exponentielle (B x 3 x 3)."""
    B = v.shape[0]
    req = s * RON + (1 - s) * RDIODE                            # resistance moyenne vue par la bobine
    M = np.zeros((B, 3, 3))                                     # systeme augmente [v, iL, 1]
    M[:, 0, 0] = -G / C_CONV * TC                               # decharge dans la charge
    M[:, 0, 1] = TC / C_CONV                                    # courant de la bobine vers le condensateur
    M[:, 1, 0] = -TC / L_BOB                                    # tension de sortie vue par la bobine
    M[:, 1, 1] = -req / L_BOB * TC                              # chute resistive
    M[:, 1, 2] = (s * vin - (1 - s) * VF) / L_BOB * TC          # source moyenne vue par la bobine
    E = expm(M)                                                 # integration exacte sur Tc
    vn = E[:, 0, 0] * v + E[:, 0, 1] * i + E[:, 0, 2]
    inn = E[:, 1, 0] * v + E[:, 1, 1] * i + E[:, 1, 2]
    neg = (inn < 0) & (s < 1)                                   # le courant passerait sous zero
    if np.any(neg):
        a = np.where(neg, i / np.maximum(i - inn, 1e-12), 1.0)  # part de la tranche avant le blocage
        a = np.clip(a, 0.0, 1.0)
        vmid = v + (vn - v) * a                                 # tension au blocage (interpolation)
        vn = np.where(neg, vmid * np.exp(-G * (1 - a) * TC / C_CONV), vn)   # puis decharge
        inn = np.where(neg, 0.0, inn)                           # courant nul
    return vn, inn, E


class EKF:
    """Filtre de Kalman etendu sur [v, iL, ln G, Vin], pour B reglages a la
    fois (ligne b du tableau = reglage b). ln G et Vin suivent une marche
    aleatoire d'ecarts types sg et sv par pas."""

    def __init__(self, B, sg, sv, v0, sig_v=1e-3, sig_i=1e-2, sig_y=SIG_Y):
        self.x = np.zeros((B, 4))                               # etat estime
        self.x[:, 0] = v0                                       # premiere mesure
        self.x[:, 1] = 0.0                                      # convertisseur au repos
        self.x[:, 2] = np.log(0.2)                              # charge de depart : 5 ohms
        self.x[:, 3] = 200.0                                    # Vin de depart
        self.P = np.zeros((B, 4, 4))                            # covariance de l'erreur d'estimation
        self.P[:, 0, 0] = sig_y ** 2
        self.P[:, 1, 1] = 1.0                                   # 1 A
        self.P[:, 2, 2] = 1.5 ** 2                              # facteur e^1.5 = 4.5 sur la charge
        self.P[:, 3, 3] = 30.0 ** 2                             # 30 V
        self.Q = np.zeros((B, 4, 4))                            # bruit d'etat par pas
        self.Q[:, 0, 0] = sig_v ** 2                            # 1 mV
        self.Q[:, 1, 1] = sig_i ** 2                            # 10 mA
        self.Q[:, 2, 2] = np.asarray(sg) ** 2
        self.Q[:, 3, 3] = np.asarray(sv) ** 2
        self.R = sig_y ** 2                                     # bruit de mesure

    def bornes(self):
        """Courant positif, charge et Vin dans des bornes physiques."""
        self.x[:, 1] = np.maximum(self.x[:, 1], 0.0)
        self.x[:, 2] = np.clip(self.x[:, 2], np.log(G_MIN), np.log(G_MAX))
        self.x[:, 3] = np.clip(self.x[:, 3], VIN_MIN, VIN_MAX)

    def mise_a_jour(self, y):
        """Correction par la mesure y de Vout (la mesure ne voit que v)."""
        P = self.P
        S = P[:, 0, 0] + self.R                                 # variance de l'innovation
        K = P[:, :, 0] / S[:, None]                             # gain de Kalman
        innov = y - self.x[:, 0]                                # innovation
        self.x = self.x + K * innov[:, None]
        self.P = P - K[:, :, None] * P[:, 0, :][:, None, :]
        self.bornes()

    def prediction(self, s):
        """Prediction d'un pas avec la fraction de conduction s de la tranche.
        Jacobien : exact pour (v, iL), par differences finies pour ln G et Vin."""
        x = self.x
        v, i, gam, vin = x[:, 0], x[:, 1], x[:, 2], x[:, 3]
        G = np.exp(gam)
        sB = np.full(len(v), s) if np.ndim(s) == 0 else s
        vn, inn, E = pas_modele(v, i, sB, G, vin)
        hg, hv = 1e-6, 1e-4                                     # pas des differences finies
        vg, ig, _ = pas_modele(v, i, sB, G * np.exp(hg), vin)
        vv, iv, _ = pas_modele(v, i, sB, G, vin + hv)
        B = len(v)
        F = np.zeros((B, 4, 4))                                 # jacobien de la prediction
        F[:, :2, :2] = E[:, :2, :2]
        F[:, 0, 2] = (vg - vn) / hg; F[:, 1, 2] = (ig - inn) / hg
        F[:, 0, 3] = (vv - vn) / hv; F[:, 1, 3] = (iv - inn) / hv
        F[:, 2, 2] = 1.0; F[:, 3, 3] = 1.0
        self.x = np.stack([vn, inn, gam, vin], 1)
        self.P = F @ self.P @ np.transpose(F, (0, 2, 1)) + self.Q
        self.bornes()


def courir(ekf, y, d):
    """Fait tourner le filtre sur la mesure y et le rapport cyclique d.
    A chaque instant k : correction par y(k), puis prediction de k a k+1
    avec d(k). Renvoie l'estimation corrigee a chaque instant (N x B x 4)."""
    N = len(y)
    hist = np.zeros((N, ekf.x.shape[0], 4))
    s_tout = frac_tranche(d, np.arange(N))
    for k in range(N):
        ekf.mise_a_jour(y[k])
        hist[k] = ekf.x
        if k < N - 1:
            ekf.prediction(s_tout[k])
    return hist


def predire_fenetres(v0, i0, G, vin, d, k0s):
    """Prediction de NF pas par le modele physique a partir des etats donnes
    au debut des fenetres k0s ; G et vin : un nombre par fenetre, ou un par
    fenetre et par pas (valeurs vraies, qui peuvent varier)."""
    nw = len(k0s)
    v, i = v0.copy(), i0.copy()
    sortie = np.zeros((nw, NF))
    for j in range(NF):
        kk = k0s + j
        s = frac_tranche(d[kk], kk)
        Gj = G[:, j] if G.ndim == 2 else G
        vj = vin[:, j] if vin.ndim == 2 else vin
        v, i, _ = pas_modele(v, i, s, Gj, vj)
        sortie[:, j] = v
    return sortie


# %% ETAPE 2 : reglage du filtre sur ELM_A1 et ELM_A2 (mesure quantifiee)

titre("ETAPE 2 : reglage du filtre sur ELM_A1 et ELM_A2 (mesure quantifiee a 48.8 mV)")
SG = [1e-4, 3e-4, 1e-3, 3e-3]                 # marche aleatoire de ln G par pas
SV = [0.01, 0.03, 0.1, 0.3]                   # marche aleatoire de Vin par pas (V)
GRILLE = [(a, b) for a in SG for b in SV]     # 16 reglages, calcules ensemble


def charger_elm(code):
    """Enregistrement Simulink de l'ELM : Vout, iL, d, et profils Vin et G."""
    m = loadmat(os.path.join(DOSSIER_PINN, f"donnees_elm_{code}.mat"))
    sc = loadmat(os.path.join(DOSSIER_PINN, f"scenario_{code}.mat"))
    v = m["vout"].ravel().astype(float)
    il = m["il"].ravel().astype(float)
    d = m["d"].ravel().astype(float)
    vin = sc["vin"].ravel()[:len(v)]
    G = (1.0 / float(sc["R0"].item()) + sc["gx"].ravel())[:len(v)]
    return v, il, d, vin, G


ERR = {}
for code in ("ELM_A1", "ELM_A2"):
    v, il, d, vin, G = charger_elm(code)
    y = Q_CAN * np.round(v / Q_CAN)                             # mesure quantifiee (boucle ouverte : le circuit n'en depend pas)
    ekf = EKF(len(GRILLE), [g[0] for g in GRILLE], [g[1] for g in GRILLE], y[0])
    t0 = time.time()
    h = courir(ekf, y, d)
    print(f"  {code} : {len(y)} pas en {time.time() - t0:.0f} s")
    ERR[code] = (np.abs(h[K10:, :, 2] - np.log(G[K10:, None])),  # erreur sur ln G
                 np.abs(h[K10:, :, 3] - vin[K10:, None]))        # erreur sur Vin

print("\n  sg      sv (V)   mediane |ln G^/G|   mediane |Vin^ - Vin| (V)   part |ln G^/G| <= ln 2")
TABLE_REGLAGE = []
for j, (a, b) in enumerate(GRILLE):
    eg = np.concatenate([ERR[c][0][:, j] for c in ERR])
    ev = np.concatenate([ERR[c][1][:, j] for c in ERR])
    TABLE_REGLAGE.append({"sg": a, "sv": b, "med_lnG": float(np.median(eg)), "med_Vin": float(np.median(ev)),
                          "part_facteur2": float(np.mean(eg <= np.log(2)))})
    print(f"  {a:.0e}  {b:5.2f}    {np.median(eg):6.3f}              {np.median(ev):6.2f}                     "
          f"{np.mean(eg <= np.log(2)) * 100:5.1f} %")
admis = [t for t in TABLE_REGLAGE if t["med_Vin"] <= 2.0]
if admis:
    RETENU = min(admis, key=lambda t: t["med_lnG"])
    print(f"\n  Regle d'origine : sg = {RETENU['sg']:.0e}, sv = {RETENU['sv']} V.")
    AMENDEMENT = False
else:
    RETENU = min(TABLE_REGLAGE, key=lambda t: t["med_lnG"])    # amendement 1
    AMENDEMENT = True
    print("\n  Aucun reglage n'a une mediane de |Vin^ - Vin| d'au plus 2 V : la regle d'origine ne designe rien.")
    print(f"  Amendement 1 : plus faible mediane de |ln G^/G| sans condition sur Vin : sg = {RETENU['sg']:.0e}, "
          f"sv = {RETENU['sv']} V.")
SG_R, SV_R = RETENU["sg"], RETENU["sv"]


# %% ETAPE 3 : diagnostic, G et Vin vrais imposes contre G et Vin libres

titre("ETAPE 3 : diagnostic sur 0.5 s de ELM_A1 (G et Vin vrais imposes, ou libres)")
v, il, d, vin, G = charger_elm("ELM_A1")
N_DIAG = 110000                               # 0.5 s
y = Q_CAN * np.round(v / Q_CAN)
ekf = EKF(2, [SG_R, SG_R], [SV_R, SV_R], y[0])
ekf.Q[1, 2, 2] = 0.0; ekf.Q[1, 3, 3] = 0.0    # ligne 1 : G et Vin connus (pas de marche aleatoire)
ekf.P[1, 2, 2] = 0.0; ekf.P[1, 3, 3] = 0.0
hist = np.zeros((N_DIAG, 2, 4)); innov = np.zeros((N_DIAG, 2))
s_tout = frac_tranche(d[:N_DIAG], np.arange(N_DIAG))
for k in range(N_DIAG):
    ekf.x[1, 2] = np.log(G[k]); ekf.x[1, 3] = vin[k]           # valeurs vraies imposees a chaque pas
    innov[k] = y[k] - ekf.x[:, 0]
    ekf.mise_a_jour(y[k]); hist[k] = ekf.x
    if k < N_DIAG - 1:
        ekf.prediction(s_tout[k])
DIAG = {"innov_libre_mV": float(np.sqrt(np.mean(innov[K10:, 0] ** 2)) * 1e3),
        "innov_vrais_mV": float(np.sqrt(np.mean(innov[K10:, 1] ** 2)) * 1e3),
        "iL_libre_A": float(np.sqrt(np.mean((hist[K10:, 0, 1] - il[K10:N_DIAG]) ** 2))),
        "iL_vrais_A": float(np.sqrt(np.mean((hist[K10:, 1, 1] - il[K10:N_DIAG]) ** 2)))}
print(f"  Erreur efficace sur iL : {DIAG['iL_vrais_A'] * 1e3:.0f} mA avec G et Vin vrais, "
      f"{DIAG['iL_libre_A']:.2f} A avec G et Vin libres.")
print(f"  Innovations efficaces : {DIAG['innov_vrais_mV']:.1f} mV contre {DIAG['innov_libre_mV']:.1f} mV : "
      "plusieurs combinaisons (iL, G, Vin) expliquent presque aussi bien la mesure.")


# %% ETAPE 4 : evaluation sur les onze essais en boucle fermee avec R0

titre("ETAPE 4 : criteres E1 a E3 sur les onze essais (boucle fermee avec R0)")


class LoiLu:
    """Loi incrementale de Lu a derivee filtree, gains figes (version R0 de
    banc_elm_pid.py, memes operations dans le meme ordre)."""

    def __init__(self, K):
        self.Kp, self.Ki, self.Kd = (float(x) for x in K)
        self.u = 0.5                          # commande de depart
        self.premier = True                   # premier pas sans a-coup

    def pas(self, e):
        if self.premier:
            self.e1, self.ef, self.g1, self.premier = e, e, 0.0, False
        g = TCN * (e - self.ef)                                 # derivee filtree (x Tc)
        brut = self.u + self.Kp * (e - self.e1) + self.Ki * e + self.Kd * (g - self.g1)
        u = min(max(brut, D_MIN), D_MAX)                        # seule saturation
        self.ef = self.ef + TCN * (e - self.ef)
        self.e1, self.g1, self.u = e, g, u
        return u


RESULTATS = {}
for sc in SCENARIOS:
    c = sc["code"]
    sim = simuler(LoiLu(K_ZN), sc)                              # trajectoire de R0 sur le banc
    yv, dv, vv, iv = sim["mesure"], sim["d"], sim["v"], sim["iL"]
    Gv = 1.0 / sc["R0"] + sc["gx"]                              # conductance vraie
    vinv = sc["vin"]                                            # Vin vraie
    N = len(yv)
    ekf = EKF(1, [SG_R], [SV_R], yv[0])
    t0 = time.time()
    h = courir(ekf, yv, dv)[:, 0, :]
    eV = np.abs(h[K30:, 3] - vinv[K30:])                        # erreur sur Vin
    eG = np.abs(h[K30:, 2] - np.log(Gv[K30:]))                  # erreur sur ln G
    E1 = float(np.mean(eV <= 5.0) * 100.0)
    E2 = float(np.mean(eG <= np.log(2.0)) * 100.0)
    eI = float(np.sqrt(np.mean((h[K30:, 1] - iv[K30:]) ** 2)))
    nw = (N - 1) // NF                                          # fenetres de prediction (de 30 ms a la fin)
    w = np.arange(K30 // NF, nw - 1)
    k0s = w * NF
    idx = k0s[:, None] + np.arange(NF)[None, :]
    pe = predire_fenetres(h[k0s, 0], h[k0s, 1], np.exp(h[k0s, 2]), h[k0s, 3], dv, k0s)   # depuis l'estimation
    pv = predire_fenetres(vv[k0s], iv[k0s], Gv[idx], vinv[idx], dv, k0s)                 # depuis l'etat vrai
    vrai = vv[idx + 1]
    rmse = np.sqrt(np.mean((pe - vrai) ** 2, 1))
    rmsv = np.sqrt(np.mean((pv - vrai) ** 2, 1))
    E3_med, E3_p99 = float(np.median(rmse) * 1e3), float(np.percentile(rmse, 99) * 1e3)
    ok = {"E1": E1 >= 95.0, "E2": E2 >= 90.0, "E3": E3_med <= 20.0 and E3_p99 <= 100.0}
    R_dem = [float(1.0 / np.exp(h[int(round(t / TC)), 2])) for t in (0.005, 0.010, 0.020, 0.029)]
    RESULTATS[c] = {"E1_pct": E1, "E2_pct": E2, "E3_med_mV": E3_med, "E3_p99_mV": E3_p99,
                    "vrai_med_mV": float(np.median(rmsv) * 1e3), "vrai_p99_mV": float(np.percentile(rmsv, 99) * 1e3),
                    "iL_eff_A": eI, "R_estimee_demarrage": R_dem, "R_estimee_fin": float(1.0 / np.exp(h[-1, 2])),
                    "R_vraie_fin": float(1.0 / Gv[-1]), "Vin_estimee_fin": float(h[-1, 3]), "criteres": ok}
    print(f"  {c:4s} E1 {E1:5.1f} %  E2 {E2:5.1f} %  E3 {E3_med:6.1f} / {E3_p99:7.1f} mV "
          f"(etat vrai {np.median(rmsv) * 1e3:.1f} / {np.percentile(rmsv, 99) * 1e3:.1f})  iL {eI:6.2f} A  "
          f"R fin {RESULTATS[c]['R_estimee_fin']:6.1f} (vraie {RESULTATS[c]['R_vraie_fin']:.1f})  "
          f"{'tout passe' if all(ok.values()) else 'echec ' + ' '.join(k for k, o in ok.items() if not o)}"
          f"  ({time.time() - t0:.0f} s)")


# %% ETAPE 5 : decision et ecriture du fichier

titre("ETAPE 5 : decision")
passe = [c for c, r in RESULTATS.items() if all(r["criteres"].values())]
E2_echoue = [c for c, r in RESULTATS.items() if not r["criteres"]["E2"]]
print(f"  Essais ou tout passe : {', '.join(passe) if passe else 'aucun'}.")
if E2_echoue:
    DECISION = ("E2 echoue (" + ", ".join(E2_echoue) + ") : la charge n'est pas estimable a partir de Vout avec "
                "les excitations de ces essais. Le PINN-PID utilise la charge nominale (5 ohms) et Vin nominale ; "
                "l'etat initial des predictions vient d'un observateur a charge nominale.")
else:
    DECISION = "E2 passe partout : le PINN-PID peut utiliser cet estimateur (voir E1 et E3)."
print("  " + DECISION)

with open(os.path.join(DOSSIER_PINN, "estimation_etat_pinn.json"), "w", encoding="utf-8") as f:
    json.dump({"version": 1, "date": "2026-10-05", "reglage_grille": TABLE_REGLAGE,
               "reglage_retenu": {"sg": SG_R, "sv": SV_R, "amendement_1": AMENDEMENT},
               "diagnostic_ELM_A1": DIAG, "essais": RESULTATS, "decision": DECISION}, f, indent=1)
print(f"\n  estimation_etat_pinn.json ecrit. Duree totale : {time.time() - T_DEBUT:.0f} s.")
