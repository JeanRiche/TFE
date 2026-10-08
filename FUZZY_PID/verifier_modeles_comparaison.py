# =============================================================================
# verifier_modeles_comparaison.py
#
# VERSION
#   1 (8 octobre 2026).
#
# OBJECTIF
#   Controle independant, sans MATLAB, des modeles de comparaison construits
#   par Construire_Modeles_Comparaison.m (<PREFIXE>_<code>.slx, par exemple
#   ELM_PID_S10.slx ou ZN_S8a.slx). Chacun doit etre identique a son modele
#   source (Buck_Commun_<Methode>.slx, ou Buck_Commun.slx pour ZN), sauf :
#     - le rappel InitFcn : exactement le texte ecrit par
#       Construire_Modeles_Comparaison.m (se placer dans le dossier du
#       modele, puis charger_scenario('<code>') sans condition) ;
#     - le StopTime : (n - 0.5) x Tc, n = nombre d'instants du scenario
#       (duree de scenarios_communs.json) ; aucun autre reglage de la
#       configuration ne change ;
#     - les blocs d'observation ajoutes, et eux seuls : trois Scope et trois
#       To Workspace (Vout et consigne, iL, rapport cyclique), plus, pour
#       les methodes adaptatives, un Gain (gains rapportes a ZN), un Scope
#       et un To Workspace des gains. Les To Workspace : variables cmp_vout,
#       cmp_iL, cmp_d, cmp_K, periode 1/(22000*10) s, sans limite de points,
#       format Timeseries. Les liaisons ajoutees vont toutes VERS ces blocs ;
#       aucune n'en sort vers le modele.
#   Tous les blocs du modele source sont gardes avec tous leurs reglages
#   (sauf Position et ZOrder, ignores comme dans verifier_modele_*.py), toutes
#   ses liaisons de signal et electriques aussi, ainsi que ses autres
#   rappels (PreLoadFcn, StartFcn, ...). Les sous-systemes (autres fichiers
#   systems/*.xml) doivent etre identiques.
#
# COMMENT LANCER CE SCRIPT
#   python verifier_modeles_comparaison.py
#     controle tous les <PREFIXE>_<code>.slx du dossier du script ;
#   python verifier_modeles_comparaison.py ELM_PID_S10.slx ZN_S1.slx
#     controle ces fichiers ;
#   option --dossier D : dossier des modeles, des modeles sources et de
#     scenarios_communs.json (par defaut, celui du script).
#   Bibliotheque standard de Python uniquement. Doit finir par
#   "RESULTAT : les N modele(s) controle(s) sont conformes." ; le code de
#   sortie vaut 1 sinon.
#
# ORDRE
#   1. Construction_<Methode>.m (deja fait) ; 2. Construire_Modeles_Comparaison.m ;
#   3. ce script ; 4. Simuler_Modeles_Comparaison.m.
# =============================================================================

import os
import re
import sys
import json
import argparse
import zipfile
import xml.etree.ElementTree as ET

TC = 1.0 / (22000 * 10)                       # periode du regulateur (s)
K_ZN = (0.093910, 301.089, 7.3227e-06)        # P, I, D de Ziegler-Nichols (Gain de la vue des gains)
PWM = "PWM Generator\n(DC-DC)"
INIT_BASE = "if ~exist('sc_R0', 'var'), charger_scenario('S1'); end"   # rappel de Buck_Commun.slx
# prefixe -> (modele source, bloc dont la sortie 1 est le vecteur des gains, ou None)
METHODES = {"ELM_PID": ("Buck_Commun_ELM_PID", "ELM-PID Adaptatif"),
            "PINN_PID": ("Buck_Commun_PINN_PID", "PINN-PID Adaptatif"),
            "Fuzzy_PID": ("Buck_Commun_Fuzzy_PID", "Ordonnanceur Flou Zhao"),
            "PSO_PID": ("Buck_Commun_PSO_PID", None),
            "ZN": ("Buck_Commun", None)}
RAPPELS = ("PreLoadFcn", "PostLoadFcn", "InitFcn", "StartFcn", "PauseFcn", "ContinueFcn", "StopFcn",
           "PreSaveFcn", "PostSaveFcn", "CloseFcn", "SetupFcn", "CleanupFcn")
DEFAUTS_SIMULINK = {"Sum": {"Inputs": "++"}, "Product": {"Inputs": "2"}, "UnitDelay": {"InitialCondition": "0"}}


# %% ETAPE 1 : lecture des fichiers .slx

