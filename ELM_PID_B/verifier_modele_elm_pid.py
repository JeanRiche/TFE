# =============================================================================
# verifier_modele_elm_pid.py
#
# VERSION
#   4 (8 octobre 2026), ELM-PID option B. Repris de
#   verifier_modele_fuzzy_pid.py (meme montage : le PID de la base commune
#   recoit ses gains d'un bloc MATLAB System), avec les deux entrees de plus
#   de l'adaptateur (mesure et commande). La version 3 (bloc qui remplacait
#   le PID) est dans ELM_PID_INCREMENTAL.
#
# OBJECTIF
#   Controle independant, sans MATLAB, du modele Buck_Commun_ELM_PID.slx
#   construit par Construction_ELM_PID.m. Il doit etre identique a
#   Buck_Commun.slx (deja verifie par verifier_modele_commun.py), sauf :
#     - bloc "PID Controller" GARDE : seul ControllerParametersSource passe
#       de internal a external (et ses entrees passent de 1 a 5) ; Simulink
#       bascule alors seul quatre aiguillages internes du masque
#       (ParallelPVariant, IVariant, DVariant, NVariant) de
#       InternalParameters a ExternalParameters, et seulement ceux-la ;
#     - six blocs ajoutes : "Echantillonneur Erreur ELM", "Echantillonneur
#       Mesure ELM", "Echantillonneur Commande ELM" (Zero-Order Hold a
#       1/(22000*10) s), "ELM-PID Adaptatif" (MATLAB System, classe
#       elm_pid_adaptatif, execution interpretee, 3 entrees, 1 sortie),
#       "Demux Gains ELM" (Demux a 3 sorties) et "Constante N Filtre"
#       (Constant, meme valeur que le champ N du PID) ;
#     - liaisons : Sum1 -> PID (sur l'entree u, dont le numero peut changer) ;
#       Sum1 -> Echantillonneur Erreur -> entree 1 de l'adaptateur ;
#       Quantification Mesure -> Echantillonneur Mesure -> entree 2 ;
#       sortie du PID -> Echantillonneur Commande -> entree 3 (le PID
#       alimente toujours le PWM) ; adaptateur -> Demux ; Demux 1, 2, 3 et
#       Constante N -> quatre autres entrees du PID, toutes differentes.
#       Toutes les autres liaisons restent.
#   L'ordre des entrees P, I, D, N du PID n'est pas ecrit dans le .slx (il
#   est dans la bibliotheque Simulink) : le script donne les numeros
#   utilises, et c'est l'auto-test T0 de Construction_ELM_PID.m (gains de
#   Ziegler-Nichols -> PID classique a 0.1 V pres) qui controle cet ordre.
#
# COMMENT LANCER CE SCRIPT :
#   python verifier_modele_elm_pid.py
#   depuis le dossier ou se trouvent Buck_Commun.slx et
#   Buck_Commun_ELM_PID.slx. Bibliotheque standard de Python uniquement.
#   Doit finir par "RESULTAT : Buck_Commun_ELM_PID.slx est conforme."
#
# ORDRE D'EXECUTION
#   1. entrainement_elm.py ; 2. ensemble_gains_elm.py ; 3. banc_elm_pid.py ;
#   4. Tester_ELM_PID_Rejeu.m ; 5. Construction_ELM_PID.m ; 6. ce script ;
#   7. Simuler_ELM_PID.m.
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
FICHIER_SOURCE = os.path.join(DOSSIER, "Buck_Commun.slx")
FICHIER_ELM = os.path.join(DOSSIER, "Buck_Commun_ELM_PID.slx")
TC = 1.0 / (22000 * 10)                       # periode attendue de l'echantillonneur (s)
PWM = "PWM Generator\n(DC-DC)"                # nom du bloc PWM (vrai saut de ligne)
PID = "PID Controller"
CLASSE = "elm_pid_adaptatif"                  # classe du bloc MATLAB System
NOM_SYS = "ELM-PID Adaptatif"
NOM_ZOHE = "Echantillonneur Erreur ELM"
NOM_ZOHM = "Echantillonneur Mesure ELM"
NOM_ZOHU = "Echantillonneur Commande ELM"
NOM_DEMUX = "Demux Gains ELM"
NOM_N = "Constante N Filtre"
QUANT = "Quantification Mesure"
TYPES_AJOUTES = {NOM_ZOHE: "ZeroOrderHold", NOM_ZOHM: "ZeroOrderHold", NOM_ZOHU: "ZeroOrderHold",
                 NOM_SYS: "MATLABSystem", NOM_DEMUX: "Demux", NOM_N: "Constant"}
# Aiguillages internes du masque du PID lies a la source de P, I, D et N (changent seuls avec elle)
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


def init_fcn(chemin):
    """Texte du rappel InitFcn du modele (vide s'il n'y en a pas)."""
    m = re.search(r'<P Name="InitFcn">(.*?)</P>', lire_texte(chemin, "simulink/blockdiagram.xml"), re.S)
    return m.group(1).strip() if m else ""


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


# %% ETAPE 2 : les controles

for f in (FICHIER_SOURCE, FICHIER_ELM):
    if not os.path.exists(f):
        raise FileNotFoundError("Fichier introuvable : " + f)
