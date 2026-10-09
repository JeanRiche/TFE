# =============================================================================
# tester_figures_et_controle_version.py
#
# VERSION
#   1 (9 octobre 2026).
#
# OBJECTIF
#   Tester sous GNU Octave (pas de MATLAB sur la machine de calcul), avec des
#   fonctions Simulink factices, deux ajouts du 9 octobre 2026 :
#     A. Simuler_Modeles_Comparaison.m (dossier ELM_PID ; meme fichier dans
#        les quatre dossiers) : une figure par modele simule.
#        Modeles factices ELM_PID_S1, ELM_PID_S2, ELM_PID_S10 (gains
#        variables), PSO_PID_S3 et ZN_S8a (gains constants). Controles :
#          - la figure se construit pour chaque modele ;
#          - ordonnees : pour chaque tuile, ylim laisse au moins 5 % de
#            l'etendue des donnees tracees de chaque cote (calcul
#            independant, sur les YData des courbes de la figure) ;
#          - abscisses : de 0 a la duree de l'essai, en ms ;
#          - tuile 4 : trois courbes (P, I, D) si gains variables, sinon un
#            texte "Gains constants" et aucune courbe ;
#          - <modele>.png et <modele>.fig ecrits dans figures_comparaison/ ;
#          - FERMER_FIGURES = true : aucune figure ne reste ouverte, les
#            fichiers sont ecrits ;
#          - resultats_*_comparaison.mat identiques avec et sans figures
#            (hors temps de calcul) : la figure ne touche aucune grandeur ;
#          - courbe plate : marge non nulle (fixer_ordonnees).
#     B. COMPARAISON/metriques/Metriques_Simulink.m : controle de version.
#        Arborescence factice : ELM_PID_B/ (fichier dont les IAE de
#        classement egalent celles du banc a 0.1 % pres) et ELM_PID/
#        (faux fichier "version incrementale" : IAE S1 81.12, S2 5.62 mV.s).
#          - DOSSIER_ELM = 'ELM_PID_B' (defaut) : fichier accepte, valeurs
#            lues ;
#          - DOSSIER_ELM = 'ELM_PID' : fichier REFUSE ("ce fichier ne
#            correspond pas a la version retenue"), ELM-PID absent des
#            tableaux ;
#          - S10 : IAE a +2 % pour l'ELM-PID, accepte (tolerance S10 de 3 %
#            ecrite avant), refuse a +4 %.
#   Ce que ce test ne controle pas : le rendu MATLAB R2024a (tiledlayout,
#   xline, exportgraphics et legendes "northoutside" sont remplaces ici par
#   des equivalents Octave), la lecture des vrais fichiers -v7.3, les vrais
#   modeles Simulink.
#
# COMMENT LANCER CE SCRIPT
#   python tester_figures_et_controle_version.py
#   Il faut octave et xvfb-run. Dossier temporaire efface a la fin.
# =============================================================================

import os
import re
import sys
import glob
import shutil
import tempfile
import subprocess

try:
    DOSSIER = os.path.dirname(os.path.abspath(__file__))
except NameError:
    DOSSIER = os.getcwd()
RACINE = os.path.dirname(DOSSIER)
ELM = os.path.join(RACINE, "ELM_PID")
METRIQUES = os.path.join(DOSSIER, "metriques")

