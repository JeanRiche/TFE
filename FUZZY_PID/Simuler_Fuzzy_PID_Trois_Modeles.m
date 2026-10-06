%% SIMULER_FUZZY_PID_TROIS_MODELES.m
%
% OBJECTIF
% --------
% Simuler les trois modeles du Fuzzy-PID de Zhao, Tomizuka et Isaka (1993)
% construits sur les modeles de base de Jean-Riche
% (Construction_Fuzzy_PID_Trois_Modeles.m), mesurer les memes grandeurs que
% Simuler_Fuzzy_PID.m, comparer chaque modele a l'essai du banc qui lui
% correspond, tracer une figure par modele et enregistrer les resultats :
%   Fuzzy_PID_Control.slx                     nominal          banc : S1
%   Fuzzy_PID_Control_control_disturbance.slx F1 a la consigne banc : S2
%   Fuzzy_PID_Control_load_disturbance.slx    F2 (4.333 ohms)  banc : S3
%
% VERSION
% -------
% 1 (6 octobre 2026). Copie de Simuler_ELM_PID_Trois_Modeles.m ; changent
% seulement les modeles, le bloc des gains (sortie de "Ordonnanceur Flou
% Zhao" : [P I D]), le bloc dont la sortie est la commande ("PID
% Controller"), les gains de reference (Ziegler-Nichols, forme Parallel)
% et le fichier de predictions.
%
% CE QUI EST ENREGISTRE PENDANT LA SIMULATION
% -------------------------------------------
% Des blocs To Workspace temporaires, ajoutes en memoire et echantillonnes
% a Tc = 1/(22000*10) s : Vout (bloc de mesure "Vout"), rapport cyclique
% (signal qui entre dans le PWM), courant de la bobine (bloc "iL") et gains
% [P I D] (sortie de "Ordonnanceur Flou Zhao"). Les To Workspace propres au modele (y et
% x du modele nominal, au pas du powergui) sont mis en commentaire pendant
% la simulation. Chaque modele est ferme SANS etre enregistre, meme si la
% simulation echoue : les fichiers .slx ne changent pas.
%
% LES GRANDEURS (memes definitions que banc_commun.py et Simuler_Fuzzy_PID.m)
% -------------------------------------------------------------------------
%   Demarrage (0 a 50 ms) : temps de montee 10-90 V, depassement, temps
%   d'etablissement dans +-1 V. De 30 ms a la fin : IAE, ecart maximal,
%   ecart efficace (e = consigne - Vout ; la consigne vaut 100 + F1(t) dans
%   le modele F1). Pour chaque evenement (50 et 70 ms dans F1 et F2) : IAE,
%   ecart maximal, retour dans la bande. Activite de la commande,
%   conduction discontinue, courant crete au demarrage.
%
% CE QU'ON ATTEND
% ---------------
% Les memes resultats que le banc et que Buck_Commun_Fuzzy_PID.slx sur S1,
% S2 et S3, a quelques mV pres, SAUF entre 2 et 6 ms environ, juste apres
% le pic de demarrage : la, un ecart de 1 mV laisse par le circuit est
% amplifie jusqu'a 0.2 V par l'ordonnanceur, puis s'eteint (amendement 1 de
% criteres_fuzzy_pid.txt) ; le depassement, l'IAE apres 30 ms et les
% evenements n'en dependent pas. Les gains changent a chaque pas (ils
% suivent e et De). Deux autres petites differences sont possibles :
%   - modele F2 : 5.001 ohms au lieu de 5 ohms hors de la fenetre ; le banc
%     prevoit +0.1 % d'IAE et une quinzaine de mV au plus d'ecart sur Vout
%     prise toutes les ms, meme avec un modele parfait ;
%   - modele F1 : F1 calcule a partir de l'horloge. En principe il commence
%     et finit exactement a 50 et 70 ms ; si l'horloge accumulait des
%     arrondis, le debut et la fin arriveraient un pas Tc plus tard (le banc
%     prevoit alors +0.6 % d'IAE).
%
% CE QUE PRODUIT CE SCRIPT
% ------------------------
%   - dans la console, un resume par modele et la comparaison au banc ;
%   - une figure par modele : Vout et consigne, rapport cyclique, courant
%     iL, gains (multiples de Ziegler-Nichols) ;
%   - resultats_Fuzzy_PID_Trois_Modeles.mat : meme format que les autres
%     fichiers de resultats (codes S1, S2, S3).
%
% ORDRE D'EXECUTION
% -----------------
%   1. Construction_Fuzzy_PID_Trois_Modeles.m ;
%   2. verifier_modeles_fuzzy_pid_trois.py ; 3. ce script.
%
% Prerequis dans le dossier courant MATLAB : les trois modeles construits,
% ordonnanceur_flou_zhao.m, fuzzy_pid_reglages.mat,
% predictions_banc_fuzzy_pid.json. Duree : deux a cinq minutes. Compatible
% R2024a. N'utilise pas la Fuzzy Logic Toolbox.
% ---------------------------------------------------------------------

clear; clc;

% Modele, essai du banc correspondant, nom, instants des evenements (s), F1 a la consigne ou non
ESSAIS = {'Fuzzy_PID_Control',                     'S1', 'Nominal (ton modele)',          [],           false; ...
          'Fuzzy_PID_Control_control_disturbance', 'S2', 'F1 a la consigne (ton modele)', [0.05, 0.07], true; ...
          'Fuzzy_PID_Control_load_disturbance',    'S3', 'F2 (ton modele)',               [0.05, 0.07], false};
NOM_SYS = 'Ordonnanceur Flou Zhao';               % bloc des gains [P I D]
NOM_PID = 'PID Controller';                       % bloc dont la sortie est la commande
TE = 1/(22000*10);                                % periode des enregistrements (s)
TE_TXT = '1/(22000*10)';                          % la meme, en texte exact
DUREE = 0.2;                                      % duree des trois modeles (s)
K_ZN = [0.093910, 301.089, 7.3227e-6];            % Ziegler-Nichols (champs P, I, D du bloc, forme Parallel)
FICHIER_RESULTATS = 'resultats_Fuzzy_PID_Trois_Modeles.mat';

% --- Prerequis ---
for f = [strcat(ESSAIS(:, 1)', '.slx'), {'ordonnanceur_flou_zhao.m', 'fuzzy_pid_reglages.mat', ...
         'predictions_banc_fuzzy_pid.json'}]
    if ~isfile(fullfile(pwd, f{1}))
        error('Fichier introuvable dans le dossier courant : %s', f{1});
    end
end
pred = jsondecode(fileread(fullfile(pwd, 'predictions_banc_fuzzy_pid.json')));
N = round(DUREE / TE) + 1;                        % instants k*Te, 0 compris (44 001)
t_profil = (0:N-1)' * TE;

resultats = struct('code', {}, 'nom', {}, 'modele', {}, 't', {}, 'v', {}, 'consigne', {}, 'mu', {}, 'd', {}, ...
                   'iL', {}, 'K', {}, 'grandeurs', {}, 'duree_calcul_s', {}, 'us_par_pas', {});
for i = 1:size(ESSAIS, 1)
    mdl = ESSAIS{i, 1}; code = ESSAIS{i, 2}; nom = ESSAIS{i, 3};
    evenements = ESSAIS{i, 4}; avec_f1 = ESSAIS{i, 5};
    fprintf('\n=== %s : %s, compare a %s du banc ===\n', mdl, nom, code);
    if bdIsLoaded(mdl)
        if strcmp(get_param(mdl, 'Dirty'), 'on')
            error('%s est ouvert avec des modifications non enregistrees : l''enregistrer ou le fermer.', mdl);
        end
        close_system(mdl, 0);
    end
    load_system(fullfile(pwd, [mdl '.slx']));
    sys = [mdl '/' NOM_SYS];
    if getSimulinkBlockHandle(sys) == -1
        close_system(mdl, 0);
        error('Bloc introuvable : %s (lancer d''abord Construction_Fuzzy_PID_Trois_Modeles.m).', sys);
    end
    src_pwm = source_entree_pwm(mdl);
    ajouter_enregistrement(mdl, [mdl '/Log Vout sc'], 'sc_log_v', TE_TXT, [mdl '/Vout'], 1);
    ajouter_enregistrement(mdl, [mdl '/Log mu sc'], 'sc_log_mu', TE_TXT, [mdl '/' NOM_PID], 1);
    ajouter_enregistrement(mdl, [mdl '/Log d sc'], 'sc_log_d', TE_TXT, src_pwm.bloc, src_pwm.port);
    ajouter_enregistrement(mdl, [mdl '/Log iL sc'], 'sc_log_iL', TE_TXT, [mdl '/iL'], 1);
    ajouter_enregistrement(mdl, [mdl '/Log K sc'], 'sc_log_K', TE_TXT, sys, 1);
    neutraliser_enregistrements_modele(mdl);
    t_debut = tic;
    try
        % StopTime : un demi-pas apres le dernier instant, pour que cet
        % instant soit enregistre quels que soient les arrondis.
        sortie = sim(mdl, 'StopTime', sprintf('%.17g', (N - 0.5) * TE), 'ReturnWorkspaceOutputs', 'on');
    catch ME
        close_system(mdl, 0);
        rethrow(ME);
    end
    duree_calcul = toc(t_debut);
    close_system(mdl, 0);                         % SANS enregistrer

    [t, v]    = extraire_enregistrement(sortie, 'sc_log_v');
    [t2, mu]  = extraire_enregistrement(sortie, 'sc_log_mu');
    [t3, d]   = extraire_enregistrement(sortie, 'sc_log_d');
    [t4, iL]  = extraire_enregistrement(sortie, 'sc_log_iL');
    [tk, K]   = extraire_matrice(sortie, 'sc_log_K');   % une ligne par instant, une colonne par gain
    if min([numel(t), numel(t2), numel(t3), numel(t4), numel(tk)]) < N
        error('%s : enregistrements trop courts (%d instants attendus).', mdl, N);
    end
    t = t(1:N); v = v(1:N); mu = mu(1:N); d = d(1:N); iL = iL(1:N); K = K(1:N, :);
    if max(abs([t - t_profil; t2(1:N) - t_profil; t3(1:N) - t_profil; t4(1:N) - t_profil; tk(1:N) - t_profil])) > 1e-9
        error('%s : enregistrements non alignes sur les instants k*Te.', mdl);
    end
    if any(d < 0.01 - 1e-9 | d > 0.99 + 1e-9)
        error('%s : le signal qui entre dans le PWM sort de [0.01 ; 0.99].', mdl);
    end
    % Consigne vue par le regulateur : 100 V, plus F1(t) dans le modele F1
    % (meme formule que le bloc MATLAB Function du modele). Les instants de
    % la fenetre sont pris par numero de pas, k de 11 000 a 15 399, comme
    % dans l'essai S2 du banc, pour ne pas dependre d'un arrondi sur t.
    consigne = 100 * ones(N, 1);
    if avec_f1
        k_pas = (0:N-1)';
        dans_f1 = k_pas >= round(0.05 / TE) & k_pas < round(0.07 / TE);
        consigne(dans_f1) = 100 + 2 * exp(cos(10 * pi * t_profil(dans_f1)));
    end
    g = grandeurs(v, consigne, d, iL, evenements, TE);
    resultats(end + 1) = struct('code', code, 'nom', nom, 'modele', mdl, 't', t, 'v', v, 'consigne', consigne, ...
                                'mu', mu, 'd', d, 'iL', iL, 'K', K, 'grandeurs', g, 'duree_calcul_s', duree_calcul, ...
                                'us_par_pas', duree_calcul / N * 1e6); %#ok<SAGROW>
    fprintf('  Simulink : %s\n', resume(g));
    fprintf('  temps de calcul : %.1f s ; gains finaux [%.5f %.4f %.4e] (Ziegler-Nichols [%.5f %.4f %.4e])\n', ...
            duree_calcul, K(end, 1), K(end, 2), K(end, 3), K_ZN(1), K_ZN(2), K_ZN(3));
    for j = 1:numel(g.evenements)
        ev = g.evenements(j);
        fprintf('    evenement a %5.1f ms : IAE %6.2f mV.s, ecart max %5.2f V, retour : %s ; iL de %.1f a %.1f A\n', ...
                ev.t_ms, ev.IAE * 1e3, ev.e_max_V, texte_retour(ev), ev.iL_min_A, ev.iL_max_A);
    end

    % Comparaison au banc
    gb = pred.essais.(code).grandeurs;
    pas_1ms = round(1e-3 / TE);
    vb = pred.essais.(code).v_toutes_les_ms(:);
    vs = v(1:pas_1ms:end);
    n_cmp = min(numel(vb), numel(vs));
    ib = pred.essais.(code).iL_toutes_les_ms(:);
    is = iL(1:pas_1ms:end);
    n_i = min(numel(ib), numel(is));
    Kb = pred.essais.(code).K_toutes_les_ms;
    Ks = K(1:pas_1ms:end, :);
    n_k = min(size(Kb, 1), size(Ks, 1));
    fprintf('  banc     : %s\n', resume(gb));
    fprintf('  ecart Simulink - banc sur Vout (toutes les ms) : %.1f mV efficace, %.1f mV au plus\n', ...
            sqrt(mean((vs(1:n_cmp) - vb(1:n_cmp)).^2)) * 1e3, max(abs(vs(1:n_cmp) - vb(1:n_cmp))) * 1e3);
    fprintf('  IAE : Simulink %.2f, banc %.2f mV.s (%+.1f %%) ; courant iL : ecart %.1f mA efficace ; gains : ecart relatif maximal %.2g\n', ...
            g.IAE * 1e3, gb.IAE * 1e3, (g.IAE / gb.IAE - 1) * 100, ...
            sqrt(mean((is(1:n_i) - ib(1:n_i)).^2)) * 1e3, ...
            max(max(abs(Ks(1:n_k, :) - Kb(1:n_k, :)) ./ abs(Kb(1:n_k, :)))));
    evb = gb.evenements;                          % structure, cellule ou vide selon jsondecode
    if iscell(evb)
        evb = [evb{:}];
    end
    for j = 1:min(numel(evb), numel(g.evenements))
        fprintf('    evenement a %5.1f ms : IAE %6.2f / %6.2f mV.s ; ecart max %5.2f / %5.2f V ; retour : %s / %s (Simulink / banc)\n', ...
                g.evenements(j).t_ms, g.evenements(j).IAE * 1e3, evb(j).IAE * 1e3, g.evenements(j).e_max_V, ...
                evb(j).e_max_V, texte_retour(g.evenements(j)), texte_retour(evb(j)));
    end

    % Figure
    fig = figure('Name', mdl, 'Color', 'w', 'Position', [60 40 1100 820]);
    tl = tiledlayout(fig, 4, 1, 'TileSpacing', 'compact', 'Padding', 'compact');
    title(tl, sprintf('%s : %s (Fuzzy-PID de Zhao)', mdl, nom), 'Interpreter', 'none');
    t_ms = t * 1e3;
    ax = gobjects(1, 4);
    for p = 1:4
        ax(p) = nexttile(tl);
        hold(ax(p), 'on');
        grid(ax(p), 'on');
        for k = 1:numel(evenements)
            xline(ax(p), evenements(k) * 1e3, ':', 'Color', [0.5 0.5 0.5], 'HandleVisibility', 'off');
        end
    end
    plot(ax(1), t_ms, v, 'LineWidth', 0.8, 'DisplayName', 'Vout');
    plot(ax(1), t_ms, consigne, 'k--', 'LineWidth', 0.8, 'DisplayName', 'consigne');
    legend(ax(1), 'Location', 'best');
    ylabel(ax(1), 'Vout (V)');
    plot(ax(2), t_ms, d, 'LineWidth', 0.6);
    ylabel(ax(2), 'rapport cyclique');
    plot(ax(3), t_ms, iL, 'LineWidth', 0.6);
    ylabel(ax(3), 'iL (A)');
    plot(ax(4), t_ms, K(:, 1) / K_ZN(1), '-', 'LineWidth', 1.0, 'DisplayName', 'P');
    plot(ax(4), t_ms, K(:, 2) / K_ZN(2), '--', 'LineWidth', 1.0, 'DisplayName', 'I');
    plot(ax(4), t_ms, K(:, 3) / K_ZN(3), ':', 'LineWidth', 1.0, 'DisplayName', 'D');
    legend(ax(4), 'Location', 'best');
    ylabel(ax(4), 'gains / ZN');
    xlabel(ax(4), 'temps (ms)');
    linkaxes(ax, 'x');
    xlim(ax(1), [0, DUREE * 1e3]);
end

save(fullfile(pwd, FICHIER_RESULTATS), 'resultats', '-v7.3');
fprintf('\n%s ecrit.\n', FICHIER_RESULTATS);

% --- Tableau recapitulatif ---
fprintf('\n  %-38s %5s %9s %9s %10s %9s %9s %9s\n', 'modele', 'banc', 'depass.%', 'etabli ms', 'IAE mV.s', ...
        'e max V', 'e eff mV', 'iL dem A');
for i = 1:numel(resultats)
    g = resultats(i).grandeurs;
    fprintf('  %-38s %5s %9.2f %9.2f %10.2f %9.2f %9.1f %9.2f\n', resultats(i).modele, resultats(i).code, ...
            g.depassement_pct, g.t_etab_ms, g.IAE * 1e3, g.e_max_V, g.e_eff_V * 1e3, g.iL_max_dem_A);
end


%% ===================== Fonctions =====================================

function o = grandeurs(v, consigne, d, iL, evenements, Te)
    % Memes definitions que la fonction grandeurs de banc_commun.py (copie
    % de Simuler_ELM_PID.m, la meme que Simuler_Fuzzy_PID.m). Les numeros de pas commencent a 0 (comme en
    % Python) ; l'indice MATLAB du pas n est n + 1.
    N = numel(v);
    n = (0:N-1)';
    e = consigne - v;
    k30 = round(0.03 / Te);
    evts = round(evenements(:)' / Te);
    k_dem = min([round(0.05 / Te), evts]);                % fin du demarrage (exclue)
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
    o.iL_ondulation_A = max(iL(k30 + 1:k_dem)) - min(iL(k30 + 1:k_dem));
    w = n >= k30;
    o.IAE = sum(abs(e(w))) * Te;
    o.ISE = sum(e(w).^2) * Te;
    o.ITAE = sum(n(w) * Te .* abs(e(w))) * Te;
    o.e_max_V = max(abs(e(w)));
    o.e_eff_V = sqrt(mean(e(w).^2));
    o.evenements = struct('t_ms', {}, 'IAE', {}, 'e_max_V', {}, 't_retour_ms', {}, 'reste_dans_bande', {}, ...
                          'revenu', {}, 'e_crete_a_crete_fin_V', {}, 'iL_max_A', {}, 'iL_min_A', {});
    bornes = [evts, N];
    n_fin = round(0.010 / Te);                            % 10 dernieres ms de chaque fenetre
    for j = 1:numel(evts)
        fen = n >= evts(j) & n < bornes(j + 1);
        fin = n >= max(evts(j), bornes(j + 1) - n_fin) & n < bornes(j + 1);
        hors = find(fen & abs(e) > 1);
        revenu = max(abs(e(fin))) <= 1;
        if isempty(hors)
            t_ret = 0;
        elseif revenu
            t_ret = (hors(end) - evts(j)) * Te * 1e3;
        else
            t_ret = NaN;
        end
        o.evenements(j) = struct('t_ms', evts(j) * Te * 1e3, 'IAE', sum(abs(e(fen))) * Te, ...
                                 'e_max_V', max(abs(e(fen))), 't_retour_ms', t_ret, ...
                                 'reste_dans_bande', isempty(hors), 'revenu', revenu, ...
                                 'e_crete_a_crete_fin_V', max(e(fin)) - min(e(fin)), ...
                                 'iL_max_A', max(iL(fen)), 'iL_min_A', min(iL(fen)));
    end
    dw = d(w);
    o.dd_moyen = mean(abs(diff(dw)));
    o.butee_pct = mean(dw <= 0.01 + 1e-12 | dw >= 0.99 - 1e-12) * 100;
    o.d_ecart_type = std(dw, 1);
    o.dcm_pct = mean(iL(w) < 0.01) * 100;
end

function s = resume(g)
    % Une ligne lisible des grandeurs principales (memes champs que le banc).
    s = sprintf(['montee %.2f ms, depassement %.2f %%, etabli a %.2f ms ; IAE %.2f mV.s, ecart max %.2f V, ' ...
                 'efficace %.1f mV ; |dd| %.4f, DCM %.1f %% ; iL crete au demarrage %.1f A'], g.t_montee_ms, ...
                g.depassement_pct, g.t_etab_ms, g.IAE * 1e3, g.e_max_V, g.e_eff_V * 1e3, g.dd_moyen, ...
                g.dcm_pct, g.iL_max_dem_A);
end

function s = texte_retour(ev)
    % Etat de retour dans la bande d'un evenement (Simulink ou banc).
    if ev.reste_dans_bande
        s = 'dans la bande';
    elseif ev.revenu
        s = sprintf('%.2f ms', ev.t_retour_ms);
    else
        s = 'pas revenu';
    end
end

function s = source_entree_pwm(mdl)
    % Bloc et numero de port qui alimentent l'entree du PWM Generator.
    pwm = [mdl '/' sprintf('PWM Generator\n(DC-DC)')];  % regle #1 : vrai saut de ligne
    if getSimulinkBlockHandle(pwm) == -1
        error('PWM Generator (DC-DC) introuvable dans %s.', mdl);
    end
    ph = get_param(pwm, 'PortHandles');
    ligne = get_param(ph.Inport(1), 'Line');
    if ligne == -1
        error('L''entree du PWM n''est reliee a rien dans %s.', mdl);
    end
    s.bloc = getfullname(get_param(ligne, 'SrcBlockHandle'));
    s.port = get_param(get_param(ligne, 'SrcPortHandle'), 'PortNumber');
end

function neutraliser_enregistrements_modele(mdl)
    % Met en commentaire, en memoire seulement, les blocs To Workspace de
    % premier niveau qui ne sont pas les enregistrements de ce script.
    blocs = find_system(mdl, 'SearchDepth', 1, 'BlockType', 'ToWorkspace');
    for i = 1:numel(blocs)
        if ~startsWith(get_param(blocs{i}, 'VariableName'), 'sc_log_')
            set_param(blocs{i}, 'Commented', 'on');
        end
    end
end

function relier(mdl, bloc_src, port_src, bloc_dst, port_dst)
    % Ligne de signal entre deux ports (handles demandes au moment meme).
    ph_src = get_param(bloc_src, 'PortHandles');
    ph_dst = get_param(bloc_dst, 'PortHandles');
    add_line(mdl, ph_src.Outport(port_src), ph_dst.Inport(port_dst), 'autorouting', 'on');
end

function ajouter_enregistrement(mdl, chemin, variable, Te_txt, bloc_src, port_src)
    % Bloc To Workspace temporaire (MaxDataPoints = inf), echantillonne a
    % Te_txt (texte exact).
    if getSimulinkBlockHandle(chemin) ~= -1
        delete_block(chemin);
    end
    pos = get_param(bloc_src, 'Position');
    add_block('simulink/Sinks/To Workspace', chemin, 'Position', [pos(3)+120, pos(2)+40, pos(3)+200, pos(2)+65]);
    set_param(chemin, 'VariableName', variable, 'SaveFormat', 'Timeseries', ...
              'SampleTime', Te_txt, 'MaxDataPoints', 'inf');
    relier(mdl, bloc_src, port_src, chemin, 1);
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
