%% OUVRIR_MODELE_S10.m
%
% OBJECTIF
% --------
% Preparer un modele Simulink de l'essai S10 qu'on ouvre et qu'on lance
% directement (bouton Run), sans toucher au modele valide de la methode.
% Le meme script est dans PSO_PID, FUZZY_PID, ELM_PID et PINN_PID : la
% methode est deduite du nom du dossier courant (ou reglee plus bas).
%
% CE QUE FAIT LE SCRIPT
% ---------------------
%   1. Verifie les prerequis dans le dossier courant MATLAB :
%      Buck_Commun_<M>.slx (construit par Construction_<M>.m), ou
%      Buck_Commun.slx pour Ziegler-Nichols ; scenario_S10.mat ;
%      charger_scenario.m ; un seul exemplaire de chacun sur le chemin.
%   2. Cree une copie FRAICHE <M>_S10.slx de Buck_Commun_<M>.slx (l'ancienne
%      copie est supprimee) : PSO_PID_S10.slx, Fuzzy_PID_S10.slx,
%      ELM_PID_S10.slx ou PINN_PID_S10.slx ; avec ZIEGLER_NICHOLS = true,
%      ZN_S10.slx a partir de Buck_Commun.slx.
%   3. Dans la COPIE seulement :
%      - le rappel InitFcn du modele est remplace par un rappel qui charge
%        TOUJOURS S10 : charger_scenario('S10') (celui d'origine ne charge
%        S1 que si sc_R0 n'existe pas, et garderait donc l'essai precedent) ;
%      - StopTime = (nombre d'instants du profil - 0.5) x Tc, comme le sim()
%        de Simuler_<M>.m : un demi-pas apres le dernier instant (200 ms),
%        pour que cet instant soit simule quels que soient les arrondis ;
%      - un Scope "Scope S10 Vout consigne" est ajoute : entree 1 = Vout
%        (bloc "Vout"), entree 2 = consigne (sortie de "Somme Consigne"),
%        echantillonne a Tc = 1/(22000*10) s. Le Scope d'origine (Vin, Vout,
%        iL) reste en place ; aucun de ses Scopes ne montrait la consigne.
%   4. Sauvegarde la copie et l'ouvre (open_system). Il ne reste qu'a
%      cliquer sur Run. Le Scope s'ouvre au debut de la simulation.
% Le modele de base valide (Buck_Commun_<M>.slx ou Buck_Commun.slx) n'est
% jamais charge ni modifie : il est seulement copie sur le disque (sa date
% de modification est controlee avant et apres).
%
% CE QUE CE MODELE N'EST PAS
% --------------------------
% Il sert a REGARDER S10 (Vout, consigne, Vin, iL) et a experimenter. Les
% chiffres OFFICIELS de S10 restent ceux de Simuler_<M>.m avec
% ESSAIS_A_SIMULER = {'S10'} (resultats_Buck_Commun_<M>_S10.mat, compares
% au banc) ; pour Ziegler-Nichols, Simuler_ZN.m (dossier PSO_PID). Les
% blocs To Workspace d'origine (x, y) enregistrent au pas du powergui :
% une simulation lancee ici est plus lente et plus lourde en memoire que
% celle de Simuler_<M>.m, qui les neutralise.
% Un Run modifie le modele en memoire (InitFcn charge les variables sc_*
% dans le workspace de base) ; la copie peut etre fermee sans enregistrer.
% Relancer ce script refait toujours une copie fraiche.
%
% Prerequis : etre DANS le dossier de la methode (dossier courant MATLAB),
% Buck_Commun_<M>.slx deja construit (Construction_<M>.m) et, pour les
% methodes a bloc MATLAB System (Fuzzy-PID, ELM-PID, PINN-PID), les
% fichiers de la classe du bloc dans ce dossier, comme pour Simuler_<M>.m.
% Duree : quelques secondes (sans la simulation). Compatible R2024a.
% ---------------------------------------------------------------------

clear; clc;

