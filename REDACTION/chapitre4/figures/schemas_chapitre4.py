# =============================================================================
# schemas_chapitre4.py
#
# OBJET
#   Dessiner les trois schemas du chapitre 4 (conception de l'ELM-PID) :
#     Fig4_1_boucle_ELM_PID        boucle fermee et boucle d'adaptation ;
#     Fig4_2_reseau_ELM            structure du reseau ELM et de son jacobien ;
#     Fig4_3_chronogramme_fenetres pas Tc, fenetres de 0,5 ms, porte, zone morte.
#   Ce sont des schemas : aucune donnee simulee n'y figure. Chaque element
#   dessine correspond a une operation de ELM_PID/banc_elm_pid.py (classes
#   BlocPID, AdaptateurELM, ELMPID), de ELM_PID/elm_pid_adaptatif.m et de
#   ELM_PID/banc_commun.py (fonction simuler) ; les reglages sont ceux de
#   ELM_PID/criteres_elm_pid.txt (sections 2 et 4).
#
# COMMENT LANCER
#   python schemas_chapitre4.py
#   Sorties dans le dossier du script : PNG 300 dpi et PDF vectoriel.
# =============================================================================

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, Arc

DOSSIER = os.path.dirname(os.path.abspath(__file__))
CM = 1 / 2.54
LARGEUR = 15.0                      # cm, bloc de texte de 15,5 cm
ROUGE = (0.80, 0.10, 0.10)          # couleur de l'ELM-PID au chapitre 5
GRIS = (0.45, 0.45, 0.45)
GRIS_CLAIR = (0.93, 0.93, 0.93)
TAILLE = 10

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": TAILLE,
    "axes.linewidth": 0.6,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
})


def nouvelle_figure(hauteur):
    fig = plt.figure(figsize=(LARGEUR * CM, hauteur * CM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, LARGEUR)
    ax.set_ylim(0, hauteur)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def boite(ax, x0, y0, x1, y1, texte="", couleur="black", lw=0.9, taille=TAILLE, fond="white", z=3):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="square,pad=0",
                                fc=fond, ec=couleur, lw=lw, zorder=z))
    if texte:
        ax.text((x0 + x1) / 2, (y0 + y1) / 2, texte, ha="center", va="center",
                fontsize=taille, zorder=z + 1, linespacing=1.25)


def fleche(ax, pts, couleur="black", lw=0.9, tete=True):
    """Polyligne terminee par une tete de fleche."""
    pts = np.asarray(pts, float)
    if len(pts) > 2:
        ax.plot(pts[:-1, 0], pts[:-1, 1], color=couleur, lw=lw, zorder=2, solid_capstyle="butt")
    if tete:
        ax.annotate("", xy=pts[-1], xytext=pts[-2],
                    arrowprops=dict(arrowstyle="-|>,head_length=0.45,head_width=0.18",
                                    color=couleur, lw=lw, shrinkA=0, shrinkB=0), zorder=2)
    else:
        ax.plot(pts[-2:, 0], pts[-2:, 1], color=couleur, lw=lw, zorder=2)


def point(ax, x, y, couleur="black"):
    ax.add_patch(Circle((x, y), 0.055, fc=couleur, ec=couleur, zorder=5))


def sauver(fig, nom):
    for ext, opts in (("png", {"dpi": 300}), ("pdf", {})):
        fig.savefig(os.path.join(DOSSIER, f"{nom}.{ext}"), facecolor="white",
                    metadata={"Creator": None, "Producer": None} if ext == "pdf" else None, **opts)
    plt.close(fig)
    print(f"{nom} : png et pdf ecrits")


