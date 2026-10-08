%% SIMULER_MODELES_COMPARAISON.m
%
% OBJECTIF
% --------
% Simuler les modeles qu'on lance d'un clic, construits par
% Construire_Modeles_Comparaison.m (<PREFIXE>_<code>.slx, par exemple
% ELM_PID_S10.slx ou ZN_S8a.slx), mesurer le temps d'execution de chaque
% simulation, et ecrire les signaux au format des fichiers de
% Simuler_<Methode>.m pour que COMPARAISON/metriques/Metriques_Simulink.m
% calcule TOUTES les metriques avec les definitions de reference
% (COMPARAISON/metriques/definitions_metriques.txt, ecrites avant calcul) :
% demarrage, IAE / ISE / ITAE de la fenetre de classement, ecarts, erreur
% en regime permanent (5 ms avant chaque evenement, 10 dernieres ms),
% ondulation, evenements, commande, temps de calcul Simulink.
% Ce script ne redefinit aucune metrique. Il affiche seulement, comme
% Simuler_<Methode>.m, les grandeurs du banc commun (fonction grandeurs,
% copie de Simuler_ELM_PID.m) et l'ecart au banc, pour reperer tout de
% suite un modele qui ne suit pas.
%
% Le meme script est dans les quatre dossiers de methode. Il trouve seul
% les modeles <PREFIXE>_<code>.slx du dossier courant.
%
% LE TEMPS D'EXECUTION
% --------------------
% duree_calcul_s = duree de sim() mesuree par tic / toc (compilation du
% modele et rappel InitFcn compris, comme un clic sur Run) ; us_par_pas =
% duree_calcul_s divisee par le nombre de periodes du regulateur (44 001
% pour 0.2 s). Memes noms de champs que Simuler_<Methode>.m : c'est le
% point 6b de definitions_metriques.txt. Ce n'est pas le cout du
% regulateur : l'execution interpretee des blocs MATLAB System et le
% circuit au pas du powergui dominent.
% Pendant la simulation, les deux To Workspace d'origine du modele commun
% (variables x et y, au pas du powergui, 5.3 millions de points par bloc)
% sont mis en commentaire EN MEMOIRE, comme dans Simuler_<Methode>.m
% (reglage NEUTRALISER_TO_WORKSPACE_DU_MODELE) : les durees se comparent
% alors a celles de Simuler_<Methode>.m. Les blocs d'observation ajoutes
% (Scope, To Workspace cmp_*) restent actifs. Aucun .slx n'est enregistre.
%
% CE QUE PRODUIT CE SCRIPT
% -------------------------
%   - dans la console : par modele, le temps de calcul, les grandeurs du
%     banc commun et l'ecart au banc (si predictions_banc_*.json est la) ;
%     puis un tableau recapitulatif ;
%   - resultats_<MODELE SOURCE>_comparaison.mat, par exemple
%     resultats_Buck_Commun_ELM_PID_comparaison.mat ou, pour ZN,
%     resultats_Buck_Commun_comparaison.mat : variable "resultats", une
%     entree par scenario, memes champs que Simuler_<Methode>.m (code, nom,
%     t, v, consigne, mu, d, iL, K, grandeurs, duree_calcul_s, us_par_pas)
%     plus "modele" (nom du modele simule). Si le fichier existe deja, les
%     scenarios simules y sont remplaces et les autres gardes : on peut
%     simuler un scenario a la fois. Les fichiers de Simuler_<Methode>.m
%     (resultats_Buck_Commun_<M>.mat et _S10.mat) ne sont jamais touches.
% Ensuite, quand les cinq methodes sont simulees : dossier courant
% COMPARAISON/metriques, Metriques_Simulink.m avec RESULTATS =
% 'comparaison' (metriques_simulink_comparaison.csv et .md).
%
% Prerequis dans le dossier courant MATLAB : les modeles
% <PREFIXE>_<code>.slx, charger_scenario.m, scenario_<code>.mat, les
% fichiers du bloc de la methode ; facultatif : predictions_banc_*.json.
% Duree par scenario de 0.2 s : environ 30 s pour ZN et le PSO-PID, une a
% deux minutes pour le Fuzzy-PID et l'ELM-PID, deux a quatre minutes pour
% le PINN-PID (execution interpretee des blocs MATLAB System).
% Compatible MATLAB R2024a.
% ---------------------------------------------------------------------

clear; clc;

