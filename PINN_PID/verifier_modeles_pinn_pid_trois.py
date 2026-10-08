# =============================================================================
# verifier_modeles_pinn_pid_trois.py
#
# VERSION
#   3 (8 octobre 2026), trois modeles construits sur les
#   modeles de base de Jean-Riche. Copie de
#   ELM_PID/verifier_modeles_elm_pid_trois.py (meme montage, repris de
#   verifier_modeles_fuzzy_pid_trois.py) ; changent seulement les noms des
#   modeles, des blocs et de la classe.
#
# OBJECTIF
#   Controle independant, sans MATLAB, des trois modeles construits par
#   Construction_PINN_PID_Trois_Modeles.m. Chacun doit etre identique a son
#   modele de base, sauf :
#     PID_Classique_Control.slx                     -> PINN_PID_Control.slx
#     PID_Classique_Control_control_disturbance.slx -> PINN_PID_Control_control_disturbance.slx
#     PID_Classique_Control_load_disturbance.slx    -> PINN_PID_Control_load_disturbance.slx
#   Differences permises :
#     - "PID Controller" GARDE : ControllerParametersSource internal ->
#       external, et les quatre aiguillages du masque que Simulink bascule
#       seul avec elle (ParallelPVariant, IVariant, DVariant, NVariant :
#       InternalParameters -> ExternalParameters) ; 5 entrees au lieu de 1 ;
#     - six blocs ajoutes : trois Zero-Order Hold a 1/(22000*10) s
#       ("Echantillonneur Erreur PINN", "Echantillonneur Mesure PINN",
#       "Echantillonneur Commande PINN"), "PINN-PID Adaptatif" (MATLAB System,
#       classe pinn_pid_adaptatif, execution interpretee, 3 entrees,
#       1 sortie), "Demux Gains PINN" (3 sorties), "Constante N Filtre"
#       (valeur du champ N du PID) ;
#     - liaisons : Sum1 -> PID (entree u) ; Sum1 -> Echantillonneur Erreur
#       -> entree 1 de l'adaptateur ; Vout -> Echantillonneur Mesure ->
#       entree 2 ; sortie du PID -> Echantillonneur Commande -> entree 3 (le
#       PID alimente toujours le PWM) ; adaptateur -> Demux ; Demux 1, 2, 3
#       et Constante N -> quatre autres entrees du PID, toutes differentes.
#       Le reste ne change pas.
#   Controles aussi : configuration, rappels du modele (InitFcn,
#   PreLoadFcn...), contenu Stateflow (calcul de F1) caractere pour
#   caractere.
#
# COMMENT LANCER CE SCRIPT :
#   python verifier_modeles_pinn_pid_trois.py
#   depuis le dossier ou se trouvent les trois modeles de base et les trois
#   modeles construits. Bibliotheque standard de Python uniquement.
#   Doit finir par "RESULTAT : les trois modeles sont conformes."
#
# ORDRE D'EXECUTION
#   1. Construction_PINN_PID_Trois_Modeles.m ; 2. ce script ;
#   3. Simuler_PINN_PID_Trois_Modeles.m.
# =============================================================================


# %% ETAPE 0 : bibliotheques et fichiers

import os                                     # chemins de fichiers
import re                                     # expressions regulieres
import zipfile                                # un .slx est une archive zip
import xml.etree.ElementTree as ET            # lecture des fichiers XML

try:                                          # dossier du script (ou dossier courant dans un notebook)
    DOSSIER = os.path.dirname(os.path.abspath(__file__))
except NameError:
    DOSSIER = os.getcwd()
PAIRES = [("PID_Classique_Control", "PINN_PID_Control"),            # (modele de base, modele construit)
          ("PID_Classique_Control_control_disturbance", "PINN_PID_Control_control_disturbance"),
          ("PID_Classique_Control_load_disturbance", "PINN_PID_Control_load_disturbance")]
