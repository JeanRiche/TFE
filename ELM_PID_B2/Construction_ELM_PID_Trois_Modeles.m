%% CONSTRUCTION_ELM_PID_TROIS_MODELES.m
%
% OBJECTIF
% --------
% Construire, pour l'ELM-PID (option B), un modele Simulink par scenario
% de base, a partir des trois modeles de Jean-Riche :
%   PID_Classique_Control.slx                     -> ELM_PID_Control.slx
%   PID_Classique_Control_control_disturbance.slx -> ELM_PID_Control_control_disturbance.slx
%   PID_Classique_Control_load_disturbance.slx    -> ELM_PID_Control_load_disturbance.slx
% Dans chaque copie, le bloc "PID Controller" de Ziegler-Nichols est GARDE :
% seuls P, I, D et N passent en entrees externes, et l'adaptateur ELM est
% branche sur l'erreur, la mesure et la commande, exactement comme dans
% Construction_ELM_PID.m. Tout le reste (circuit, source 200 V, charge, F1
% calcule par le bloc MATLAB Function, F2 par l'interrupteur ideal, Scope,
% configuration) reste celui de ton modele : on ouvre le modele construit
% et on clique sur Run. La mesure est ici la sortie du bloc "Vout" (ces
% modeles n'ont ni bruit ni quantification de la mesure).
% ATTENTION : ces noms sont ceux des modeles de la version incrementale.
% Le script les supprime et les reconstruit toujours a partir d'une copie
% fraiche de tes modeles de base.
%
% VERSION
% -------
% 3 (8 octobre 2026), option B (M4 de criteres_elm_pid.txt). Reprend
% Construction_Fuzzy_PID_Trois_Modeles.m (meme montage, valide sous
% Simulink le 6 octobre) avec les deux entrees de plus de l'adaptateur. La
% version 2 (loi incrementale) est dans ELM_PID_INCREMENTAL.
%
% CE QUE LE SCRIPT CHANGE DANS CHAQUE COPIE, ET RIEN D'AUTRE
% -----------------------------------------------------------
%   1. "PID Controller" : ControllerParametersSource internal -> external
%      (Simulink bascule seul les aiguillages P, I, D, N du masque) ; les
%      entrees u, P, I, D, N sont reperees par leur nom ; la liaison
%      Sum1 -> PID est refaite sur l'entree u ; PID -> PWM est gardee.
%   2. Trois Zero-Order Hold a 1/(22000*10) s : "Echantillonneur Erreur
%      ELM" (Sum1), "Echantillonneur Mesure ELM" (sortie du bloc "Vout",
%      branche) et "Echantillonneur Commande ELM" (sortie du PID, branche).
%   3. "ELM-PID Adaptatif" (MATLAB System, elm_pid_adaptatif, execution
%      interpretee, sans traversee directe) -> "Demux Gains ELM" -> entrees
%      P, I, D.
%   4. "Constante N Filtre" (Constant, valeur du champ N du PID) -> entree N.
% La configuration de simulation n'est pas touchee. Tes modeles de base ne
% sont jamais modifies.
%
% LES AUTO-TESTS (apres la sauvegarde ; modeles fermes sans enregistrer)
% ----------------------------------------------------------------------
% Pour chaque modele, 20 ms (avant 50 ms, les trois essais sont le
% demarrage nominal) :
%   T0  adaptateur force aux gains de Ziegler-Nichols : Vout toutes les ms
%       comparee au PID classique du banc (S1), 0.1 V au plus ;
%   T1  ELM-PID : Vout comparee a l'essai du banc (S1, S2, S3), 0.05 V au
%       plus, et gains a 19 ms egaux a ceux du banc a 1 % pres (le banc les
%       change a 4 ms).
% Les auto-tests ne remplacent pas verifier_modeles_elm_pid_trois.py.
%
% REGLES APPLIQUEES : #7 et #17 (add_line avec des handles demandes au
% dernier moment), #16 (on ne supprime que la ligne Sum1 -> PID, refaite
% aussitot), #20 (copie fraiche, un seul exemplaire de chaque fichier sur
% le chemin).
%
% ORDRE D'EXECUTION
% -----------------
%   1. ce script ; 2. verifier_modeles_elm_pid_trois.py ;
%   3. Simuler_ELM_PID_Trois_Modeles.m.
%
% Prerequis dans le dossier courant MATLAB : les trois modeles de base
% ci-dessus, elm_pid_adaptatif.m, elm_pid_modele.mat, elm_pid_reglages.mat,
% ensemble_gains_elm.mat, predictions_banc_elm_pid.json,
% predictions_banc_pid_classique.json.
% Duree : trois a six minutes. Compatible R2024a.
% ---------------------------------------------------------------------