% --- Reglages ---
ZIEGLER_NICHOLS = false;    % true : Ziegler-Nichols (Buck_Commun.slx -> ZN_S10.slx)
METHODE = '';               % '' : deduite du dossier courant ; sinon 'PSO_PID', 'Fuzzy_PID', 'ELM_PID' ou 'PINN_PID'
AJOUTER_SCOPE = true;       % Scope Vout / consigne dans la copie
TE = 1/(22000*10);          % periode du regulateur (s)
TE_TXT = '1/(22000*10)';    % la meme, en texte exact pour Simulink

% --- Modele source et nom de la copie ---
if ZIEGLER_NICHOLS
    SOURCE = 'Buck_Commun';
    COPIE = 'ZN_S10';
    CONSTRUCTION = '';
else
    if isempty(METHODE)
        [~, dossier] = fileparts(pwd);
        switch upper(dossier)
            case 'PSO_PID'
                METHODE = 'PSO_PID';
            case 'FUZZY_PID'
                METHODE = 'Fuzzy_PID';
            case 'ELM_PID'
                METHODE = 'ELM_PID';
            case 'PINN_PID'
                METHODE = 'PINN_PID';
            otherwise
                error(['Dossier courant "%s" : la methode ne peut pas etre deduite. Se placer dans ' ...
                       'PSO_PID, FUZZY_PID, ELM_PID ou PINN_PID, ou regler METHODE en tete du script.'], dossier);
        end
    end
    SOURCE = ['Buck_Commun_' METHODE];
    COPIE = [METHODE '_S10'];
    CONSTRUCTION = ['Construction_' METHODE '.m'];
end
fprintf('Modele source : %s.slx ; copie pour S10 : %s.slx (dossier %s).\n', SOURCE, COPIE, pwd);

% --- 1. Prerequis ---
for f = {[SOURCE '.slx'], 'charger_scenario.m', 'scenario_S10.mat'}
    if ~isfile(fullfile(pwd, f{1}))
        if strcmp(f{1}, [SOURCE '.slx']) && ~isempty(CONSTRUCTION)
            error('%s introuvable dans le dossier courant : lancer d''abord %s (le modele de la methode n''est pas fourni, il est construit).', ...
                  f{1}, CONSTRUCTION);
        end
        error('Fichier introuvable dans le dossier courant : %s', f{1});
    end
    copies = which(f{1}, '-all');
    if numel(copies) > 1
        error('Il doit exister un seul %s sur le chemin MATLAB, il y en a %d :\n%s', ...
              f{1}, numel(copies), strjoin(copies, newline));
    end
end
autres = which([COPIE '.slx'], '-all');                 % une autre copie ailleurs sur le chemin masquerait celle-ci
autres = autres(~strcmpi(autres, fullfile(pwd, [COPIE '.slx'])));
if ~isempty(autres)
    error('Un autre %s.slx est sur le chemin MATLAB : %s. Le retirer du chemin.', COPIE, strjoin(autres, ', '));
end
if bdIsLoaded(SOURCE) && strcmp(get_param(SOURCE, 'Dirty'), 'on')
    error('%s est ouvert avec des modifications non enregistrees : l''enregistrer ou le fermer (la copie part du fichier).', SOURCE);
end
if bdIsLoaded(COPIE)
    close_system(COPIE, 0);                              % ancienne copie : fermee sans enregistrer
end
sc = charger_scenario('S10');                            % controle du fichier et variables sc_* (workspace de base)
if ~strcmp(sc.code, 'S10')
    error('scenario_S10.mat contient l''essai %s, pas S10.', sc.code);
end
n = numel(sc.t);
stop = (n - 0.5) * TE;                                   % comme Simuler_<M>.m : un demi-pas apres le dernier instant
fprintf('S10 : %s, %d instants (0 a %.3f s), evenements a %s ms.\n', sc.nom, n, sc.duree, ...
        strjoin(arrayfun(@(x) sprintf('%g', x * 1e3), sc.evenements, 'UniformOutput', false), ', '));
info_source = dir(fullfile(pwd, [SOURCE '.slx']));

