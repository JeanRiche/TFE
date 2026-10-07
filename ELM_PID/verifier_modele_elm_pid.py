# =============================================================================
# verifier_modele_elm_pid.py
#
# VERSION
#   1 (4 octobre 2026), ELM-PID sur la base commune v2.
#
# OBJECTIF
#   Controle independant, sans MATLAB, du modele Buck_Commun_ELM_PID.slx
#   construit par Construction_ELM_PID.m. Il doit etre identique a
#   Buck_Commun.slx (deja verifie par verifier_modele_commun.py), sauf :
#     - le bloc "PID Controller", supprime ;
#     - quatre blocs ajoutes : "Echantillonneur Erreur ELM" et
#       "Echantillonneur Mesure ELM" (Zero-Order Hold a 1/(22000*10) s),
#       "ELM-PID Adaptatif" (MATLAB System, classe elm_pid_adaptatif,
#       execution interpretee) et "Terminaison Gains ELM" (Terminator) ;
#     - liaisons : Sum1 -> Echantillonneur Erreur ELM -> ELM-PID (entree 1),
#       Quantification Mesure -> Echantillonneur Mesure ELM -> ELM-PID
#       (entree 2), ELM-PID (sortie 1) -> PWM, ELM-PID (sortie 2) ->
#       Terminaison Gains ELM ; les deux liaisons du PID disparaissent,
#       toutes les autres restent (dont Quantification Mesure -> Sum1).
#
# CE QUE LE SCRIPT CONTROLE
#   1. Blocs gardes : memes reglages que dans Buck_Commun.slx (valeurs par
#      defaut de Simulink pour les reglages absents ; lien de bibliotheque
#      mis a jour a l'enregistrement note sans etre compte).
#   2. Blocs ajoutes : exactement les quatre prevus, types et reglages.
#   3. Liaisons de signal : celles de Buck_Commun.slx, moins les deux du
#      PID, plus les six prevues. Liaisons electriques : identiques.
#   4. Configuration de simulation et rappel InitFcn identiques.
#
# COMMENT LANCER CE SCRIPT :
#   python verifier_modele_elm_pid.py
#   (ou le notebook verifier_modele_elm_pid.ipynb, meme code), depuis le
#   dossier ou se trouvent Buck_Commun.slx et Buck_Commun_ELM_PID.slx.
#   Bibliotheque standard de Python uniquement.
#   Doit finir par "RESULTAT : Buck_Commun_ELM_PID.slx est conforme."
#
# ORDRE D'EXECUTION (etape 3 de l'ELM-PID)
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
TC = 1.0 / (22000 * 10)                       # periode attendue des echantillonneurs (s)
PWM = "PWM Generator\n(DC-DC)"                # nom du bloc PWM (vrai saut de ligne)
CLASSE = "elm_pid_adaptatif"                  # classe du bloc MATLAB System
NOM_SYS = "ELM-PID Adaptatif"
NOM_ZOHE = "Echantillonneur Erreur ELM"
NOM_ZOHM = "Echantillonneur Mesure ELM"
NOM_TERM = "Terminaison Gains ELM"
TYPES_AJOUTES = {NOM_ZOHE: "ZeroOrderHold", NOM_ZOHM: "ZeroOrderHold", NOM_SYS: "MATLABSystem",
                 NOM_TERM: "Terminator"}
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
re_ = lire_xml(FICHIER_ELM, "simulink/systems/system_root.xml")
bs = {b.get("Name"): b for b in rs.findall("Block")}
be = {b.get("Name"): b for b in re_.findall("Block")}
ok, pb, notes = [], [], []

# 1. Blocs gardes
n_pb = len(pb)
if "PID Controller" in be:
    pb.append("Le bloc 'PID Controller' est encore present.")
for nom in sorted(set(bs) - {"PID Controller"}):
    if nom not in be:
        pb.append(f"Bloc disparu : {nom!r}.")
        continue
    a, b = reglages(bs[nom]), reglages(be[nom])
    diff = sorted(k for k in set(a) | set(b) if k not in ("Position", "ZOrder") and a.get(k) != b.get(k))
    lien = [k for k in diff if k in ("SourceBlock", "LibraryVersion")]
    if lien and a.get("LibrarySourceBlock") and a.get("LibrarySourceBlock") == b.get("LibrarySourceBlock"):
        notes.append(f"Bloc {nom!r} : lien de bibliotheque mis a jour par Simulink ("
                     + ", ".join(f"{k} {a.get(k)!r} -> {b.get(k)!r}" for k in lien) + ").")
        diff = [k for k in diff if k not in lien]
    if diff:
        pb.append(f"Bloc {nom!r} modifie : " + ", ".join(f"{k} {a.get(k)!r} -> {b.get(k)!r}" for k in diff))