# -----------------------------------------------------------------------------
# Figure 4.1 : boucle fermee et boucle d'adaptation
# -----------------------------------------------------------------------------
def figure_4_1():
    H = 10.6
    fig, ax = nouvelle_figure(H)
    ym = 2.2                               # ligne principale

    # deux echelles de temps (fonds)
    ax.add_patch(Rectangle((0.05, 0.05), LARGEUR - 0.1, 5.15, fc=(0.975, 0.975, 0.975),
                           ec=GRIS, lw=0.6, ls=(0, (4, 3)), zorder=0))
    ax.text(0.2, 4.95, "À chaque pas $T_c$ = 1/220 000 s", ha="left", va="top", color="black")
    ax.add_patch(Rectangle((0.05, 5.45), LARGEUR - 0.1, H - 5.5, fc="white",
                           ec=GRIS, lw=0.6, ls=(0, (4, 3)), zorder=0))
    ax.text(0.2, H - 0.2, "En fin de chaque fenêtre $n$ de 0,5 ms (110 $T_c$)",
            ha="left", va="top", color="black")

    # consigne et sommateur
    ax.text(0.2, ym + 0.15, r"$v_\mathrm{ref}$", ha="left", va="bottom")
    fleche(ax, [(0.2, ym), (0.98, ym)])
    ax.add_patch(Circle((1.2, ym), 0.22, fc="white", ec="black", lw=0.9, zorder=3))
    ax.text(0.83, ym - 0.42, "+", ha="center", va="center", fontsize=9)
    ax.text(1.42, ym - 0.42, "−", ha="center", va="center", fontsize=9)

    # e -> PID
    fleche(ax, [(1.42, ym), (2.1, ym)])
    ax.text(1.62, ym + 0.08, "$e$", ha="left", va="bottom")
    point(ax, 1.62, ym)
    boite(ax, 2.1, ym - 0.65, 4.3, ym + 0.65, "Bloc PID\nparallèle commun\n($P$, $I$, $D$)")

    # saturation
    fleche(ax, [(4.3, ym), (4.75, ym)])
    boite(ax, 4.75, ym - 0.55, 5.85, ym + 0.55)
    xs = np.array([4.9, 5.12, 5.48, 5.7])
    ax.plot(xs, [ym - 0.33, ym - 0.33, ym + 0.33, ym + 0.33], color="black", lw=0.9, zorder=4)
    ax.text(5.3, ym - 0.62, "[0,01 ; 0,99]", ha="center", va="top")

    # d -> MLI -> Buck
    fleche(ax, [(5.85, ym), (6.65, ym)])
    point(ax, 6.2, ym)
    ax.text(6.3, ym + 0.08, "$d$", ha="left", va="bottom")
    boite(ax, 6.65, ym - 0.5, 7.85, ym + 0.5, "MLI\n22 kHz")
    fleche(ax, [(7.85, ym), (8.3, ym)])
    boite(ax, 8.3, ym - 0.65, 10.3, ym + 0.65, "Convertisseur\nBuck")
    fleche(ax, [(9.3, ym + 1.3), (9.3, ym + 0.65)], couleur=GRIS)
    ax.text(9.42, ym + 0.95, r"$V_\mathrm{in}$, charge", ha="left", va="center", color="black")

    # v_o -> mesure -> y
    fleche(ax, [(10.3, ym), (10.95, ym)])
    ax.text(10.62, ym + 0.08, "$v_o$", ha="center", va="bottom")
    boite(ax, 10.95, ym - 0.55, 12.75, ym + 0.55, "Mesure\n(bruit, CAN)")
    fleche(ax, [(12.75, ym), (14.6, ym)])
    point(ax, 13.45, ym)
    ax.text(14.2, ym + 0.08, "$y$", ha="center", va="bottom")
    # retour
    fleche(ax, [(13.45, ym), (13.45, 0.55), (1.2, 0.55), (1.2, ym - 0.22)])

    # boite des moyennes (cadence Tc, sortie en fin de fenetre)
    ya0, ya1 = 3.55, 4.75
    boite(ax, 5.0, ya0, 12.9, ya1,
          "Moyennes sur la fenêtre $n$ : $\\bar{e}(n)$, $\\bar{y}(n)$, $\\bar{d}(n)$, sensibilité $s(n)$\n"
          "fenêtre suspecte si $d$ en butée à un pas de la fenêtre", couleur=ROUGE)
    # entrees : e (avec saut au-dessus de la fleche des gains), d, y
    xg = 3.2                                 # verticale des gains
    ye = 4.15
    ax.plot([1.62, 1.62, xg - 0.15], [ym, ye, ye], color=ROUGE, lw=0.9, zorder=2)
    ax.add_patch(Arc((xg, ye), 0.3, 0.3, theta1=0, theta2=180, color=ROUGE, lw=0.9, zorder=2))
    fleche(ax, [(xg + 0.15, ye), (5.0, ye)], couleur=ROUGE)
    fleche(ax, [(6.2, ym), (6.2, ya0)], couleur=ROUGE)
    fleche(ax, [(13.45, ym), (13.45, ye), (12.9, ye)], couleur=ROUGE)

    # chaine de fin de fenetre (de droite a gauche)
    yb0, yb1 = 6.1, 7.6
    boite(ax, 10.6, yb0, 14.0, yb1, "Réseau ELM\nprédiction $\\hat{y}(n)$\njacobien $J(n)$", couleur=ROUGE)
    boite(ax, 7.2, yb0, 10.0, yb1, "Porte\net zone morte", couleur=ROUGE)
    boite(ax, 4.1, yb0, 6.6, yb1, "Gradient\nnormalisé\n$\\Delta x(n)$", couleur=ROUGE)
    boite(ax, 0.5, yb0, 3.5 + 0.4, yb1, "Projection sur\nl'ensemble\nadmissible", couleur=ROUGE)
    ym2 = (yb0 + yb1) / 2
    fleche(ax, [(10.6, ym2), (10.0, ym2)], couleur=ROUGE)
    fleche(ax, [(7.2, ym2), (6.6, ym2)], couleur=ROUGE)
    fleche(ax, [(4.1, ym2), (3.9, ym2)], couleur=ROUGE)
    # entrees venant des moyennes
    fleche(ax, [(12.3, ya1), (12.3, yb0)], couleur=ROUGE)
    ax.text(12.4, (ya1 + yb0) / 2, "$\\bar{y}$, $\\bar{d}$", ha="left", va="center")
    fleche(ax, [(8.6, ya1), (8.6, yb0)], couleur=ROUGE)
    ax.text(8.7, (ya1 + yb0) / 2, "$\\bar{e}$, butée", ha="left", va="center")
    fleche(ax, [(5.35, ya1), (5.35, yb0)], couleur=ROUGE)
    ax.text(5.45, (ya1 + yb0) / 2, "$\\bar{e}$, $s$", ha="left", va="center")
    # gains vers le PID
    fleche(ax, [(xg, yb0), (xg, ym + 0.65)], couleur=ROUGE)
    ax.text(xg - 0.12, 5.2, "$K = K_\\mathrm{ZN} \\odot x$", ha="right", va="center")

    # details au-dessus des boites
    yd = yb1 + 0.12
    ax.text(12.3, yd, "OS-ELM si\n$|\\bar{y}-\\hat{y}|$ > 0,1 V", ha="center", va="bottom")
    ax.text(8.6, yd, "butée en $n$, $n-1$, $n-2$ : fermée\n$|\\bar{e}|$ > 0,1 V et $J$ > 0", ha="center", va="bottom")
    ax.text(5.35, yd, "$\\varphi = J\\,(s \\odot K_\\mathrm{ZN})$\n"
            "$\\eta\\,\\bar{e}\\,\\varphi/(\\varepsilon+\\varphi\\cdot\\varphi)$ + inertie",
            ha="center", va="bottom")
    ax.text(2.2, yd, "Rosen : glissement\net restauration", ha="center", va="bottom")
    sauver(fig, "Fig4_1_boucle_ELM_PID")