TC = 1.0 / (22000 * 10)                       # periode attendue de l'echantillonneur (s)
PWM = "PWM Generator\n(DC-DC)"                # nom du bloc PWM (vrai saut de ligne)
PID = "PID Controller"
CLASSE = "pinn_pid_adaptatif"                  # classe du bloc MATLAB System
NOM_SYS = "PINN-PID Adaptatif"
NOM_ZOHE = "Echantillonneur Erreur PINN"
NOM_ZOHM = "Echantillonneur Mesure PINN"
NOM_ZOHU = "Echantillonneur Commande PINN"
NOM_DEMUX = "Demux Gains PINN"
NOM_N = "Constante N Filtre"
MESURE = "Vout"                               # bloc de mesure (pas de bruit ni de quantification ici)
TYPES_AJOUTES = {NOM_ZOHE: "ZeroOrderHold", NOM_ZOHM: "ZeroOrderHold", NOM_ZOHU: "ZeroOrderHold",
                 NOM_SYS: "MATLABSystem", NOM_DEMUX: "Demux", NOM_N: "Constant"}
VARIANTES_PID = ("ParallelPVariant", "IVariant", "DVariant", "NVariant")
print("Dossier de travail :", DOSSIER)

# Valeurs par defaut internes de Simulink pour les reglages compares
# (memes valeurs que verifier_modele_commun.py, version 2.1).
DEFAUTS_SIMULINK = {"Sum": {"Inputs": "++"}, "Product": {"Inputs": "2"},
                    "UnitDelay": {"InitialCondition": "0"}}


# %% ETAPE 1 : lecture des fichiers

def lire_xml(chemin, interne):
    """Racine XML d'un fichier interne de l'archive .slx."""
    with zipfile.ZipFile(chemin) as z:
        with z.open(interne) as f:
            return ET.parse(f).getroot()


def lire_texte(chemin, interne):
    """Contenu texte d'un fichier interne de l'archive (vide s'il manque)."""
    with zipfile.ZipFile(chemin) as z:
        if interne not in z.namelist():
            return ""
        return z.read(interne).decode("utf-8", errors="replace")


def reglages(bloc):
    """Reglages d'un bloc : valeurs par defaut de son type, puis reglages ecrits."""
    sortie = dict(DEFAUTS_SIMULINK.get(bloc.get("BlockType"), {}))
    for p in bloc.findall("P"):
        sortie[p.get("Name")] = (p.text or "").strip()
    for inst in bloc.findall("InstanceData"):
        for p in inst.findall("P"):
            sortie[p.get("Name")] = (p.text or "").strip()
    return sortie


def param(bloc, nom):
    """Valeur du reglage 'nom' a n'importe quelle profondeur du bloc, ou
    None s'il n'est pas ecrit (Simulink n'ecrit pas les valeurs par defaut)."""
    for p in bloc.iter("P"):
        if p.get("Name") == nom:
            return (p.text or "").strip()
    return None


def contient(bloc, texte):
    """Vrai si 'texte' apparait quelque part dans la definition du bloc."""
    return texte in ET.tostring(bloc, encoding="unicode")


def extremites(racine):
    """Liaisons de signal (ensemble de couples source -> destination) et
    liaisons electriques (liste triee des listes triees de bornes), avec
    les noms des blocs, branches comprises."""
    nom = {b.get("SID"): b.get("Name") for b in racine.findall("Block")}

    def lisible(texte):
        m = re.match(r"(\d+)#(.*)", texte or "")
        return f"{nom.get(m.group(1), '?')}#{m.group(2)}" if m else (texte or "")

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
    """Reglages de simulation (configSet0.xml) : chemin XML -> valeur."""
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
    """Rappels du modele (InitFcn, PreLoadFcn, StartFcn, ...) : nom -> texte."""
    texte = lire_texte(chemin, "simulink/blockdiagram.xml")
    return {m.group(1): m.group(2).strip() for m in re.finditer(r'<P Name="(\w*Fcn)">(.*?)</P>', texte, re.S)}


def fichiers_stateflow(chemin):
    """Fichiers Stateflow (blocs MATLAB Function) de l'archive, sans machine.xml."""
    with zipfile.ZipFile(chemin) as z:
        return sorted(n for n in z.namelist() if n.startswith("simulink/stateflow/") and n.endswith(".xml")
                      and not n.endswith("machine.xml"))