def lire_xml(chemin, interne):
    with zipfile.ZipFile(chemin) as z:
        with z.open(interne) as f:
            return ET.parse(f).getroot()


def systemes(chemin):
    with zipfile.ZipFile(chemin) as z:
        return sorted(n for n in z.namelist() if re.fullmatch(r"simulink/systems/[^/]+\.xml", n))


def membres(chemin):
    with zipfile.ZipFile(chemin) as z:
        return set(z.namelist())


def reglages(bloc):
    """Reglages d'un bloc (valeurs par defaut de son type, puis reglages
    ecrits, InstanceData compris), nombre de ports, et contenu des autres
    elements (masque, etc.) sous forme de texte."""
    sortie = dict(DEFAUTS_SIMULINK.get(bloc.get("BlockType"), {}))
    for p in bloc.findall("P"):
        sortie[p.get("Name")] = (p.text or "").strip()
    for inst in bloc.findall("InstanceData"):
        for p in inst.findall("P"):
            sortie["InstanceData." + p.get("Name")] = (p.text or "").strip()
    pc = bloc.find("PortCounts")
    sortie["PortCounts"] = str(sorted(pc.attrib.items())) if pc is not None else ""
    for enfant in bloc:
        if enfant.tag not in ("P", "InstanceData", "PortCounts"):
            sortie["<" + enfant.tag + ">"] = ET.tostring(enfant, encoding="unicode").strip()
    sortie["BlockType"] = bloc.get("BlockType")
    return sortie


def param(bloc, nom):
    """Reglage ecrit directement sous le bloc (pas dans un objet imbrique,
    comme la configuration d'un Scope), ou None s'il n'est pas ecrit
    (Simulink n'ecrit pas les valeurs par defaut)."""
    for p in bloc.findall("P"):
        if p.get("Name") == nom:
            return (p.text or "").strip()
    return None


def extremites(racine):
    """Liaisons de signal (couples source -> destination, branches comprises)
    et liaisons electriques (liste triee des listes triees de bornes)."""
    nom = {b.get("SID"): b.get("Name") for b in racine.findall("Block")}

    def lisible(texte):
        m = re.match(r"(\d+)#(.*)", texte or "")
        return f"{nom.get(m.group(1), '?' + m.group(1))}#{m.group(2)}" if m else (texte or "")

    signal, electrique = set(), []
    for ligne in racine.findall("Line"):
        bornes = [(p.get("Name"), lisible(p.text)) for p in ligne.iter("P") if p.get("Name") in ("Src", "Dst")]
        if ligne.get("LineType") == "Connection":
            electrique.append(tuple(sorted(b for _, b in bornes)))
        else:
            sources = [b for k, b in bornes if k == "Src"]
            for k, b in bornes:
                if k == "Dst" and sources:
                    signal.add((sources[0], b))
    return signal, sorted(electrique)


def configuration(chemin):
    sortie = {}

    def parcourir(element, chemin_xml):
        for enfant in element:
            cle = enfant.get("Name") or enfant.get("ClassName") or enfant.tag
            if enfant.tag == "P":
                sortie[chemin_xml + "/" + cle] = (enfant.text or "").strip()
            else:
                parcourir(enfant, chemin_xml + "/" + cle)

    parcourir(lire_xml(chemin, "simulink/configSet0.xml"), "")
    return sortie


def rappels(chemin):
    """Rappels du modele (blockdiagram.xml, niveau Model), fins de ligne
    normalisees."""
    modele = lire_xml(chemin, "simulink/blockdiagram.xml").find("Model")
    sortie = {}
    for p in modele.findall("P"):
        if p.get("Name") in RAPPELS:
            sortie[p.get("Name")] = (p.text or "").replace("\r\n", "\n").strip()
    return sortie


def nombre(texte):
    t = (texte or "").strip()
    if t.lower() == "inf":
        return float("inf")
    if not re.fullmatch(r"[0-9eE.+\-*/() ]+", t):
        return None
    try:
        return float(eval(t, {"__builtins__": {}}, {}))
    except Exception:
        return None


def texte_initfcn(mdl, code, ancien):
    """Meme texte que texte_initfcn de Construire_Modeles_Comparaison.m."""
    lignes = [f"% Modele de comparaison {mdl} (Construire_Modeles_Comparaison.m) : scenario {code}.",
              f"cmp_dossier_modele = fileparts(get_param('{mdl}', 'FileName'));",
              "if ~strcmp(pwd, cmp_dossier_modele), cd(cmp_dossier_modele); end",
              "clear cmp_dossier_modele",
              f"charger_scenario('{code}');"]
    txt = "\n".join(lignes)
    if ancien.strip() and ancien.strip() != INIT_BASE:
        txt += "\n" + ancien
    return txt


