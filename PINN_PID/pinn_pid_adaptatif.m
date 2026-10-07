classdef pinn_pid_adaptatif < matlab.System
    %% PINN_PID_ADAPTATIF -- bloc MATLAB System du PINN-PID (base commune v2)
    %
    % VERSION
    % -------
    % 1 (5 octobre 2026) : base commune v2 (L = 10 mH, C = 47 uF, 22 kHz,
    % regulateur a Tc = 1/(22000*10) s). Remplace le bloc de l'ancienne base
    % (Te = 5 us, bornes internes [-1.5 ; 0.99], ensemble admissible
    % Kp 0.7-1, Ki 0.002-0.005, Kd 12-16), annule par le protocole commun.
    %
    % CE QUE FAIT CE BLOC
    % -------------------
    % Regulateur PID incremental (loi de Lu et al., eq. 13-14, terme derive
    % sur l'erreur filtree ; la meme loi, le meme depart et la meme boite
    % de gains que l'ELM-PID) dont les gains Kp, Ki, Kd sont reoptimises
    % toutes les 0.5 ms, si l'erreur de la fenetre depasse un seuil, par
    % 5 iterations d'Adam (Ito et Wasa, probleme P6). Le gradient vient
    % d'une simulation de 110 pas (horizon) avec un PINN qui predit le
    % convertisseur, a partir de l'etat estime par un observateur (filtre
    % de Kalman etendu a charge nominale). C'est la copie exacte de la
    % classe PINNPID de banc_pinn_pid.py : memes reglages, memes noms, meme
    % ordre des operations. Tester_PINN_PID_Rejeu.m verifie que les deux
    % donnent la meme commande et les memes gains pas par pas.
    %
    % ENTREES ET SORTIES (une fois par periode Tc, imposee par deux
    % Zero-Order Hold a 1/(22000*10) s places devant le bloc)
    %   entree 1 : e      = consigne - mesure (sortie de Sum1)
    %   entree 2 : mesure = tension mesuree (sortie du capteur) : le
    %              regulateur lit le capteur, jamais 100 - e
    %   sortie 1 : u      = rapport cyclique, deja borne a [0.01 ; 0.99]
    %              (seule saturation du rapport cyclique), vers le PWM
    %   sortie 2 : K      = gains [Kp Ki Kd] utilises pour ce pas (1 x 3)
    %
    % L'ALGORITHME, A CHAQUE PERIODE Tc (instant k)
    % ---------------------------------------------
    % 1. Observateur, correction par la mesure : etat [Vout iL Vin_eff],
    %    charge nominale G = 1/5 S (l'etape 3 a montre que la charge n'est
    %    pas estimable a partir de Vout).
    % 2. Loi de Lu : g = Tc N (e - ef) ; ef <- ef + Tc N (e - ef) ;
    %    u = sat( u + Kp (e - e1) + Ki e + Kd (g - g1) ) ; depart u = 0.5,
    %    premier pas sans a-coup.
    % 3. Observateur, prediction d'un pas avec la fraction de conduction
    %    appliquee : s = min(max(ceil(u x 1200) - phase, 0), 120) / 120,
    %    phase = mod(k x 120, 1200).
    % 4. Fin de fenetre (110 periodes) : si l'erreur efficace de la fenetre
    %    depasse SEUIL, 5 iterations d'Adam sur theta (gains normalises dans
    %    la boite), cout J = moyenne de [e^2 + RHO (du/0.01)^2] sur
    %    l'horizon + MU |theta - theta_debut|^2, gradient par
    %    retropropagation dans le temps ; projection sur [0 ; 1].
    %
    % FICHIERS LUS (dans le dossier courant, un seul exemplaire)
    %   pinn_pid_modele.mat   : poids du PINN (entrainement_pinn.py)
    %   pinn_pid_reglages.mat : boite, reglages d'Adam, cout, observateur,
    %                           table du modele physique (banc_pinn_pid.py)
    % Aucun nombre de l'algorithme n'est ecrit dans ce fichier : tout vient
    % de ces deux fichiers, pour que le bloc et le banc ne puissent pas
    % diverger.
    %
    % Utilise dans Simulink en execution interpretee (Construction_PINN_PID.m).
    % Compatible MATLAB R2024a.

    properties (Nontunable)
        FichierModele = 'pinn_pid_modele.mat';      % poids du PINN
        FichierReglages = 'pinn_pid_reglages.mat';  % reglages du bloc
        AfficherBilan (1,1) logical = true;         % une ligne de bilan a la fin de chaque simulation
    end

    properties (Access = private)
        % PINN (couches cachees tanh, puis couche lineaire)
        Wc; bc; nc; SVP; SIP; GC; GE
        % Reglages
        KMIN; KMAX; dK; K0; SEUIL; NH; ALPHA; BETA1; BETA2; EPSA; NADAM; MU; RHO; DUE; PSAT
        GNOM; VIN0; SIGY; SIGV; SIGI; SIGVIN; P0I; P0VIN
        NF; TCN; DMIN; DMAX; U0; NPER; NREG; LMOD; VF; PHI; GAM; NS; PRED_PINN
        % Etat de la loi PID
        K; theta; u; e1; ef; g1; premier
        % Observateur
        xo; Po; Qo; Ro; obs_init
        % Compteurs et fenetre
        k; cpt; se2; nfen; nb_adapt; der_adapte
    end

    methods
        function obj = pinn_pid_adaptatif(varargin)
            setProperties(obj, nargin, varargin{:});
        end

        function info = lire_fenetre(obj)
            % Etat de la derniere fenetre terminee (pour le test de rejeu).
            info = struct('nfen', obj.nfen, 'adapte', obj.der_adapte, 'vin_eff', obj.xo(3), 'iL', obj.xo(2));
        end

        function [vn, inn, D] = tester_pas_pinn(obj, v, i, s, vin)
            % Un pas du PINN et ses derivees (pour les vecteurs de test).
            [vn, inn, P, dvs, dis] = pas_pinn(obj, v, i, s, vin);
            D = [P(1,1) - 1, P(2,1); P(1,2), P(2,2) - 1; dvs, dis];
        end
    end

    methods (Access = protected)

        function setupImpl(obj)
            m = pinn_pid_adaptatif.charger(obj.FichierModele);
            r = pinn_pid_adaptatif.charger(obj.FichierReglages);
            % PINN : W1..Wn, b1..bn
            obj.Wc = {}; obj.bc = {};
            l = 1;
            while isfield(m, sprintf('W%d', l))
                obj.Wc{l} = double(m.(sprintf('W%d', l)));
                obj.bc{l} = double(m.(sprintf('b%d', l)));
                obj.bc{l} = obj.bc{l}(:)';
                l = l + 1;
            end
            obj.nc = numel(obj.Wc);
            if obj.nc < 2 || size(obj.Wc{1}, 1) ~= 6 || size(obj.Wc{end}, 2) ~= 2
                error('pinn_pid_adaptatif : tailles inattendues dans %s.', obj.FichierModele);
            end
            obj.SVP = double(m.SV); obj.SIP = double(m.SI);
            obj.GC = double(m.G_CENTRE); obj.GE = double(m.G_ECHELLE);
            if abs(double(m.TC) - double(r.TC)) > 1e-18
                error('pinn_pid_adaptatif : %s et %s n''ont pas la meme periode Tc.', obj.FichierModele, obj.FichierReglages);
            end
            % Reglages
            obj.KMIN = double(r.K_MIN(:)'); obj.KMAX = double(r.K_MAX(:)');
            obj.dK = obj.KMAX - obj.KMIN; obj.K0 = double(r.K_DEPART(:)');
            obj.SEUIL = double(r.SEUIL); obj.NH = double(r.NH);
            obj.ALPHA = double(r.ALPHA); obj.BETA1 = double(r.BETA1); obj.BETA2 = double(r.BETA2);
            obj.EPSA = double(r.EPS_ADAM); obj.NADAM = double(r.N_ADAM);
            obj.MU = double(r.MU); obj.RHO = double(r.RHO); obj.DUE = double(r.DU_ECHELLE); obj.PSAT = double(r.PENTE_SAT);
            obj.GNOM = double(r.G_NOM); obj.VIN0 = double(r.VIN_DEPART);
            obj.SIGY = double(r.SIG_Y); obj.SIGV = double(r.SIG_V); obj.SIGI = double(r.SIG_I);
            obj.SIGVIN = double(r.SIG_VIN); obj.P0I = double(r.P0_I); obj.P0VIN = double(r.P0_VIN);
            obj.NF = double(r.NF); obj.TCN = double(r.TC) * double(r.N_FILTRE);   % meme produit que TCN dans le banc
            obj.DMIN = double(r.D_MIN); obj.DMAX = double(r.D_MAX); obj.U0 = double(r.U_DEPART);
            obj.NPER = double(r.NPER); obj.NREG = double(r.NREG);
            obj.LMOD = double(r.L_MOD); obj.VF = double(r.VF);
            obj.PHI = double(r.PHI); obj.GAM = double(r.GAM);          % 121 x 4 ([p11 p12 p21 p22]) et 121 x 2
            obj.NS = size(obj.PHI, 1) - 1;
            obj.PRED_PINN = double(r.PREDICTEUR_PINN) ~= 0;
        end

        function resetImpl(obj)
            obj.theta = min(max((obj.K0 - obj.KMIN) ./ obj.dK, 0), 1);   % depart dans la boite
            obj.K = obj.KMIN + obj.theta .* obj.dK;
            obj.u = obj.U0;
            obj.e1 = 0; obj.ef = 0; obj.g1 = 0;
            obj.premier = true;
            obj.obs_init = false;
            obj.xo = [0, 0, obj.VIN0]; obj.Po = zeros(3); obj.Qo = zeros(3); obj.Ro = 0;
            obj.k = 0; obj.cpt = 0; obj.se2 = 0;
            obj.nfen = 0; obj.nb_adapt = 0; obj.der_adapte = false;
        end

        function [u, Kout] = stepImpl(obj, e, mesure)
            Kout = obj.K;                             % gains utilises pour ce pas
            kk = obj.k;
            if ~obj.obs_init                          % observateur : depart sur la premiere mesure
                obj.xo = [mesure, 0, obj.VIN0];
                if obj.SIGVIN > 0
                    p3 = obj.P0VIN;
                else
                    p3 = 0;
                end
                obj.Po = diag([obj.SIGY * obj.SIGY, obj.P0I, p3]);
                obj.Qo = diag([obj.SIGV * obj.SIGV, obj.SIGI * obj.SIGI, obj.SIGVIN * obj.SIGVIN]);
                obj.Ro = obj.SIGY * obj.SIGY;
                obj.obs_init = true;
            end
            % 1. Correction de l'observateur par la mesure
            P = obj.Po;
            S = P(1,1) + obj.Ro;
            Kk = P(:,1)' / S;                         % gain de Kalman (1 x 3)
            obj.xo = obj.xo + Kk * (mesure - obj.xo(1));
            obj.Po = P - Kk' * P(1,:);
            r = e + mesure;                           % consigne courante
            % 2. Loi de Lu
            if obj.premier
                obj.e1 = e; obj.ef = e; obj.g1 = 0;   % premier pas sans a-coup
                obj.premier = false;
            end
            g = obj.TCN * (e - obj.ef);               % derivee filtree (x Tc)
            brut = obj.u + obj.K(1) * (e - obj.e1) + obj.K(2) * e + obj.K(3) * (g - obj.g1);
            u = min(max(brut, obj.DMIN), obj.DMAX);   % seule saturation du rapport cyclique
            obj.ef = obj.ef + obj.TCN * (e - obj.ef); % filtre, Forward Euler
            obj.e1 = e; obj.g1 = g; obj.u = u;
            % 3. Prediction de l'observateur avec la fraction de conduction appliquee
            ph = mod(kk * obj.NREG, obj.NPER);        % phase de la porteuse
            s_app = min(max(ceil(u * obj.NPER) - ph, 0), obj.NREG) / obj.NREG;
            [vn, inn, Pm, ~, ~, dv_vin, di_vin] = pas_modele(obj, obj.xo(1), obj.xo(2), s_app, obj.xo(3));
            F = [Pm(1,1), Pm(1,2), dv_vin; Pm(2,1), Pm(2,2), di_vin; 0, 0, 1];
            obj.xo = [vn, inn, obj.xo(3)];
            obj.Po = F * obj.Po * F' + obj.Qo;
            % 4. Fenetre
            obj.se2 = obj.se2 + e * e;
            obj.cpt = obj.cpt + 1;
            obj.k = obj.k + 1;
            if obj.cpt >= obj.NF
                eff = sqrt(obj.se2 / obj.NF);
                adapte = false;
                if eff > obj.SEUIL
                    optimiser(obj, r);
                    adapte = true;
                    obj.nb_adapt = obj.nb_adapt + 1;
                end
                obj.der_adapte = adapte;
                obj.nfen = obj.nfen + 1;
                obj.cpt = 0; obj.se2 = 0;
            end
        end

        function releaseImpl(obj)
            if obj.AfficherBilan && ~isempty(obj.nfen) && obj.nfen > 0
                fprintf(['  PINN-PID : %d fenetres, gains changes sur %d ; gains finaux Kp=%.5f Ki=%.4e Kd=%.4f ; ' ...
                         'Vin_eff=%.1f V\n'], obj.nfen, obj.nb_adapt, obj.K(1), obj.K(2), obj.K(3), obj.xo(3));
            end
        end

        function n = getNumInputsImpl(~)
            n = 2;
        end
        function n = getNumOutputsImpl(~)
            n = 2;
        end
        function [n1, n2] = getInputNamesImpl(~)
            n1 = 'e';
            n2 = 'mesure';
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

        function [vn, inn, P, dvs, dis, dv_vin, di_vin] = pas_modele(obj, v, i, s, vin)
            % Un pas Tc du modele physique nominal (table interpolee en s),
            % memes formules que modele_pas dans banc_pinn_pid.py.
            x = s * obj.NS;
            j = min(floor(x), obj.NS - 1); f = x - j;   % segment de la table (indice j+1 en MATLAB)
            a = obj.PHI(j + 1, :); b = obj.PHI(j + 2, :);
            Pl = a + f * (b - a); dPl = (b - a) * obj.NS;
            ga = obj.GAM(j + 1, :); gb = obj.GAM(j + 2, :);
            gg = ga + f * (gb - ga); dg = (gb - ga) * obj.NS;
            src = (s * vin - (1 - s) * obj.VF) / obj.LMOD; dsrc = (vin + obj.VF) / obj.LMOD;
            vn = Pl(1) * v + Pl(2) * i + gg(1) * src;
            inn = Pl(3) * v + Pl(4) * i + gg(2) * src;
            dvs = dPl(1) * v + dPl(2) * i + dg(1) * src + gg(1) * dsrc;
            dis = dPl(3) * v + dPl(4) * i + dg(2) * src + gg(2) * dsrc;
            P = [Pl(1), Pl(2); Pl(3), Pl(4)];
            dv_vin = gg(1) * s / obj.LMOD; di_vin = gg(2) * s / obj.LMOD;
        end

        function [vn, inn, P, dvs, dis] = pas_pinn(obj, v, i, s, vin)
            % Un pas Tc du PINN a charge nominale, avec ses derivees par
            % rapport a (v, iL) et a s en mode direct (memes formules que
            % pinn_pas dans banc_pinn_pid.py).
            z = [1.0, (v - 100.0) / 60.0, (i - 12.0) / 10.0, 2 * s - 1, (vin - 195.0) / 45.0, ...
                 (obj.GNOM - obj.GC) / obj.GE];
            T = zeros(3, 6); T(1, 2) = 1 / 60.0; T(2, 3) = 1 / 10.0; T(3, 4) = 2.0;   % dz / d(v, iL, s)
            h = z;
            for l = 1:obj.nc - 1
                h = tanh(h * obj.Wc{l} + obj.bc{l});
                T = (T * obj.Wc{l}) .* (1 - h .* h);
            end
            N = h * obj.Wc{obj.nc} + obj.bc{obj.nc};
            TN = T * obj.Wc{obj.nc};
            vn = v + obj.SVP * N(1); inn = i + obj.SIP * N(2);
            P = [1 + obj.SVP * TN(1,1), obj.SVP * TN(2,1); obj.SIP * TN(1,2), 1 + obj.SIP * TN(2,2)];
            dvs = obj.SVP * TN(3,1); dis = obj.SIP * TN(3,2);
        end

        function [J, gK] = horizon(obj, Kh, x0, ctrl, r, k1, vin)
            % Simule NH pas avec la loi de Lu de gains Kh et le predicteur ;
            % cout (sans la proximite) et gradient par rapport a Kh
            % (retropropagation dans le temps). Copie de horizon() du banc.
            NHh = obj.NH;
            Kp = Kh(1); Ki = Kh(2); Kd = Kh(3);
            u_p = ctrl(1); e_p = ctrl(2); efh = ctrl(3); g_p = ctrl(4);
            v = x0(1); i = x0(2);
            pe = zeros(NHh, 1); pep = pe; pg = pe; pgp = pe; pu = pe; pup = pe; pdu = pe; pds = pe;
            pP = zeros(NHh, 4); pdvs = pe; pdis = pe;
            J = 0;
            for j = 1:NHh
                e = r - v;                            % erreur predite
                g = obj.TCN * (e - efh);              % derivee filtree
                b = u_p + Kp * (e - e_p) + Ki * e + Kd * (g - g_p);
                if b < obj.DMIN
                    u = obj.DMIN; du = obj.PSAT;
                elseif b > obj.DMAX
                    u = obj.DMAX; du = obj.PSAT;
                else
                    u = b; du = 1.0;
                end
                ph = mod((k1 + j - 1) * obj.NREG, obj.NPER);   % phase de la porteuse
                y = u * obj.NPER - ph;                % fraction de conduction continue et sa derivee
                if y <= 0
                    s = 0; ds = 0;
                elseif y >= obj.NREG
                    s = 1; ds = 0;
                else
                    s = y / obj.NREG; ds = obj.NPER / obj.NREG;
                end
                if obj.PRED_PINN
                    [vn, inn, Pm, dvs, dis] = pas_pinn(obj, v, i, s, vin);
                else
                    [vn, inn, Pm, dvs, dis] = pas_modele(obj, v, i, s, vin);
                end
                t_u = (u - u_p) / obj.DUE;
                J = J + (e * e + obj.RHO * (t_u * t_u));
                pe(j) = e; pep(j) = e_p; pg(j) = g; pgp(j) = g_p; pu(j) = u; pup(j) = u_p;
                pdu(j) = du; pds(j) = ds; pP(j, :) = [Pm(1,1), Pm(1,2), Pm(2,1), Pm(2,2)];
                pdvs(j) = dvs; pdis(j) = dis;
                efh = efh + obj.TCN * (e - efh);
                u_p = u; e_p = e; g_p = g;
                v = vn; i = inn;
            end
            J = J / NHh;
            gK = [0, 0, 0];
            cu = 2 * obj.RHO / (obj.DUE * obj.DUE) / NHh;
            lv = 0; li = 0; lu = 0; le = 0; lef = 0; lg = 0;   % adjoints
            for j = NHh:-1:1
                e = pe(j); e_p = pep(j); g = pg(j); g_p = pgp(j); u = pu(j); u_p = pup(j);
                dJu = lu + cu * (u - u_p) + (lv * pdvs(j) + li * pdis(j)) * pds(j);
                db = dJu * pdu(j);
                gK(1) = gK(1) + db * (e - e_p); gK(2) = gK(2) + db * e; gK(3) = gK(3) + db * (g - g_p);
                dJg = lg + db * Kd;
                dJe = 2 * e / NHh + db * (Kp + Ki) + dJg * obj.TCN + lef * obj.TCN + le;
                dJup = db - cu * (u - u_p);
                dJep = -db * Kp;
                dJgp = -db * Kd;
                dJef = -obj.TCN * dJg + lef * (1 - obj.TCN);
                lv_new = pP(j, 1) * lv + pP(j, 3) * li - dJe;
                li_new = pP(j, 2) * lv + pP(j, 4) * li;
                lv = lv_new; li = li_new; lu = dJup; le = dJep; lef = dJef; lg = dJgp;
            end
        end

        function optimiser(obj, r)
            % NADAM iterations d'Adam sur theta, horizon depuis l'etat estime.
            x0 = obj.xo(1:2); vin = obj.xo(3);
            ctrl = [obj.u, obj.e1, obj.ef, obj.g1];
            th0 = obj.theta; th = th0;
            m = [0, 0, 0]; vv = [0, 0, 0];            % moments d'Adam, remis a zero
            b1t = 1.0; b2t = 1.0;                     % BETA1^it et BETA2^it, par produits
            for it = 1:obj.NADAM
                b1t = b1t * obj.BETA1; b2t = b2t * obj.BETA2;
                [~, gK] = horizon(obj, obj.KMIN + th .* obj.dK, x0, ctrl, r, obj.k, vin);
                gth = gK .* obj.dK + 2 * obj.MU * (th - th0);
                m = obj.BETA1 * m + (1 - obj.BETA1) * gth;
                vv = obj.BETA2 * vv + (1 - obj.BETA2) * gth .* gth;
                th = th - obj.ALPHA * (m / (1 - b1t)) ./ (sqrt(vv / (1 - b2t)) + obj.EPSA);
                th = min(max(th, 0), 1);              % projection sur la boite
            end
            obj.theta = th;
            obj.K = obj.KMIN + th .* obj.dK;
        end
    end

    methods (Static, Access = private)
        function s = charger(nom)
            % Charge un fichier .mat du dossier courant, avec un message clair s'il manque.
            if exist(nom, 'file') ~= 2
                error('pinn_pid_adaptatif : %s introuvable (il doit etre dans le dossier du modele).', nom);
            end
            s = load(nom);
        end
    end
end
