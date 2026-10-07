classdef elm_pid_adaptatif < matlab.System
    %% ELM_PID_ADAPTATIF -- bloc MATLAB System de l'ELM-PID (base commune v2.1)
    %
    % VERSION
    % -------
    % 3 (7 octobre 2026) : porte limitee a la saturation et zone morte
    % d'estimation pour l'OS-ELM (M1), projection des gains sur l'ensemble
    % admissible avec glissement le long de sa frontiere (M2). Methode et
    % references : criteres_elm_pid.txt.
    %
    % CE QUE FAIT CE BLOC
    % -------------------
    % Regulateur PID incremental (loi de Lu et al., terme derive sur l'erreur
    % filtree) dont les gains Kp, Ki, Kd sont ajustes toutes les 0.5 ms par
    % un gradient normalise. Le sens et l'amplitude de chaque ajustement
    % viennent du jacobien d'un modele ELM du convertisseur, mis a jour en
    % ligne (OS-ELM). C'est la copie exacte de la classe ELMPID de
    % banc_elm_pid.py : memes reglages, memes noms, meme ordre des
    % operations. Tester_ELM_PID_Rejeu.m verifie que les deux donnent la meme
    % commande et les memes gains pas par pas.
    %
    % ENTREES ET SORTIES (une fois par periode Tc, imposee par deux
    % Zero-Order Hold a 1/(22000*10) s places devant le bloc)
    %   entree 1 : e      = consigne - mesure (sortie de Sum1)
    %   entree 2 : mesure = tension mesuree (jamais 100 - e)
    %   sortie 1 : u      = rapport cyclique, deja borne a [0.01 ; 0.99]
    %   sortie 2 : K      = gains [Kp Ki Kd] utilises pour ce pas (1 x 3)
    %
    % L'ALGORITHME, A CHAQUE PERIODE Tc
    % ---------------------------------
    % 1. g(k) = Tc N (e(k) - ef(k)) ; ef(k+1) = ef(k) + Tc N (e(k) - ef(k)) ;
    %    u(k) = sat( u(k-1) + Kp (e(k) - e(k-1)) + Ki e(k) + Kd (g(k) - g(k-1)) ),
    %    depart u = 0.5, premier pas sans a-coup.
    % 2. Fenetre de 110 periodes (0.5 ms) : moyennes ybar, dbar, ebar,
    %    sensibilite moyenne s de u aux gains ; une saturation de la loi rend
    %    la fenetre suspecte.
    % 3. Fin de fenetre : l'ELM predit ybar(n) depuis [ybar(n-1) ybar(n-2)
    %    dbar(n) dbar(n-1) dbar(n-2)] et donne J = d ybar(n) / d dbar(n).
    % 4. Porte (M1) : ni la fenetre ni les deux precedentes suspectes.
    %    a. OS-ELM si APPRENDRE et |ybar - prediction| > ZONE_MORTE_ESTIMATION ;
    %    b. si |ebar| > ZONE_MORTE et J > 0 : x = K ./ K_DEPART,
    %       phi = J (s .* K_DEPART) ;
    %       dx = ETA ebar phi / (EPS_PHI + phi phi') + ALPHA (x - x_prec) ;
    %       projection de x + dx sur l'ensemble admissible (M2,
    %       ensemble_gains_elm.mat) ; K = K_DEPART .* x.
    %
    % FICHIERS LUS (dans le dossier courant, un seul exemplaire)
    %   elm_pid_modele.mat      : modele ELM (entrainement_elm.py)
    %   elm_pid_reglages.mat    : reglages (banc_elm_pid.py)
    %   ensemble_gains_elm.mat  : table de l'ensemble admissible
    %                             (ensemble_gains_elm.py)
    % Aucun nombre de l'algorithme n'est ecrit dans ce fichier.
    %
    % Utilise dans Simulink en execution interpretee (Construction_ELM_PID.m).
    % Compatible MATLAB R2024a.

    properties (Nontunable)
        FichierModele = 'elm_pid_modele.mat';
        FichierReglages = 'elm_pid_reglages.mat';
        FichierEnsemble = 'ensemble_gains_elm.mat';
        AfficherBilan (1,1) logical = true;
    end

    properties (Access = private)
        W; B; BETA0; P0; XM; XE; TM; TE_; n
        BETA; P
        K0; ETA; ZM; ZME; ALPHA; EPS; LAMBDA; APPRENDRE; JC; GLISSEMENT
        XMIN; XMAX; NBIS; HGRAD
        GT; L2MIN; PASL2; NT
        NF; TCN; DMIN; DMAX; U0
        K; x; x_prec; u; e1; ef; g1; premier
        cpt; sy; sd; se; hors; S; sS
        yb1; yb2; db1; db2; sus1; sus2; nfen
        der_porte; der_adapte; nb_portes; nb_adapt
    end

    methods
        function obj = elm_pid_adaptatif(varargin)
            setProperties(obj, nargin, varargin{:});
        end

        function info = lire_fenetre(obj)
            % Etat de la derniere fenetre terminee (pour le test de rejeu).
            info = struct('nfen', obj.nfen, 'porte', obj.der_porte, 'adapte', obj.der_adapte);
        end
    end

    methods (Access = protected)

        function setupImpl(obj)
            m = elm_pid_adaptatif.charger(obj.FichierModele);
            r = elm_pid_adaptatif.charger(obj.FichierReglages);
            t = elm_pid_adaptatif.charger(obj.FichierEnsemble);
            obj.W = double(m.W);
            obj.B = double(m.B(:)');
            obj.BETA0 = double(m.BETA(:));
            obj.P0 = double(m.P0);
            obj.XM = double(m.X_MOY(:)');
            obj.XE = double(m.X_EC(:)');
            obj.TM = double(m.T_MOY);
            obj.TE_ = double(m.T_EC);
            obj.n = size(obj.W, 2);
            if size(obj.W, 1) ~= 5 || numel(obj.BETA0) ~= obj.n + 6 || ~isequal(size(obj.P0), [obj.n + 6, obj.n + 6])
                error('elm_pid_adaptatif : tailles inattendues dans %s.', obj.FichierModele);
            end
            obj.K0 = double(r.K_DEPART(:)');
            obj.ETA = double(r.ETA);
            obj.ZM = double(r.ZONE_MORTE);
            obj.ZME = double(r.ZONE_MORTE_ESTIMATION);
            obj.ALPHA = double(r.ALPHA);
            obj.EPS = double(r.EPS_PHI);
            obj.LAMBDA = double(r.LAMBDA);
            obj.APPRENDRE = double(r.APPRENDRE) ~= 0;
            obj.JC = double(r.JACOBIEN_CONSTANT);
            obj.GLISSEMENT = double(r.GLISSEMENT) ~= 0;
            obj.XMIN = double(r.MULT_MIN);
            obj.XMAX = double(r.MULT_MAX);
            obj.NBIS = double(r.N_BISSECTIONS);
            obj.HGRAD = double(r.H_GRADIENT);
            obj.NF = double(r.NF);
            obj.TCN = double(r.TC) * double(r.N_FILTRE);
            obj.DMIN = double(r.D_MIN);
            obj.DMAX = double(r.D_MAX);
            obj.U0 = double(r.U_DEPART);
            obj.GT = double(t.G_TABLE);
            obj.L2MIN = double(t.LOG2_MIN);
            obj.PASL2 = double(t.PAS_LOG2);
            obj.NT = size(obj.GT, 1);
            if max(abs(double(t.K_DEPART(:)') - obj.K0) ./ obj.K0) > 1e-12
                error('elm_pid_adaptatif : %s et %s n''ont pas les memes gains de depart.', ...
                      obj.FichierEnsemble, obj.FichierReglages);
            end
            if double(m.NF) ~= obj.NF || abs(double(m.TC) - double(r.TC)) > 1e-18
                error('elm_pid_adaptatif : %s et %s n''ont pas les memes fenetres (NF ou TC).', ...
                      obj.FichierModele, obj.FichierReglages);
            end
        end

        function resetImpl(obj)
            obj.BETA = obj.BETA0;
            obj.P = obj.P0;
            obj.x = [1 1 1];                          % multiplicateurs de Ziegler-Nichols
            obj.x_prec = obj.x;
            obj.K = obj.K0 .* obj.x;
            obj.u = obj.U0;
            obj.e1 = 0; obj.ef = 0; obj.g1 = 0;
            obj.premier = true;
            obj.cpt = 0; obj.sy = 0; obj.sd = 0; obj.se = 0; obj.hors = false;
            obj.S = [0 0 0]; obj.sS = [0 0 0];
            obj.yb1 = 0; obj.yb2 = 0; obj.db1 = 0; obj.db2 = 0;
            obj.sus1 = true; obj.sus2 = true;
            obj.nfen = 0;
            obj.der_porte = false; obj.der_adapte = false; obj.nb_portes = 0; obj.nb_adapt = 0;
        end

        function [u, Kout] = stepImpl(obj, e, mesure)
            Kout = obj.K;
            if obj.premier
                obj.e1 = e; obj.ef = e; obj.g1 = 0;
                obj.premier = false;
            end
            g = obj.TCN * (e - obj.ef);
            x1 = e - obj.e1;
            x2 = e;
            x3 = g - obj.g1;
            brut = obj.u + obj.K(1) * x1 + obj.K(2) * x2 + obj.K(3) * x3;
            u = min(max(brut, obj.DMIN), obj.DMAX);
            obj.ef = obj.ef + obj.TCN * (e - obj.ef);
            obj.e1 = e; obj.g1 = g; obj.u = u;
            obj.S = obj.S + [x1, x2, x3];
            obj.sS = obj.sS + obj.S;
            obj.sy = obj.sy + mesure;
            obj.sd = obj.sd + u;
            obj.se = obj.se + e;
            if brut < obj.DMIN || brut > obj.DMAX
                obj.hors = true;
            end
            obj.cpt = obj.cpt + 1;
            if obj.cpt >= obj.NF
                fin_de_fenetre(obj);
            end
        end

        function releaseImpl(obj)
            if obj.AfficherBilan && ~isempty(obj.nfen) && obj.nfen > 0
                fprintf(['  ELM-PID : %d fenetres, porte ouverte sur %d, gains changes sur %d ; ' ...
                         'gains finaux Kp=%.5f Ki=%.4e Kd=%.4f (x ZN %.3f %.3f %.3f)\n'], obj.nfen, obj.nb_portes, ...
                        obj.nb_adapt, obj.K(1), obj.K(2), obj.K(3), obj.x(1), obj.x(2), obj.x(3));
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

        function fin_de_fenetre(obj)
            yb = obj.sy / obj.NF;
            db = obj.sd / obj.NF;
            eb = obj.se / obj.NF;
            s = obj.sS / obj.NF;
            sus = obj.hors;
            porte = false;
            adapte = false;
            if obj.nfen >= 2
                xin = [obj.yb1, obj.yb2, db, obj.db1, obj.db2];
                [yhat, J, h] = elm_pid_adaptatif.evaluer_modele(obj.W, obj.B, obj.BETA, ...
                    obj.XM, obj.XE, obj.TM, obj.TE_, xin);
                if ~isnan(obj.JC)
                    J = obj.JC;                       % ablation : jacobien constant
                end
                err = yb - yhat;
                porte = ~sus && ~obj.sus1 && ~obj.sus2;   % M1 : saturation seulement
                if porte
                    if obj.APPRENDRE && abs(err) > obj.ZME    % a. OS-ELM, zone morte d'estimation
                        hc = h';
                        Ph = obj.P * hc;
                        gain = Ph / (obj.LAMBDA + hc' * Ph);
                        obj.BETA = obj.BETA + gain * (err / obj.TE_);
                        obj.P = (obj.P - gain * Ph') / obj.LAMBDA;
                    end
                    ancien = obj.x;
                    if abs(eb) > obj.ZM && J > 0       % b. gains
                        phi = J * (s .* obj.K0);
                        dx = obj.ETA * eb * phi / (obj.EPS + phi * phi') + obj.ALPHA * (obj.x - obj.x_prec);
                        obj.x = projeter(obj, obj.x, dx);
                        adapte = true;
                        obj.nb_adapt = obj.nb_adapt + 1;
                    end
                    obj.x_prec = ancien;
                    obj.K = obj.K0 .* obj.x;
                    obj.nb_portes = obj.nb_portes + 1;
                end
            end
            obj.der_porte = porte;
            obj.der_adapte = adapte;
            obj.yb2 = obj.yb1; obj.yb1 = yb;
            obj.db2 = obj.db1; obj.db1 = db;
            obj.sus2 = obj.sus1; obj.sus1 = sus;
            obj.nfen = obj.nfen + 1;
            obj.cpt = 0; obj.sy = 0; obj.sd = 0; obj.se = 0; obj.hors = false;
            obj.S = [0 0 0]; obj.sS = [0 0 0];
        end

        function g = g_interp(obj, x)
            % g de l'ensemble admissible, interpolation trilineaire en log2
            % des multiplicateurs (memes operations que g_interp du banc).
            uu = (log2(x) - obj.L2MIN) / obj.PASL2;
            uu = min(max(uu, 0), obj.NT - 1);
            i = min(floor(uu), obj.NT - 2);
            f = uu - i;
            g = 0;
            for di = 0:1
                if di, wi = f(1); else, wi = 1 - f(1); end
                for dj = 0:1
                    if dj, wj = f(2); else, wj = 1 - f(2); end
                    for dk = 0:1
                        if dk, wk = f(3); else, wk = 1 - f(3); end
                        g = g + wi * wj * wk * obj.GT(i(1) + di + 1, i(2) + dj + 1, i(3) + dk + 1);
                    end
                end
            end
        end

        function xn = projeter(obj, xc, dx)
            % Projection du pas sur l'ensemble admissible (M2), avec
            % glissement le long de la frontiere (meme algorithme que
            % projeter() du banc).
            lo_ = obj.XMIN; hi_ = obj.XMAX;
            xn = min(max(xc + dx, lo_), hi_);
            if g_interp(obj, xn) <= 0
                return;
            end
            a = 0; b = 1;
            for it = 1:obj.NBIS
                m = 0.5 * (a + b);
                if g_interp(obj, min(max(xc + m * dx, lo_), hi_)) <= 0
                    a = m;
                else
                    b = m;
                end
            end
            xb = min(max(xc + a * dx, lo_), hi_);
            if ~obj.GLISSEMENT
                xn = xb;
                return;
            end
            hh = obj.HGRAD;
            gr = [0 0 0];
            for q = 1:3
                ep = [0 0 0];
                ep(q) = hh;
                gr(q) = (g_interp(obj, xb + ep) - g_interp(obj, xb - ep)) / (2 * hh);
            end
            reste = (1 - a) * dx;
            sortant = gr * reste';
            if sortant > 0
                reste = reste - sortant / (gr * gr') * gr;
            end
            xn = min(max(xb + reste, lo_), hi_);
            if g_interp(obj, xn) <= 0
                return;
            end
            a = 0; b = 1;
            for it = 1:obj.NBIS
                m = 0.5 * (a + b);
                if g_interp(obj, min(max(xb + m * reste, lo_), hi_)) <= 0
                    a = m;
                else
                    b = m;
                end
            end
            xn = min(max(xb + a * reste, lo_), hi_);
        end
    end

    methods (Static)

        function [y, J, h] = evaluer_modele(W, B, BETA, XM, XE, TM, TE_, x)
            % Prediction ybar(n), jacobien d ybar(n) / d dbar(n) et vecteur h
            % (memes formules que ELMPID.modele dans banc_elm_pid.py).
            n = size(W, 2);
            xn = (x - XM) ./ XE;
            g = 1 ./ (1 + exp(-(xn * W + B)));
            h = [g, xn, 1];
            y = (h * BETA) * TE_ + TM;
            dy = ((g .* (1 - g)) .* BETA(1:n)') * W' + BETA(n+1:n+5)';
            J = dy(3) / XE(3) * TE_;
        end
    end

    methods (Static, Access = private)
        function s = charger(nom)
            if exist(nom, 'file') ~= 2
                error('elm_pid_adaptatif : %s introuvable (il doit etre dans le dossier du modele).', nom);
            end
            s = load(nom);
        end
    end
end