% --- 2. Copie fraiche ---
chemin = fullfile(pwd, [COPIE '.slx']);
if isfile(chemin)
    delete(chemin);
    fprintf('Ancien %s.slx supprime (on repart toujours d''une copie fraiche).\n', COPIE);
end
copyfile(fullfile(pwd, [SOURCE '.slx']), chemin);
fileattrib(chemin, '+w');                                % la copie doit etre modifiable
load_system(chemin);
if ~bdIsLoaded(COPIE)
    error('La copie %s n''a pas ete chargee sous le nom attendu.', chemin);
end

% --- 3. Modifications de la copie ---
ancien = get_param(COPIE, 'InitFcn');
if ~contains(ancien, 'charger_scenario')
    warning('InitFcn de %s inattendu (pas de charger_scenario) : "%s". Il est remplace quand meme.', SOURCE, ancien);
end
nouveau = sprintf(['%% Copie pour S10 ecrite par Ouvrir_Modele_S10.m : charge TOUJOURS l''essai S10\n' ...
                   '%% (dossier courant = dossier de la methode).\n' ...
                   'charger_scenario(''S10'');']);
set_param(COPIE, 'InitFcn', nouveau);
set_param(COPIE, 'StopTime', sprintf('%.17g', stop));
fprintf('InitFcn : "%s"\n  remplace par : charger_scenario(''S10'');\n', ancien);
fprintf('StopTime : %s s (%d instants de %.4g us, plus un demi-pas).\n', get_param(COPIE, 'StopTime'), n, TE * 1e6);

if AJOUTER_SCOPE
    vout = [COPIE '/Vout'];
    cons = [COPIE '/Somme Consigne'];
    scope = [COPIE '/Scope S10 Vout consigne'];
    if getSimulinkBlockHandle(vout) == -1 || getSimulinkBlockHandle(cons) == -1
        warning('Bloc "Vout" ou "Somme Consigne" introuvable dans %s : Scope non ajoute.', COPIE);
    else
        pos = get_param(vout, 'Position');
        add_block('simulink/Sinks/Scope', scope, 'Position', [pos(3) + 160, pos(2) + 90, pos(3) + 210, pos(2) + 140]);
        set_param(scope, 'NumInputPorts', '2');
        ph_s = get_param(scope, 'PortHandles');          % handles demandes apres le reglage du nombre d'entrees
        ph_v = get_param(vout, 'PortHandles');
        ph_c = get_param(cons, 'PortHandles');
        add_line(COPIE, ph_v.Outport(1), ph_s.Inport(1), 'autorouting', 'on');
        add_line(COPIE, ph_c.Outport(1), ph_s.Inport(2), 'autorouting', 'on');
        try
            set_param(scope, 'SampleTime', TE_TXT);      % un point par periode Tc (pas au pas du powergui)
        catch ME
            warning('Periode du Scope non reglee (%s) : il affichera au pas du powergui.', ME.message);
        end
        try
            set_param(scope, 'OpenAtSimulationStart', 'on');
        catch
            % reglage d'affichage seulement : sans importance s'il n'existe pas
        end
        fprintf('Scope ajoute : "%s" (entree 1 Vout, entree 2 consigne, a Tc).\n', 'Scope S10 Vout consigne');
    end
end

% --- 4. Sauvegarde et ouverture ---
save_system(COPIE);
info_apres = dir(fullfile(pwd, [SOURCE '.slx']));
if info_apres.datenum ~= info_source.datenum || info_apres.bytes ~= info_source.bytes
    error('%s.slx a change pendant le script : ce ne devrait pas etre possible, le signaler.', SOURCE);
end
open_system(COPIE);
fprintf(['\n%s.slx enregistre et ouvert. Cliquer sur Run (%s.slx n''a pas ete modifie).\n' ...
         'Chiffres officiels de S10 : Simuler_<M>.m avec ESSAIS_A_SIMULER = {''S10''} ' ...
         '(Ziegler-Nichols : Simuler_ZN.m, dossier PSO_PID).\n'], COPIE, SOURCE);