# -----------------------------------------------------------------------------
# Figure 4.2 : reseau ELM (RVFL : liaisons directes)
# -----------------------------------------------------------------------------
def figure_4_2():
    H = 10.0
    fig, ax = nouvelle_figure(H)
    xe, xc, xs = 2.6, 7.0, 11.3
    noms = ["$\\bar{y}(n-1)$", "$\\bar{y}(n-2)$", "$\\bar{d}(n)$", "$\\bar{d}(n-1)$", "$\\bar{d}(n-2)$"]
    ye = np.linspace(7.6, 2.6, 5)
    yc = np.linspace(8.9, 1.3, 12)
    ys = 5.1
    r_e, r_c = 0.22, 0.2

    # poids d'entree fixes (gris fin)
    for a in ye:
        for b in yc:
            ax.plot([xe + r_e, xc - r_c], [a, b], color=(0.72, 0.72, 0.72), lw=0.35, zorder=1)
    # poids de sortie appris (accent)
    for b in yc:
        ax.plot([xc + r_c, xs - 0.3], [b, ys], color=ROUGE, lw=0.6, zorder=1)
    # liaisons directes entree -> sortie (tirets, sous les neurones caches)
    for a in ye:
        xx = np.linspace(xe + r_e, xs - 0.3, 60)
        t = (xx - xx[0]) / (xx[-1] - xx[0])
        yy = a + (ys - a) * t - 0.0
        bosse = -4.9 * np.sin(np.pi * t) ** 1.0
        ax.plot(xx, np.minimum(yy + bosse, 99), color=ROUGE, lw=0.6, ls=(0, (3, 2)), zorder=1)

    for a, nom in zip(ye, noms):
        ax.add_patch(Circle((xe, a), r_e, fc="white", ec="black", lw=0.9, zorder=3))
        ax.text(xe - 0.35, a, nom, ha="right", va="center")
    for b in yc:
        ax.add_patch(Circle((xc, b), r_c, fc="white", ec="black", lw=0.9, zorder=3))
        sx = np.linspace(-0.12, 0.12, 30)
        ax.plot(xc + sx, b + 0.22 * (1 / (1 + np.exp(-sx * 40)) - 0.5), color="black", lw=0.6, zorder=4)
    ax.add_patch(Circle((xs, ys), 0.3, fc="white", ec="black", lw=0.9, zorder=3))
    ax.text(xs, ys, "$\\Sigma$", ha="center", va="center", zorder=4)
    fleche(ax, [(xs + 0.3, ys), (12.4, ys)])
    ax.text(12.5, ys, "$\\hat{y}(n)$", ha="left", va="center")
    ax.text(12.5, ys - 0.45, "(prédiction\nde $\\bar{y}(n)$)", ha="left", va="top")

    # biais de sortie
    ax.add_patch(Circle((xs, 8.2), 0.2, fc="white", ec="black", lw=0.9, zorder=3))
    ax.text(xs, 8.2, "1", ha="center", va="center", zorder=4)
    fleche(ax, [(xs, 8.0), (xs, ys + 0.3)], couleur=ROUGE, lw=0.6)
    ax.text(xs + 0.12, 7.0, "$\\beta_0$", ha="left", va="center")

    # titres de colonnes
    ax.text(xe, 9.65, "5 entrées\n(moyennes par fenêtre,\ncentrées réduites)", ha="center", va="top")
    ax.text(xc, 9.65, "12 neurones logistiques", ha="center", va="top")
    ax.text(xs, 9.65, "sortie linéaire", ha="center", va="top")

    # annotations des poids
    ax.text(4.6, 0.75, "$w_j$, $b_j$ : tirés au hasard\ndans [−1 ; 1], fixés", ha="center", va="top")
    ax.text(9.15, 9.2, "$\\beta_j$", ha="center", va="center", color="black")
    ax.text(7.6, 0.2, "liaisons directes $\\beta_{L,i}$", ha="center", va="bottom")
    ax.text(xc + 0.35, yc[0], "$g_j$", ha="left", va="center")

    # encadre : apprentissage et jacobien
    ax.text(12.5, 3.2,
            "$\\beta$ = ($\\beta_j$, $\\beta_{L,i}$, $\\beta_0$) :\n"
            "moindres carrés\nrégularisés hors ligne\n($C$ = 0,1), puis\nOS-ELM en ligne",
            ha="left", va="top")
    ax.text(12.5, 8.6, "$J(n) = \\partial\\hat{y}(n)/\\partial\\bar{d}(n)$\n"
            "dérivée à travers\n$g_j(1-g_j)$ et la\nliaison directe",
            ha="left", va="top")
    sauver(fig, "Fig4_2_reseau_ELM")


