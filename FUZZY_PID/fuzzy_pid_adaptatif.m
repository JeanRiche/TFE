classdef fuzzy_pid_adaptatif < matlab.System
    %% FUZZY_PID_ADAPTATIF -- bloc MATLAB System du Fuzzy-PID (base commune v2)
    %
    % VERSION
    % -------
    % 1 (6 octobre 2026) : base commune v2 (L = 10 mH, C = 47 uF, 22 kHz,
    % regulateur a Tc = 1/(22000*10) s), loi de Lu a derivee filtree, boite
    % des gains de boite_gains_elm.py, systeme flou de criteres_fuzzy_pid.txt.
    % Remplace l'ancien dossier FUZZY (bloc Fuzzy Logic Controller, gains
    % integres sans fuite, ancien circuit).
    %
    % CE QUE FAIT CE BLOC
    % -------------------
    % Regulateur PID incremental (loi de Lu et al., eq. 13-14, terme derive
    % sur l'erreur filtree) dont les gains Kp, Ki, Kd sont places toutes les
    % 0.5 ms dans la boite par un systeme flou (principe de Zhao, Tomizuka et
    % Isaka, 1993) a deux entrees : l'erreur moyenne de la fenetre E et sa
    % variation dE. C'est la copie exacte de la classe FuzzyPID de
    % banc_fuzzy_pid.py : memes reglages, memes noms, meme ordre des
    % operations. Tester_Fuzzy_PID_Rejeu.m verifie que les deux donnent la
    % meme commande et les memes gains pas par pas.
    %
    % ENTREE ET SORTIES (une fois par periode Tc, imposee par un Zero-Order
    % Hold a 1/(22000*10) s place devant le bloc)
    %   entree 1 : e = consigne - mesure (sortie de Sum1)
    %   sortie 1 : u = rapport cyclique, deja borne a [0.01 ; 0.99] (seule
    %              saturation du rapport cyclique), vers le PWM
    %   sortie 2 : K = gains [Kp Ki Kd] utilises pour ce pas (1 x 3),
    %              enregistres par Simuler_Fuzzy_PID.m
    %
    % L'ALGORITHME, A CHAQUE PERIODE Tc
    % ---------------------------------
    % 1. g(k) = Tc N (e(k) - ef(k)) ; ef(k+1) = ef(k) + Tc N (e(k) - ef(k)) ;
    %    u(k) = sat( u(k-1) + Kp (e(k) - e(k-1)) + Ki e(k) + Kd (g(k) - g(k-1)) ),
    %    depart u = 0.5, premier pas sans a-coup (e(k-1) = e(0), ef = e(0)).
    % 2. Sur chaque fenetre de NF = 110 periodes (0.5 ms) : erreur moyenne.
    % 3. Fin de fenetre n : E = ebar(n), dE = ebar(n) - ebar(n-1) (0 a la
    %    premiere fenetre). Appartenances aux cinq ensembles NG NP ZE PP PG
    %    (points de cassure SEUILS = [0.1 1 10] V), 25 regles, ET minimum,
    %    moyenne ponderee des singletons des tables TABLE_P, TABLE_I,
    %    TABLE_D : theta dans [0 ; 1]^3, K = K_MIN + theta .* dK, utilise
    %    pendant la fenetre n + 1. Aucun integrateur sur les gains.
    %
    % FICHIER LU (dans le dossier courant, un seul exemplaire)
    %   fuzzy_pid_reglages.mat : boite des gains, gains de depart, SEUILS,
    %                            TABLE_P, TABLE_I, TABLE_D, NF, TC, N_FILTRE,
    %                            D_MIN, D_MAX, U_DEPART (banc_fuzzy_pid.py)
    % Aucun nombre de l'algorithme n'est ecrit dans ce fichier : tout vient
    % du fichier de reglages, pour que le bloc et le banc ne puissent pas
    % diverger.
    %
    % Utilise dans Simulink en execution interpretee (Construction_Fuzzy_PID.m).
    % Compatible MATLAB R2024a. N'utilise pas la Fuzzy Logic Toolbox.

    properties (Nontunable)
        FichierReglages = 'fuzzy_pid_reglages.mat';  % reglages du bloc
        AfficherBilan (1,1) logical = true;          % une ligne de bilan a la fin de chaque simulation
    end

    properties (Access = private)
        % Reglages
        KMIN; KMAX; dK; K0; SEUILS; TABLES; NF; TCN; DMIN; DMAX; U0
        % Etat de la loi PID
        K; theta; u; e1; ef; g1; premier
        % Fenetre courante et precedente
        cpt; se; eb1; nfen
        % Diagnostic
        der_E; der_dE; der_theta; nb_hors_zn; theta_zn
    end

    methods
        function obj = fuzzy_pid_adaptatif(varargin)
            setProperties(obj, nargin, varargin{:});
        end

        function info = lire_fenetre(obj)
            % Etat de la derniere fenetre terminee (pour le test de rejeu).
            info = struct('nfen', obj.nfen, 'E', obj.der_E, 'dE', obj.der_dE, 'theta', obj.der_theta);
        end
    end

    methods (Access = protected)

        function setupImpl(obj)
            r = fuzzy_pid_adaptatif.charger(obj.FichierReglages);
            obj.KMIN = double(r.K_MIN(:)');           % 1 x 3
            obj.KMAX = double(r.K_MAX(:)');
            obj.dK = obj.KMAX - obj.KMIN;
            obj.K0 = double(r.K_DEPART(:)');
            obj.SEUILS = double(r.SEUILS(:)');        % [a b c] (V)
            obj.TABLES = zeros(3, 5, 5);              % sortie x ligne E x colonne dE
            obj.TABLES(1, :, :) = reshape(double(r.TABLE_P), [1 5 5]);
            obj.TABLES(2, :, :) = reshape(double(r.TABLE_I), [1 5 5]);
            obj.TABLES(3, :, :) = reshape(double(r.TABLE_D), [1 5 5]);
            obj.NF = double(r.NF);
            obj.TCN = double(r.TC) * double(r.N_FILTRE);   % meme produit que TCN dans le banc
            obj.DMIN = double(r.D_MIN);
            obj.DMAX = double(r.D_MAX);
            obj.U0 = double(r.U_DEPART);
            if ~isequal(size(r.TABLE_P), [5 5]) || ~isequal(size(r.TABLE_I), [5 5]) || ...
               ~isequal(size(r.TABLE_D), [5 5]) || numel(obj.SEUILS) ~= 3 || ...
               ~(obj.SEUILS(1) < obj.SEUILS(2) && obj.SEUILS(2) < obj.SEUILS(3))
                error('fuzzy_pid_adaptatif : tables ou seuils inattendus dans %s.', obj.FichierReglages);
            end
            obj.theta_zn = min(max((obj.K0 - obj.KMIN) ./ obj.dK, 0), 1);
            if max(abs(squeeze(obj.TABLES(:, 3, 3))' - obj.theta_zn)) > 1e-12
                error('fuzzy_pid_adaptatif : la regle (ZE, ZE) ne redonne pas les gains de depart.');
            end
        end

        function resetImpl(obj)
            obj.theta = obj.theta_zn;                 % depart a Ziegler-Nichols, dans la boite
            obj.K = obj.KMIN + obj.theta .* obj.dK;
            obj.u = obj.U0;
            obj.e1 = 0; obj.ef = 0; obj.g1 = 0;
            obj.premier = true;
            obj.cpt = 0; obj.se = 0; obj.eb1 = 0; obj.nfen = 0;
            obj.der_E = 0; obj.der_dE = 0; obj.der_theta = obj.theta; obj.nb_hors_zn = 0;
        end

        function [u, Kout] = stepImpl(obj, e)
            Kout = obj.K;                             % gains utilises pour ce pas
            if obj.premier
                obj.e1 = e; obj.ef = e; obj.g1 = 0;   % premier pas sans a-coup
                obj.premier = false;
            end
            g = obj.TCN * (e - obj.ef);               % derivee filtree (x Tc)
            brut = obj.u + obj.K(1) * (e - obj.e1) + obj.K(2) * e + obj.K(3) * (g - obj.g1);
            u = min(max(brut, obj.DMIN), obj.DMAX);   % seule saturation du rapport cyclique
            obj.ef = obj.ef + obj.TCN * (e - obj.ef); % filtre, Forward Euler
            obj.e1 = e; obj.g1 = g; obj.u = u;
            obj.se = obj.se + e;
            obj.cpt = obj.cpt + 1;
            if obj.cpt >= obj.NF
                fin_de_fenetre(obj);
            end
        end

        function releaseImpl(obj)
            if obj.AfficherBilan && ~isempty(obj.nfen) && obj.nfen > 0
                fprintf(['  Fuzzy-PID : %d fenetres, gains hors Ziegler-Nichols sur %d ; ' ...
                         'gains finaux Kp=%.5f Ki=%.4e Kd=%.4f\n'], obj.nfen, obj.nb_hors_zn, ...
                        obj.K(1), obj.K(2), obj.K(3));
            end
        end

        function n = getNumInputsImpl(~)
            n = 1;
        end
        function n = getNumOutputsImpl(~)
            n = 2;
        end
        function n1 = getInputNamesImpl(~)
            n1 = 'e';
        end
        function [n1, n2] = getOutputNamesImpl(~)
            n1 = 'u';
            n2 = 'K';
        end
        function [s1, s2] = getOutputSizeImpl(~)
            s1 = [1 1];
            s2 = [1 3];
        end
        function [d1, d2] = getOutputDataTypeImpl(~)
            d1 = 'double';
            d2 = 'double';
        end
        function [c1, c2] = isOutputComplexImpl(~)
            c1 = false;
            c2 = false;
        end
        function [f1, f2] = isOutputFixedSizeImpl(~)
            f1 = true;
            f2 = true;
        end
    end

    methods (Access = private)

        function fin_de_fenetre(obj)
            eb = obj.se / obj.NF;                     % erreur moyenne de la fenetre
            if obj.nfen == 0
                dE = 0;                               % pas de fenetre precedente
            else
                dE = eb - obj.eb1;
            end
            obj.theta = fuzzy_pid_adaptatif.inference(eb, dE, obj.TABLES, obj.SEUILS);
            obj.K = obj.KMIN + obj.theta .* obj.dK;
            if max(abs(obj.theta - obj.theta_zn)) > 0
                obj.nb_hors_zn = obj.nb_hors_zn + 1;
            end
            obj.der_E = eb; obj.der_dE = dE; obj.der_theta = obj.theta;
            obj.eb1 = eb;
            obj.nfen = obj.nfen + 1;
            obj.cpt = 0; obj.se = 0;
        end
    end

    methods (Static)

        function m = appartenances(x, s)
            % Degres d'appartenance de x a [NG NP ZE PP PG], points de cassure
            % s = [a b c] (memes formules que appartenances dans le banc).
            a = s(1); b = s(2); c = s(3);
            ax = abs(x);
            if ax <= a
                ze = 1; p = 0; gr = 0;
            elseif ax < b
                ze = (b - ax) / (b - a);
                p = (ax - a) / (b - a); gr = 0;
            elseif ax < c
                ze = 0;
                p = (c - ax) / (c - b); gr = (ax - b) / (c - b);
            else
                ze = 0; p = 0; gr = 1;
            end
            if x >= 0
                m = [0, 0, ze, p, gr];
            else
                m = [gr, p, ze, 0, 0];
            end
        end

        function theta = inference(E, dE, tables, s)
            % Sortie du systeme flou : ET minimum sur les 25 regles, moyenne
            % ponderee des singletons (regles parcourues ligne par ligne,
            % comme dans le banc). tables : 3 x 5 x 5.
            mE = fuzzy_pid_adaptatif.appartenances(E, s);
            mD = fuzzy_pid_adaptatif.appartenances(dE, s);
            num = [0, 0, 0];
            den = 0;
            for i = 1:5
                for j = 1:5
                    w = min(mE(i), mD(j));
                    if w > 0
                        num = num + w * tables(:, i, j)';
                        den = den + w;
                    end
                end
            end
            theta = num / den;
        end
    end

    methods (Static, Access = private)
        function s = charger(nom)
            % Charge un fichier .mat du dossier courant, avec un message clair s'il manque.
            if exist(nom, 'file') ~= 2
                error('fuzzy_pid_adaptatif : %s introuvable (il doit etre dans le dossier du modele).', nom);
            end
            s = load(nom);
        end
    end
end
