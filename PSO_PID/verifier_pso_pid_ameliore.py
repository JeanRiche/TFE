# =============================================================================
# verifier_pso_pid_ameliore.py
#
# VERSION
#   1 (6 octobre 2026). Copie de verifier_pid_fige.py (3 octobre 2026) ;
#   seuls le modele controle et le fichier de gains changent.
#
# OBJECTIF
#   Controle independant, sans MATLAB, du modele Buck_Commun_PSO_PID_Ameliore.slx
#   construit par Construction_PSO_PID_Ameliore.m. Ce modele doit etre identique a
#   Buck_Commun.slx (deja verifie par verifier_modele_commun.py), sauf les
#   gains P, I et D du bloc "PID Controller", qui doivent valoir ceux de
#   predictions_banc_pso_pid_ameliore.json (ecrit par banc_pso_pid_ameliore.py).
#
# CE QUE LE SCRIPT CONTROLE
#   1. Memes blocs, avec les memes reglages, dans les deux fichiers, sauf
#      P, I et D du bloc "PID Controller". Un reglage absent du fichier vaut
#      la valeur par defaut de son type de bloc (Simulink n'ecrit pas ces
#      valeurs). Un lien de bibliotheque mis a jour par Simulink a
#      l'enregistrement (SourceBlock, LibraryVersion, meme
#      LibrarySourceBlock) est note sans etre compte.
#   2. P, I et D valent les gains du fichier JSON a 1e-12 pres en relatif ;
#      N vaut toujours 64122.9.
#   3. Memes liaisons de signal et memes liaisons electriques (bornes
#      reliees, branches comprises).
#   4. Meme configuration de simulation et meme rappel InitFcn.
#
# COMMENT LANCER CE SCRIPT :
#   python verifier_pso_pid_ameliore.py
#   depuis le dossier
#   de la base commune. Bibliotheque standard de Python uniquement.
#   Doit finir par "RESULTAT : Buck_Commun_PSO_PID_Ameliore.slx est conforme."
#
# ORDRE D'EXECUTION (PSO-PID ameliore)
#   1. recherche_pso_pid_ameliore.py ; 2. banc_pso_pid_ameliore.py ; 3. Construction_PSO_PID_Ameliore.m ;
#   4. ce script ; 5. Simuler_PSO_PID_Ameliore.m.
# =============================================================================


# %% ETAPE 0 : bibliotheques et fichiers

import os                                     # chemins de fichiers
import re                                     # expressions regulieres (nombres)
import json                                   # lecture des gains attendus
import zipfile                                # un .slx est une archive zip
import xml.etree.ElementTree as ET            # lecture des fichiers XML

try:                                          # dossier du script (ou dossier courant dans un notebook)
    DOSSIER = os.path.dirname(os.path.abspath(__file__))
except NameError:
    DOSSIER = os.getcwd()
FICHIER_SOURCE = os.path.join(DOSSIER, "Buck_Commun.slx")
FICHIER_FIGE = os.path.join(DOSSIER, "Buck_Commun_PSO_PID_Ameliore.slx")
FICHIER_GAINS = os.path.join(DOSSIER, "predictions_banc_pso_pid_ameliore.json")
print("Dossier de travail :", DOSSIER)

# Valeurs par defaut internes de Simulink pour les reglages compares (memes
# valeurs que dans verifier_modele_commun.py, version 2.1).
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
    """Reglages d'un bloc : valeurs par defaut de son type, puis reglages
    ecrits (balises <P> sous le bloc et sous son InstanceData)."""
    sortie = dict(DEFAUTS_SIMULINK.get(bloc.get("BlockType"), {}))
    for p in bloc.findall("P"):
        sortie[p.get("Name")] = (p.text or "").strip()
    for inst in bloc.findall("InstanceData"):
        for p in inst.findall("P"):
            sortie[p.get("Name")] = (p.text or "").strip()
    return sortie


def liaisons(racine):
    """Liste triee des liaisons, chacune decrite par le type et la liste
    triee de ses extremites (nom du bloc et port), branches comprises."""
    nom = {b.get("SID"): b.get("Name") for b in racine.findall("Block")}
    sortie = []
    for ligne in racine.findall("Line"):
        bornes = []
        for p in ligne.iter("P"):
            if p.get("Name") in ("Src", "Dst"):
                m = re.match(r"(\d+)#(.*)", p.text or "")
                bornes.append(f"{nom.get(m.group(1), '?')}#{m.group(2)}" if m else (p.text or ""))
        sortie.append((ligne.get("LineType", "Signal"), tuple(sorted(bornes))))
    return sorted(sortie)


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