# -----------------------------------------------------------------------------
# Figure 4.3 : chronogramme des fenetres
# -----------------------------------------------------------------------------
def figure_4_3():
    H = 11.0
    fig = plt.figure(figsize=(LARGEUR * CM, H * CM))
    gauche, droite = 0.19, 0.985
    nf = 6                                     # fenetres m-1 ... m+4
    noms = ["$m-1$", "$m$", "$m+1$", "$m+2$", "$m+3$", "$m+4$"]
    pas = 11                                   # un trait pour 10 Tc : 11 par fenetre
    t = np.arange(nf * pas) / pas * 0.5 + 0.5 / pas / 2   # ms
    lignes = [("Pas du PID", 0.6), ("Erreur", 1.6), ("Rapport\ncyclique", 1.4),
              ("Fenêtre\nsuspecte", 0.55), ("Porte", 0.55), ("Gains\nmodifiés", 0.7)]
    tot = sum(h for _, h in lignes)
    bas, haut = 0.13, 0.97
    axes = []
    y = haut
    for nom, h in lignes:
        hh = (haut - bas) * h / tot
        y -= hh
        a = fig.add_axes([gauche, y + 0.012, droite - gauche, hh - 0.024])
        a.set_xlim(0, nf * 0.5)
        for s in ("top", "right", "left"):
            a.spines[s].set_visible(False)
        a.spines["bottom"].set_color(GRIS)
        a.set_yticks([])
        a.set_xticks([])
        for k in range(nf + 1):
            a.axvline(0.5 * k, color=GRIS, lw=0.5, ls=(0, (3, 3)), zorder=0)
        fig.text(gauche - 0.015, y + hh / 2, nom, ha="right", va="center", linespacing=1.15)
        axes.append(a)
    a_tc, a_e, a_d, a_s, a_p, a_g = axes

    # 1. pas du PID
    a_tc.set_ylim(0, 1)
    a_tc.vlines(t, 0, 0.55, color="black", lw=0.6)
    a_tc.text(0.03, 0.95, "un trait pour 10 pas de $T_c$ ; 110 pas par fenêtre", va="top", ha="left",
              fontsize=9)

    # 2. erreur e(k) et moyenne ebar(n)
    ebar = [0.05, 1.20, 0.45, 0.28, 0.18, 0.06]
    forme = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    e = []
    for i in range(nf):
        tt = np.linspace(0, 1, pas)
        if i == 1:
            v = 2.2 * np.sin(np.pi * np.clip(tt * 1.15, 0, 1)) + 0.0
            v = v - v.mean() + ebar[i]
        else:
            v = ebar[i] + 0.08 * np.sin(2 * np.pi * tt * 1.5 + i)
        e.extend(v)
    e = np.array(e)
    a_e.set_ylim(-0.5, 2.6)
    a_e.axhspan(-0.1, 0.1, color=GRIS_CLAIR, zorder=0)
    a_e.axhline(0, color=GRIS, lw=0.5)
    a_e.plot(t, e, "o", ms=2.2, color="black", zorder=3)
    for i in range(nf):
        a_e.plot([0.5 * i + 0.02, 0.5 * (i + 1) - 0.02], [ebar[i]] * 2, color="black", lw=1.6, zorder=4)
    a_e.text(0.5 * nf - 0.03, 2.5, "points : $e(k)$ ; traits : $\\bar{e}(n)$", ha="right", va="top", fontsize=9)
    a_e.annotate("$|\\bar{e}|$ < 0,1 V\n(zone morte)", xy=(2.75, 0.06), xytext=(2.75, 1.05),
                 ha="center", va="bottom", fontsize=9,
                 arrowprops=dict(arrowstyle="-", color=GRIS, lw=0.6))
    a_e.text(0.25, 0.85, "zone morte", ha="center", va="bottom", fontsize=9)
    a_e.plot([0.25, 0.25], [0.12, 0.8], color=GRIS, lw=0.6)

    # 3. rapport cyclique, butee dans la fenetre m
    d = np.full(nf * pas, 0.5)
    i0, i1 = pas + 1, pas + 6
    d[i0:i1] = 0.99
    d[i1:i1 + 3] = [0.8, 0.65, 0.56]
    d = d + 0.015 * np.sin(np.arange(len(d)) * 1.3)
    d[i0:i1] = 0.99
    a_d.set_ylim(0.3, 1.12)
    a_d.axhline(0.99, color=GRIS, lw=0.6, ls=(0, (4, 2)))
    a_d.text(0.03, 1.0, "0,99", ha="left", va="bottom", fontsize=9)
    a_d.step(t, d, where="mid", color="black", lw=0.9)
    a_d.annotate("$d$ en butée", xy=(t[i0 + 2], 0.99), xytext=(1.25, 1.07), ha="left", va="center",
                 fontsize=9, arrowprops=dict(arrowstyle="-", color=GRIS, lw=0.6))

    # 4. fenetre suspecte
    a_s.set_ylim(0, 1)
    a_s.add_patch(Rectangle((0.5, 0.15), 0.5, 0.6, fc=GRIS, ec="black", lw=0.6))
    a_s.text(1.03, 0.45, "fenêtre $m$ suspecte", ha="left", va="center", fontsize=9)

    # 5. porte : etat lu en fin de fenetre
    a_p.set_ylim(0, 1)
    ouverte = [True, False, False, False, True, True]
    for i in range(nf):
        x0 = 0.5 * i
        if not ouverte[i]:
            a_p.add_patch(Rectangle((x0 + 0.02, 0.2), 0.46, 0.5, fc="white", ec="black", lw=0.6, hatch="////"))
    a_p.text(0.25, 0.45, "ouverte", ha="center", va="center", fontsize=9)
    a_p.text(2.25, 0.45, "ouverte", ha="center", va="center", fontsize=9)
    a_p.text(2.75, 0.45, "ouverte", ha="center", va="center", fontsize=9)
    # 6. decisions en fin de fenetre
    a_g.set_ylim(0, 1)
    raisons = ["zone\nmorte", "porte\nfermée", "porte\nfermée", "porte\nfermée", None, "zone\nmorte"]
    for i in range(nf):
        xf = 0.5 * (i + 1)
        if raisons[i] is None:
            a_g.plot(xf, 0.75, "o", ms=6, color=ROUGE, zorder=5)
            a_g.text(xf - 0.05, 0.75, "oui", ha="right", va="center", fontsize=9)
        else:
            a_g.plot(xf, 0.75, "o", ms=6, mfc="white", mec="black", mew=0.8, zorder=5)
            a_g.text(xf - 0.05, 0.75, "non", ha="right", va="center", fontsize=9)
            a_g.text(xf - 0.25, 0.05, raisons[i], ha="center", va="bottom", fontsize=9, linespacing=1.0)
    a_g.set_ylim(-0.25, 1.05)
    a_g.text(0.5 * 5 + 0.03, 0.75, "", fontsize=9)

    # fleche de 1,5 ms : de la fin de m a la premiere decision ouverte (fin de m+3)
    a_p.annotate("", xy=(2.5, 0.95), xytext=(1.0, 0.95),
                 arrowprops=dict(arrowstyle="<->,head_length=0.35,head_width=0.15", color="black", lw=0.7),
                 annotation_clip=False)
    a_p.text(1.75, 1.0, "1,5 ms : décisions de $m$, $m+1$, $m+2$ bloquées", ha="center", va="bottom",
             fontsize=9)

    # axe des fenetres
    a_g.spines["bottom"].set_color("black")
    a_g.set_xticks(0.5 * np.arange(nf + 1))
    a_g.set_xticklabels([f"{0.5 * k:.1f}".replace(".", ",") for k in range(nf + 1)])
    a_g.tick_params(axis="x", length=3, width=0.6)
    a_g.set_xlabel("Temps (ms)", labelpad=2)
    for i in range(nf):
        a_tc.text(0.5 * i + 0.25, 1.02, "fenêtre " + noms[i], ha="center", va="bottom", fontsize=9,
                  transform=a_tc.transData)
    a_tc.set_ylim(0, 1.0)
    sauver(fig, "Fig4_3_chronogramme_fenetres")


if __name__ == "__main__":
    figure_4_1()
    figure_4_2()
    figure_4_3()
