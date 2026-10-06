# =============================================================================
# verifier_modeles_pso_pid_trois.py
#
# VERSION
#   1 (6 octobre 2026), PSO-PID (Gaing, 2004), trois modeles construits sur
#   les modeles de base de Jean-Riche. Lecture des fichiers reprise de
#   verifier_modeles_fuzzy_pid_trois.py.
#
# OBJECTIF
#   Controle independant, sans MATLAB, des trois modeles construits par
#   Construction_PSO_PID_Trois_Modeles.m :
#     PID_Classique_Control.slx                     -> PSO_PID_Control.slx
#     PID_Classique_Control_control_disturbance.slx -> PSO_PID_Control_control_disturbance.slx
#     PID_Classique_Control_load_disturbance.slx    -> PSO_PID_Control_load_disturbance.slx
#   Chacun doit etre identique a son modele de base, sauf P, I et D du bloc
#   "PID Controller", egaux a ceux de predictions_banc_pso_pid.json a 1e-12
#   pres (N inchange). Controles : blocs et reglages, liaisons de signal et
#   electriques, configuration, rappels du modele, contenu Stateflow (calcul
#   de F1) caractere pour caractere.
#
# COMMENT LANCER CE SCRIPT :
#   python verifier_modeles_pso_pid_trois.py
#   Bibliotheque standard de Python uniquement.
#   Doit finir par "RESULTAT : les trois modeles sont conformes."
#
# ORDRE D'EXECUTION
#   1. Construction_PSO_PID_Trois_Modeles.m ; 2. ce script ;
#   3. Simuler_PSO_PID_Trois_Modeles.m.
# =============================================================================


# %% ETAPE 0 : bibliotheques et fichiers

import os                                     # chemins de fichiers
import re                                     # expressions regulieres
import json                                   # gains attendus
import zipfile                                # un .slx est une archive zip
import xml.etree.ElementTree as ET            # lecture des fichiers XML

try:                                          # dossier du script (ou dossier courant dans un notebook)
    DOSSIER = os.path.dirname(os.path.abspath(__file__))
except NameError:
    DOSSIER = os.getcwd()
PAIRES = [("PID_Classique_Control", "PSO_PID_Control"),          # (modele de base, modele construit)
          ("PID_Classique_Control_control_disturbance", "PSO_PID_Control_control_disturbance"),
          ("PID_Classique_Control_load_disturbance", "PSO_PID_Control_load_disturbance")]
PID = "PID Controller"
FICHIER_GAINS = os.path.join(DOSSIER, "predictions_banc_pso_pid.json")
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

with open(FICHIER_GAINS, encoding="utf-8") as f:
    GAINS = json.load(f)["gains"]             # P, I, D, N attendus


