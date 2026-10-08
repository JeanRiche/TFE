# =============================================================================
# verifier_modele_commun.py
#
# VERSION
#   2 (3 octobre 2026) : profils lus a la periode du regulateur
#   Tc = 1/(22000*10) s, retards des sources commandees d'un pas du powergui
#   (1/(22000*1200) s).
#   2.2 (3 octobre 2026) : controle que le snubber de la diode est supprime
#   (Rs = inf ou Cs = 0).
#   2.1 (3 octobre 2026), apres le premier essai sous R2024a : un reglage
#   absent du fichier prend la valeur par defaut de son type de bloc
#   (DEFAUTS_SIMULINK) ; un lien de bibliotheque mis a jour par Simulink a
#   l'enregistrement (SourceBlock, LibraryVersion, meme LibrarySourceBlock)
#   est note sans etre compte comme une modification.
#
# OBJECTIF
#   Controler, sans faire confiance au script de construction, que le modele
#   Buck_Commun.slx construit par Construction_Modele_Commun.m est exactement
#   PID_Classique_Control.slx avec les seuls changements prevus. Le controle
#   lit directement les fichiers .slx (ce sont des archives zip de fichiers
#   XML) ; il n'utilise ni MATLAB ni Simulink.
#
# CE QUI EST CONTROLE
#   1. Les blocs du modele de base sont tous presents, avec exactement les
#      memes reglages, sauf deux changements attendus : "DC Voltage Source"
#      a disparu et la resistance de "Series RLC Branch2" vaut sc_R0.
#   2. Les blocs ajoutes sont exactement ceux prevus, du bon type, avec les
#      bons reglages : source de tension commandee, charge electronique
#      (source de courant commandee), quatre profils From Workspace (sc_dvref,
#      sc_vin, sc_gx, sc_bruit ; periode Tc = 1/(22000*10) s ; sans
#      interpolation ; derniere valeur gardee), deux retards d'un pas du
#      powergui (1/(22000*1200) s), le produit, deux sommes "++", la
#      quantification au pas sc_q.
#   3. Les liaisons de signal sont celles de la base, moins les deux liaisons
#      remplacees (Vout -> Sum1 entree 2 et Constant1 -> Sum1 entree 1), plus
#      les treize liaisons prevues, et rien d'autre.
#   4. Le circuit de puissance a les memes noeuds electriques que la base, la
#      source commandee prenant la place de la source DC (dans un sens ou dans
#      l'autre) et la charge electronique etant branchee entre le noeud de
#      sortie et la masse.
#   5. La configuration de simulation est identique a celle de la base (seule
#      l'option ReturnWorkspaceOutputs peut differer, elle est signalee).
#   6. Le rappel InitFcn du modele charge l'essai S1 si aucun essai n'est
#      charge.
#   7. Aucune liaison decorative (sans source ni destination) ni liaison
#      electrique a une seule borne ; aucun bloc MATLAB Function (Stateflow).
#
# FICHIERS LUS (dossier du script)
#   PID_Classique_Control.slx et Buck_Commun.slx.
#
# BIBLIOTHEQUES NECESSAIRES : aucune hors de la bibliotheque standard de Python.
#
# COMMENT LANCER CE SCRIPT :
#   python verifier_modele_commun.py
#   (ou le notebook verifier_modele_commun.ipynb, meme code). Duree : une
#   seconde.
#
# ORDRE D'EXECUTION DE LA BASE COMMUNE
#   1. scenarios_communs.py ; 2. banc_commun.py ; 3. Construction_Modele_Commun.m ;
#   4. ce script ; 5. Simuler_Scenarios.m (PID classique).
# =============================================================================


# %% ETAPE 0 : bibliotheques et fichiers

import os                                     # chemins de fichiers
import re                                     # expressions regulieres (lecture des extremites)
import zipfile                                # un .slx est une archive zip
import xml.etree.ElementTree as ET            # lecture des fichiers XML