# --------------------------------------------------------------------------
# Fonctions Simulink et graphiques factices (Octave 8.4)
# --------------------------------------------------------------------------
SHIMS = {
    "gobjects.m": """function h = gobjects(varargin)
  h = zeros(varargin{:});
end
""",
    "contains.m": """function tf = contains(s, motif)
  if iscell(s)
    tf = ~cellfun(@isempty, strfind(s, motif));
  else
    tf = ~isempty(strfind(s, motif));
  end
end
""",
    "tiledlayout.m": """function tl = tiledlayout(fig, m, n, varargin)
  % Equivalent Octave : axes invisible qui porte le titre ; les tuiles sont
  % des axes empiles (nexttile).
  setappdata(fig, 'tl_m', m); setappdata(fig, 'tl_n', n); setappdata(fig, 'tl_k', 0);
  tl = axes('Parent', fig, 'Position', [0.08 0.955 0.88 0.01], 'Visible', 'off', 'Tag', 'tl_shim');
end
""",
    "nexttile.m": """function ax = nexttile(tl)
  fig = ancestor(tl, 'figure');
  m = getappdata(fig, 'tl_m'); k = getappdata(fig, 'tl_k') + 1; setappdata(fig, 'tl_k', k);
  h = 0.86 / m;
  ax = axes('Parent', fig, 'Position', [0.08, 0.93 - k * h + 0.02, 0.88, h - 0.06]);
end
""",
    "xline.m": """function h = xline(ax, x, ls, varargin)
  h = line(ax, [x x], [-1e6 1e6], 'LineStyle', ls, 'Color', [0.5 0.5 0.5], 'Tag', 'xline_shim', 'HandleVisibility', 'off');
end
""",
    "exportgraphics.m": """function exportgraphics(fig, fichier, varargin)
  r = 200;
  for i = 1:2:numel(varargin)
    if strcmpi(varargin{i}, 'Resolution'), r = varargin{i + 1}; end
  end
  print(fig, '-dpng', sprintf('-r%d', r), fichier);
end
""",
    "which_shim.m": """function c = which_shim(nom, varargin)
  if isfile(fullfile(pwd, nom)), c = {fullfile(pwd, nom)}; else, c = {}; end
end
""",
    "bdIsLoaded.m": "function tf = bdIsLoaded(m)\n  tf = false;\nend\n",
    "load_system.m": "function load_system(varargin)\nend\n",
    "close_system.m": "function close_system(varargin)\nend\n",
    "set_param.m": "function set_param(varargin)\nend\n",
    "getSimulinkBlockHandle.m": "function h = getSimulinkBlockHandle(b)\n  h = 1;\nend\n",
    "faux_code.m": """function code = faux_code(mdl)
  t = regexp(mdl, '_(S[0-9a-z]+)$', 'tokens', 'once');
  code = t{1};
end
""",
    "faux_adaptatif.m": """function tf = faux_adaptatif(mdl)
  tf = ~isempty(regexp(mdl, '^(ELM_PID|PINN_PID|Fuzzy_PID)_', 'once'));
end
""",
    "find_system.m": """function c = find_system(mdl, varargin)
  c = {[mdl '/cmp_vout'], [mdl '/cmp_iL'], [mdl '/cmp_d'], [mdl '/x'], [mdl '/y']};
  if faux_adaptatif(mdl), c{end + 1} = [mdl '/cmp_K']; end
  c = c';
end
""",
    "get_param.m": """function r = get_param(obj, p)
  if iscell(obj)
    r = cellfun(@(o) get_param(o, p), obj, 'UniformOutput', false);
    return;
  end
  switch p
    case 'VariableName'
      r = obj(find(obj == '/', 1, 'last') + 1:end);
    case 'StopTime'
      m = load(['scenario_' faux_code(obj) '.mat']);
      r = sprintf('%.17g', (numel(m.t) - 0.5) / 220000);
    case 'InitFcn'
      r = sprintf('charger_scenario(''%s'');', faux_code(obj));
    case 'Dirty'
      r = 'off';
    case {'P', 'I', 'D'}
      mdl = obj(1:find(obj == '/', 1) - 1);
      if strncmp(mdl, 'ZN_', 3)
        v = struct('P', '0.09391', 'I', '301.089', 'D', '7.3227e-06');
      else
        v = struct('P', '0.0602', 'I', '412.5', 'D', '5.1e-06');
      end
      r = v.(p);
    otherwise
      error('get_param factice : %s', p);
  end
end
""",
    "sim.m": """function sortie = sim(mdl, varargin)
  % Signaux factices, aux instants du profil (k Tc), de forme realiste.
  m = load(['scenario_' faux_code(mdl) '.mat']);
  t = double(m.t(:));
  c = 100 + double(m.dvref(:));
  ev = double(m.evenements(:))';
  v = c .* (1 - exp(-t / 1.5e-3)) + 12 * exp(-t / 4e-3) .* sin(2 * pi * 300 * t) + 0.05 * sin(2 * pi * 22000 * t);
  iL = 2 + 15 * exp(-t / 2e-3) + 0.5 * sin(2 * pi * 22000 * t);
  d = min(0.99, 0.55 + 2 * exp(-t / 1e-3) + 0.01 * sin(2 * pi * 1000 * t));
  for j = 1:numel(ev)
    s = (t >= ev(j)) .* exp(-max(t - ev(j), 0) / 2e-3);
    v = v - 5 * s; iL = iL + 4 * s; d = min(0.99, d + 0.05 * s);
  end
  K_ZN = [0.093910, 301.089, 7.3227e-06];
  K = [K_ZN(1) * (1 + 0.3 * exp(-t / 5e-3)), K_ZN(2) * (1 + 0.2 * sin(2 * pi * 50 * t)), K_ZN(3) * (1 - 0.1 * t / t(end))];
  donnees = struct('cmp_vout', v, 'cmp_iL', iL, 'cmp_d', d);
  if faux_adaptatif(mdl), donnees.cmp_K = K; end
  noms = fieldnames(donnees);
  S = struct();
  for i = 1:numel(noms)
    S.(noms{i}) = struct('time', t, 'signals', struct('values', donnees.(noms{i})));
  end
  sortie.who = noms;
  sortie.get = @(n) S.(n);
end
""",
}

