# =============================================================================
# verifier_modele_donnees_elm.py
#
# VERSION
#   1 (3 octobre 2026), ELM-PID sur la base commune v2.
#
# OBJECTIF
#   Controle independant, sans MATLAB, du modele Donnees_ELM.slx construit
#   par Construction_Modele_Donnees_ELM.m. Il doit etre identique a
#   Buck_Commun.slx (deja verifie par verifier_modele_commun.py), sauf :
#     - le bloc "PID Controller", supprime ;
#     - "Commande Excitation" (From Workspace) ajoute : variable sc_dexc,
#       periode 1/(22000*10) s, sans interpolation, derniere valeur gardee ;
#     - "Terminaison Erreur" (Terminator) ajoute ;
#     - liaisons : Commande Excitation -> entree du PWM a la place de
#       PID Controller -> PWM, et Sum1 -> Terminaison Erreur a la place de
#       Sum1 -> PID Controller ;
#     - rappel InitFcn qui charge aussi sc_dexc par defaut.
#
# CE QUE LE SCRIPT CONTROLE
#   1. Blocs gardes : memes reglages (valeurs par defaut de Simulink pour
#      les reglages absents ; lien de bibliotheque mis a jour a
#      l'enregistrement note sans etre compte).
#   2. Blocs ajoutes : exactement les deux prevus, avec leurs reglages.
#   3. Liaisons de signal : celles de Buck_Commun.slx, moins les deux du
#      PID, plus les deux prevues. Liaisons electriques : identiques.
#   4. Configuration de simulation identique ; rappel InitFcn.
#
# COMMENT LANCER CE SCRIPT :
#   python verifier_modele_donnees_elm.py
#   (ou le notebook verifier_modele_donnees_elm.ipynb, meme code), depuis le
#   dossier de la base commune. Bibliotheque standard de Python uniquement.
#   Doit finir par "RESULTAT : Donnees_ELM.slx est conforme."
#
# ORDRE D'EXECUTION (etape 1 de l'ELM-PID : les donnees)
#   1. excitation_donnees_elm.py ; 2. Construction_Modele_Donnees_ELM.m ;
#   3. ce script ; 4. Generer_Donnees_ELM.m.
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
FICHIER_DONNEES = os.path.join(DOSSIER, "Donnees_ELM.slx")
TC = 1.0 / (22000 * 10)                       # periode attendue de la commande imposee (s)
PWM = "PWM Generator\n(DC-DC)"                # nom du bloc PWM (vrai saut de ligne)
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

for f in (FICHIER_SOURCE, FICHIER_DONNEES):
    if not os.path.exists(f):
        raise FileNotFoundError("Fichier introuvable : " + f)
rs = lire_xml(FICHIER_SOURCE, "simulink/systems/system_root.xml")
rd = lire_xml(FICHIER_DONNEES, "simulink/systems/system_root.xml")
bs = {b.get("Name"): b for b in rs.findall("Block")}
bd = {b.get("Name"): b for b in rd.findall("Block")}
ok, pb, notes = [], [], []

# 1. Blocs gardes
n_pb = len(pb)
if "PID Controller" in bd:
    pb.append("Le bloc 'PID Controller' est encore present.")
for nom in sorted(set(bs) - {"PID Controller"}):
    if nom not in bd:
        pb.append(f"Bloc disparu : {nom!r}.")
        continue
    a, b = reglages(bs[nom]), reglages(bd[nom])
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
ajoutes = set(bd) - set(bs)
if ajoutes != {"Commande Excitation", "Terminaison Erreur"}:
    pb.append(f"Blocs ajoutes : {sorted(ajoutes)} au lieu de ['Commande Excitation', 'Terminaison Erreur'].")
if "Commande Excitation" in bd:
    c = bd["Commande Excitation"]
    r = reglages(c)
    if c.get("BlockType") != "FromWorkspace":
        pb.append(f"'Commande Excitation' : type {c.get('BlockType')!r} au lieu de 'FromWorkspace'.")
    if r.get("VariableName") != "sc_dexc":
        pb.append(f"'Commande Excitation' : variable {r.get('VariableName')!r} au lieu de 'sc_dexc'.")
    periode = nombre(r.get("SampleTime"))
    if periode is None or abs(periode - TC) > 1e-9 * TC:
        pb.append(f"'Commande Excitation' : periode {r.get('SampleTime')!r} au lieu de 1/(22000*10).")
    if r.get("Interpolate") != "off":
        pb.append(f"'Commande Excitation' : interpolation {r.get('Interpolate')!r} (attendu 'off').")
    if r.get("OutputAfterFinalValue") != "Holding final value":
        pb.append(f"'Commande Excitation' : apres la fin des donnees, {r.get('OutputAfterFinalValue')!r}.")
if "Terminaison Erreur" in bd and bd["Terminaison Erreur"].get("BlockType") != "Terminator":
    pb.append(f"'Terminaison Erreur' : type {bd['Terminaison Erreur'].get('BlockType')!r} au lieu de 'Terminator'.")
if len(pb) == n_pb:
    ok.append("Les deux blocs ajoutes sont ceux prevus (sc_dexc a 1/(22000*10) s, sans interpolation).")

# 3. Liaisons
sig_s, elec_s = extremites(rs)
sig_d, elec_d = extremites(rd)
retirees = {("Sum1#out:1", "PID Controller#in:1"), ("PID Controller#out:1", f"{PWM}#in:1")}
nouvelles = {("Commande Excitation#out:1", f"{PWM}#in:1"), ("Sum1#out:1", "Terminaison Erreur#in:1")}
attendu = (sig_s - retirees) | nouvelles
if not retirees <= sig_s:
    pb.append("Buck_Commun.slx n'a pas les liaisons du PID attendues : fichier de depart inattendu.")
if sig_d == attendu:
    ok.append(f"Liaisons de signal : les {len(sig_s) - 2} liaisons gardees et les 2 prevues, rien d'autre.")
else:
    manque = sorted(attendu - sig_d)
    trop = sorted(sig_d - attendu)
    pb.append("Liaisons de signal differentes : manquantes " + str([f"{a} -> {b}" for a, b in manque])
              + ", en trop " + str([f"{a} -> {b}" for a, b in trop]))
if elec_s == elec_d:
    ok.append(f"Liaisons electriques identiques ({len(elec_s)} liaisons).")
else:
    pb.append("Liaisons electriques differentes de celles de Buck_Commun.slx.")

# 4. Configuration et rappel InitFcn
cs, cd = configuration(FICHIER_SOURCE), configuration(FICHIER_DONNEES)
diff_conf = sorted(k for k in set(cs) | set(cd) if cs.get(k) != cd.get(k))
if diff_conf:
    pb.append("Configuration modifiee : " + ", ".join(f"{k}: {cs.get(k)!r} -> {cd.get(k)!r}" for k in diff_conf))
else:
    ok.append("Configuration de simulation identique.")
texte_bd = lire_texte(FICHIER_DONNEES, "simulink/blockdiagram.xml")
if "charger_scenario" in texte_bd and "sc_dexc" in texte_bd:
    ok.append("Rappel InitFcn present (S1 et sc_dexc par defaut).")
else:
    pb.append("Rappel InitFcn absent ou incomplet (charger_scenario et sc_dexc attendus).")


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
    print("\nRESULTAT : Donnees_ELM.slx ne correspond pas a ce qui est prevu.")
else:
    print("\nRESULTAT : Donnees_ELM.slx est conforme. Etape suivante : Generer_Donnees_ELM.m.")
