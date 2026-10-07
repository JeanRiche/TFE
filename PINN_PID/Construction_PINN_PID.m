%% CONSTRUCTION_PINN_PID.m
%
% OBJECTIF
% --------
% Construire Buck_Commun_PINN_PID.slx, le modele du PINN-PID : une copie de
% Buck_Commun.slx (base commune v2, verifiee) dans laquelle le bloc
% "PID Controller" est remplace par le bloc MATLAB System du PINN-PID.
%
% VERSION
% -------
% 1 (5 octobre 2026), PINN-PID sur la base commune v2 (meme structure que
% Construction_ELM_PID.m, validee chez Jean-Riche le 5 octobre 2026).
% Remplace Construction_Simulink_PINN_PID.m (ancienne base : Te = 5 us,
% bornes internes elargies, saturation apres F1).
%
% CE QUE LE SCRIPT CHANGE, ET RIEN D'AUTRE
% -----------------------------------------
%   1. Le bloc "PID Controller" et ses deux liaisons sont supprimes.
%   2. Deux Zero-Order Hold a Tc = 1/(22000*10) s (texte exact) sont
%      ajoutes : "Echantillonneur Erreur PINN", alimente par Sum1 (l'erreur,
%      comme l'etait le PID), et "Echantillonneur Mesure PINN", alimente par
%      "Quantification Mesure" (la mesure vue par le regulateur ; la liaison
%      vers Sum1 est gardee, une branche est ajoutee).
%   3. "PINN-PID Adaptatif" (MATLAB System, classe pinn_pid_adaptatif,
%      execution interpretee) recoit l'erreur et la mesure ; sa sortie 1
%      (rapport cyclique, deja borne a [0.01 ; 0.99] par la loi) alimente
%      l'entree du PWM comme le faisait le PID ; sa sortie 2 (les gains)
%      va dans "Terminaison Gains PINN" (Terminator). Simuler_PINN_PID.m
%      enregistre cette sortie en memoire.
% Le circuit de puissance, les sources commandees, la mesure, la consigne,
% le PWM, le powergui, la configuration et le rappel InitFcn ne changent
% pas. Il n'y a pas d'autre saturation : celle de la loi est la seule
% saturation physique, juste avant le PWM (regle du protocole).
%
% LES AUTO-TESTS (apres la sauvegarde)
% -------------------------------------
%   T1  20 ms de S1 : Vout toutes les ms comparee au banc
%       (predictions_banc_pinn_pid.json), ecart maximal tolere 0.05 V ;
%       gains a 19 ms affiches a cote de ceux du banc (le PINN-PID adapte
%       ses gains pendant le demarrage, sur quelques fenetres).
%   T2  20 ms de S8b (98 ohms) : meme comparaison, ecart tolere 0.5 V
%       (demarrage tres peu amorti, ou une adaptation peut se decaler d'une
%       fenetre entre Simulink et le banc) ; gains a 19 ms affiches.
% Les auto-tests ne remplacent pas verifier_modele_pinn_pid.py.
%
% REGLES APPLIQUEES : #7 et #17 (add_line avec des handles demandes au
% dernier moment), #8 (ReturnWorkspaceOutputs = 'off'), #16 (on ne supprime
% que les lignes du bloc PID), #20 (copie fraiche, un seul exemplaire de
% chaque fichier sur le chemin).
%
% ORDRE D'EXECUTION (PINN-PID)
% ----------------------------
%   1. entrainement_pinn.py ; 2. estimation_etat_pinn.py ; 3. banc_pinn_pid.py ;
%   4. Tester_PINN_PID_Rejeu.m ; 5. ce script ; 6. verifier_modele_pinn_pid.py ;
%   7. Simuler_PINN_PID.m.
%
% Prerequis dans le dossier courant MATLAB : Buck_Commun.slx (construit et
% verifie), charger_scenario.m, scenario_S1.mat, scenario_S8b.mat,
% pinn_pid_adaptatif.m, pinn_pid_modele.mat, pinn_pid_reglages.mat et
% predictions_banc_pinn_pid.json.
% Duree : une a trois minutes (auto-tests compris). Compatible R2024a.
% ---------------------------------------------------------------------

clear; clc;

SOURCE = 'Buck_Commun';                           % modele commun (jamais modifie)
MDL    = 'Buck_Commun_PINN_PID';                   % modele construit
TC_TXT = '1/(22000*10)';                          % periode du regulateur (texte exact)
TC     = 1/(22000*10);                            % la meme, en nombre (s)
CLASSE = 'pinn_pid_adaptatif';                     % classe du bloc MATLAB System
NOM_SYS  = 'PINN-PID Adaptatif';
NOM_ZOHE = 'Echantillonneur Erreur PINN';
NOM_ZOHM = 'Echantillonneur Mesure PINN';
NOM_TERM = 'Terminaison Gains PINN';
PWM      = sprintf('PWM Generator\n(DC-DC)');     % regle #1 : vrai saut de ligne