# %% ETAPE 2 : controle d'un modele

def controler(fichier, dossier, durees):
    """Renvoie (ok, notes, problemes) pour un modele <PREFIXE>_<code>.slx."""
    ok, notes, pb = [], [], []
    mdl = os.path.splitext(os.path.basename(fichier))[0]
    prefixe = next((p for p in sorted(METHODES, key=len, reverse=True) if mdl.startswith(p + "_")), None)
    if prefixe is None:
        return ok, notes, [f"{mdl} : prefixe inconnu (attendu : {', '.join(METHODES)})."]
    code = mdl[len(prefixe) + 1:]
    source_nom, bloc_gains = METHODES[prefixe]
    source = os.path.join(dossier, source_nom + ".slx")
    if not os.path.exists(source):
        return ok, notes, [f"modele source introuvable : {source}"]
    if code not in durees:
        return ok, notes, [f"scenario {code} absent de scenarios_communs.json."]

    # 1. Fichiers de l'archive et sous-systemes
    sys_s, sys_f = systemes(source), systemes(fichier)
    if sys_s != sys_f:
        pb.append(f"Systemes differents : {sys_s} -> {sys_f}.")
    for nom_sys in sys_s:
        if nom_sys != "simulink/systems/system_root.xml" and nom_sys in sys_f:
            a, b = lire_xml(source, nom_sys), lire_xml(fichier, nom_sys)
            ba = {x.get("Name"): reglages(x) for x in a.findall("Block")}
            bb = {x.get("Name"): reglages(x) for x in b.findall("Block")}
            for d in (ba, bb):
                for r in d.values():
                    r.pop("ZOrder", None)
                    r.pop("Position", None)
            if ba != bb or extremites(a) != extremites(b):
                pb.append(f"Sous-systeme modifie : {nom_sys}.")
    autres = sorted(membres(fichier) ^ membres(source))
    if autres:
        notes.append("Fichiers de l'archive presents d'un seul cote (sans effet sur le modele s'il s'agit de "
                     "metadonnees) : " + ", ".join(autres))

    rs = lire_xml(source, "simulink/systems/system_root.xml")
    rf = lire_xml(fichier, "simulink/systems/system_root.xml")
    bs = {b.get("Name"): b for b in rs.findall("Block")}
    bf = {b.get("Name"): b for b in rf.findall("Block")}

    # 2. Blocs gardes
    n_pb = len(pb)
    for nom in sorted(bs):
        if nom not in bf:
            pb.append(f"Bloc disparu : {nom!r}.")
            continue
        a, b = reglages(bs[nom]), reglages(bf[nom])
        diff = sorted(k for k in set(a) | set(b) if k not in ("Position", "ZOrder") and a.get(k) != b.get(k))
        if diff:
            pb.append(f"Bloc {nom!r} modifie : " + "; ".join(f"{k} {a.get(k)!r} -> {b.get(k)!r}" for k in diff))
    if len(pb) == n_pb:
        ok.append(f"Les {len(bs)} blocs du modele source sont gardes avec tous leurs reglages.")

    # 3. Blocs ajoutes
    sig_s, elec_s = extremites(rs)
    src_pwm = [s for s, d in sig_s if d == f"{PWM}#in:1"]
    if len(src_pwm) != 1:
        return ok, notes, pb + ["Le modele source n'a pas une seule liaison vers l'entree du PWM."]
    src_pwm = src_pwm[0]
    TYPES = {"Observation Vout et consigne": ("Scope", 2), "Observation iL": ("Scope", 1),
             "Observation rapport cyclique": ("Scope", 1), "Enregistrement Vout": ("ToWorkspace", 1),
             "Enregistrement iL": ("ToWorkspace", 1), "Enregistrement rapport cyclique": ("ToWorkspace", 1)}
    VARIABLES = {"Enregistrement Vout": "cmp_vout", "Enregistrement iL": "cmp_iL",
                 "Enregistrement rapport cyclique": "cmp_d"}
    nouvelles = {("Vout#out:1", "Observation Vout et consigne#in:1"),
                 ("Somme Consigne#out:1", "Observation Vout et consigne#in:2"),
                 ("Vout#out:1", "Enregistrement Vout#in:1"), ("iL#out:1", "Observation iL#in:1"),
                 ("iL#out:1", "Enregistrement iL#in:1"), (src_pwm, "Observation rapport cyclique#in:1"),
                 (src_pwm, "Enregistrement rapport cyclique#in:1")}
    if bloc_gains:
        if bloc_gains not in bs:
            pb.append(f"Bloc des gains {bloc_gains!r} absent du modele source.")
        TYPES.update({"Observation gains rapportes a ZN": ("Gain", 1), "Observation gains": ("Scope", 1),
                      "Enregistrement gains": ("ToWorkspace", 1)})
        VARIABLES["Enregistrement gains"] = "cmp_K"
        nouvelles |= {(f"{bloc_gains}#out:1", "Observation gains rapportes a ZN#in:1"),
                      ("Observation gains rapportes a ZN#out:1", "Observation gains#in:1"),
                      (f"{bloc_gains}#out:1", "Enregistrement gains#in:1")}
    n_pb = len(pb)
    ajoutes = set(bf) - set(bs)
    if ajoutes != set(TYPES):
        pb.append(f"Blocs ajoutes : {sorted(ajoutes)} au lieu de {sorted(TYPES)}.")
    for nom, (type_attendu, n_in) in TYPES.items():
        if nom not in bf:
            continue
        b = bf[nom]
        if b.get("BlockType") != type_attendu:
            pb.append(f"{nom!r} : type {b.get('BlockType')!r} au lieu de {type_attendu!r}.")
            continue
        pc = b.find("PortCounts")
        n_lu = int(pc.get("in", "0")) if pc is not None else None
        if n_lu is not None and n_lu != n_in:
            pb.append(f"{nom!r} : {n_lu} entree(s) au lieu de {n_in}.")
        if type_attendu == "ToWorkspace":
            if param(b, "VariableName") != VARIABLES[nom]:
                pb.append(f"{nom!r} : variable {param(b, 'VariableName')!r} au lieu de {VARIABLES[nom]!r}.")
            periode = nombre(param(b, "SampleTime"))
            if periode is None or abs(periode - TC) > 1e-12 * TC:
                pb.append(f"{nom!r} : periode {param(b, 'SampleTime')!r} au lieu de 1/(22000*10).")
            if nombre(param(b, "MaxDataPoints")) != float("inf"):
                pb.append(f"{nom!r} : MaxDataPoints {param(b, 'MaxDataPoints')!r} au lieu de 'inf'.")
            fmt = param(b, "SaveFormat")
            if fmt is not None and fmt != "Timeseries":
                pb.append(f"{nom!r} : format {fmt!r} au lieu de 'Timeseries'.")
        elif type_attendu == "Gain":
            vals = re.findall(r"1/([0-9eE.+\-]+)", param(b, "Gain") or "")
            if len(vals) != 3 or any(abs(float(x) - k) > 1e-12 * k for x, k in zip(vals, K_ZN)):
                pb.append(f"{nom!r} : gain {param(b, 'Gain')!r} au lieu de [1/P 1/I 1/D] de Ziegler-Nichols.")
            mult = param(b, "Multiplication")
            if mult is not None and mult != "Element-wise(K.*u)":
                pb.append(f"{nom!r} : multiplication {mult!r} au lieu de 'Element-wise(K.*u)'.")
        elif type_attendu == "Scope":
            st = param(b, "SampleTime")
            if st is not None and (nombre(st) is None or abs(nombre(st) - TC) > 1e-12 * TC):
                pb.append(f"{nom!r} : periode {st!r} au lieu de 1/(22000*10).")
    if len(pb) == n_pb:
        ok.append(f"Les {len(TYPES)} blocs d'observation ajoutes sont ceux prevus (types, entrees, variables cmp_*, "
                  "periode Tc, sans limite de points).")

    # 4. Liaisons
    sig_f, elec_f = extremites(rf)
    attendu = sig_s | nouvelles
    if sig_f == attendu:
        ok.append(f"Liaisons de signal : les {len(sig_s)} du modele source et les {len(nouvelles)} liaisons "
                  "d'observation, rien d'autre.")
    else:
        pb.append("Liaisons de signal differentes : manquantes " + str(sorted(attendu - sig_f))
                  + ", en trop " + str(sorted(sig_f - attendu)))
    sortantes = [(s, d) for s, d in sig_f if s.split("#")[0] in ajoutes and d.split("#")[0] not in ajoutes]
    if sortantes:
        pb.append("Des blocs ajoutes alimentent le modele : " + str(sorted(sortantes)))
    if elec_s == elec_f:
        ok.append(f"Liaisons electriques identiques ({len(elec_s)}).")
    else:
        pb.append("Liaisons electriques differentes de celles du modele source.")

    # 5. Configuration : seul StopTime change
    cs, cf = configuration(source), configuration(fichier)
    cles_stop = [k for k in set(cs) | set(cf) if k.split("/")[-1] == "StopTime"]
    diff = sorted(k for k in set(cs) | set(cf) if k not in cles_stop and cs.get(k) != cf.get(k))
    if diff:
        pb.append("Configuration modifiee hors StopTime : " + "; ".join(f"{k}: {cs.get(k)!r} -> {cf.get(k)!r}"
                                                                       for k in diff))
    n = int(round(durees[code] / TC)) + 1
    stop_attendu = (n - 0.5) * TC
    if len(cles_stop) != 1:
        pb.append(f"StopTime introuvable ou en double dans la configuration ({cles_stop}).")
    else:
        stop = nombre(cf.get(cles_stop[0]))
        if stop is None or abs(stop - stop_attendu) > 1e-15:
            pb.append(f"StopTime {cf.get(cles_stop[0])!r} au lieu de {stop_attendu!r} ((n - 0.5) x Tc, n = {n}).")
        elif not diff:
            ok.append(f"Configuration identique sauf StopTime = {cf.get(cles_stop[0])} s ((n - 0.5) x Tc, n = {n}).")

    # 6. Rappels
    ra, rb = rappels(source), rappels(fichier)
    init_attendu = texte_initfcn(mdl, code, ra.get("InitFcn", ""))
    if rb.get("InitFcn", "") == init_attendu:
        ok.append(f"Rappel InitFcn : charge {code} sans condition (texte de Construire_Modeles_Comparaison.m).")
    else:
        pb.append(f"Rappel InitFcn {rb.get('InitFcn', '')!r} au lieu de {init_attendu!r}.")
    autres_r = sorted(k for k in set(ra) | set(rb) if k != "InitFcn" and ra.get(k) != rb.get(k))
    if autres_r:
        pb.append("Autres rappels modifies : " + ", ".join(autres_r))
    return ok, notes, pb


