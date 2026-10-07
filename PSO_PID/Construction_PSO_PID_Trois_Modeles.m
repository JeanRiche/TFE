%% CONSTRUCTION_PSO_PID_TROIS_MODELES.m
%
% OBJECTIF
% --------
% Construire, pour le PSO-PID (essaim de Gaing 2004, modifications M1 a M3 de criteres_pso_pid.txt, reglage hors ligne), un modele
% Simulink par scenario de base, a partir des trois modeles de Jean-Riche :
%   PID_Classique_Control.slx                     -> PSO_PID_Control.slx
%   PID_Classique_Control_control_disturbance.slx -> PSO_PID_Control_control_disturbance.slx
%   PID_Classique_Control_load_disturbance.slx    -> PSO_PID_Control_load_disturbance.slx
% Dans chaque copie, seuls P, I et D du bloc "PID Controller" changent : ils
% prennent les valeurs de predictions_banc_pso_pid.json (banc_pso_pid.py),
% ecrites avec 17 chiffres significatifs. Tout le reste (circuit, source
% 200 V, charge, F1, F2, Scope, configuration) reste celui de ton modele :
% on ouvre le modele construit et on clique sur Run.
%
% VERSION
% -------
% 1 (6 octobre 2026). Meme changement que Construction_PSO_PID.m.
%
% CONTROLES ET AUTO-TESTS
% -----------------------
%   - avant : circuit de la base commune v2 (diode sans snubber, 10 mH,
%     47 uF, 22 kHz, pas exacts) et PID de Ziegler-Nichols dans le modele
%     de base ;
%   - apres : P, I, D relus dans le fichier enregistre egaux a ceux du
%     fichier JSON a 1e-12 pres ;
%   - 20 ms par modele : Vout toutes les ms comparee a l'essai du banc (S1,
%     S2, S3 ; avant 50 ms, c'est le demarrage nominal), 0.05 V au plus
%     (gains fixes : pas d'amplification comme avec le Fuzzy-PID ; le PID
%     classique dans ces modeles est a 10 a 15 mV du banc).
% Les auto-tests ne remplacent pas verifier_modeles_pso_pid_trois.py.
%
% ORDRE D'EXECUTION
% -----------------
%   1. ce script ; 2. verifier_modeles_pso_pid_trois.py ;
%   3. Simuler_PSO_PID_Trois_Modeles.m.
%
% Prerequis dans le dossier courant MATLAB : les trois modeles de base et
% predictions_banc_pso_pid.json. Duree : une a trois minutes. Compatible
% R2024a.
% ---------------------------------------------------------------------

clear; clc;

MODELES = {'PID_Classique_Control',                     'PSO_PID_Control',                     'S1'; ...
           'PID_Classique_Control_control_disturbance', 'PSO_PID_Control_control_disturbance', 'S2'; ...
           'PID_Classique_Control_load_disturbance',    'PSO_PID_Control_load_disturbance',    'S3'};
JSON = 'predictions_banc_pso_pid.json';
ZN = struct('P', 0.093910, 'I', 301.089, 'D', 7.3227e-6, 'N', 64122.9);   % gains attendus dans les modeles de base
TC = 1/(22000*10);
DUREE_TEST = 0.020;
TOLERANCE_TEST = 0.05;