rs = lire_xml(FICHIER_SOURCE, "simulink/systems/system_root.xml")
rf = lire_xml(FICHIER_ELM, "simulink/systems/system_root.xml")
bs = {b.get("Name"): b for b in rs.findall("Block")}
bf = {b.get("Name"): b for b in rf.findall("Block")}
ok, pb, notes = [], [], []

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
        # Aiguillages internes du masque que Simulink bascule seul avec la source des parametres :
        # un par parametre devenu externe, et seulement de InternalParameters a ExternalParameters.
        bascules = [k for k in diff if k in VARIANTES_PID]
        for k in bascules:
            if a.get(k) != "InternalParameters" or b.get(k) != "ExternalParameters":
                pb.append(f"PID : {k} {a.get(k)!r} -> {b.get(k)!r} au lieu de 'InternalParameters' -> "
                          "'ExternalParameters'.")
        if bascules:
            notes.append("PID : aiguillages internes du masque bascules par Simulink avec la source des parametres "
                         "(InternalParameters -> ExternalParameters) : " + ", ".join(sorted(bascules)) + ".")
        diff = [k for k in diff if k != "ControllerParametersSource" and k not in VARIANTES_PID]
    if diff:
        pb.append(f"Bloc {nom!r} modifie : " + ", ".join(f"{k} {a.get(k)!r} -> {b.get(k)!r}" for k in diff))
if len(pb) == n_pb:
    ok.append(f"Les {len(bs)} blocs de Buck_Commun.slx sont gardes avec leurs reglages ; le PID n'a change que "
              "sa source de parametres (internal -> external).")
ports_pid = bf[PID].find("PortCounts") if PID in bf else None
if ports_pid is None or ports_pid.get("in") != "5" or ports_pid.get("out") != "1":
    pb.append(f"PID : entrees/sorties {None if ports_pid is None else (ports_pid.get('in'), ports_pid.get('out'))} "
              "au lieu de 5 entrees et 1 sortie.")

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
if avant not in sig_s or (f"{QUANT}#out:1", "Sum1#in:2") not in sig_s or (f"{PID}#out:1", f"{PWM}#in:1") not in sig_s:
    pb.append("Buck_Commun.slx n'a pas les liaisons du PID et de la mesure attendues : fichier de depart inattendu.")
vers_pid = {}                                 # source -> entree du PID
for src, dst in sig_f:
    if dst.startswith(f"{PID}#in:"):
        vers_pid[src] = int(dst.split(":")[-1])
sources_pid = {"Sum1#out:1": "u", f"{NOM_DEMUX}#out:1": "P", f"{NOM_DEMUX}#out:2": "I", f"{NOM_DEMUX}#out:3": "D",
               f"{NOM_N}#out:1": "N"}
if set(vers_pid) != set(sources_pid) or len(set(vers_pid.values())) != 5 or set(vers_pid.values()) != {1, 2, 3, 4, 5}:
    pb.append(f"Entrees du PID : {sorted(vers_pid.items())} ; attendu u, P, I, D, N sur cinq entrees differentes.")
else:
    notes.append("Entrees du PID utilisees : " + ", ".join(f"{sources_pid[s]} = {vers_pid[s]}" for s in sources_pid)
                 + " (ordre controle par l'auto-test T0 de Construction_ELM_PID.m).")
nouvelles = {("Sum1#out:1", f"{NOM_ZOHE}#in:1"), (f"{NOM_ZOHE}#out:1", f"{NOM_SYS}#in:1"),
             (f"{QUANT}#out:1", f"{NOM_ZOHM}#in:1"), (f"{NOM_ZOHM}#out:1", f"{NOM_SYS}#in:2"),
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
if (f"{PID}#out:1", f"{PWM}#in:1") not in sig_f:
    pb.append("La sortie du PID n'alimente plus le PWM.")
if elec_s == elec_f:
    ok.append(f"Liaisons electriques identiques ({len(elec_s)} liaisons).")
else:
    pb.append("Liaisons electriques differentes de celles de Buck_Commun.slx.")

# 4. Configuration et rappel InitFcn
cs, cf = configuration(FICHIER_SOURCE), configuration(FICHIER_ELM)
diff_conf = sorted(k for k in set(cs) | set(cf) if cs.get(k) != cf.get(k))
if diff_conf:
    pb.append("Configuration modifiee : " + ", ".join(f"{k}: {cs.get(k)!r} -> {cf.get(k)!r}" for k in diff_conf))
else:
    ok.append("Configuration de simulation identique.")
if init_fcn(FICHIER_SOURCE) == init_fcn(FICHIER_ELM):
    ok.append("Rappel InitFcn identique a celui de Buck_Commun.slx.")
else:
    pb.append(f"Rappel InitFcn modifie : {init_fcn(FICHIER_SOURCE)!r} -> {init_fcn(FICHIER_ELM)!r}.")


# %% ETAPE 3 : bilan

print("\nControles reussis :")
for x in ok:
    print("  [OK]", x)
for x in notes:
    print("  [NOTE]", x)
if pb:
    print("\nProblemes :")
    for x in pb:
        print("  [PROBLEME]", x)
    print("\nRESULTAT : Buck_Commun_ELM_PID.slx ne correspond pas a ce qui est prevu.")
else:
    print("\nRESULTAT : Buck_Commun_ELM_PID.slx est conforme. Etape suivante : Simuler_ELM_PID.m.")