# %% ETAPE 3 : programme

def main(argv=None):
    try:
        defaut = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        defaut = os.getcwd()
    ap = argparse.ArgumentParser(description="Controle des modeles <PREFIXE>_<code>.slx (sans MATLAB).")
    ap.add_argument("modeles", nargs="*", help="fichiers .slx a controler (par defaut : tous ceux du dossier)")
    ap.add_argument("--dossier", default=defaut, help="dossier des modeles, des sources et de scenarios_communs.json")
    args = ap.parse_args(argv)
    dossier = os.path.abspath(args.dossier)
    print("Dossier de travail :", dossier)
    with open(os.path.join(dossier, "scenarios_communs.json"), encoding="utf-8") as f:
        liste = json.load(f)
    durees = {e["code"]: float(e["duree"]) for e in liste["essais"] + liste.get("essais_complementaires", [])}
    if args.modeles:
        fichiers = [m if os.path.isabs(m) else os.path.join(dossier, m) for m in args.modeles]
    else:
        motif = re.compile(r"(" + "|".join(METHODES) + r")_(" + "|".join(map(re.escape, durees)) + r")\.slx")
        fichiers = sorted(os.path.join(dossier, f) for f in os.listdir(dossier) if motif.fullmatch(f))
    if not fichiers:
        print("Aucun modele <PREFIXE>_<code>.slx a controler (lancer Construire_Modeles_Comparaison.m).")
        return 1
    non_conformes = []
    for fichier in fichiers:
        print(f"\n=== {os.path.basename(fichier)} ===")
        if not os.path.exists(fichier):
            print(f"  [PROBLEME] fichier introuvable : {fichier}")
            non_conformes.append(fichier)
            continue
        ok, notes, pb = controler(fichier, dossier, durees)
        for x in ok:
            print("  [OK]", x)
        for x in notes:
            print("  [NOTE]", x)
        for x in pb:
            print("  [PROBLEME]", x)
        print("  -> " + ("conforme." if not pb else "NON CONFORME."))
        if pb:
            non_conformes.append(fichier)
    if non_conformes:
        print(f"\nRESULTAT : {len(non_conformes)} modele(s) sur {len(fichiers)} NON CONFORME(S) : "
              + ", ".join(os.path.basename(f) for f in non_conformes))
        return 1
    print(f"\nRESULTAT : les {len(fichiers)} modele(s) controle(s) sont conformes. Etape suivante : "
          "Simuler_Modeles_Comparaison.m.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