% --- Prerequis ---
for f = [strcat(MODELES(:, 1)', '.slx'), {JSON}]
    if ~isfile(fullfile(pwd, f{1}))
        error('Fichier introuvable dans le dossier courant : %s', f{1});
    end
    if numel(which(f{1}, '-all')) > 1
        error('Il doit exister un seul %s sur le chemin MATLAB : %s', f{1}, strjoin(which(f{1}, '-all'), ', '));
    end
end
pred = jsondecode(fileread(fullfile(pwd, JSON)));
if ~isfield(pred, 'version') || pred.version ~= 2 || ~isfield(pred, 'gains')
    error('%s ne vient pas de banc_pso_pid.py (version 2 de la base commune).', JSON);
end
g = pred.gains;
fprintf('Gains lus dans %s : P = %.10g, I = %.10g, D = %.10g, N = %.10g\n', JSON, g.P, g.I, g.D, g.N);
if abs(g.N - ZN.N) > 1e-9 * ZN.N
    error('Le N du fichier JSON (%.10g) n''est pas celui du PID de reference (%.10g).', g.N, ZN.N);
end
for i = 1:size(MODELES, 1)
    base = MODELES{i, 1};
    if bdIsLoaded(base) && strcmp(get_param(base, 'Dirty'), 'on')
        error('%s est ouvert avec des modifications non enregistrees : l''enregistrer ou le fermer.', base);
    end
    for m = MODELES(i, 1:2)
        if bdIsLoaded(m{1})
            close_system(m{1}, 0);
        end
    end
end

noms = {'P', 'I', 'D', 'N'};
for i = 1:size(MODELES, 1)
    SOURCE = MODELES{i, 1};
    MDL = MODELES{i, 2};
    fprintf('\n=== %s -> %s ===\n', SOURCE, MDL);
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
    controler_base(MDL, SOURCE);
    bloc = [MDL '/PID Controller'];
    for k = 1:numel(noms)                         % on part bien du PID de Ziegler-Nichols
        v = evalin('base', get_param(bloc, noms{k}));
        if ~(abs(v - ZN.(noms{k})) <= 1e-9 * abs(ZN.(noms{k})))
            close_system(MDL, 0);
            error('%s de %s vaut %.10g au lieu de %.10g.', noms{k}, SOURCE, v, ZN.(noms{k}));
        end
    end
    set_param(bloc, 'P', sprintf('%.17g', g.P), 'I', sprintf('%.17g', g.I), 'D', sprintf('%.17g', g.D));
    save_system(MDL);
    close_system(MDL, 0);
    load_system(chemin);                          % gains relus dans le fichier enregistre
    for k = 1:3
        v = evalin('base', get_param(bloc, noms{k}));
        if ~(abs(v - g.(noms{k})) <= 1e-12 * abs(g.(noms{k})))
            close_system(MDL, 0);
            error('%s relu dans %s.slx vaut %.17g au lieu de %.17g.', noms{k}, MDL, v, g.(noms{k}));
        end
    end
    fprintf('Gains relus dans %s.slx : P = %s, I = %s, D = %s, N = %s\n', MDL, get_param(bloc, 'P'), ...
            get_param(bloc, 'I'), get_param(bloc, 'D'), get_param(bloc, 'N'));
    close_system(MDL, 0);
end

fprintf('\n=== Auto-tests (%.0f ms par modele) ===\n', DUREE_TEST * 1e3);
pas_1ms = round(1e-3 / TC);
for i = 1:size(MODELES, 1)
    MDL = MODELES{i, 2};
    code = MODELES{i, 3};
    v = simuler_court(MDL, DUREE_TEST);
    vb = pred.essais.(code).v_toutes_les_ms(:);
    vs = v(1:pas_1ms:end);
    n = min(numel(vs), numel(vb));
    ecart = max(abs(vs(1:n) - vb(1:n)));
    fprintf('  %s : ecart maximal au banc (%s) sur Vout toutes les ms %.1f mV ; Vout maximal %.2f V (banc %.2f V)\n', ...
            MDL, code, ecart * 1e3, max(v), max(vb));
    if ~(ecart <= TOLERANCE_TEST)
        error('%s : ecart au banc de %.3f V, au-dela de %.2f V : envoie cette sortie.', MDL, ecart, TOLERANCE_TEST);
    end
end
fprintf(['\nLes trois modeles sont construits et leurs auto-tests sont passes :\n' ...
         '  %s.slx, %s.slx, %s.slx\n' ...
         'Lance maintenant verifier_modeles_pso_pid_trois.py.\n'], MODELES{:, 2});


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

function v = simuler_court(mdl, duree)
    % Simulation avec un enregistrement temporaire de Vout, modele ferme SANS
    % enregistrer, meme en cas d'erreur.
    load_system(fullfile(pwd, [mdl '.slx']));
    chemin = [mdl '/Log Vout tmp'];
    pos = get_param([mdl '/Vout'], 'Position');
    add_block('simulink/Sinks/To Workspace', chemin, 'Position', [pos(3)+120, pos(2)+40, pos(3)+200, pos(2)+65]);
    set_param(chemin, 'VariableName', 'tmp_v', 'SaveFormat', 'Timeseries', 'SampleTime', '1/(22000*10)', ...
              'MaxDataPoints', 'inf');
    ph_src = get_param([mdl '/Vout'], 'PortHandles');
    ph_dst = get_param(chemin, 'PortHandles');
    add_line(mdl, ph_src.Outport(1), ph_dst.Inport(1), 'autorouting', 'on');
    blocs = find_system(mdl, 'SearchDepth', 1, 'BlockType', 'ToWorkspace');
    for i = 1:numel(blocs)
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
    donnee = sortie.get('tmp_v');
    if isa(donnee, 'timeseries')
        v = double(squeeze(donnee.Data));
    else
        v = double(squeeze(donnee.signals.values));
    end
    v = v(:);
end