for f in (FICHIER_SOURCE, FICHIER_FIGE, FICHIER_GAINS):
    if not os.path.exists(f):
        raise FileNotFoundError("Fichier introuvable : " + f)
with open(FICHIER_GAINS, encoding="utf-8") as f:
    GAINS = json.load(f)["gains"]             # P, I, D, N attendus
rs = lire_xml(FICHIER_SOURCE, "simulink/systems/system_root.xml")
rf = lire_xml(FICHIER_FIGE, "simulink/systems/system_root.xml")
bs = {b.get("Name"): b for b in rs.findall("Block")}
bf = {b.get("Name"): b for b in rf.findall("Block")}
ok, pb, notes = [], [], []

# 1. Blocs et reglages
if set(bs) != set(bf):
    pb.append("Blocs differents : en moins " + str(sorted(set(bs) - set(bf))) + ", en plus " + str(sorted(set(bf) - set(bs))))
n_pb = len(pb)
for nom in sorted(set(bs) & set(bf)):
    a, b = reglages(bs[nom]), reglages(bf[nom])
    diff = sorted(k for k in set(a) | set(b) if k not in ("Position", "ZOrder") and a.get(k) != b.get(k))
    lien = [k for k in diff if k in ("SourceBlock", "LibraryVersion")]
    if lien and a.get("LibrarySourceBlock") and a.get("LibrarySourceBlock") == b.get("LibrarySourceBlock"):
        notes.append(f"Bloc {nom!r} : lien de bibliotheque mis a jour par Simulink ("
                     + ", ".join(f"{k} {a.get(k)!r} -> {b.get(k)!r}" for k in lien) + ").")
        diff = [k for k in diff if k not in lien]
    if nom == "PID Controller":
        diff = [k for k in diff if k not in ("P", "I", "D")]
    if diff:
        pb.append(f"Bloc {nom!r} modifie : " + ", ".join(f"{k} {a.get(k)!r} -> {b.get(k)!r}" for k in diff))
if len(pb) == n_pb:
    ok.append(f"Les {len(bs)} blocs sont les memes, avec les memes reglages, sauf P, I et D du PID.")

# 2. Gains du PID
pid = reglages(bf["PID Controller"]) if "PID Controller" in bf else {}
n_pb = len(pb)
for cle in ("P", "I", "D", "N"):
    lu, attendu = nombre(pid.get(cle)), GAINS[cle]
    if lu is None or abs(lu - attendu) > 1e-12 * abs(attendu):
        pb.append(f"PID Controller : {cle} = {pid.get(cle)!r} au lieu de {attendu!r}.")
if len(pb) == n_pb:
    ok.append(f"Gains du PSO-PID ameliore : P = {pid['P']}, I = {pid['I']}, D = {pid['D']}, N = {pid['N']}.")

# 3. Liaisons
if liaisons(rs) == liaisons(rf):
    ok.append(f"Memes {len(liaisons(rs))} liaisons de signal et electriques.")
else:
    pb.append("Liaisons differentes de celles de Buck_Commun.slx.")

# 4. Configuration et rappel InitFcn
cs, cf = configuration(FICHIER_SOURCE), configuration(FICHIER_FIGE)
diff_conf = sorted(k for k in set(cs) | set(cf) if cs.get(k) != cf.get(k))
if diff_conf:
    pb.append("Configuration modifiee : " + ", ".join(f"{k}: {cs.get(k)!r} -> {cf.get(k)!r}" for k in diff_conf))
else:
    ok.append("Configuration de simulation identique.")
if "charger_scenario" in lire_texte(FICHIER_FIGE, "simulink/blockdiagram.xml"):
    ok.append("Rappel InitFcn present.")
else:
    pb.append("Rappel InitFcn absent.")


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
    print("\nRESULTAT : Buck_Commun_PSO_PID_Ameliore.slx ne correspond pas a ce qui est prevu.")
else:
    print("\nRESULTAT : Buck_Commun_PSO_PID_Ameliore.slx est conforme. Etape suivante : Simuler_PSO_PID_Ameliore.m.")