try:                                          # dossier du script (ou dossier courant dans un notebook)
    DOSSIER = os.path.dirname(os.path.abspath(__file__))
except NameError:
    DOSSIER = os.getcwd()
FICHIER_BASE = os.path.join(DOSSIER, "PID_Classique_Control.slx")
FICHIER_COMMUN = os.path.join(DOSSIER, "Buck_Commun.slx")
TC = 1.0 / (22000 * 10)                       # periode des profils (s)
TS = 1.0 / (22000 * 1200)                     # pas du powergui (s), periode des retards
print("Dossier de travail :", DOSSIER)


# %% ETAPE 1 : lecture des fichiers .slx

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


def noms_internes(chemin):
    """Liste des fichiers contenus dans l'archive."""
    with zipfile.ZipFile(chemin) as z:
        return z.namelist()


def blocs(racine):
    """Dictionnaire nom -> balise <Block> du niveau principal."""
    return {b.get("Name"): b for b in racine.findall("Block")}


# Valeurs par defaut internes de Simulink pour les reglages controles ici.
# Simulink n'ecrit dans system_root.xml que les reglages differents de la
# valeur par defaut du type de bloc, et depuis R2023 environ il n'ecrit plus
# ces valeurs dans simulink/bddefaults.xml. Exemple constate sous R2024a le
# 3 octobre 2026 : un Sum regle sur '++' n'a pas de balise Inputs.
DEFAUTS_SIMULINK = {"Sum": {"Inputs": "++"}, "Product": {"Inputs": "2"},
                    "UnitDelay": {"InitialCondition": "0"}}


def defauts_blocs(chemin):
    """Valeurs par defaut des reglages, par type de bloc : celles de
    DEFAUTS_SIMULINK, completees ou remplacees par celles que le fichier
    ecrit dans simulink/bddefaults.xml (anciennes versions de Simulink)."""
    sortie = {k: dict(v) for k, v in DEFAUTS_SIMULINK.items()}
    if "simulink/bddefaults.xml" not in noms_internes(chemin):
        return sortie
    racine = lire_xml(chemin, "simulink/bddefaults.xml")
    for b in racine.iter("Block"):
        if b.get("BlockType"):
            sortie.setdefault(b.get("BlockType"), {}).update(
                {p.get("Name"): (p.text or "").strip() for p in b.findall("P")})
    return sortie


def reglages(bloc, defauts):
    """Reglages d'un bloc : valeurs par defaut de son type (defauts_blocs),
    puis reglages ecrits (balises <P> sous le bloc et sous son InstanceData),
    qui les remplacent."""
    sortie = dict(defauts.get(bloc.get("BlockType"), {}))
    for p in bloc.findall("P"):
        sortie[p.get("Name")] = (p.text or "").strip()
    for inst in bloc.findall("InstanceData"):
        for p in inst.findall("P"):
            sortie[p.get("Name")] = (p.text or "").strip()
    return sortie


def extremite_lisible(extremite, sid_vers_nom):
    """'24#in:2' -> 'Sum1#in:2' (le numero de bloc remplace par son nom)."""
    m = re.match(r"(\d+)#(.*)", extremite or "")
    if not m:
        return None
    return f"{sid_vers_nom.get(m.group(1), '?' + m.group(1))}#{m.group(2)}"


def liaisons(racine):
    """Liaisons de signal (source, destination) et liaisons electriques
    (listes de bornes), avec les noms des blocs."""
    sid_vers_nom = {b.get("SID"): b.get("Name") for b in racine.findall("Block")}
    signal, electrique, decoratives = set(), [], 0
    for ligne in racine.findall("Line"):
        bornes = [p.text for p in ligne.iter("P") if p.get("Name") in ("Src", "Dst")]
        if not bornes:
            decoratives += 1
            continue
        if ligne.get("LineType") == "Connection":
            electrique.append([extremite_lisible(x, sid_vers_nom) for x in bornes])
        else:
            src = ligne.find("P[@Name='Src']")
            for p in ligne.iter("P"):
                if p.get("Name") == "Dst":
                    signal.add((extremite_lisible(src.text if src is not None else None, sid_vers_nom),
                                extremite_lisible(p.text, sid_vers_nom)))
    return signal, electrique, decoratives


