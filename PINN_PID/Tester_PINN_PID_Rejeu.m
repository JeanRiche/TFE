%% TESTER_PINN_PID_REJEU.m
%
% VERSION
% -------
% 1 (5 octobre 2026), PINN-PID sur la base commune v2.
%
% OBJECTIF
% --------
% Verifier, avant toute simulation Simulink, que le bloc MATLAB
% pinn_pid_adaptatif.m calcule exactement ce que calcule la classe PINNPID
% de banc_pinn_pid.py. Le banc a enregistre, pas par pas, l'erreur e et la
% mesure recues par le PINN-PID sur quatre essais (S1, S7b, S8b, S9), ainsi
% que la commande u et les gains K qu'il a produits, et, a chaque fin de
% fenetre, la decision d'adapter et l'etat de l'observateur. Ce script
% donne les memes e et mesure au bloc MATLAB, en dehors de Simulink, et
% compare.
%
% CE QUI EST COMPARE
% ------------------
%   - les vecteurs de test du PINN (pinn_pid_modele.mat) : un pas du
%     reseau et ses derivees par rapport a Vout, iL et s, contre les
%     valeurs ecrites par entrainement_pinn.py ;
%   - pour chaque essai et chaque pas : u et les trois gains ;
%   - pour chaque fenetre de 0.5 ms : adaptation ou non, Vin_eff et iL
%     estimes par l'observateur.
% Tolerances : 1e-9 sur u, 1e-9 en relatif sur les gains, 1e-9 V et 1e-9 A
% sur l'observateur, aucune decision de fenetre differente. Les ecarts
% attendus viennent seulement de l'ordre des operations dans les produits
% matriciels et des fonctions tanh et sqrt (quelques 1e-15 a 1e-13).
%
% MESURE EN PLUS : temps de calcul d'un pas du regulateur seul (MATLAB
% interprete, hors Simulink), moyenne et pas le plus long (fenetre adaptee).
%
% ORDRE D'EXECUTION (PINN-PID)
% ----------------------------
%   1. entrainement_pinn.py ; 2. estimation_etat_pinn.py ; 3. banc_pinn_pid.py ;
%   4. ce script ; 5. Construction_PINN_PID.m ; 6. verifier_modele_pinn_pid.py ;
%   7. Simuler_PINN_PID.m ; 8. Construction_PINN_PID_Trois_Modeles.m ;
%   9. verifier_modeles_pinn_pid_trois.py ; 10. Simuler_PINN_PID_Trois_Modeles.m.
%
% Prerequis dans le dossier courant MATLAB : pinn_pid_adaptatif.m,
% pinn_pid_modele.mat, pinn_pid_reglages.mat, reference_rejeu_pinn_pid.mat.
% Duree : une a quelques minutes (230 000 pas). Compatible R2024a.
% ---------------------------------------------------------------------

clear; clc;

% --- Prerequis ---
for f = {'pinn_pid_adaptatif.m', 'pinn_pid_modele.mat', 'pinn_pid_reglages.mat', 'reference_rejeu_pinn_pid.mat'}
    if ~isfile(fullfile(pwd, f{1}))
        error('Fichier introuvable dans le dossier courant : %s', f{1});
    end
    if numel(which(f{1}, '-all')) ~= 1
        error('Il doit exister exactement un %s sur le chemin MATLAB.', f{1});
    end
end
clear pinn_pid_adaptatif                          % recharger la classe si elle a change

% --- 1. Vecteurs de test du PINN ---
m = load('pinn_pid_modele.mat');
bloc = pinn_pid_adaptatif('AfficherBilan', false);
setup(bloc, 0, 0);                                % charge les fichiers sans avancer
ecart = 0;
for q = 1:size(m.X_TEST, 1)
    x = double(m.X_TEST(q, :));                   % [Vout iL s Vin G]
    [vn, inn, D] = tester_pas_pinn(bloc, x(1), x(2), x(3), x(4));
    Dref = reshape(double(m.D_TEST(q, :)), 2, 3)';   % lignes : d/dVout, d/diL, d/ds ; colonnes : Vout', iL'
    ecart = max([ecart, abs(vn - m.Y_TEST(q, 1)), abs(inn - m.Y_TEST(q, 2)), max(abs(D(:) - Dref(:)))]);