CONTROLES_FIGURES = r"""
% ---- Controles des figures (ajoutes par le test) ----
ok_tout = true;
figs = findobj(0, 'type', 'figure');
printf('TEST figures ouvertes : %d\n', numel(figs));
for f = reshape(figs, 1, [])
  nom = get(f, 'Name');
  m = load(['scenario_' faux_code(nom) '.mat']);
  t_fin_ms = (numel(m.t) - 1) / 220000 * 1e3;
  axs = findobj(f, 'type', 'axes');
  axs = axs(~strcmp(get(axs, 'Tag'), 'tl_shim') & ~strcmp(get(axs, 'Tag'), 'legend'));
  printf('TEST %s titre : %s\n', nom, get(get(findobj(f, 'Tag', 'tl_shim'), 'Title'), 'String'));
  n_courbes = 0; n_texte = 0;
  for ax = reshape(axs, 1, [])
    lignes = findobj(ax, 'type', 'line');
    if ~isempty(lignes)
      lignes = lignes(~strcmp(get(lignes, 'Tag'), 'xline_shim'));
    end
    if isempty(lignes)
      tx = findobj(ax, 'type', 'text');
      chaines = {};
      for q = 1:numel(tx)
        s_ = get(tx(q), 'String');
        if iscell(s_), chaines = [chaines, s_(:)']; else, chaines{end + 1} = s_; end
      end
      if any(~cellfun(@isempty, strfind(chaines, 'Gains constants')))
        n_texte = n_texte + 1;
        printf('TEST %s tuile texte : %s\n', nom, strjoin(chaines, ' | '));
      end
      continue;
    end
    n_courbes = n_courbes + 1;
    Y = [];
    for l = reshape(lignes, 1, [])
      Y = [Y; get(l, 'YData')(:)];
    end
    Y = Y(isfinite(Y));
    bas = min(Y); haut = max(Y); e = haut - bas;
    if e <= 0, e = 0.1 * max(abs(haut), 1); end
    yl = get(ax, 'YLim'); xl = get(ax, 'XLim');
    mb = (bas - yl(1)) / e; mh = (yl(2) - haut) / e;
    ok = mb >= 0.05 - 1e-9 && mh >= 0.05 - 1e-9 && abs(xl(1)) < 1e-9 && abs(xl(2) - t_fin_ms) < 1e-6;
    ok_tout = ok_tout && ok;
    printf('TEST %s %-16s donnees [%.4g ; %.4g] ylim [%.4g ; %.4g] marges %.3f / %.3f xlim [%g ; %g] %s\n', ...
           nom, get(get(ax, 'YLabel'), 'String'), bas, haut, yl(1), yl(2), mb, mh, xl(1), xl(2), ...
           ifelse_txt(ok));
  end
  attendu_courbes = 3 + faux_adaptatif(nom);
  ok_t = n_courbes == attendu_courbes && n_texte == ~faux_adaptatif(nom);
  ok_tout = ok_tout && ok_t;
  printf('TEST %s : %d tuiles a courbes, %d tuile texte (attendu %d et %d) %s\n', nom, n_courbes, n_texte, ...
         attendu_courbes, ~faux_adaptatif(nom), ifelse_txt(ok_t));
  for ext = {'.png', '.fig'}
    fi = fullfile(pwd, 'figures_comparaison', [nom ext{1}]);
    d_ = dir(fi);
    ok_f = ~isempty(d_) && d_.bytes > 0;
    ok_tout = ok_tout && ok_f;
    printf('TEST fichier %s %s\n', ['figures_comparaison/' nom ext{1}], ifelse_txt(ok_f));
  end
end
% Courbe plate et donnees non finies
figure('visible', 'off'); a_ = axes();
plot(a_, 1:10, 5 * ones(1, 10)); fixer_ordonnees(a_, 5 * ones(10, 1), 0.08);
yl = get(a_, 'YLim'); ok_p = yl(1) < 5 && yl(2) > 5 && (5 - yl(1)) >= 0.05 * 0.5 - 1e-12;
printf('TEST courbe plate a 5 : ylim [%.4g ; %.4g] %s\n', yl(1), yl(2), ifelse_txt(ok_p));
fixer_ordonnees(a_, [NaN; 1; 3; Inf], 0.08); yl = get(a_, 'YLim');
ok_n = abs(yl(1) - (1 - 0.16)) < 1e-12 && abs(yl(2) - (3 + 0.16)) < 1e-12;
printf('TEST donnees avec NaN et Inf : ylim [%.4g ; %.4g] %s\n', yl(1), yl(2), ifelse_txt(ok_n));
ok_tout = ok_tout && ok_p && ok_n;
printf('TEST BILAN FIGURES : %s\n', ifelse_txt(ok_tout));
"""