def noeuds(electrique):
    """Noeuds electriques : les bornes d'une meme liaison sont reliees, et
    deux liaisons qui partagent une borne forment un meme noeud (structure
    union-find). Renvoie un ensemble de groupes de bornes."""
    parent = {}

    def chef(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for bornes in electrique:
        for x in bornes:
            chef(x)
        for x in bornes[1:]:
            parent[chef(bornes[0])] = chef(x)
    groupes = {}
    for x in parent:
        groupes.setdefault(chef(x), set()).add(x)
    return {frozenset(g) for g in groupes.values()}


def configuration(chemin):
    """Reglages de simulation (configSet0.xml) : chemin XML -> valeur."""
    sortie = {}

    def parcourir(element, chemin_xml):
        for enfant in element:
            nom = enfant.get("Name") or enfant.get("ClassName") or enfant.tag
            if enfant.tag == "P":
                sortie[chemin_xml + "/" + nom] = (enfant.text or "").strip()
            else:
                parcourir(enfant, chemin_xml + "/" + nom)

    parcourir(lire_xml(chemin, "simulink/configSet0.xml"), "")
    return sortie


def nombre(texte):
    """Valeur numerique d'un reglage, ou None s'il n'est pas numerique.
    Accepte un nombre ou une expression arithmetique simple, comme
    '1/(22000*10)' (chiffres, point, exposant, + - * / et parentheses)."""
    if texte is None:
        return None
    t = texte.strip()
    if not re.fullmatch(r"[0-9eE.+\-*/() ]+", t):
        return None
    try:
        return float(eval(t, {"__builtins__": {}}, {}))
    except Exception:
        return None


# %% ETAPE 2 : les controles

ok, pb, notes = [], [], []
for f in (FICHIER_BASE, FICHIER_COMMUN):
    if not os.path.exists(f):
        raise FileNotFoundError("Fichier introuvable : " + f)
rb = lire_xml(FICHIER_BASE, "simulink/systems/system_root.xml")
rc = lire_xml(FICHIER_COMMUN, "simulink/systems/system_root.xml")
bb, bc = blocs(rb), blocs(rc)
DEF_B, DEF_C = defauts_blocs(FICHIER_BASE), defauts_blocs(FICHIER_COMMUN)   # valeurs par defaut de chaque fichier

# 1. Blocs du modele de base
n_pb = len(pb)                                            # nombre de problemes avant ce controle
for nom, bloc in bb.items():
    if nom == "DC Voltage Source":
        if nom in bc:
            pb.append("La source DC est encore presente.")
        continue
    if nom not in bc:
        pb.append(f"Bloc de base disparu : {nom!r}.")
        continue
    rb_, rc_ = reglages(bloc, DEF_B), reglages(bc[nom], DEF_C)
    if nom == "Series RLC Branch2":
        if rc_.get("Resistance") != "sc_R0":
            pb.append(f"Series RLC Branch2 : Resistance = {rc_.get('Resistance')!r} au lieu de 'sc_R0'.")
        rb_.pop("Resistance", None)
        rc_.pop("Resistance", None)
    ignores = {"Position", "ZOrder"}                      # la mise en page peut bouger
    differences = sorted(k for k in set(rb_) | set(rc_) if k not in ignores and rb_.get(k) != rc_.get(k))
    # Lien de bibliotheque mis a jour par Simulink a l'enregistrement : si le
    # bloc de bibliotheque d'origine (LibrarySourceBlock) est le meme, un
    # changement de SourceBlock (bloc reel apres les renvois de bibliotheque,
    # par exemple sps_lib/powergui -> spspowerguiLib/powergui) ou de
    # LibraryVersion ne change aucun reglage : on le note sans le compter.
    lien = [k for k in differences if k in ("SourceBlock", "LibraryVersion")]
    if lien and rb_.get("LibrarySourceBlock") and rb_.get("LibrarySourceBlock") == rc_.get("LibrarySourceBlock"):
        notes.append(f"Bloc {nom!r} : lien de bibliotheque mis a jour par Simulink ("
                     + ", ".join(f"{k} {rb_.get(k)!r} -> {rc_.get(k)!r}" for k in lien)
                     + f"), meme bloc d'origine {rb_.get('LibrarySourceBlock')!r} ; les autres reglages sont compares normalement.")
        differences = [k for k in differences if k not in lien]
    if differences:
        pb.append(f"Bloc {nom!r} modifie : " + ", ".join(f"{k} {rb_.get(k)!r} -> {rc_.get(k)!r}" for k in differences))
if len(pb) == n_pb:
    ok.append(f"Les {len(bb) - 1} blocs de base gardes ont leurs reglages d'origine ; la source DC a disparu ; "
              "R = sc_R0.")

# 1b. Snubber de la diode supprime (Rs = inf ou Cs = 0). Le snubber RC par
# defaut de Simscape (500 ohms, 250 nF) n'a pas ete dimensionne : il dissipe
# 12 a 28 W et empeche le courant de la bobine de s'annuler a charge legere.
diode = reglages(bc["Diode"], DEF_C) if "Diode" in bc else {}
rs_txt, cs_txt = diode.get("Rs", "").strip(), diode.get("Cs", "").strip()
if rs_txt.lower() in ("inf", "+inf") or nombre(cs_txt) == 0.0:
    ok.append(f"Snubber de la diode supprime (Rs = {rs_txt}, Cs = {cs_txt}).")
else:
    pb.append(f"Snubber de la diode actif (Rs = {rs_txt!r}, Cs = {cs_txt!r}) : mettre Rs = inf dans "
              "PID_Classique_Control.slx, puis reconstruire Buck_Commun.slx.")

# 2. Blocs ajoutes
n_pb = len(pb)
PREVUS = {
    "Source Vin Commandee": ("Reference", {}, "Controlled Voltage Source"),
    "Charge Electronique": ("Reference", {}, "Controlled Current Source"),
    "Profil Consigne": ("FromWorkspace", {"VariableName": "sc_dvref"}, None),
    "Profil Vin": ("FromWorkspace", {"VariableName": "sc_vin"}, None),
    "Profil Charge": ("FromWorkspace", {"VariableName": "sc_gx"}, None),
    "Bruit Mesure": ("FromWorkspace", {"VariableName": "sc_bruit"}, None),
    "Retard Vin": ("UnitDelay", {"InitialCondition": "sc_vin(1,2)"}, None),
    "Retard Charge": ("UnitDelay", {}, None),
    "Courant Charge": ("Product", {}, None),
    "Somme Consigne": ("Sum", {"Inputs": "++"}, None),
    "Somme Bruit Mesure": ("Sum", {"Inputs": "++"}, None),
    "Quantification Mesure": ("Quantizer", {"QuantizationInterval": "sc_q"}, None),
}
ajoutes = sorted(set(bc) - set(bb))
inattendus = [n for n in ajoutes if n not in PREVUS]
absents = [n for n in PREVUS if n not in bc]
if inattendus:
    pb.append("Blocs ajoutes non prevus : " + ", ".join(repr(n) for n in inattendus))
if absents:
    pb.append("Blocs prevus absents : " + ", ".join(repr(n) for n in absents))
for nom, (type_attendu, attendus, source) in PREVUS.items():
    if nom not in bc:
        continue
    bloc = bc[nom]
    r = reglages(bloc, DEF_C)
    if bloc.get("BlockType") != type_attendu:
        pb.append(f"{nom!r} : type {bloc.get('BlockType')!r} au lieu de {type_attendu!r}.")
    for cle, valeur in attendus.items():
        if r.get(cle) != valeur:
            pb.append(f"{nom!r} : {cle} = {r.get(cle)!r} au lieu de {valeur!r}.")
    if source is not None and source not in (r.get("SourceBlock", "") + r.get("LibrarySourceBlock", "")):
        pb.append(f"{nom!r} : ne vient pas du bloc de bibliotheque {source!r}.")
    if type_attendu in ("FromWorkspace", "UnitDelay"):
        periode = TC if type_attendu == "FromWorkspace" else TS
        texte_p = "1/(22000*10)" if type_attendu == "FromWorkspace" else "1/(22000*1200)"
        lu = nombre(r.get("SampleTime"))
        if lu is None or abs(lu - periode) > 1e-9 * periode:
            pb.append(f"{nom!r} : periode {r.get('SampleTime')!r} au lieu de {texte_p}.")
    if type_attendu == "FromWorkspace":
        if r.get("Interpolate") != "off":
            pb.append(f"{nom!r} : interpolation {r.get('Interpolate')!r} (attendu 'off').")
        if r.get("OutputAfterFinalValue") != "Holding final value":
            pb.append(f"{nom!r} : apres la fin des donnees, {r.get('OutputAfterFinalValue')!r} "
                      "(attendu 'Holding final value').")
    if nom == "Retard Charge" and r.get("InitialCondition", "0") not in ("0", "0.0"):
        pb.append(f"'Retard Charge' : condition initiale {r.get('InitialCondition')!r} (attendu 0).")
    if nom == "Courant Charge" and r.get("Inputs", "2") not in ("2", "**"):
        pb.append(f"'Courant Charge' : entrees {r.get('Inputs')!r} (attendu deux entrees multipliees).")
if len(pb) == n_pb:
    ok.append(f"Les {len(PREVUS)} blocs ajoutes sont ceux prevus, avec les bons reglages.")

# 3. Liaisons de signal
sig_b, elec_b, deco_b = liaisons(rb)
sig_c, elec_c, deco_c = liaisons(rc)
RETIREES = {("Vout#out:1", "Sum1#in:2"), ("Constant1#out:1", "Sum1#in:1")}
NOUVELLES = {("Vout#out:1", "Somme Bruit Mesure#in:1"), ("Bruit Mesure#out:1", "Somme Bruit Mesure#in:2"),
             ("Somme Bruit Mesure#out:1", "Quantification Mesure#in:1"), ("Quantification Mesure#out:1", "Sum1#in:2"),
             ("Constant1#out:1", "Somme Consigne#in:1"), ("Profil Consigne#out:1", "Somme Consigne#in:2"),
             ("Somme Consigne#out:1", "Sum1#in:1"), ("Profil Vin#out:1", "Retard Vin#in:1"),
             ("Retard Vin#out:1", "Source Vin Commandee#in:1"), ("Profil Charge#out:1", "Courant Charge#in:1"),
             ("Vout#out:1", "Courant Charge#in:2"), ("Courant Charge#out:1", "Retard Charge#in:1"),
             ("Retard Charge#out:1", "Charge Electronique#in:1")}
attendu = (sig_b - RETIREES) | NOUVELLES
manquantes, en_trop = sorted(attendu - sig_c, key=str), sorted(sig_c - attendu, key=str)
if manquantes:
    pb.append("Liaisons de signal manquantes : " + ", ".join(f"{a} -> {b}" for a, b in manquantes))
if en_trop:
    pb.append("Liaisons de signal en trop : " + ", ".join(f"{a} -> {b}" for a, b in en_trop))
if not manquantes and not en_trop:
    ok.append(f"Liaisons de signal : les {len(sig_b) - len(RETIREES)} liaisons gardees de la base et les "
              f"{len(NOUVELLES)} liaisons prevues, rien d'autre.")

# 4. Noeuds electriques
nb, nc = noeuds(elec_b), noeuds(elec_c)
plus = next(g for g in nb if "DC Voltage Source#rconn:1" in g)
moins = next(g for g in nb if "DC Voltage Source#lconn:1" in g)
sortie_r = next(g for g in nb if "Series RLC Branch2#lconn:1" in g)
bornes_src = sorted(x for g in nc for x in g if x.startswith("Source Vin Commandee#"))
bornes_chg = sorted(x for g in nc for x in g if x.startswith("Charge Electronique#"))
if len(bornes_src) != 2 or len(bornes_chg) != 2:
    pb.append(f"Bornes electriques inattendues : source {bornes_src}, charge {bornes_chg}.")
else:
    trouve = None
    for s_plus, s_moins in (bornes_src, bornes_src[::-1]):
        for c_haut, c_bas in (bornes_chg, bornes_chg[::-1]):
            attendu_n = set()
            for g in nb:
                g2 = set(g) - {"DC Voltage Source#rconn:1", "DC Voltage Source#lconn:1"}
                if g == plus:
                    g2.add(s_plus)
                if g == moins:
                    g2 |= {s_moins, c_bas}
                if g == sortie_r:
                    g2.add(c_haut)
                attendu_n.add(frozenset(g2))
            if attendu_n == nc:
                trouve = (s_plus, s_moins, c_haut, c_bas)
    if trouve:
        ok.append(f"Circuit de puissance : memes {len(nb)} noeuds que la base ; source commandee a la place de "
                  f"la source DC (+ sur {trouve[0].split('#')[1]}, - sur {trouve[1].split('#')[1]}) ; charge "
                  "electronique entre la sortie et la masse.")
    else:
        pb.append("Noeuds electriques differents de ceux attendus : " +
                  "; ".join(", ".join(sorted(g)) for g in sorted(nc, key=lambda g: sorted(g))))
une_borne = [b for b in elec_c if len(b) < 2]
if une_borne or deco_c:
    pb.append(f"{len(une_borne)} liaison(s) electrique(s) a une seule borne et {deco_c} liaison(s) decorative(s).")
else:
    ok.append("Aucune liaison decorative ni liaison electrique pendante.")

# 5. Configuration
cb, cc = configuration(FICHIER_BASE), configuration(FICHIER_COMMUN)
diff_conf = sorted(k for k in set(cb) | set(cc) if cb.get(k) != cc.get(k))
tolerees = [k for k in diff_conf if k.endswith("/ReturnWorkspaceOutputs")]
autres = [k for k in diff_conf if k not in tolerees]
if autres:
    pb.append("Configuration modifiee : " + ", ".join(f"{k}: {cb.get(k)!r} -> {cc.get(k)!r}" for k in autres))
else:
    ok.append("Configuration de simulation identique a la base.")
if tolerees:
    notes.append("ReturnWorkspaceOutputs differe de la base (le script le met a 'off', regle #8).")

# 6. Rappel InitFcn
texte_bd = lire_texte(FICHIER_COMMUN, "simulink/blockdiagram.xml")
if "charger_scenario" in texte_bd and "InitFcn" in texte_bd:
    ok.append("Rappel InitFcn present : S1 est charge si aucun essai ne l'est.")
else:
    pb.append("Rappel InitFcn absent ou sans charger_scenario.")

# 7. Pas de bloc MATLAB Function
if [n for n in noms_internes(FICHIER_COMMUN) if n.startswith("simulink/stateflow/") and "chart" in n]:
    pb.append("Le modele contient un bloc MATLAB Function (Stateflow) non prevu.")


# %% ETAPE 3 : verdict

print("\nControles reussis :")
for x in ok:
    print("  [OK] " + x)
for x in notes:
    print("  [NOTE] " + x)
if pb:
    print("\nProblemes :")
    for x in pb:
        print("  [PROBLEME] " + x)
    print("\nRESULTAT : Buck_Commun.slx ne correspond pas a ce qui est prevu. Ne pas l'utiliser avant correction.")
else:
    print("\nRESULTAT : Buck_Commun.slx est conforme. Etape suivante : Simuler_Scenarios.m.")