end
release(bloc);
fprintf('Vecteurs de test du PINN : ecart maximal %.1e.\n', ecart);
if ecart > 1e-9
    error('Le pas du PINN du bloc ne redonne pas les vecteurs de test de entrainement_pinn.py.');
end

% --- 2. Rejeu pas par pas ---
ref = load('reference_rejeu_pinn_pid.mat');
codes = {'S1', 'S7b', 'S8b', 'S9'};
tout_ok = true;
temps_pas = [];
for c = 1:numel(codes)
    r = ref.(codes{c});
    e = double(r.e(:));
    mes = double(r.mesure(:));
    N = numel(e);
    bloc = pinn_pid_adaptatif('AfficherBilan', false);
    u = zeros(N, 1);
    K = zeros(N, 3);
    duree_pas = zeros(N, 1);
    adapte = false(0, 1);
    vin_eff = zeros(0, 1);
    iL_obs = zeros(0, 1);
    nfen = 0;
    t0 = tic;
    for k = 1:N
        tp = tic;
        [u(k), K(k, :)] = bloc(e(k), mes(k));
        duree_pas(k) = toc(tp);
        info = lire_fenetre(bloc);
        if info.nfen > nfen                       % une fenetre vient de se terminer
            nfen = info.nfen;
            adapte(end + 1, 1) = info.adapte; %#ok<SAGROW>
            vin_eff(end + 1, 1) = info.vin_eff; %#ok<SAGROW>
            iL_obs(end + 1, 1) = info.iL; %#ok<SAGROW>
        end
    end
    duree = toc(t0);
    release(bloc);
    temps_pas = [temps_pas; duree_pas]; %#ok<AGROW>
    ecart_u = max(abs(u - double(r.u(:))));
    ecart_K = max(max(abs(K - double(r.K)) ./ abs(double(r.K))));
    nw = min(numel(adapte), numel(r.adapte));
    diff_adapte = sum(adapte(1:nw) ~= logical(r.adapte(1:nw)));
    ecart_obs = max([max(abs(vin_eff(1:nw) - double(r.vin_eff(1:nw)))), max(abs(iL_obs(1:nw) - double(r.iL_obs(1:nw))))]);
    ok = ecart_u <= 1e-9 && ecart_K <= 1e-9 && ecart_obs <= 1e-9 && diff_adapte == 0 && numel(adapte) == numel(r.adapte);
    tout_ok = tout_ok && ok;
    fprintf(['%-4s : %6d pas, %4d fenetres ; ecart max sur u %.1e, sur les gains %.1e (relatif), ' ...
             'sur l''observateur %.1e ; adaptations differentes %d ; %5.1f s  -> %s\n'], codes{c}, N, numel(adapte), ...
            ecart_u, ecart_K, ecart_obs, diff_adapte, duree, ternaire(ok, 'identique', 'DIFFERENT'));
    fprintf('       gains finaux : Kp %.6f, Ki %.6e, Kd %.6f (banc : %.6f, %.6e, %.6f)\n', K(end, 1), K(end, 2), ...
            K(end, 3), r.K(end, 1), r.K(end, 2), r.K(end, 3));
end
fprintf('\nTemps d''un pas du regulateur seul (MATLAB interprete) : moyenne %.1f us, le plus long %.1f ms.\n', ...
        mean(temps_pas) * 1e6, max(temps_pas) * 1e3);
if tout_ok
    fprintf('\nRESULTAT : le bloc pinn_pid_adaptatif.m reproduit banc_pinn_pid.py. Etape suivante : Construction_PINN_PID.m.\n');
else
    error('Le bloc pinn_pid_adaptatif.m ne reproduit pas le banc : ne pas construire le modele Simulink.');
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