AIDE_OCTAVE = """function s = ifelse_txt(ok)
  if ok, s = 'OK'; else, s = 'ECHEC'; end
end
"""


def pour_octave(source, remplacements=()):
    """Fonctions locales placees en tete (Octave), which -> which_shim,
    -v7.3 -> -v7, puis remplacements de reglages."""
    texte = open(source, encoding="utf-8").read()
    i = texte.index("%% ===================== Fonctions")
    script, fonctions = texte[:i], texte[i:]
    texte = "1;\n" + fonctions + "\n" + script
    texte = texte.replace("which(", "which_shim(").replace("'-v7.3'", "'-v7'")
    for a, b in remplacements:
        assert texte.count(a) == 1, a
        texte = texte.replace(a, b)
    return texte


def octave(dossier, commande, env_fonts):
    env = dict(os.environ, OCTAVE_FONTS_DIR=env_fonts)
    p = subprocess.run(["xvfb-run", "-a", "octave", "--no-gui", "--quiet", "--eval", commande], cwd=dossier,
                       env=env, capture_output=True, text=True, timeout=1800)
    return p.stdout + p.stderr


def preparer_polices(tmp):
    # Octave 8.4 (Ubuntu) cherche FreeSans.otf, absent ici : liens vers les .ttf.
    d = os.path.join(tmp, "polices")
    os.makedirs(d)
    for s in ["", "Bold", "Oblique", "BoldOblique"]:
        os.symlink(f"/usr/share/fonts/truetype/freefont/FreeSans{s}.ttf", os.path.join(d, f"FreeSans{s}.otf"))
    return d