% --- Prerequis ---
for f = {[SOURCE '.slx'], 'charger_scenario.m', 'scenario_S1.mat', 'scenario_S8b.mat', [CLASSE '.m'], ...
         'pinn_pid_modele.mat', 'pinn_pid_reglages.mat', 'predictions_banc_pinn_pid.json'}
    if ~isfile(fullfile(pwd, f{1}))
        error('Fichier introuvable dans le dossier courant : %s', f{1});
    end
    if numel(which(f{1}, '-all')) > 1
        error('Il doit exister un seul %s sur le chemin MATLAB : %s', f{1}, strjoin(which(f{1}, '-all'), ', '));
    end
end
if bdIsLoaded(SOURCE) && strcmp(get_param(SOURCE, 'Dirty'), 'on')
    error('%s est ouvert avec des modifications non enregistrees : l''enregistrer ou le fermer.', SOURCE);
end
for m = {MDL, SOURCE}
    if bdIsLoaded(m{1})
        close_system(m{1}, 0);                    % fermer sans enregistrer
    end
end
clear(CLASSE);                                    % recharger la classe si elle a change
charger_scenario('S1');                           % variables sc_* presentes avant le chargement

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

%% 2. Le PID, sa source, sa destination et la mesure
pid = [MDL '/PID Controller'];
quant = [MDL '/Quantification Mesure'];
for b = {pid, quant, [MDL '/Sum1'], [MDL '/' PWM]}
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
    error('Le PID devrait etre alimente par Sum1 et alimenter seulement le PWM.');
end
lq = get_param(quant, 'LineHandles');
[~, dst_q] = extremites_ligne(lq.Outport(1));     % la mesure doit aller sur l'entree 2 de Sum1
if ~any(arrayfun(@(d) strcmp(d.bloc, [MDL '/Sum1']) && d.port == 2, dst_q))
    close_system(MDL, 0);
    error('"Quantification Mesure" devrait alimenter l''entree 2 (-) de Sum1.');
end

%% 3. Remplacement du PID par le PINN-PID
pos = get_param(pid, 'Position');                 % [gauche haut droite bas]
delete_line(lh.Inport(1));                        % lignes du PID seulement (regle #16)
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
relier(MDL, quant, 1, zohm, 1);                     % mesure -> echantillonneur (branche)
relier(MDL, zohe, 1, sys, 1);
relier(MDL, zohm, 1, sys, 2);
relier(MDL, sys, 1, dst_cmd(1).bloc, dst_cmd(1).port);   % rapport cyclique -> PWM
relier(MDL, sys, 2, term, 1);                       % gains -> terminaison
fprintf('PID remplace par "%s" (%s, execution interpretee), alimente par l''erreur et la mesure echantillonnees a %s s.\n', ...
        NOM_SYS, CLASSE, TC_TXT);

%% 4. Hygiene (#8) et sauvegarde
set_param(MDL, 'ReturnWorkspaceOutputs', 'off');
save_system(MDL);
close_system(MDL, 0);
fprintf('%s.slx sauvegarde.\n', MDL);

%% 5. Auto-tests
fprintf('\n=== Auto-tests ===\n');
pred = jsondecode(fileread(fullfile(pwd, 'predictions_banc_pinn_pid.json')));
for essai = {{'T1', 'S1', 0.020, 0.05}, {'T2', 'S8b', 0.020, 0.5}}
    nom = essai{1}{1}; code = essai{1}{2}; duree = essai{1}{3}; tol = essai{1}{4};
    charger_scenario(code);
    r = simuler_court(MDL, NOM_SYS, duree);
    vb = pred.essais.(code).v_toutes_les_ms(:);
    Kb = pred.essais.(code).K_toutes_les_ms;
    pas_1ms = round(1e-3 / TC);                   % 220 periodes Tc
    vs = r.v(1:pas_1ms:end);
    n = min(numel(vs), numel(vb));
    ecart = max(abs(vs(1:n) - vb(1:n)));
    Ks = r.K(1 + (n - 1) * pas_1ms, :);           % gains a (n-1) ms, meme instant que Kb(n, :)
    fprintf('  %s (%s, %.0f ms) : ecart maximal au banc sur Vout (toutes les ms) %.1f mV ; gains a %d ms : [%.5f %.4e %.4f] (banc [%.5f %.4e %.4f])\n', ...
            nom, code, duree * 1e3, ecart * 1e3, n - 1, Ks(1), Ks(2), Ks(3), Kb(n, 1), Kb(n, 2), Kb(n, 3));
    if ~(ecart <= tol)
        error('%s : ecart au banc de %.3f V, au-dela de %.2f V : verifier la construction.', nom, ecart, tol);
    end
end
fprintf(['\n%s.slx est construit et ses auto-tests sont passes.\n' ...
         'Lance maintenant verifier_modele_pinn_pid.py.\n'], MDL);


%% ===================== Fonctions =====================================

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
