%% TESTER_FUZZY_PID_REJEU.m
%
% VERSION
% -------
% 1 (6 octobre 2026), Fuzzy-PID sur la base commune v2.
%
% OBJECTIF
% --------
% Verifier, avant toute simulation Simulink, que le bloc MATLAB
% fuzzy_pid_adaptatif.m calcule exactement ce que calcule la classe
% FuzzyPID de banc_fuzzy_pid.py. Le banc a enregistre, pas par pas,
% l'erreur e recue par le Fuzzy-PID sur quatre essais (S1, S7b, S8b, S9),
% ainsi que la commande u et les gains K qu'il a produits, et la sortie du
% systeme flou seul sur une grille de 225 points (E, dE). Ce script donne
% les memes entrees au bloc MATLAB, en dehors de Simulink, et compare.
%
% CE QUI EST COMPARE
% ------------------
%   - le systeme flou seul (inference) sur les 225 points de la grille,
%     dont les points de cassure 0.1, 1 et 10 V ;
%   - pour chaque essai et chaque pas : u et les trois gains ;
%   - pour chaque fenetre de 0.5 ms : E, dE et theta.
% Tolerances : 1e-12 sur le systeme flou seul, 1e-9 sur u, 1e-9 en
% relatif sur les gains, 1e-9 sur E, dE et theta.
%
% ORDRE D'EXECUTION
% -----------------
%   1. banc_fuzzy_pid.py ; 2. ce script ; 3. Construction_Fuzzy_PID.m ;
%   4. verifier_modele_fuzzy_pid.py ; 5. Simuler_Fuzzy_PID.m.
%
% Prerequis dans le dossier courant MATLAB : fuzzy_pid_adaptatif.m,
% fuzzy_pid_reglages.mat, reference_rejeu_fuzzy_pid.mat.
% Duree : une demi-minute a deux minutes (230 000 pas). Compatible R2024a.
% N'utilise pas la Fuzzy Logic Toolbox.
% ---------------------------------------------------------------------

clear; clc;

% --- Prerequis ---
for f = {'fuzzy_pid_adaptatif.m', 'fuzzy_pid_reglages.mat', 'reference_rejeu_fuzzy_pid.mat'}
    if ~isfile(fullfile(pwd, f{1}))
        error('Fichier introuvable dans le dossier courant : %s', f{1});
    end
    if numel(which(f{1}, '-all')) ~= 1
        error('Il doit exister exactement un %s sur le chemin MATLAB.', f{1});
    end
end
clear fuzzy_pid_adaptatif                          % recharger la classe si elle a change

% --- 1. Le systeme flou seul ---
reg = load('fuzzy_pid_reglages.mat');
ref = load('reference_rejeu_fuzzy_pid.mat');
tables = zeros(3, 5, 5);
tables(1, :, :) = reshape(double(reg.TABLE_P), [1 5 5]);
tables(2, :, :) = reshape(double(reg.TABLE_I), [1 5 5]);
tables(3, :, :) = reshape(double(reg.TABLE_D), [1 5 5]);
pts = double(ref.FIS_ENTREES);
attendu = double(ref.FIS_SORTIES);
ecart_fis = 0;
for i = 1:size(pts, 1)
    th = fuzzy_pid_adaptatif.inference(pts(i, 1), pts(i, 2), tables, double(reg.SEUILS(:)'));
    ecart_fis = max(ecart_fis, max(abs(th - attendu(i, :))));
end
fprintf('Systeme flou seul : %d points, ecart maximal %.1e.\n', size(pts, 1), ecart_fis);
if ecart_fis > 1e-12
    error('inference ne redonne pas le systeme flou de banc_fuzzy_pid.py.');
end

% --- 2. Rejeu pas par pas ---
codes = {'S1', 'S7b', 'S8b', 'S9'};
tout_ok = true;
for c = 1:numel(codes)
    r = ref.(codes{c});
    e = double(r.e(:));
    N = numel(e);
    bloc = fuzzy_pid_adaptatif('AfficherBilan', false);
    u = zeros(N, 1);
    K = zeros(N, 3);
    E = zeros(0, 1); dE = zeros(0, 1); TH = zeros(0, 3);
    nfen = 0;
    t0 = tic;
    for k = 1:N
        [u(k), K(k, :)] = bloc(e(k));
        info = lire_fenetre(bloc);
        if info.nfen > nfen                       % une fenetre vient de se terminer
            nfen = info.nfen;
            E(end + 1, 1) = info.E; %#ok<SAGROW>
            dE(end + 1, 1) = info.dE; %#ok<SAGROW>
            TH(end + 1, :) = info.theta; %#ok<SAGROW>
        end
    end
    duree = toc(t0);
    release(bloc);
    ecart_u = max(abs(u - double(r.u(:))));
    ecart_K = max(max(abs(K - double(r.K)) ./ abs(double(r.K))));
    nw = min(numel(E), numel(r.E));
    ecart_fen = max([max(abs(E(1:nw) - double(r.E(1:nw)))), max(abs(dE(1:nw) - double(r.dE(1:nw)))), ...
                     max(max(abs(TH(1:nw, :) - double(r.theta(1:nw, :)))))]);
    ok = ecart_u <= 1e-9 && ecart_K <= 1e-9 && ecart_fen <= 1e-9 && numel(E) == numel(r.E);
    tout_ok = tout_ok && ok;
    fprintf(['%-4s : %6d pas, %4d fenetres ; ecart max sur u %.1e, sur les gains %.1e (relatif), ' ...
             'sur E, dE, theta %.1e ; %4.1f s  -> %s\n'], codes{c}, N, numel(E), ecart_u, ecart_K, ecart_fen, ...
            duree, ternaire(ok, 'identique', 'DIFFERENT'));
    fprintf('       gains finaux : Kp %.6f, Ki %.6e, Kd %.6f (banc : %.6f, %.6e, %.6f)\n', K(end, 1), K(end, 2), ...
            K(end, 3), r.K(end, 1), r.K(end, 2), r.K(end, 3));
end
if tout_ok
    fprintf('\nRESULTAT : le bloc fuzzy_pid_adaptatif.m reproduit banc_fuzzy_pid.py. Etape suivante : Construction_Fuzzy_PID.m.\n');
else
    error('Le bloc fuzzy_pid_adaptatif.m ne reproduit pas le banc : ne pas construire le modele Simulink.');
end


%% ===================== Fonctions =====================================

function s = ternaire(condition, si_vrai, si_faux)
    % Choix entre deux textes.
    if condition
        s = si_vrai;
    else
        s = si_faux;
    end
end