def test_figures(tmp, polices):
    print("=" * 78)
    print("A. Simuler_Modeles_Comparaison.m : figures")
    print("=" * 78)
    shims = os.path.join(tmp, "shims")
    os.makedirs(shims)
    for n, c in SHIMS.items():
        open(os.path.join(shims, n), "w").write(c)
    open(os.path.join(shims, "ifelse_txt.m"), "w").write(AIDE_OCTAVE)
    bilans = []
    for cas, remp in [("figures", [("AVEC_ZIEGLER_NICHOLS = false;", "AVEC_ZIEGLER_NICHOLS = true;")]),
                      ("fermer", [("AVEC_ZIEGLER_NICHOLS = false;", "AVEC_ZIEGLER_NICHOLS = true;"),
                                  ("FERMER_FIGURES = false;", "FERMER_FIGURES = true;")]),
                      ("sans_figures", [("AVEC_ZIEGLER_NICHOLS = false;", "AVEC_ZIEGLER_NICHOLS = true;"),
                                        ("FIGURES = true;", "FIGURES = false;")])]:
        d = os.path.join(tmp, cas)
        os.makedirs(d)
        for f in ["charger_scenario.m", "scenario_S1.mat", "scenario_S2.mat", "scenario_S3.mat",
                  "scenario_S8a.mat", "scenario_S10.mat", "predictions_banc_elm_pid.json"]:
            shutil.copy(os.path.join(ELM, f), d)
        shutil.copy(os.path.join(RACINE, "PSO_PID", "predictions_banc_pso_pid.json"), d)
        shutil.copy(os.path.join(ELM, "predictions_banc_pid_classique.json"), d)
        for mdl in ["ELM_PID_S1", "ELM_PID_S2", "ELM_PID_S10", "PSO_PID_S3", "ZN_S8a"]:
            open(os.path.join(d, mdl + ".slx"), "w").close()
        open(os.path.join(d, "Simuler_Modeles_Comparaison_octave.m"), "w").write(
            pour_octave(os.path.join(ELM, "Simuler_Modeles_Comparaison.m"), remp))
        controles = CONTROLES_FIGURES if cas == "figures" else ""
        if cas == "fermer":
            controles = r"""
figs = findobj(0, 'type', 'figure');
n_png = numel(dir(fullfile(pwd, 'figures_comparaison', '*.png')));
n_fig = numel(dir(fullfile(pwd, 'figures_comparaison', '*.fig')));
ok = isempty(figs) && n_png == 5 && n_fig == 5;
printf('TEST FERMER_FIGURES = true : %d figure(s) ouverte(s), %d PNG, %d .fig %s\n', numel(figs), n_png, n_fig, ifelse_txt(ok));
printf('TEST BILAN FERMER : %s\n', ifelse_txt(ok));
"""
        if cas == "sans_figures":
            controles = r"""
ok = isempty(findobj(0, 'type', 'figure')) && ~isfolder(fullfile(pwd, 'figures_comparaison'));
printf('TEST FIGURES = false : aucune figure, pas de dossier figures_comparaison %s\n', ifelse_txt(ok));
printf('TEST BILAN SANS FIGURES : %s\n', ifelse_txt(ok));
"""
        cmd = (f"addpath('{shims}'); graphics_toolkit('qt'); set(0, 'defaultfigurevisible', 'off'); "
               f"Simuler_Modeles_Comparaison_octave; {controles}")
        sortie = octave(d, cmd, polices)
        lignes = sortie.splitlines()
        garde = [l for l in lignes if l.startswith("TEST") or "figure :" in l or "error" in l.lower()
                 or "warning" in l.lower() and "figure" in l.lower() or l.startswith("===")]
        print(f"\n--- cas {cas} ---")
        print("\n".join(garde))
        bilans += [l for l in lignes if l.startswith("TEST BILAN")]
    # Resultats identiques avec et sans figures (hors temps de calcul)
    cmd = r"""
ok = true;
for f = {'resultats_Buck_Commun_ELM_PID_comparaison.mat', 'resultats_Buck_Commun_PSO_PID_comparaison.mat', 'resultats_Buck_Commun_comparaison.mat'}
  a = load(fullfile('figures', f{1})); b = load(fullfile('sans_figures', f{1}));
  ra = rmfield(a.resultats, {'duree_calcul_s', 'us_par_pas'}); rb = rmfield(b.resultats, {'duree_calcul_s', 'us_par_pas'});
  ok_f = isequal(ra, rb);
  printf('TEST %s identique avec et sans figures (hors temps de calcul) : %d\n', f{1}, ok_f);
  ok = ok && ok_f;
end
if ok, printf('TEST BILAN RESULTATS INCHANGES : OK\n'); else, printf('TEST BILAN RESULTATS INCHANGES : ECHEC\n'); end
"""
    sortie = octave(tmp, cmd, polices)
    print("\n--- resultats avec et sans figures ---")
    print("\n".join(l for l in sortie.splitlines() if l.startswith("TEST") or "error" in l.lower()))
    bilans += [l for l in sortie.splitlines() if l.startswith("TEST BILAN")]
    pngs = sorted(glob.glob(os.path.join(tmp, "figures", "figures_comparaison", "*.png")))
    return bilans, pngs