def nombre(texte):
    """Valeur d'un reglage numerique simple (nombre ou expression avec
    chiffres, point, exposant, + - * / et parentheses), sinon None."""
    t = (texte or "").strip()
    if not re.fullmatch(r"[0-9eE.+\-*/() ]+", t):
        return None
    try:
        return float(eval(t, {"__builtins__": {}}, {}))
    except Exception:
        return None


# %% ETAPE 2 : les controles, modele par modele

def verifier(nom_base, nom_fz):
    """Controles pour un modele construit ; renvoie (ok, notes, problemes)."""
    fichier_base = os.path.join(DOSSIER, nom_base + ".slx")
    fichier_fz = os.path.join(DOSSIER, nom_fz + ".slx")
    ok, pb, notes = [], [], []
    for f in (fichier_base, fichier_fz):
        if not os.path.exists(f):
            return ok, notes, [f"Fichier introuvable : {os.path.basename(f)}"]
    rs = lire_xml(fichier_base, "simulink/systems/system_root.xml")
    rf = lire_xml(fichier_fz, "simulink/systems/system_root.xml")
    bs = {b.get("Name"): b for b in rs.findall("Block")}
    bf = {b.get("Name"): b for b in rf.findall("Block")}

    # 1. Blocs gardes (le PID compris)
    n_pb = len(pb)
    for nom in sorted(bs):
        if nom not in bf:
            pb.append(f"Bloc disparu : {nom!r}.")
            continue
        a, b = reglages(bs[nom]), reglages(bf[nom])
        diff = sorted(k for k in set(a) | set(b) if k not in ("Position", "ZOrder") and a.get(k) != b.get(k))
        lien = [k for k in diff if k in ("SourceBlock", "LibraryVersion")]
        if lien and a.get("LibrarySourceBlock") and a.get("LibrarySourceBlock") == b.get("LibrarySourceBlock"):
            notes.append(f"Bloc {nom!r} : lien de bibliotheque mis a jour par Simulink ("
                         + ", ".join(f"{k} {a.get(k)!r} -> {b.get(k)!r}" for k in lien) + ").")
            diff = [k for k in diff if k not in lien]
        if nom == PID:
            if a.get("ControllerParametersSource") != "internal" or b.get("ControllerParametersSource") != "external":
                pb.append(f"PID : ControllerParametersSource {a.get('ControllerParametersSource')!r} -> "
                          f"{b.get('ControllerParametersSource')!r} au lieu de 'internal' -> 'external'.")
            bascules = [k for k in diff if k in VARIANTES_PID]
            for k in bascules:
                if a.get(k) != "InternalParameters" or b.get(k) != "ExternalParameters":
                    pb.append(f"PID : {k} {a.get(k)!r} -> {b.get(k)!r} au lieu de 'InternalParameters' -> "
                              "'ExternalParameters'.")
            if bascules:
                notes.append("PID : aiguillages internes du masque bascules par Simulink avec la source des "
                             "parametres : " + ", ".join(sorted(bascules)) + ".")
            diff = [k for k in diff if k != "ControllerParametersSource" and k not in VARIANTES_PID]
        if diff:
            pb.append(f"Bloc {nom!r} modifie : " + ", ".join(f"{k} {a.get(k)!r} -> {b.get(k)!r}" for k in diff))
    if len(pb) == n_pb:
        ok.append(f"Les {len(bs)} blocs de {nom_base}.slx sont gardes avec leurs reglages ; le PID n'a change que "
                  "sa source de parametres.")
    ports_pid = bf[PID].find("PortCounts") if PID in bf else None
    if ports_pid is None or ports_pid.get("in") != "5" or ports_pid.get("out") != "1":
        pb.append(f"PID : entrees/sorties {None if ports_pid is None else (ports_pid.get('in'), ports_pid.get('out'))}"
                  " au lieu de 5 entrees et 1 sortie.")

    # 2. Blocs ajoutes
    n_pb = len(pb)
    ajoutes = set(bf) - set(bs)
    if ajoutes != set(TYPES_AJOUTES):
        pb.append(f"Blocs ajoutes : {sorted(ajoutes)} au lieu de {sorted(TYPES_AJOUTES)}.")
    for nom, type_attendu in TYPES_AJOUTES.items():
        if nom in bf and bf[nom].get("BlockType") != type_attendu:
            pb.append(f"{nom!r} : type {bf[nom].get('BlockType')!r} au lieu de {type_attendu!r}.")
    for nom_z in (NOM_ZOHE, NOM_ZOHM, NOM_ZOHU):
        if nom_z in bf:
            periode = nombre(param(bf[nom_z], "SampleTime"))
            if periode is None or abs(periode - TC) > 1e-9 * TC:
                pb.append(f"{nom_z!r} : periode {param(bf[nom_z], 'SampleTime')!r} au lieu de 1/(22000*10).")
    if NOM_SYS in bf:
        classe = param(bf[NOM_SYS], "System")
        if classe is not None and classe != CLASSE:
            pb.append(f"{NOM_SYS!r} : classe {classe!r} au lieu de {CLASSE!r}.")
        elif classe is None and not contient(bf[NOM_SYS], CLASSE):
            pb.append(f"{NOM_SYS!r} : la classe {CLASSE!r} n'apparait pas dans sa definition.")
        mode = param(bf[NOM_SYS], "SimulateUsing")
        if mode is None:
            notes.append(f"{NOM_SYS!r} : reglage SimulateUsing non ecrit sous ce nom dans le fichier (a verifier a "
                         "l'oeil : Simulate using = Interpreted execution).")
        elif mode != "Interpreted execution":
            pb.append(f"{NOM_SYS!r} : SimulateUsing = {mode!r} au lieu de 'Interpreted execution'.")
        gf = param(bf[NOM_SYS], "GainsFixes")
        if gf is not None and gf.lower() not in ("false", "off", "0"):
            pb.append(f"{NOM_SYS!r} : GainsFixes = {gf!r} ; le modele enregistre doit avoir GainsFixes = false.")
        pc = bf[NOM_SYS].find("PortCounts")
        if pc is not None and (pc.get("in") != "3" or pc.get("out") != "1"):
            pb.append(f"{NOM_SYS!r} : {pc.get('in')} entrees et {pc.get('out')} sorties au lieu de 3 et 1.")
    if NOM_DEMUX in bf and (param(bf[NOM_DEMUX], "Outputs") or "") != "3":
        pb.append(f"{NOM_DEMUX!r} : Outputs = {param(bf[NOM_DEMUX], 'Outputs')!r} au lieu de '3'.")
    if NOM_N in bf and PID in bs:
        vn, vp = nombre(param(bf[NOM_N], "Value")), nombre(reglages(bs[PID]).get("N"))
        if vn is None or vp is None or vn != vp:
            pb.append(f"{NOM_N!r} : valeur {param(bf[NOM_N], 'Value')!r} au lieu de N = {reglages(bs[PID]).get('N')!r}.")
    if len(pb) == n_pb:
        ok.append(f"Les six blocs ajoutes sont ceux prevus (trois echantillonneurs a 1/(22000*10) s, classe {CLASSE}, "
                  "Demux a 3 sorties, N egal au champ du PID).")

    # 3. Liaisons
    sig_s, elec_s = extremites(rs)
    sig_f, elec_f = extremites(rf)
    avant = ("Sum1#out:1", f"{PID}#in:1")
    if avant not in sig_s or (f"{PID}#out:1", f"{PWM}#in:1") not in sig_s or (f"{MESURE}#out:1", "Sum1#in:2") not in sig_s:
        pb.append(f"{nom_base}.slx n'a pas les liaisons du PID attendues : fichier de depart inattendu.")
    vers_pid = {}                             # source -> entree du PID
    for src, dst in sig_f:
        if dst.startswith(f"{PID}#in:"):
            vers_pid[src] = int(dst.split(":")[-1])
    sources_pid = {"Sum1#out:1": "u", f"{NOM_DEMUX}#out:1": "P", f"{NOM_DEMUX}#out:2": "I",
                   f"{NOM_DEMUX}#out:3": "D", f"{NOM_N}#out:1": "N"}
    if set(vers_pid) != set(sources_pid) or set(vers_pid.values()) != {1, 2, 3, 4, 5}:
        pb.append(f"Entrees du PID : {sorted(vers_pid.items())} ; attendu u, P, I, D, N sur cinq entrees differentes.")
    else:
        notes.append("Entrees du PID utilisees : " + ", ".join(f"{sources_pid[s]} = {vers_pid[s]}" for s in sources_pid)
                     + " (ordre controle par l'auto-test T0 de la construction).")
    nouvelles = {("Sum1#out:1", f"{NOM_ZOHE}#in:1"), (f"{NOM_ZOHE}#out:1", f"{NOM_SYS}#in:1"),
                 (f"{MESURE}#out:1", f"{NOM_ZOHM}#in:1"), (f"{NOM_ZOHM}#out:1", f"{NOM_SYS}#in:2"),
                 (f"{PID}#out:1", f"{NOM_ZOHU}#in:1"), (f"{NOM_ZOHU}#out:1", f"{NOM_SYS}#in:3"),
                 (f"{NOM_SYS}#out:1", f"{NOM_DEMUX}#in:1")}
    nouvelles |= {(s, f"{PID}#in:{n}") for s, n in vers_pid.items()}
    attendu = (sig_s - {avant}) | nouvelles
    if sig_f == attendu:
        ok.append(f"Liaisons de signal : les {len(sig_s) - 1} liaisons gardees, Sum1 -> PID (entree u) et les "
                  f"{len(nouvelles) - 1} prevues, rien d'autre.")
    else:
        manque = sorted(attendu - sig_f)
        trop = sorted(sig_f - attendu)
        pb.append("Liaisons de signal differentes : manquantes " + str([f"{a} -> {b}" for a, b in manque])
                  + ", en trop " + str([f"{a} -> {b}" for a, b in trop]))
    if elec_s == elec_f:
        ok.append(f"Liaisons electriques identiques ({len(elec_s)} liaisons).")
    else:
        pb.append(f"Liaisons electriques differentes de celles de {nom_base}.slx.")

    # 4. Configuration et rappels du modele
    cs, cf = configuration(fichier_base), configuration(fichier_fz)
    diff_conf = sorted(k for k in set(cs) | set(cf) if cs.get(k) != cf.get(k))
    if diff_conf:
        pb.append("Configuration modifiee : " + ", ".join(f"{k}: {cs.get(k)!r} -> {cf.get(k)!r}" for k in diff_conf))
    else:
        ok.append("Configuration de simulation identique.")
    rb, rc = rappels(fichier_base), rappels(fichier_fz)
    if rb == rc:
        ok.append("Rappels du modele identiques" + (f" ({', '.join(sorted(rb))})." if rb else " (aucun rappel)."))
    else:
        pb.append(f"Rappels du modele modifies : {rb!r} -> {rc!r}.")

    # 5. Contenu Stateflow (calcul de F1)
    sf_b, sf_f = fichiers_stateflow(fichier_base), fichiers_stateflow(fichier_fz)
    if sf_b != sf_f:
        pb.append(f"Fichiers Stateflow differents : base {sf_b}, construit {sf_f}.")
    elif sf_b:
        changes = [n for n in sf_b if lire_texte(fichier_base, n) != lire_texte(fichier_fz, n)]
        if changes:
            pb.append(f"Contenu Stateflow modifie ({', '.join(changes)}) : le calcul de F1 a ete altere.")
        else:
            ok.append(f"Contenu Stateflow identique ({len(sf_b)} fichier(s)) : calcul de F1 intact.")
    return ok, notes, pb


# %% ETAPE 3 : bilan

conformes = []
for nom_base, nom_fz in PAIRES:
    ok, notes, pb = verifier(nom_base, nom_fz)
    print(f"\n=== {nom_fz}.slx (construit sur {nom_base}.slx) ===")
    for x in ok:
        print("  [OK]", x)
    for x in notes:
        print("  [NOTE]", x)
    for x in pb:
        print("  [PROBLEME]", x)
    print(f"  -> {'conforme' if not pb else 'NON CONFORME'}")
    if not pb:
        conformes.append(nom_fz)

if len(conformes) == len(PAIRES):
    print("\nRESULTAT : les trois modeles sont conformes. Etape suivante : Simuler_PINN_PID_Trois_Modeles.m.")
else:
    print(f"\nRESULTAT : {len(PAIRES) - len(conformes)} modele(s) sur {len(PAIRES)} ne correspondent pas a ce "
          "qui est prevu (voir les problemes ci-dessus).")