if len(pb) == n_pb:
    ok.append(f"Les {len(bs) - 1} blocs gardes ont les reglages de Buck_Commun.slx ; le PID a disparu.")

# 2. Blocs ajoutes
n_pb = len(pb)
ajoutes = set(be) - set(bs)
if ajoutes != set(TYPES_AJOUTES):
    pb.append(f"Blocs ajoutes : {sorted(ajoutes)} au lieu de {sorted(TYPES_AJOUTES)}.")
for nom, type_attendu in TYPES_AJOUTES.items():
    if nom in be and be[nom].get("BlockType") != type_attendu:
        pb.append(f"{nom!r} : type {be[nom].get('BlockType')!r} au lieu de {type_attendu!r}.")
for nom in (NOM_ZOHE, NOM_ZOHM):
    if nom in be:
        periode = nombre(param(be[nom], "SampleTime"))
        if periode is None or abs(periode - TC) > 1e-9 * TC:
            pb.append(f"{nom!r} : periode {param(be[nom], 'SampleTime')!r} au lieu de 1/(22000*10).")
if NOM_SYS in be:
    classe = param(be[NOM_SYS], "System")
    if classe is not None and classe != CLASSE:
        pb.append(f"{NOM_SYS!r} : classe {classe!r} au lieu de {CLASSE!r}.")
    elif classe is None and not contient(be[NOM_SYS], CLASSE):
        pb.append(f"{NOM_SYS!r} : la classe {CLASSE!r} n'apparait pas dans sa definition.")
    mode = param(be[NOM_SYS], "SimulateUsing")
    if mode is None:
        notes.append(f"{NOM_SYS!r} : reglage SimulateUsing non ecrit sous ce nom dans le fichier. Non bloquant : "
                     "en mode Code generation, la simulation s'arreterait des la compilation (load et exist n'y "
                     "sont pas pris en charge), l'erreur ne passerait donc pas inapercue. A verifier a l'oeil "
                     "(bloc > Simulate using : Interpreted execution).")
    elif mode != "Interpreted execution":
        pb.append(f"{NOM_SYS!r} : SimulateUsing = {mode!r} au lieu de 'Interpreted execution'.")
if len(pb) == n_pb:
    ok.append("Les quatre blocs ajoutes sont ceux prevus (echantillonneurs a 1/(22000*10) s, classe "
              f"{CLASSE}, terminaison des gains).")

# 3. Liaisons
sig_s, elec_s = extremites(rs)
sig_e, elec_e = extremites(re_)
retirees = {("Sum1#out:1", "PID Controller#in:1"), ("PID Controller#out:1", f"{PWM}#in:1")}
nouvelles = {("Sum1#out:1", f"{NOM_ZOHE}#in:1"), ("Quantification Mesure#out:1", f"{NOM_ZOHM}#in:1"),
             (f"{NOM_ZOHE}#out:1", f"{NOM_SYS}#in:1"), (f"{NOM_ZOHM}#out:1", f"{NOM_SYS}#in:2"),
             (f"{NOM_SYS}#out:1", f"{PWM}#in:1"), (f"{NOM_SYS}#out:2", f"{NOM_TERM}#in:1")}
attendu = (sig_s - retirees) | nouvelles
if not retirees <= sig_s or ("Quantification Mesure#out:1", "Sum1#in:2") not in sig_s:
    pb.append("Buck_Commun.slx n'a pas les liaisons du PID et de la mesure attendues : fichier de depart inattendu.")
if sig_e == attendu:
    ok.append(f"Liaisons de signal : les {len(sig_s) - 2} liaisons gardees et les {len(nouvelles)} prevues, rien d'autre.")
else:
    manque = sorted(attendu - sig_e)
    trop = sorted(sig_e - attendu)
    pb.append("Liaisons de signal differentes : manquantes " + str([f"{a} -> {b}" for a, b in manque])
              + ", en trop " + str([f"{a} -> {b}" for a, b in trop]))
if elec_s == elec_e:
    ok.append(f"Liaisons electriques identiques ({len(elec_s)} liaisons).")
else:
    pb.append("Liaisons electriques differentes de celles de Buck_Commun.slx.")

# 4. Configuration et rappel InitFcn
cs, ce = configuration(FICHIER_SOURCE), configuration(FICHIER_ELM)
diff_conf = sorted(k for k in set(cs) | set(ce) if cs.get(k) != ce.get(k))
if diff_conf:
    pb.append("Configuration modifiee : " + ", ".join(f"{k}: {cs.get(k)!r} -> {ce.get(k)!r}" for k in diff_conf))
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