FABRIQUER = r"""
function fabriquer(dossier, modele, cibles, Te)
  % Fichier resultats_<modele>.mat au format de Simuler_<M>.m : pour chaque
  % scenario, Vout = consigne - e, e choisi pour que l'IAE de classement
  % (definitions_metriques.txt) vaille exactement la cible (mV.s).
  codes = fieldnames(cibles);
  resultats = struct('code', {}, 'nom', {}, 't', {}, 'v', {}, 'consigne', {}, 'mu', {}, 'd', {}, 'iL', {}, ...
                     'K', {}, 'grandeurs', {}, 'duree_calcul_s', {}, 'us_par_pas', {});
  for i = 1:numel(codes)
    code = codes{i};
    m = load(fullfile(dossier, ['scenario_' code '.mat']));
    N = numel(m.t); t = (0:N-1)' * Te;
    consigne = 100 + double(m.dvref(:));
    switch code
      case 'S1', ka = 0; kb = round(0.03 / Te);
      case 'S10', ka = round(0.10 / Te); kb = N;
      otherwise, ka = round(0.03 / Te); kb = N;
    end
    forme = 0.2 + exp(-t / 2e-3);
    w = (ka + 1):kb;
    c = cibles.(code) / (sum(forme(w)) * Te * 1e3);
    e = 0.3 * forme; e(w) = c * forme(w);
    v = consigne - e;
    d = 0.5 * ones(N, 1); iL = 3 * ones(N, 1);
    resultats(end + 1) = struct('code', code, 'nom', code, 't', t, 'v', v, 'consigne', consigne, 'mu', d, ...
                                'd', d, 'iL', iL, 'K', [], 'grandeurs', struct('evenements', []), ...
                                'duree_calcul_s', 10, 'us_par_pas', 227);
  end
  MODELE = modele;
  save('-v7', fullfile(dossier, ['resultats_' modele '.mat']), 'resultats', 'MODELE');
end
"""


def lire_banc():
    banc = {}
    for l in open(os.path.join(METRIQUES, "metriques_banc.csv"), encoding="utf-8").read().splitlines()[1:]:
        s, m, g, f, me, v, u = l.split(";")
        if g == "classement" and me == "IAE":
            banc[(s, m)] = float(v)
    return banc