clear; clc;

% Modele de base, modele construit, essai du banc qui lui correspond
MODELES = {'PID_Classique_Control',                     'ELM_PID_Control',                     'S1'; ...
           'PID_Classique_Control_control_disturbance', 'ELM_PID_Control_control_disturbance', 'S2'; ...
           'PID_Classique_Control_load_disturbance',    'ELM_PID_Control_load_disturbance',    'S3'};
TC_TXT = '1/(22000*10)';                          % periode du regulateur (texte exact)
TC     = 1/(22000*10);                            % la meme, en nombre (s)
CLASSE = 'elm_pid_adaptatif';                     % classe du bloc MATLAB System
NOM_SYS   = 'ELM-PID Adaptatif';
NOM_ZOHE  = 'Echantillonneur Erreur ELM';
NOM_ZOHM  = 'Echantillonneur Mesure ELM';
NOM_ZOHU  = 'Echantillonneur Commande ELM';
NOM_DEMUX = 'Demux Gains ELM';
NOM_N     = 'Constante N Filtre';
PWM       = sprintf('PWM Generator\n(DC-DC)');    % regle #1 : vrai saut de ligne
DUREE_TEST = 0.020;                               % duree des auto-tests (s)

% --- Prerequis ---
for f = [strcat(MODELES(:, 1)', '.slx'), {[CLASSE '.m'], 'elm_pid_modele.mat', 'elm_pid_reglages.mat', ...
         'ensemble_gains_elm.mat', 'predictions_banc_elm_pid.json', 'predictions_banc_pid_classique.json'}]
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

    %% 3. Le PID, sa source et sa destination
    pid = [MDL '/PID Controller'];
    for b = {pid, [MDL '/Sum1'], [MDL '/' PWM]}
        if getSimulinkBlockHandle(b{1}) == -1
            close_system(MDL, 0);
            error('Bloc introuvable : %s', strrep(b{1}, newline, ' '));
        end
    end
    if ~strcmp(get_param(pid, 'ControllerParametersSource'), 'internal') || ~strcmp(get_param(pid, 'Form'), 'Parallel')
        close_system(MDL, 0);
        error('%s : le PID devrait avoir des parametres internes et la forme Parallel.', SOURCE);
    end
    lh = get_param(pid, 'LineHandles');
    if numel(lh.Inport) ~= 1
        close_system(MDL, 0);
        error('%s : le PID devrait avoir une seule entree.', SOURCE);
    end
    [src_err, ~] = extremites_ligne(lh.Inport(1));    % ce qui alimente le PID (Sum1, sortie 1)
    [~, dst_cmd] = extremites_ligne(lh.Outport(1));   % ce que le PID alimente (entree du PWM)
    if ~strcmp(src_err.bloc, [MDL '/Sum1']) || numel(dst_cmd) ~= 1 || ~strcmp(dst_cmd(1).bloc, [MDL '/' PWM])
        close_system(MDL, 0);
        error('%s : le PID devrait etre alimente par Sum1 et alimenter seulement le PWM.', SOURCE);
    end
    mesure = [MDL '/Vout'];
    if getSimulinkBlockHandle(mesure) == -1
        close_system(MDL, 0);
        error('%s : bloc de mesure "Vout" introuvable.', SOURCE);
    end
    lm = get_param(mesure, 'LineHandles');
    [~, dst_m] = extremites_ligne(lm.Outport(1));     % la mesure doit aller sur l'entree 2 (-) de Sum1
    if ~any(arrayfun(@(d) strcmp(d.bloc, [MDL '/Sum1']) && d.port == 2, dst_m))
        close_system(MDL, 0);
        error('%s : "Vout" devrait alimenter l''entree 2 (-) de Sum1.', SOURCE);
    end
    N_TXT = get_param(pid, 'N');                  % valeur du filtre, telle qu'ecrite dans le bloc
    fprintf('PID de Ziegler-Nichols : P = %s, I = %s, D = %s, N = %s (ces champs ne serviront plus).\n', ...
            get_param(pid, 'P'), get_param(pid, 'I'), get_param(pid, 'D'), N_TXT);

    %% 4. Parametres du PID en entrees externes
    delete_line(lh.Inport(1));                    % seule ligne supprimee (regle #16), refaite plus bas
    set_param(pid, 'ControllerParametersSource', 'external');
    ports = ports_par_nom(pid);                   % numero d'entree de u, P, I, D, N
    for nom = {'u', 'P', 'I', 'D', 'N'}
        if ~isfield(ports, nom{1})
            noms = fieldnames(ports);
            close_system(MDL, 0);
            error('Entree "%s" introuvable sous le masque du PID ; entrees trouvees : %s.', nom{1}, strjoin(noms', ', '));
        end
    end
    ph_pid = get_param(pid, 'PortHandles');
    if numel(ph_pid.Inport) ~= 5
        close_system(MDL, 0);
        error('Le PID a parametres externes devrait avoir 5 entrees (u, P, I, D, N), il en a %d.', numel(ph_pid.Inport));
    end
    fprintf('PID en parametres externes : entrees u = %d, P = %d, I = %d, D = %d, N = %d.\n', ...
            ports.u, ports.P, ports.I, ports.D, ports.N);

    %% 5. Adaptateur ELM et branchements
    pos = get_param(pid, 'Position');             % [gauche haut droite bas]
    zohe  = [MDL '/' NOM_ZOHE];
    zohm  = [MDL '/' NOM_ZOHM];
    zohu  = [MDL '/' NOM_ZOHU];
    sys   = [MDL '/' NOM_SYS];
    demux = [MDL '/' NOM_DEMUX];
    cn    = [MDL '/' NOM_N];
    add_block('simulink/Discrete/Zero-Order Hold', zohe, 'Position', [pos(1)-260, pos(4)+40, pos(1)-220, pos(4)+70]);
    set_param(zohe, 'SampleTime', TC_TXT);
    add_block('simulink/Discrete/Zero-Order Hold', zohm, 'Position', [pos(1)-260, pos(4)+90, pos(1)-220, pos(4)+120]);
    set_param(zohm, 'SampleTime', TC_TXT);
    add_block('simulink/Discrete/Zero-Order Hold', zohu, 'Position', [pos(3)+40, pos(4)+40, pos(3)+80, pos(4)+70]);
    set_param(zohu, 'SampleTime', TC_TXT);
    add_block('simulink/User-Defined Functions/MATLAB System', sys, 'Position', [pos(1)-190, pos(4)+30, pos(1)-110, pos(4)+120]);
    set_param(sys, 'System', CLASSE);
    set_param(sys, 'SimulateUsing', 'Interpreted execution');
    ph = get_param(sys, 'PortHandles');
    if numel(ph.Inport) ~= 3 || numel(ph.Outport) ~= 1
        close_system(MDL, 0);
        error('Le bloc %s devrait avoir 3 entrees et 1 sortie (il en a %d et %d).', NOM_SYS, numel(ph.Inport), numel(ph.Outport));
    end
    add_block('simulink/Signal Routing/Demux', demux, 'Position', [pos(1)-80, pos(4)+25, pos(1)-75, pos(4)+85]);
    set_param(demux, 'Outputs', '3');
    add_block('simulink/Sources/Constant', cn, 'Position', [pos(1)-80, pos(4)+100, pos(1)-40, pos(4)+120]);
    set_param(cn, 'Value', N_TXT);

    relier(MDL, src_err.bloc, src_err.port, pid, ports.u);   % Sum1 -> entree u du PID (refaite)
    relier(MDL, src_err.bloc, src_err.port, zohe, 1);        % Sum1 -> echantillonneur (branche)
    relier(MDL, mesure, 1, zohm, 1);                         % Vout -> echantillonneur (branche)
    relier(MDL, pid, 1, zohu, 1);                            % commande du PID -> echantillonneur (branche)
    relier(MDL, zohe, 1, sys, 1);
    relier(MDL, zohm, 1, sys, 2);
    relier(MDL, zohu, 1, sys, 3);
    relier(MDL, sys, 1, demux, 1);
    relier(MDL, demux, 1, pid, ports.P);
    relier(MDL, demux, 2, pid, ports.I);
    relier(MDL, demux, 3, pid, ports.D);
    relier(MDL, cn, 1, pid, ports.N);
    fprintf('Adaptateur "%s" (erreur, mesure, commande) branche sur P, I, D ; N = %s constant.\n', NOM_SYS, N_TXT);

    %% 6. Sauvegarde (configuration de simulation non touchee)
    save_system(MDL);
    close_system(MDL, 0);
    fprintf('%s.slx sauvegarde.\n', MDL);
end

%% 7. Auto-tests
fprintf('\n=== Auto-tests (%.0f ms par modele) ===\n', DUREE_TEST * 1e3);
pred_zn = jsondecode(fileread(fullfile(pwd, 'predictions_banc_pid_classique.json')));
pred = jsondecode(fileread(fullfile(pwd, 'predictions_banc_elm_pid.json')));
reg = load(fullfile(pwd, 'elm_pid_reglages.mat'));
reg.K_ZN = double(reg.K_DEPART(:)');
pas_1ms = round(1e-3 / TC);                       % 220 periodes Tc
for i = 1:size(MODELES, 1)
    MDL = MODELES{i, 2};
    code = MODELES{i, 3};
    for fixes = [true, false]
        r = simuler_court(MDL, NOM_SYS, DUREE_TEST, fixes);
        if fixes
            nom = 'T0'; vb = pred_zn.essais.S1.v_toutes_les_ms(:); quoi = 'PID classique du banc, S1'; tol = 0.1;
        else
            nom = 'T1'; vb = pred.essais.(code).v_toutes_les_ms(:); quoi = ['ELM-PID du banc, ' code]; tol = 0.05;
        end
        vs = r.v(1:pas_1ms:end);
        n = min(numel(vs), numel(vb));
        ecart = max(abs(vs(1:n) - vb(1:n)));
        ecart_fin = max(abs(vs(11:n) - vb(11:n)));    % de 10 ms a la fin
        Ks = r.K(1 + (n - 1) * pas_1ms, :);
        fprintf('  %s %s (%s) : ecart maximal sur Vout %.1f mV, de 10 a %d ms %.1f mV ; Vout maximal %.2f V ; gains a %d ms x[%.3f %.3f %.3f] de ZN\n', ...
                MDL, nom, quoi, ecart * 1e3, n - 1, ecart_fin * 1e3, max(r.v), n - 1, ...
                Ks(1) / reg.K_ZN(1), Ks(2) / reg.K_ZN(2), Ks(3) / reg.K_ZN(3));
        if ~(ecart <= tol)
            error('%s %s : ecart de %.3f V, au-dela de %.2f V : envoie cette sortie.', MDL, nom, ecart, tol);
        end
        if ~fixes
            Kb = pred.essais.(code).K_toutes_les_ms(n, :);
            fprintf('       gains du banc a %d ms x[%.3f %.3f %.3f]\n', n - 1, Kb(1) / reg.K_ZN(1), Kb(2) / reg.K_ZN(2), ...
                    Kb(3) / reg.K_ZN(3));
            if max(abs(Ks - Kb) ./ abs(Kb)) > 0.01
                error(['%s T1 : gains a %d ms differents de ceux du banc de plus de 1 %% : une decision ' ...
                       'd''adaptation a bascule. Envoie cette sortie.'], MDL, n - 1);
            end
        end
        if fixes && max(abs(r.K(end, :) - reg.K_ZN(:)') ./ reg.K_ZN(:)') > 0
            error('%s T0 : l''adaptateur n''a pas sorti les gains de Ziegler-Nichols.', MDL);
        end
    end
end
fprintf(['\nLes trois modeles sont construits et leurs auto-tests sont passes :\n' ...
         '  %s.slx, %s.slx, %s.slx\n' ...
         'Lance maintenant verifier_modeles_elm_pid_trois.py.\n'], MODELES{:, 2});


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

function ports = ports_par_nom(bloc)
    % Numero de chaque entree du bloc, d'apres le nom des Inport sous son
    % masque (lien de bibliotheque suivi).
    ib = find_system(bloc, 'LookUnderMasks', 'all', 'FollowLinks', 'on', 'SearchDepth', 1, 'BlockType', 'Inport');
    ports = struct();
    for i = 1:numel(ib)
        nom = get_param(ib{i}, 'Name');
        if isvarname(nom)
            ports.(nom) = str2double(get_param(ib{i}, 'Port'));
        end
    end
end

function r = simuler_court(mdl, nom_sys, duree, gains_fixes)
    % Simulation avec enregistrements temporaires (Vout et gains), modele
    % ferme SANS enregistrer, meme en cas d'erreur.
    load_system(fullfile(pwd, [mdl '.slx']));
    if gains_fixes                                % propriete logique : 'true' ou 'on' selon la version
        try
            set_param([mdl '/' nom_sys], 'GainsFixes', 'true');
        catch
            set_param([mdl '/' nom_sys], 'GainsFixes', 'on');
        end
    end
    ajouter_enregistrement(mdl, [mdl '/Log Vout tmp'], 'tmp_v', [mdl '/Vout'], 1);
    ajouter_enregistrement(mdl, [mdl '/Log K tmp'], 'tmp_K', [mdl '/' nom_sys], 1);
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