% --- Reglages ---
CODES = {'S1', 'S2', 'S3', 'S8a', 'S10'};        % scenarios cherches quand la liste est vide
MODELES_A_SIMULER = {};                          % {} : tous les <PREFIXE>_<code>.slx du dossier ;
                                                 % sinon par exemple {'ELM_PID_S10', 'ZN_S10'}
AVEC_ZIEGLER_NICHOLS = false;                    % liste vide : true pour simuler aussi les ZN_<code>.slx
NEUTRALISER_TO_WORKSPACE_DU_MODELE = true;       % To Workspace d'origine (x, y) en commentaire, en memoire
TC = 1/(22000*10);                               % periode du regulateur et des enregistrements (s)

% Prefixes : prefixe des modeles, modele source (nom des fichiers de
% resultats, comme Simuler_<Methode>.m), methode, resultats attendus du banc.
PREFIXES = {'ELM_PID',   'Buck_Commun_ELM_PID',   'ELM-PID',         'predictions_banc_elm_pid.json'; ...
            'PINN_PID',  'Buck_Commun_PINN_PID',  'PINN-PID',        'predictions_banc_pinn_pid.json'; ...
            'Fuzzy_PID', 'Buck_Commun_Fuzzy_PID', 'Fuzzy-PID',       'predictions_banc_fuzzy_pid.json'; ...
            'PSO_PID',   'Buck_Commun_PSO_PID',   'PSO-PID',         'predictions_banc_pso_pid.json'; ...
            'ZN',        'Buck_Commun',           'Ziegler-Nichols', 'predictions_banc_pid_classique.json'};

% --- Liste des modeles ---
liste = struct('modele', {}, 'source', {}, 'methode', {}, 'code', {}, 'predictions', {});
if isempty(MODELES_A_SIMULER)
    for p = 1:size(PREFIXES, 1)
        if strcmp(PREFIXES{p, 1}, 'ZN') && ~AVEC_ZIEGLER_NICHOLS
            continue
        end
        for c = CODES
            mdl = [PREFIXES{p, 1} '_' c{1}];
            if isfile(fullfile(pwd, [mdl '.slx']))
                liste(end + 1) = struct('modele', mdl, 'source', PREFIXES{p, 2}, 'methode', PREFIXES{p, 3}, ...
                                        'code', c{1}, 'predictions', PREFIXES{p, 4}); %#ok<SAGROW>
            end
        end
    end
    if isempty(liste)
        error(['Aucun modele <PREFIXE>_<code>.slx dans le dossier courant %s.\n' ...
               'Lancer d''abord Construire_Modeles_Comparaison.m.'], pwd);
    end