def verifier(nom_base, nom_pso):
    """Controles pour un modele construit ; renvoie (ok, notes, problemes)."""
    fichier_base = os.path.join(DOSSIER, nom_base + ".slx")
    fichier_pso = os.path.join(DOSSIER, nom_pso + ".slx")
    ok, pb, notes = [], [], []
    for f in (fichier_base, fichier_pso):
        if not os.path.exists(f):
            return ok, notes, [f"Fichier introuvable : {os.path.basename(f)}"]
    rs = lire_xml(fichier_base, "simulink/systems/system_root.xml")
    rf = lire_xml(fichier_pso, "simulink/systems/system_root.xml")
    bs = {b.get("Name"): b for b in rs.findall("Block")}
    bf = {b.get("Name"): b for b in rf.findall("Block")}

    # 1. Blocs et reglages
    if set(bs) != set(bf):
        pb.append("Blocs differents : en moins " + str(sorted(set(bs) - set(bf))) + ", en plus "
                  + str(sorted(set(bf) - set(bs))))
    n_pb = len(pb)
    for nom in sorted(set(bs) & set(bf)):
        a, b = reglages(bs[nom]), reglages(bf[nom])
        diff = sorted(k for k in set(a) | set(b) if k not in ("Position", "ZOrder") and a.get(k) != b.get(k))
        lien = [k for k in diff if k in ("SourceBlock", "LibraryVersion")]
        if lien and a.get("LibrarySourceBlock") and a.get("LibrarySourceBlock") == b.get("LibrarySourceBlock"):
            notes.append(f"Bloc {nom!r} : lien de bibliotheque mis a jour par Simulink ("
                         + ", ".join(f"{k} {a.get(k)!r} -> {b.get(k)!r}" for k in lien) + ").")
            diff = [k for k in diff if k not in lien]
        if nom == PID:
            diff = [k for k in diff if k not in ("P", "I", "D")]
        if diff:
            pb.append(f"Bloc {nom!r} modifie : " + ", ".join(f"{k} {a.get(k)!r} -> {b.get(k)!r}" for k in diff))
    if len(pb) == n_pb:
        ok.append(f"Les {len(bs)} blocs sont ceux de {nom_base}.slx, avec les memes reglages, sauf P, I et D du PID.")

    # 2. Gains du PID
    pid = reglages(bf[PID]) if PID in bf else {}
    n_pb = len(pb)
    for cle in ("P", "I", "D", "N"):
        lu, attendu = nombre(pid.get(cle)), GAINS[cle]
        if lu is None or abs(lu - attendu) > 1e-12 * abs(attendu):
            pb.append(f"PID Controller : {cle} = {pid.get(cle)!r} au lieu de {attendu!r}.")
    if len(pb) == n_pb:
        ok.append(f"Gains du PSO-PID : P = {pid['P']}, I = {pid['I']}, D = {pid['D']}, N = {pid['N']}.")

    # 3. Liaisons
    sig_s, elec_s = extremites(rs)
    sig_f, elec_f = extremites(rf)
    if sig_s == sig_f and elec_s == elec_f:
        ok.append(f"Memes liaisons de signal ({len(sig_s)}) et electriques ({len(elec_s)}).")
    else:
        pb.append("Liaisons differentes de celles de " + nom_base + ".slx : manquantes "
                  + str(sorted(sig_s - sig_f)) + ", en trop " + str(sorted(sig_f - sig_s))
                  + ("" if elec_s == elec_f else " ; liaisons electriques differentes"))

    # 4. Configuration et rappels du modele
    cs, cf = configuration(fichier_base), configuration(fichier_pso)
    diff_conf = sorted(k for k in set(cs) | set(cf) if cs.get(k) != cf.get(k))
    if diff_conf:
        pb.append("Configuration modifiee : " + ", ".join(f"{k}: {cs.get(k)!r} -> {cf.get(k)!r}" for k in diff_conf))
    else:
        ok.append("Configuration de simulation identique.")
    rb, rc = rappels(fichier_base), rappels(fichier_pso)
    if rb == rc:
        ok.append("Rappels du modele identiques" + (f" ({', '.join(sorted(rb))})." if rb else " (aucun rappel)."))
    else:
        pb.append(f"Rappels du modele modifies : {rb!r} -> {rc!r}.")

    # 5. Contenu Stateflow (calcul de F1)
    sf_b, sf_f = fichiers_stateflow(fichier_base), fichiers_stateflow(fichier_pso)
    if sf_b != sf_f:
        pb.append(f"Fichiers Stateflow differents : base {sf_b}, construit {sf_f}.")
    elif sf_b:
        changes = [n for n in sf_b if lire_texte(fichier_base, n) != lire_texte(fichier_pso, n)]
        if changes:
            pb.append(f"Contenu Stateflow modifie ({', '.join(changes)}) : le calcul de F1 a ete altere.")
        else:
            ok.append(f"Contenu Stateflow identique ({len(sf_b)} fichier(s)) : calcul de F1 intact.")
    return ok, notes, pb


# %% ETAPE 3 : bilan

conformes = []
for nom_base, nom_pso in PAIRES:
    ok, notes, pb = verifier(nom_base, nom_pso)
    print(f"\n=== {nom_pso}.slx (construit sur {nom_base}.slx) ===")
    for x in ok:
        print("  [OK]", x)
    for x in notes:
        print("  [NOTE]", x)
    for x in pb:
        print("  [PROBLEME]", x)
    print(f"  -> {'conforme' if not pb else 'NON CONFORME'}")
    if not pb:
        conformes.append(nom_pso)

if len(conformes) == len(PAIRES):
    print("\nRESULTAT : les trois modeles sont conformes. Etape suivante : Simuler_PSO_PID_Trois_Modeles.m.")
else:
    print(f"\nRESULTAT : {len(PAIRES) - len(conformes)} modele(s) sur {len(PAIRES)} ne correspondent pas a ce "
          "qui est prevu (voir les problemes ci-dessus).")
