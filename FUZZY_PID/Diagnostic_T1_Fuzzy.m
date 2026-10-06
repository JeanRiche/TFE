%% DIAGNOSTIC_T1_FUZZY.m
%
% OBJECTIF
% --------
% Comprendre l'ecart de l'auto-test T1 de Construction_Fuzzy_PID.m (148 mV
% sur Vout, 20 ms de S1, alors que T0, gains de Ziegler-Nichols, donne
% 2.3 mV). Ce script ne modifie rien : il simule Buck_Commun_Fuzzy_PID.slx
% (deja enregistre par Construction_Fuzzy_PID.m) sur 20 ms de S1 et
% enregistre, a chaque periode Tc :
%   e      : sortie de "Echantillonneur Erreur Fuzzy" (l'erreur vue par l'ordonnanceur)
%   G      : sortie de "Ordonnanceur Flou Zhao" ([P I D])
%   u      : sortie du bloc "PID Controller" (rapport cyclique)
%   v, iL  : tension de sortie et courant de la bobine
% puis les ecrit dans diagnostic_T1_fuzzy.mat. Le meme enregistrement est
% fait avec les gains forces a Ziegler-Nichols (comme T0), pour comparer.
% comparer_diagnostic_T1.py rejoue ensuite, pas par pas, la loi du banc avec
% l'erreur e de Simulink : si la commande du banc et celle de Simulink sont
% identiques, le PID et l'ordonnanceur calculent la meme chose et l'ecart
% vient de la sensibilite du demarrage ; sinon, le premier pas different
% dit ce que le bloc PID fait autrement.
%
% Prerequis : Buck_Commun_Fuzzy_PID.slx (construit par
% Construction_Fuzzy_PID.m, meme si T1 a echoue), ordonnanceur_flou_zhao.m,
% fuzzy_pid_reglages.mat, charger_scenario.m, scenario_S1.mat.
% Duree : une a deux minutes. Compatible R2024a. Ne modifie aucun fichier
% .slx (modele ferme sans enregistrer).
% ---------------------------------------------------------------------

clear; clc;

MDL = 'Buck_Commun_Fuzzy_PID';
NOM_SYS = 'Ordonnanceur Flou Zhao';
NOM_ZOHE = 'Echantillonneur Erreur Fuzzy';
DUREE = 0.020;
TC = 1/(22000*10);

for f = {[MDL '.slx'], 'ordonnanceur_flou_zhao.m', 'fuzzy_pid_reglages.mat', 'charger_scenario.m', 'scenario_S1.mat'}
    if ~isfile(fullfile(pwd, f{1}))
        error('Fichier introuvable dans le dossier courant : %s', f{1});
    end
end
if bdIsLoaded(MDL)
    close_system(MDL, 0);
end
clear ordonnanceur_flou_zhao

diag = struct();
for cas = {{'fuzzy', false}, {'zn', true}}
    nom = cas{1}{1}; fixes = cas{1}{2};
    charger_scenario('S1');
    load_system(fullfile(pwd, [MDL '.slx']));
    if fixes
        try
            set_param([MDL '/' NOM_SYS], 'GainsFixes', 'true');
        catch
            set_param([MDL '/' NOM_SYS], 'GainsFixes', 'on');
        end
    end
    ajouter_enregistrement(MDL, [MDL '/Diag e'], 'dg_e', [MDL '/' NOM_ZOHE], 1);
    ajouter_enregistrement(MDL, [MDL '/Diag G'], 'dg_G', [MDL '/' NOM_SYS], 1);
    ajouter_enregistrement(MDL, [MDL '/Diag u'], 'dg_u', [MDL '/PID Controller'], 1);
    ajouter_enregistrement(MDL, [MDL '/Diag v'], 'dg_v', [MDL '/Vout'], 1);
    ajouter_enregistrement(MDL, [MDL '/Diag iL'], 'dg_iL', [MDL '/iL'], 1);
    blocs = find_system(MDL, 'SearchDepth', 1, 'BlockType', 'ToWorkspace');
    for i = 1:numel(blocs)                        % journaux d'origine neutralises en memoire
        if ~startsWith(get_param(blocs{i}, 'VariableName'), 'dg_')
            set_param(blocs{i}, 'Commented', 'on');
        end
    end
    try
        sortie = sim(MDL, 'StopTime', sprintf('%.17g', DUREE - 0.5 * TC), 'ReturnWorkspaceOutputs', 'on', 'SaveTime', 'off');
    catch ME
        close_system(MDL, 0);
        rethrow(ME);
    end
    close_system(MDL, 0);                         % SANS enregistrer
    d = struct();
    for v = {'e', 'G', 'u', 'v', 'iL'}
        M = lire(sortie, ['dg_' v{1}]);
        if size(M, 2) ~= 1 && size(M, 1) == 3 && size(M, 2) ~= 3
            M = M.';
        end
        d.(v{1}) = M;
    end
    if size(d.G, 2) ~= 3
        d.G = d.G.';
    end
    diag.(nom) = d;
    fprintf('%-5s : %d pas enregistres ; Vout a 20 ms %.4f V ; commande finale %.6f\n', nom, numel(d.v), d.v(end), d.u(end));
end
save('diagnostic_T1_fuzzy.mat', '-struct', 'diag', '-v7');
fprintf('\ndiagnostic_T1_fuzzy.mat ecrit (%.1f Mo). Envoie-le, avec la sortie de cette console.\n', ...
        dir('diagnostic_T1_fuzzy.mat').bytes / 1e6);


%% ===================== Fonctions =====================================

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