else
    for m = reshape(cellstr(MODELES_A_SIMULER), 1, [])
        p = find(cellfun(@(x) startsWith(m{1}, [x '_']), PREFIXES(:, 1)), 1);
        if isempty(p)
            error('MODELES_A_SIMULER : %s ne commence par aucun prefixe connu (%s).', m{1}, ...
                  strjoin(PREFIXES(:, 1)', ', '));
        end
        if ~isfile(fullfile(pwd, [m{1} '.slx']))
            error('Modele introuvable dans le dossier courant : %s.slx (lancer Construire_Modeles_Comparaison.m).', m{1});
        end
        liste(end + 1) = struct('modele', m{1}, 'source', PREFIXES{p, 2}, 'methode', PREFIXES{p, 3}, ...
                                'code', m{1}(numel(PREFIXES{p, 1}) + 2:end), 'predictions', PREFIXES{p, 4}); %#ok<SAGROW>
    end
end
fprintf('Modeles simules : %s.\n', strjoin({liste.modele}, ', '));

% --- Prerequis ---
manquants = {};
for f = [{'charger_scenario.m'}, strcat('scenario_', unique({liste.code}, 'stable'), '.mat')]
    if ~isfile(fullfile(pwd, f{1}))
        manquants{end + 1} = f{1}; %#ok<SAGROW>
    end
end
if ~isempty(manquants)
    error('Fichier(s) introuvable(s) dans le dossier courant %s :\n  %s', pwd, strjoin(manquants, '\n  '));
end
for f = [{'charger_scenario.m'}, strcat({liste.modele}, '.slx')]
    copies = which(f{1}, '-all');
    if numel(copies) ~= 1
        error('Il doit exister exactement un %s sur le chemin MATLAB, il y en a %d :\n%s', ...
              f{1}, numel(copies), strjoin(copies, newline));
    end
end
predictions = containers.Map();                  % fichiers de resultats attendus, lus une fois

% --- Simulations ---
nouveaux = struct('code', {}, 'nom', {}, 't', {}, 'v', {}, 'consigne', {}, 'mu', {}, 'd', {}, 'iL', {}, ...
                  'K', {}, 'grandeurs', {}, 'duree_calcul_s', {}, 'us_par_pas', {}, 'modele', {});
sources = {};                                    % modele source de chaque entree
banc_iae = [];                                   % IAE du banc (30 ms a la fin), NaN si absent
for i = 1:numel(liste)
    L = liste(i);
    MDL = L.modele;
    sc = charger_scenario(L.code);
    fprintf('\n=== %s : %s, %s (%.0f ms) ===\n', MDL, L.methode, sc.nom, sc.duree * 1e3);
    if bdIsLoaded(MDL)
        if strcmp(get_param(MDL, 'Dirty'), 'on')
            error('%s est ouvert avec des modifications non enregistrees : l''enregistrer ou le fermer.', MDL);
        end
        close_system(MDL, 0);
    end
    load_system(fullfile(pwd, [MDL '.slx']));
    try
        % Le modele doit etre celui de Construire_Modeles_Comparaison.m
        stop_attendu = (numel(sc.t) - 0.5) * TC;
        stop = str2double(get_param(MDL, 'StopTime'));
        if ~(abs(stop - stop_attendu) <= 1e-12)
            error('%s : StopTime %s au lieu de %.17g. Reconstruire avec Construire_Modeles_Comparaison.m.', ...
                  MDL, get_param(MDL, 'StopTime'), stop_attendu);
        end
        if ~contains(get_param(MDL, 'InitFcn'), sprintf('charger_scenario(''%s'');', L.code))
            error('%s : le rappel InitFcn ne charge pas %s. Reconstruire avec Construire_Modeles_Comparaison.m.', ...
                  MDL, L.code);
        end
        tw = find_system(MDL, 'SearchDepth', 1, 'BlockType', 'ToWorkspace');
        variables = get_param(tw, 'VariableName');
        for v_ = {'cmp_vout', 'cmp_iL', 'cmp_d'}
            if ~any(strcmp(variables, v_{1}))
                error(['%s : enregistrement %s absent (modele fait par un autre script ?). ' ...
                       'Reconstruire avec Construire_Modeles_Comparaison.m.'], MDL, v_{1});
            end
        end
        avec_gains = any(strcmp(variables, 'cmp_K'));
        if NEUTRALISER_TO_WORKSPACE_DU_MODELE
            for j = 1:numel(tw)
                if ~startsWith(get_param(tw{j}, 'VariableName'), 'cmp_')
                    set_param(tw{j}, 'Commented', 'on');   % en memoire seulement
                end
            end
        end
        t_debut = tic;
        sortie = sim(MDL, 'ReturnWorkspaceOutputs', 'on');
        duree_calcul = toc(t_debut);
    catch ME
        close_system(MDL, 0);
        rethrow(ME);
    end
    close_system(MDL, 0);                                 % SANS enregistrer

    n_sc = numel(sc.t);
    [t, v] = extraire_enregistrement(sortie, 'cmp_vout');
    [t2, iL] = extraire_enregistrement(sortie, 'cmp_iL');
    [t3, d] = extraire_enregistrement(sortie, 'cmp_d');
    if numel(t) >= n_sc && numel(t2) >= n_sc && numel(t3) >= n_sc
        t = t(1:n_sc); t2 = t2(1:n_sc); t3 = t3(1:n_sc);
        v = v(1:n_sc); iL = iL(1:n_sc); d = d(1:n_sc);
    end
    if ~isequal(numel(t), numel(t2), numel(t3), n_sc) || max(abs([t - t2; t - t3; t - sc.t])) > 1e-9
        error('%s : enregistrements non alignes avec le profil (%d instants attendus, %d obtenus).', MDL, n_sc, numel(t));
    end
    K = [];
    if avec_gains
        [tk, K] = extraire_matrice(sortie, 'cmp_K');
        if size(K, 1) >= n_sc
            K = K(1:n_sc, :);
            tk = tk(1:n_sc);
        end
        if size(K, 1) ~= n_sc || max(abs(tk - sc.t)) > 1e-9
            error('%s : enregistrement des gains non aligne avec le profil.', MDL);
        end
    end
    if any(d < 0.01 - 1e-9 | d > 0.99 + 1e-9)
        error(['%s : le signal qui entre dans le PWM sort de [0.01 ; 0.99] (de %.4f a %.4f). ' ...
               'Il manque la saturation physique devant le PWM.'], MDL, min(d), max(d));
    end
    consigne = 100 + sc.dvref;
    g = grandeurs(v, consigne, d, iL, sc.evenements, TC);
    us = duree_calcul / n_sc * 1e6;
    % mu : sortie du bloc regulateur. Dans les cinq modeles, la sortie du PID
    % (saturation [0.01 ; 0.99] comprise) est l'entree du PWM : mu = d.
    nouveaux(end + 1) = struct('code', sc.code, 'nom', sc.nom, 't', t, 'v', v, 'consigne', consigne, 'mu', d, ...
                               'd', d, 'iL', iL, 'K', K, 'grandeurs', g, 'duree_calcul_s', duree_calcul, ...
                               'us_par_pas', us, 'modele', MDL); %#ok<SAGROW>
    sources{end + 1} = L.source; %#ok<SAGROW>

    fprintf('  temps de calcul : %.1f s (%.1f us par periode du regulateur)\n', duree_calcul, us);
    fprintf('  Simulink : %s\n', resume(g));
    for j = 1:numel(g.evenements)
        ev = g.evenements(j);
        fprintf('    evenement a %6.1f ms : IAE %7.2f mV.s, ecart max %6.2f V, %s\n', ev.t_ms, ev.IAE * 1e3, ...
                ev.e_max_V, texte_retour(ev));
    end
    if ~isempty(K)
        fprintf('  gains finaux [P I D] : [%.5g %.5g %.5g]\n', K(end, :));
    end
    % Comparaison au banc (resultats attendus de la methode)
    if ~isKey(predictions, L.predictions)
        pred = [];
        if isfile(fullfile(pwd, L.predictions))
            pred = jsondecode(fileread(fullfile(pwd, L.predictions)));
            if ~isfield(pred, 'version') || pred.version ~= 2
                warning('%s ne vient pas de la version 2 du banc : pas de comparaison.', L.predictions);
                pred = [];
            end
        end
        predictions(L.predictions) = pred;
    end
    pred = predictions(L.predictions);
    banc_iae(end + 1) = NaN; %#ok<SAGROW>
    if ~isempty(pred) && isfield(pred.essais, L.code)
        gb = pred.essais.(L.code).grandeurs;
        vb = pred.essais.(L.code).v_toutes_les_ms(:);
        vs = v(1:round(1e-3 / TC):end);
        n_cmp = min(numel(vb), numel(vs));
        banc_iae(end) = gb.IAE;
        fprintf('  banc     : %s\n', resume(gb));
        fprintf(['  IAE de 30 ms a la fin : Simulink %.3f, banc %.3f mV.s (%+.1f %%) ; ecart Simulink - banc sur ' ...
                 'Vout (toutes les ms) : %.1f mV efficace, %.1f mV au plus\n'], g.IAE * 1e3, gb.IAE * 1e3, ...
                (g.IAE / gb.IAE - 1) * 100, sqrt(mean((vs(1:n_cmp) - vb(1:n_cmp)).^2)) * 1e3, ...
                max(abs(vs(1:n_cmp) - vb(1:n_cmp))) * 1e3);
        if ~isempty(K) && isfield(pred.essais.(L.code), 'K_toutes_les_ms')
            Kb = pred.essais.(L.code).K_toutes_les_ms;
            Ks = K(1:round(1e-3 / TC):end, :);
            n_k = min(size(Kb, 1), size(Ks, 1));
            fprintf('  gains : ecart relatif maximal Simulink - banc (toutes les ms) %.2g\n', ...
                    max(max(abs(Ks(1:n_k, :) - Kb(1:n_k, :)) ./ abs(Kb(1:n_k, :)))));
        end
        evb = gb.evenements;
        if iscell(evb)
            evb = [evb{:}];
        end
        for j = 1:min(numel(evb), numel(g.evenements))
            fprintf('    evenement a %6.1f ms : IAE %7.2f / %7.2f mV.s ; retour : %s / %s (Simulink / banc)\n', ...
                    g.evenements(j).t_ms, g.evenements(j).IAE * 1e3, evb(j).IAE * 1e3, ...
                    texte_retour(g.evenements(j)), texte_retour(evb(j)));
        end
    end
end

% --- Fichiers : un par modele source, au format de Simuler_<Methode>.m ---
for s = unique(sources, 'stable')
    MODELE = s{1}; %#ok<NASGU>
    fichier = fullfile(pwd, ['resultats_' s{1} '_comparaison.mat']);
    neufs = nouveaux(strcmp(sources, s{1}));
    resultats = neufs;
    if isfile(fichier)                                    % garder les scenarios non resimules
        try
            ancien = load(fichier, 'resultats');
            garde = ancien.resultats(~ismember({ancien.resultats.code}, {neufs.code}));
            resultats = [garde(:)', neufs(:)'];
            rang = zeros(1, numel(resultats));            % ordre de CODES, les autres a la suite
            for q = 1:numel(resultats)
                r_ = find(strcmp(CODES, resultats(q).code), 1);
                if isempty(r_)
                    r_ = numel(CODES) + q;
                end
                rang(q) = r_;
            end
            [~, o] = sort(rang);
            resultats = resultats(o);
            if ~isempty(garde)
                fprintf('\n%s : scenarios gardes de la simulation precedente : %s.\n', fichier, ...
                        strjoin({garde.code}, ', '));
            end
        catch ME
            warning('%s illisible ou d''un autre format (%s) : remplace.', fichier, ME.message);
            resultats = neufs;
        end
    end
    save(fichier, 'resultats', 'MODELE', '-v7.3');
    fprintf('\n%s ecrit (%s).\n', fichier, strjoin({resultats.code}, ', '));
end

% --- Tableau recapitulatif ---
fprintf('\n==========================================================================================\n');
fprintf(' Recapitulatif (Simulink). Les metriques completes : COMPARAISON/metriques/Metriques_Simulink.m,\n');
fprintf(' reglage RESULTATS = ''comparaison''.\n');
fprintf('==========================================================================================\n');
fprintf('  %-14s %-16s %10s %10s %14s %14s %8s\n', 'modele', 'methode', 'calcul s', 'us / Tc', ...
        'IAE30-fin mV.s', 'banc mV.s', 'ecart %');
for i = 1:numel(nouveaux)
    g = nouveaux(i).grandeurs;
    fprintf('  %-14s %-16s %10.1f %10.1f %14.3f %14.3f %8.2f\n', nouveaux(i).modele, liste(i).methode, ...
            nouveaux(i).duree_calcul_s, nouveaux(i).us_par_pas, g.IAE * 1e3, banc_iae(i) * 1e3, ...
            (g.IAE / banc_iae(i) - 1) * 100);
end


%% ===================== Fonctions =====================================

function o = grandeurs(v, consigne, d, iL, evenements, Te)
    % Memes definitions que la fonction grandeurs de banc_commun.py (copie
    % sans changement de Simuler_ELM_PID.m). Les numeros de pas commencent a
    % 0 (comme en Python) ; l'indice MATLAB du pas n est n + 1.
    N = numel(v);
    n = (0:N-1)';
    e = consigne - v;
    k30 = round(0.03 / Te);
    evts = round(evenements(:)' / Te);
    k_dem = min([round(0.05 / Te), evts]);                % fin du demarrage (exclue)
    % Demarrage
    k10 = find(v >= 10, 1);
    k90 = find(v >= 90, 1);
    if isempty(k10) || isempty(k90)
        o.t_montee_ms = NaN;
    else
        o.t_montee_ms = (k90 - k10) * Te * 1e3;
    end
    o.depassement_pct = max(0, (max(v(1:k_dem)) - 100) / 100 * 100);
    hors = find(abs(e(1:k_dem)) > 1);
    if isempty(hors)
        o.t_etab_ms = 0;
    else
        o.t_etab_ms = hors(end) * Te * 1e3;               % (indice Python + 1) x Te
    end
    o.erreur_moy_dem_V = mean(e(k30 + 1:k_dem));
    o.ondulation_V = max(v(k30 + 1:k_dem)) - min(v(k30 + 1:k_dem));
    o.iL_max_dem_A = max(iL(1:k_dem));                    % courant crete du demarrage (observe)
    o.iL_ondulation_A = max(iL(k30 + 1:k_dem)) - min(iL(k30 + 1:k_dem));   % ondulation de courant en regime
    % De 30 ms a la fin
    w = n >= k30;
    o.IAE = sum(abs(e(w))) * Te;
    o.ISE = sum(e(w).^2) * Te;
    o.ITAE = sum(n(w) * Te .* abs(e(w))) * Te;
    o.e_max_V = max(abs(e(w)));
    o.e_eff_V = sqrt(mean(e(w).^2));
    % Evenements
    o.evenements = struct('t_ms', {}, 'IAE', {}, 'e_max_V', {}, 't_retour_ms', {}, 'reste_dans_bande', {}, ...
                          'revenu', {}, 'e_crete_a_crete_fin_V', {}, 'iL_max_A', {}, 'iL_min_A', {});
    bornes = [evts, N];
    n_fin = round(0.010 / Te);                            % 10 dernieres ms de chaque fenetre (2200 instants)
    for j = 1:numel(evts)
        fen = n >= evts(j) & n < bornes(j + 1);           % de l'evenement au suivant
        fin = n >= max(evts(j), bornes(j + 1) - n_fin) & n < bornes(j + 1);   % ses 10 dernieres ms
        hors = find(fen & abs(e) > 1);                    % indices MATLAB des pas hors bande
        revenu = max(abs(e(fin))) <= 1;                   % dans la bande sur les 10 dernieres ms
        if isempty(hors)
            t_ret = 0;                                    % jamais sorti de la bande
        elseif revenu
            t_ret = (hors(end) - evts(j)) * Te * 1e3;     % (indice Python - kj + 1) x Te
        else
            t_ret = NaN;                                  % pas revenu avant l'evenement suivant
        end
        o.evenements(j) = struct('t_ms', evts(j) * Te * 1e3, 'IAE', sum(abs(e(fen))) * Te, ...
                                 'e_max_V', max(abs(e(fen))), 't_retour_ms', t_ret, ...
                                 'reste_dans_bande', isempty(hors), 'revenu', revenu, ...
                                 'e_crete_a_crete_fin_V', max(e(fin)) - min(e(fin)), ...
                                 'iL_max_A', max(iL(fen)), 'iL_min_A', min(iL(fen)));
    end
    % Activite de la commande et conduction discontinue
    dw = d(w);
    o.dd_moyen = mean(abs(diff(dw)));
    o.butee_pct = mean(dw <= 0.01 + 1e-12 | dw >= 0.99 - 1e-12) * 100;
    o.d_ecart_type = std(dw, 1);                          % ecart type "population", comme numpy
    o.dcm_pct = mean(iL(w) < 0.01) * 100;
end

function s = resume(g)
    % Une ligne lisible des grandeurs principales (memes champs que le banc).
    s = sprintf(['montee %.2f ms, depassement %.2f %%, etabli a %.2f ms ; IAE %.2f mV.s, ecart max %.2f V, ' ...
                 'efficace %.1f mV ; |dd| %.4f, butee %.1f %%, DCM %.1f %%'], g.t_montee_ms, g.depassement_pct, ...
                g.t_etab_ms, g.IAE * 1e3, g.e_max_V, g.e_eff_V * 1e3, g.dd_moyen, g.butee_pct, g.dcm_pct);
    if isfield(g, 'iL_max_dem_A')
        s = sprintf('%s ; iL crete au demarrage %.1f A', s, g.iL_max_dem_A);
    end
end

function s = texte_retour(ev)
    % Etat de retour dans la bande d'un evenement (Simulink ou banc).
    if ev.reste_dans_bande
        s = 'reste dans la bande';
    elseif ev.revenu
        s = sprintf('retour en %.2f ms', ev.t_retour_ms);
    else
        s = 'PAS REVENU';
    end
end

function [t, M] = extraire_matrice(sortie, nom)
    % Lit un enregistrement To Workspace d'un signal vectoriel : une ligne
    % par instant, une colonne par composante.
    if ~any(strcmp(sortie.who, nom))
        error('Enregistrement "%s" absent des resultats de simulation.', nom);
    end
    donnee = sortie.get(nom);
    if isa(donnee, 'timeseries')
        t = donnee.Time;
        D = donnee.Data;
    else
        t = donnee.time;
        D = donnee.signals.values;
    end
    t = t(:);
    D = double(squeeze(D));
    if size(D, 1) ~= numel(t)                             % composantes en lignes : on transpose
        D = D.';
    end
    M = D;
end

function [t, v] = extraire_enregistrement(sortie, nom)
    % Lit un enregistrement To Workspace dans l'objet renvoye par sim().
    if ~any(strcmp(sortie.who, nom))
        error('Enregistrement "%s" absent des resultats de simulation.', nom);
    end
    donnee = sortie.get(nom);
    if isa(donnee, 'timeseries')
        t = donnee.Time;
        v = squeeze(donnee.Data);
    else
        t = donnee.time;
        v = squeeze(donnee.signals.values);
    end
    t = t(:);
    v = double(v(:));
end
