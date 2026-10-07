%% CONSTRUCTION_PINN_PID_TROIS_MODELES.m
%
% OBJECTIF
% --------
% Construire, pour le PINN-PID, un modele Simulink par scenario de
% base, a partir des trois modeles de Jean-Riche :
%   PID_Classique_Control.slx                     -> PINN_PID_Control.slx
%   PID_Classique_Control_control_disturbance.slx -> PINN_PID_Control_control_disturbance.slx
%   PID_Classique_Control_load_disturbance.slx    -> PINN_PID_Control_load_disturbance.slx
% Dans chaque copie, seul le bloc "PID Controller" est remplace par le
% bloc du PINN-PID. Tout le reste (circuit, source 200 V, charge, F1
% calcule par le bloc MATLAB Function, F2 par l'interrupteur ideal, Scope,
% configuration) reste celui du modele de Jean-Riche : on ouvre le modele
% construit et on clique sur Run, comme pour le PID classique.
%
% VERSION
% -------
% 1 (5 octobre 2026), PINN-PID (etapes 1 a 4 sur la base commune
% v2.1). Meme bloc, memes reglages et meme facon de remplacer le PID que
% Construction_PINN_PID.m, qui construit Buck_Commun_PINN_PID.slx ; seule la
% source de la mesure change : ici, la sortie du bloc de mesure "Vout"
% (ces modeles n'ont ni bruit ni quantification de la mesure).
%
% POURQUOI CES TROIS MODELES, EN PLUS DE Buck_Commun_PINN_PID.slx
% ---------------------------------------------------------------
% Ils sont construits sur les fichiers de Jean-Riche, sans profils lus dans
% le workspace : chacun se simule seul, d'un clic. Ils servent aussi de
% controle croise : sur les essais S1 (nominal), S2 (F1) et S3 (F2), ils
% doivent redonner les resultats du banc et de Buck_Commun_PINN_PID.slx.
% Deux petites differences sont possibles : dans ton modele F2, la charge
% vaut 5.001 ohms hors de la fenetre (interrupteur ferme, Ron = 1 mohm en
% parallele sur -0.667 ohm) au lieu de 5 ohms (effet prevu par le banc :
% +0.1 % d'IAE, une quinzaine de mV au plus sur Vout) ; dans ton modele F1,
% F1(t) est calcule a partir de l'horloge. En principe F1 commence et finit
% exactement a 50 et 70 ms (11 000 x Tc et 15 400 x Tc valent 0.05 et 0.07
% en double precision) ; si l'horloge accumulait des arrondis, le debut et
% la fin arriveraient un pas Tc plus tard (effet prevu : +0.6 % d'IAE).
%
% CE QUE LE SCRIPT CHANGE DANS CHAQUE COPIE, ET RIEN D'AUTRE
% -----------------------------------------------------------
%   1. Le bloc "PID Controller" et ses deux liaisons sont supprimes.
%   2. Deux Zero-Order Hold a Tc = 1/(22000*10) s (texte exact) :
%      "Echantillonneur Erreur PINN", alimente par Sum1 (l'erreur, comme
%      l'etait le PID), et "Echantillonneur Mesure PINN", alimente par la
%      sortie du bloc de mesure "Vout" (une branche de plus sur la meme
%      liaison ; Sum1, le Goto et le To Workspace restent alimentes).
%   3. "PINN-PID Adaptatif" (MATLAB System, classe pinn_pid_adaptatif,
%      execution interpretee) recoit l'erreur et la mesure ; sa sortie 1
%      (rapport cyclique, deja borne a [0.01 ; 0.99]) alimente le PWM comme
%      le faisait le PID ; sa sortie 2 (les gains Kp, Ki, Kd) va dans
%      "Terminaison Gains PINN" (Terminator). Simuler_PINN_PID_Trois_Modeles.m
%      enregistre cette sortie et trace les gains.
% La configuration de simulation n'est pas touchee. Les modeles de
% Jean-Riche ne sont jamais modifies : chaque modele est construit a partir
% d'une copie.
%
% LES AUTO-TESTS (apres la sauvegarde)
% -------------------------------------
% Pour chaque modele construit : 20 ms de simulation, Vout toutes les ms
% comparee au banc (predictions_banc_pinn_pid.json, essais S1, S2 et S3 :
% avant 50 ms, les trois essais sont le demarrage nominal), ecart maximal
% tolere 0.05 V ; gains a la fin du test affiches a cote de ceux du banc
% au meme instant (le PINN-PID adapte ses gains sur quelques fenetres
% pendant le demarrage nominal). Les auto-tests ne remplacent pas
% verifier_modeles_pinn_pid_trois.py.
%
% REGLES APPLIQUEES : #7 et #17 (add_line avec des handles demandes au
% dernier moment), #16 (on ne supprime que les lignes du bloc PID), #20
% (copie fraiche, un seul exemplaire de chaque fichier sur le chemin).
%
% ORDRE D'EXECUTION
% -----------------
%   1. ce script ; 2. verifier_modeles_pinn_pid_trois.py ;
%   3. Simuler_PINN_PID_Trois_Modeles.m.
%
% Prerequis dans le dossier courant MATLAB : les trois modeles de base
% ci-dessus, pinn_pid_adaptatif.m, pinn_pid_modele.mat, pinn_pid_reglages.mat, ensemble_gains_pinn.mat
% et predictions_banc_pinn_pid.json (PINN-PID).
% Duree : deux a cinq minutes (trois constructions et trois auto-tests).
% Compatible R2024a.
% ---------------------------------------------------------------------

clear; clc;

% Modele de base, modele construit, essai du banc qui lui correspond
MODELES = {'PID_Classique_Control',                     'PINN_PID_Control',                     'S1'; ...
           'PID_Classique_Control_control_disturbance', 'PINN_PID_Control_control_disturbance', 'S2'; ...
           'PID_Classique_Control_load_disturbance',    'PINN_PID_Control_load_disturbance',    'S3'};
TC_TXT = '1/(22000*10)';                          % periode du regulateur (texte exact)
TC     = 1/(22000*10);                            % la meme, en nombre (s)
CLASSE = 'pinn_pid_adaptatif';                     % classe du bloc MATLAB System
NOM_SYS  = 'PINN-PID Adaptatif';
NOM_ZOHE = 'Echantillonneur Erreur PINN';
NOM_ZOHM = 'Echantillonneur Mesure PINN';
NOM_TERM = 'Terminaison Gains PINN';
PWM      = sprintf('PWM Generator\n(DC-DC)');     % regle #1 : vrai saut de ligne
DUREE_TEST = 0.020;                               % duree des auto-tests (s)
TOLERANCE_TEST = 0.05;                            % ecart maximal au banc (V)

% --- Prerequis ---
for f = [strcat(MODELES(:, 1)', '.slx'), {[CLASSE '.m'], 'pinn_pid_modele.mat', 'pinn_pid_reglages.mat', ...
         'ensemble_gains_pinn.mat', 'predictions_banc_pinn_pid.json'}]
    if ~isfile(fullfile(pwd, f{1}))
        error('Fichier introuvable dans le dossier courant : %s', f{1});
    end
    if numel(which(f{1}, '-all')) > 1
        error('Il doit exister un seul %s sur le chemin MATLAB : %s', f{1}, strjoin(which(f{1}, '-all'), ', '));
    end
end
for i = 1:size(MODELES, 1)
    base = MODELES{i, 1};
    if bdIsLoaded(base) && strcmp(get_param(base, 'Dirty'), 'on')
        error('%s est ouvert avec des modifications non enregistrees : l''enregistrer ou le fermer.', base);
    end
    for m = MODELES(i, 1:2)
        if bdIsLoaded(m{1})
            close_system(m{1}, 0);                % fermer sans enregistrer
        end
    end
end
clear(CLASSE);                                    % recharger la classe si elle a change

for i = 1:size(MODELES, 1)
    SOURCE = MODELES{i, 1};
    MDL = MODELES{i, 2};
    fprintf('\n=== %s -> %s ===\n', SOURCE, MDL);

    %% 1. Copie fraiche
    chemin = fullfile(pwd, [MDL '.slx']);
    if isfile(chemin)
        delete(chemin);
        fprintf('Ancien %s.slx supprime (on repart toujours d''une copie fraiche).\n', MDL);
    end
    copyfile(fullfile(pwd, [SOURCE '.slx']), chemin);
    if numel(which([MDL '.slx'], '-all')) ~= 1
        error('Il doit exister exactement un %s.slx sur le chemin MATLAB.', MDL);
    end
    load_system(chemin);
    fprintf('Copie de %s.slx chargee sous le nom %s.\n', SOURCE, MDL);

    %% 2. Controle du circuit de base (meme circuit que la base commune v2)
    controler_base(MDL, SOURCE);

    %% 3. Le PID, sa source, sa destination et la mesure
    pid = [MDL '/PID Controller'];
    mesure = [MDL '/Vout'];
    for b = {pid, mesure, [MDL '/Sum1'], [MDL '/' PWM]}
        if getSimulinkBlockHandle(b{1}) == -1
            close_system(MDL, 0);
            error('Bloc introuvable : %s', strrep(b{1}, newline, ' '));
        end
    end
    lh = get_param(pid, 'LineHandles');
    [src_err, ~] = extremites_ligne(lh.Inport(1));    % ce qui alimente le PID (Sum1, sortie 1)
    [~, dst_cmd] = extremites_ligne(lh.Outport(1));   % ce que le PID alimente (entree du PWM)
    if ~strcmp(src_err.bloc, [MDL '/Sum1']) || numel(dst_cmd) ~= 1 || ~strcmp(dst_cmd(1).bloc, [MDL '/' PWM])
        close_system(MDL, 0);
        error('%s : le PID devrait etre alimente par Sum1 et alimenter seulement le PWM.', SOURCE);
    end
    lm = get_param(mesure, 'LineHandles');
    [~, dst_m] = extremites_ligne(lm.Outport(1));     % la mesure doit aller sur l'entree 2 (-) de Sum1
    if ~any(arrayfun(@(d) strcmp(d.bloc, [MDL '/Sum1']) && d.port == 2, dst_m))
        close_system(MDL, 0);
        error('%s : la sortie du bloc "Vout" devrait alimenter l''entree 2 (-) de Sum1.', SOURCE);
    end

    %% 4. Remplacement du PID par le PINN-PID
    pos = get_param(pid, 'Position');             % [gauche haut droite bas]
    delete_line(lh.Inport(1));                    % lignes du PID seulement (regle #16)
    delete_line(lh.Outport(1));
    delete_block(pid);

    zohe = [MDL '/' NOM_ZOHE];
    zohm = [MDL '/' NOM_ZOHM];
    sys = [MDL '/' NOM_SYS];
    term = [MDL '/' NOM_TERM];
    add_block('simulink/Discrete/Zero-Order Hold', zohe, 'Position', [pos(1)-110, pos(2), pos(1)-70, pos(2)+30]);
    add_block('simulink/Discrete/Zero-Order Hold', zohm, 'Position', [pos(1)-110, pos(4)+20, pos(1)-70, pos(4)+50]);
    set_param(zohe, 'SampleTime', TC_TXT);
    set_param(zohm, 'SampleTime', TC_TXT);
    add_block('simulink/User-Defined Functions/MATLAB System', sys, 'Position', [pos(1), pos(2), pos(3)+40, pos(4)+40]);
    set_param(sys, 'System', CLASSE);
    set_param(sys, 'SimulateUsing', 'Interpreted execution');
    ph = get_param(sys, 'PortHandles');
    if numel(ph.Inport) ~= 2 || numel(ph.Outport) ~= 2
        close_system(MDL, 0);
        error('Le bloc %s devrait avoir 2 entrees et 2 sorties (il en a %d et %d).', NOM_SYS, ...
              numel(ph.Inport), numel(ph.Outport));
    end
    add_block('simulink/Sinks/Terminator', term, 'Position', [pos(3)+90, pos(4)+20, pos(3)+110, pos(4)+40]);

    relier(MDL, src_err.bloc, src_err.port, zohe, 1);   % Sum1 -> echantillonneur de l'erreur
    relier(MDL, mesure, 1, zohm, 1);                    % Vout -> echantillonneur (branche)
    relier(MDL, zohe, 1, sys, 1);
    relier(MDL, zohm, 1, sys, 2);
    relier(MDL, sys, 1, dst_cmd(1).bloc, dst_cmd(1).port);   % rapport cyclique -> PWM
    relier(MDL, sys, 2, term, 1);                       % gains -> terminaison
    fprintf('PID remplace par "%s" (%s, execution interpretee), alimente par l''erreur et Vout echantillonnees a %s s.\n', ...
            NOM_SYS, CLASSE, TC_TXT);

    %% 5. Sauvegarde (configuration de simulation non touchee)
    save_system(MDL);
    close_system(MDL, 0);
    fprintf('%s.slx sauvegarde.\n', MDL);
end

%% 6. Auto-tests
fprintf('\n=== Auto-tests (%.0f ms par modele) ===\n', DUREE_TEST * 1e3);
pred = jsondecode(fileread(fullfile(pwd, 'predictions_banc_pinn_pid.json')));
pas_1ms = round(1e-3 / TC);                       % 220 periodes Tc
for i = 1:size(MODELES, 1)
    MDL = MODELES{i, 2};
    code = MODELES{i, 3};
    r = simuler_court(MDL, NOM_SYS, DUREE_TEST);
    vb = pred.essais.(code).v_toutes_les_ms(:);
    vs = r.v(1:pas_1ms:end);
    n = min(numel(vs), numel(vb));
    ecart = max(abs(vs(1:n) - vb(1:n)));
    Kb = pred.essais.(code).K_toutes_les_ms;      % gains du banc toutes les ms
    Ks = r.K(1 + (n - 1) * pas_1ms, :);           % gains a (n-1) ms, meme instant que Kb(n, :)
    fprintf(['  %s : ecart maximal au banc (%s) sur Vout toutes les ms %.1f mV ; Vout maximal %.2f V ; ' ...
             'gains a %d ms [%.5f %.4e %.4f] (banc [%.5f %.4e %.4f])\n'], ...
            MDL, code, ecart * 1e3, max(r.v), n - 1, Ks(1), Ks(2), Ks(3), Kb(n, 1), Kb(n, 2), Kb(n, 3));
    if ~(ecart <= TOLERANCE_TEST)
        error('%s : ecart au banc de %.3f V, au-dela de %.2f V : verifier la construction.', MDL, ecart, TOLERANCE_TEST);
    end
end
fprintf(['\nLes trois modeles sont construits et leurs auto-tests sont passes :\n' ...
         '  %s.slx, %s.slx, %s.slx\n' ...
         'Lance maintenant verifier_modeles_pinn_pid_trois.py.\n'], MODELES{:, 2});


%% ===================== Fonctions =====================================

function controler_base(mdl, source)
    % Le modele de base doit etre le circuit de la base commune v2 (celui du
    % banc) : snubber de la diode supprime, L = 10 mH, C = 47 uF, MLI a
    % 22 kHz, powergui discret a 1/(22000*1200) s, PID a 1/(22000*10) s.
    % Sinon, les resultats ne seraient pas comparables au banc.
    pb = {};
    diode = [mdl '/Diode'];
    if getSimulinkBlockHandle(diode) == -1
        pb{end+1} = 'bloc Diode introuvable';
    else
        rs = str2double(strtrim(get_param(diode, 'Rs')));
        cs = str2double(strtrim(get_param(diode, 'Cs')));
        if ~(isinf(rs) || cs == 0)
            pb{end+1} = 'snubber de la diode actif (ecrire inf dans "Snubber resistance Rs")';
        end
    end
    attendus = {[mdl '/Series RLC Branch'], 'Inductance', 10e-3; ...
                [mdl '/Series RLC Branch1'], 'Capacitance', 47e-6; ...
                [mdl '/' sprintf('PWM Generator\n(DC-DC)')], 'Fsw', 22000};
    for k = 1:size(attendus, 1)
        if getSimulinkBlockHandle(attendus{k, 1}) == -1
            pb{end+1} = sprintf('bloc %s introuvable', strrep(attendus{k, 1}, newline, ' ')); %#ok<AGROW>
        else
            valeur = str2double(strtrim(get_param(attendus{k, 1}, attendus{k, 2})));
            if ~(abs(valeur - attendus{k, 3}) <= 1e-9 * attendus{k, 3})
                pb{end+1} = sprintf('%s = %s au lieu de %g', attendus{k, 2}, ...
                                    get_param(attendus{k, 1}, attendus{k, 2}), attendus{k, 3}); %#ok<AGROW>
            end
        end
    end
    if ~strcmp(strtrim(get_param([mdl '/powergui'], 'SampleTime')), '1/(22000*1200)')
        pb{end+1} = 'pas du powergui different de 1/(22000*1200)';
    end
    if ~strcmp(strtrim(get_param([mdl '/PID Controller'], 'SampleTime')), '1/(22000*10)')
        pb{end+1} = 'periode du PID differente de 1/(22000*10)';
    end
    if ~isempty(pb)
        close_system(mdl, 0);
        error('%s.slx n''est pas le circuit de la base commune v2 : %s.', source, strjoin(pb, ' ; '));
    end
    fprintf('Circuit de %s.slx controle (diode sans snubber, 10 mH, 47 uF, 22 kHz, pas exacts).\n', source);
end

function r = simuler_court(mdl, nom_sys, duree)
    % Simulation avec enregistrements temporaires (Vout et gains), modele
    % ferme SANS enregistrer, meme en cas d'erreur.
    load_system(fullfile(pwd, [mdl '.slx']));
    ajouter_enregistrement(mdl, [mdl '/Log Vout tmp'], 'tmp_v', [mdl '/Vout'], 1);
    ajouter_enregistrement(mdl, [mdl '/Log K tmp'], 'tmp_K', [mdl '/' nom_sys], 2);
    blocs = find_system(mdl, 'SearchDepth', 1, 'BlockType', 'ToWorkspace');
    for i = 1:numel(blocs)                        % journaux d'origine neutralises en memoire
        if ~startsWith(get_param(blocs{i}, 'VariableName'), 'tmp_')
            set_param(blocs{i}, 'Commented', 'on');
        end
    end
    try
        sortie = sim(mdl, 'StopTime', sprintf('%.17g', duree - 0.5 * 1/(22000*10)), ...
                     'ReturnWorkspaceOutputs', 'on', 'SaveTime', 'off');
    catch ME
        close_system(mdl, 0);
        rethrow(ME);
    end
    close_system(mdl, 0);
    r.v = lire(sortie, 'tmp_v');
    K = lire(sortie, 'tmp_K');
    if size(K, 2) ~= 3                            % composantes en lignes : on transpose
        K = K.';
    end
    r.K = K;
end

function M = lire(sortie, nom)
    % Lit un enregistrement To Workspace (scalaire ou vecteur) dans l'objet renvoye par sim().
    if ~any(strcmp(sortie.who, nom))
        error('Enregistrement "%s" absent des resultats de simulation.', nom);
    end
    donnee = sortie.get(nom);
    if isa(donnee, 'timeseries')
        M = double(squeeze(donnee.Data));
    else
        M = double(squeeze(donnee.signals.values));
    end
    if isvector(M)
        M = M(:);
    end
end

function [src, dst] = extremites_ligne(ligne)
    % Source et destinations d'une ligne de signal (regle #18 : les -1
    % sont filtres).
    h_sb = get_param(ligne, 'SrcBlockHandle');
    h_sp = get_param(ligne, 'SrcPortHandle');
    src = struct('bloc', getfullname(h_sb), 'port', get_param(h_sp, 'PortNumber'));
    h_db = get_param(ligne, 'DstBlockHandle');
    h_dp = get_param(ligne, 'DstPortHandle');
    dst = struct('bloc', {}, 'port', {});
    for i = 1:numel(h_db)
        if h_db(i) ~= -1 && h_dp(i) ~= -1
            dst(end+1) = struct('bloc', getfullname(h_db(i)), 'port', get_param(h_dp(i), 'PortNumber')); %#ok<AGROW>
        end
    end
end

function relier(mdl, bloc_src, port_src, bloc_dst, port_dst)
    % Ligne de signal entre deux ports, handles demandes au moment meme.
    ph_src = get_param(bloc_src, 'PortHandles');
    ph_dst = get_param(bloc_dst, 'PortHandles');
    add_line(mdl, ph_src.Outport(port_src), ph_dst.Inport(port_dst), 'autorouting', 'on');
end

function ajouter_enregistrement(mdl, chemin, variable, bloc_src, port_src)
    % Bloc To Workspace temporaire a Tc (texte exact), MaxDataPoints = inf.
    pos = get_param(bloc_src, 'Position');
    add_block('simulink/Sinks/To Workspace', chemin, 'Position', [pos(3)+120, pos(2)+40, pos(3)+200, pos(2)+65]);
    set_param(chemin, 'VariableName', variable, 'SaveFormat', 'Timeseries', ...
              'SampleTime', '1/(22000*10)', 'MaxDataPoints', 'inf');
    relier(mdl, bloc_src, port_src, chemin, 1);
end