def test_controle(tmp, polices):
    print()
    print("=" * 78)
    print("B. Metriques_Simulink.m : noms des dossiers et controle de version")
    print("=" * 78)
    banc = lire_banc()
    racine = os.path.join(tmp, "Regulateurs")
    met = os.path.join(racine, "COMPARAISON", "metriques")
    os.makedirs(met)
    shutil.copy(os.path.join(METRIQUES, "metriques_banc.csv"), met)
    shims = os.path.join(tmp, "shims")
    open(os.path.join(tmp, "fabriquer.m"), "w").write(FABRIQUER)
    dossiers = {"PSO_PID": ("Buck_Commun_PSO_PID", "PSO-PID"), "FUZZY_PID": ("Buck_Commun_Fuzzy_PID", "Fuzzy-PID"),
                "ELM_PID_B": ("Buck_Commun_ELM_PID", "ELM-PID"), "ELM_PID": ("Buck_Commun_ELM_PID", "ELM-PID"),
                "PINN_PID": ("Buck_Commun_PINN_PID", "PINN-PID")}
    codes = ["S1", "S2", "S3", "S8a", "S10"]
    for dos in dossiers:
        os.makedirs(os.path.join(racine, dos))
        for c in codes:
            shutil.copy(os.path.join(ELM, f"scenario_{c}.mat"), os.path.join(racine, dos))
    for c in codes:
        shutil.copy(os.path.join(ELM, f"scenario_{c}.mat"), os.path.join(racine, "PSO_PID"))

    def cibles_txt(cibles):
        return "struct(" + ", ".join(f"'{c}', {v!r}" for c, v in cibles.items()) + ")"

    lignes = [f"addpath('{tmp}'); addpath('{shims}'); Te = 1/220000;"]
    for dos, (modele, meth) in dossiers.items():
        if dos == "ELM_PID":
            # faux fichier "version incrementale" : IAE S1 81.12 et S2 5.62 (sortie de l'etudiant)
            cibles = {"S1": 81.12, "S2": 5.62, "S3": banc[("S3", meth)] * 1.10, "S8a": banc[("S8a", meth)] * 1.10}
        else:
            cibles = {c: banc[(c, meth)] * 1.001 for c in codes}
        lignes.append(f"fabriquer('{os.path.join(racine, dos)}', '{modele}', {cibles_txt(cibles)}, Te);")
    zn = {c: banc[(c, "Ziegler-Nichols")] * 1.02 for c in codes}   # ZN : non controle, +2 % garde
    lignes.append(f"fabriquer('{os.path.join(racine, 'PSO_PID')}', 'Buck_Commun', {cibles_txt(zn)}, Te);")
    sortie = octave(tmp, " ".join(lignes), polices)
    if "error" in sortie.lower():
        print(sortie)

    def lancer(cas, remplacements, attendus, refus_attendus):
        open(os.path.join(met, "Metriques_Simulink_octave.m"), "w").write(
            pour_octave(os.path.join(METRIQUES, "Metriques_Simulink.m"), remplacements))
        cmd = f"addpath('{shims}'); Metriques_Simulink_octave"
        sortie = octave(met, cmd, polices)
        print(f"\n--- cas {cas} ---")
        garde = [l for l in sortie.splitlines() if "REFUSE" in l or "Dossiers lus" in l or l.startswith("  ELM-PID")
                 or "ELM-PID " in l and ": lu dans" in l or "ABSENTS" in l or "error" in l.lower()
                 or l.startswith("| ELM-PID") or "FICHIERS REFUSES" in l]
        print("\n".join(garde[:30]))
        ok = True
        for motif in attendus:
            present = any(motif in l for l in sortie.splitlines())
            print(f"TEST attendu present : {motif!r} : {'OK' if present else 'ECHEC'}")
            ok = ok and present
        n_refus = sum(1 for l in sortie.splitlines() if l.startswith("  REFUSE : "))
        okr = n_refus == refus_attendus
        print(f"TEST fichiers refuses : {n_refus} (attendu {refus_attendus}) {'OK' if okr else 'ECHEC'}")
        ok = ok and okr
        csv = open(os.path.join(met, "metriques_simulink.csv"), encoding="utf-8").read()
        return ok, sortie, csv

    bilans = []
    ok1, s1, csv1 = lancer("DOSSIER_ELM = 'ELM_PID_B' (defaut)", [],
                           ["ELM-PID          S1   : lu dans", "ELM_PID_B/resultats_Buck_Commun_ELM_PID.mat"], 0)
    ok1 = ok1 and ";ELM-PID;classement;classement;IAE;" in csv1 and re.search(r"Ziegler-Nichols +S1 +: lu dans", s1) is not None
    bilans.append(f"TEST BILAN CONTROLE (ELM_PID_B accepte) : {'OK' if ok1 else 'ECHEC'}")
    ok2, s2, csv2 = lancer("DOSSIER_ELM = 'ELM_PID' (ancien dossier, version incrementale)",
                           [("DOSSIER_ELM   = 'ELM_PID_B';", "DOSSIER_ELM   = 'ELM_PID';")],
                           ["ce fichier ne correspond pas a la version retenue", "IAE de classement S1 81.12",
                            "ELM-PID S1", "FICHIERS REFUSES"], 1)
    ok2 = ok2 and ";ELM-PID;" not in csv2
    bilans.append(f"TEST BILAN CONTROLE (version incrementale refusee) : {'OK' if ok2 else 'ECHEC'}")
    # S10 : tolerance ecrite avant de 3 % pour l'ELM-PID
    resultats = []
    for facteur, refus in [(1.02, 0), (1.04, 1)]:
        cibles = {c: banc[(c, "ELM-PID")] * 1.001 for c in codes}
        cibles["S10"] = banc[("S10", "ELM-PID")] * facteur
        octave(tmp, f"addpath('{tmp}'); fabriquer('{os.path.join(racine, 'ELM_PID_B')}', 'Buck_Commun_ELM_PID', "
                    f"{cibles_txt(cibles)}, 1/220000);", polices)
        ok, _, _ = lancer(f"ELM-PID S10 a {100 * (facteur - 1):+.0f} %", [], [], refus)
        resultats.append(ok)
    bilans.append(f"TEST BILAN CONTROLE (S10 : +2 % accepte, +4 % refuse) : {'OK' if all(resultats) else 'ECHEC'}")
    return bilans


def main():
    tmp = tempfile.mkdtemp(prefix="test_figures_")
    try:
        polices = preparer_polices(tmp)
        bilans, pngs = test_figures(tmp, polices)
        if "--garder-png" in sys.argv:
            dest = sys.argv[sys.argv.index("--garder-png") + 1]
            os.makedirs(dest, exist_ok=True)
            for p in pngs:
                shutil.copy(p, dest)
        bilans += test_controle(tmp, polices)
        print()
        print("=" * 78)
        print("BILAN")
        print("=" * 78)
        print("\n".join(bilans))
        attendus = ["FIGURES :", "FERMER :", "SANS FIGURES :", "RESULTATS INCHANGES :", "ELM_PID_B accepte",
                    "version incrementale refusee", "S10 : +2 % accepte"]
        manquants = [a for a in attendus if not any(a in l for l in bilans)]
        for a in manquants:
            print(f"TEST BILAN MANQUANT ({a}) : ECHEC")
        return 0 if all(l.endswith("OK") for l in bilans) and not manquants else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
