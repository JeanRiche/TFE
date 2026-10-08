# =============================================================================
# tester_verifier_modeles_comparaison.py
#
# VERSION
#   1 (8 octobre 2026).
#
# OBJECTIF
#   Tester, sans MATLAB, le verificateur verifier_modeles_comparaison.py
#   (dossiers de methode) sur des modeles FABRIQUES par ce script a partir
#   de Buck_Commun.slx (copie modifiee directement dans le XML de l'archive,
#   comme le ferait Construire_Modeles_Comparaison.m) :
#     A. modeles conformes : ZN_<code>.slx pour S1, S2, S3, S8a, S10 ; et,
#        avec une fausse source adaptative (Buck_Commun.slx + un bloc
#        "ELM-PID Adaptatif" isole), ELM_PID_S2.slx et ELM_PID_S10.slx
#        (blocs d'observation des gains en plus) : tous doivent passer ;
#     B. variantes a rejeter : inductance du circuit modifiee (10e-3 ->
#        11e-3), gain P du PID modifie, StopTime faux, InitFcn d'origine
#        garde, bloc non prevu ajoute (Constant), solveur change, bloc
#        ajoute qui renvoie un signal dans le modele : chacune doit etre
#        rejetee.
#   Ce test ne remplace pas le controle des vrais modeles construits sous
#   MATLAB : le XML ecrit par Simulink peut differer de celui fabrique ici
#   (reglages par defaut ecrits ou non, forme des branches de liaison).
#
# COMMENT LANCER CE SCRIPT
#   python tester_verifier_modeles_comparaison.py
#   (quelques secondes ; dossier temporaire efface a la fin). Il faut a cote
#   le dossier ../ELM_PID (Buck_Commun.slx, scenarios_communs.json,
#   verifier_modeles_comparaison.py).
# =============================================================================

import os
import io
import re
import sys
import json
import shutil
import zipfile
import tempfile
import contextlib
from xml.sax.saxutils import escape

try:
    DOSSIER = os.path.dirname(os.path.abspath(__file__))
except NameError:
    DOSSIER = os.getcwd()
ELM = os.path.join(os.path.dirname(DOSSIER), "ELM_PID")
sys.path.insert(0, ELM)
import verifier_modeles_comparaison as V          # noqa: E402

BASE = os.path.join(ELM, "Buck_Commun.slx")
with open(os.path.join(ELM, "scenarios_communs.json"), encoding="utf-8") as f:
    LISTE = json.load(f)
DUREES = {e["code"]: float(e["duree"]) for e in LISTE["essais"] + LISTE.get("essais_complementaires", [])}
TC_TXT = "1/(22000*10)"


def lire(chemin):
    with zipfile.ZipFile(chemin) as z:
        return {n: z.read(n) for n in z.namelist()}


def ecrire(chemin, contenu):
    with zipfile.ZipFile(chemin, "w", zipfile.ZIP_DEFLATED) as z:
        for n, d in contenu.items():
            z.writestr(n, d)


def bloc_xml(type_, nom, sid, n_in, n_out, params):
    pc = " ".join(x for x in ((f'in="{n_in}"' if n_in else ""), (f'out="{n_out}"' if n_out else "")) if x)
    ps = "".join(f'\n    <P Name="{k}">{escape(v)}</P>' for k, v in params.items())
    return (f'  <Block BlockType="{type_}" Name="{escape(nom)}" SID="{sid}">\n    <PortCounts {pc} />'
            f'\n    <P Name="Position">[2000, {100 + 50 * sid}, 2060, {130 + 50 * sid}]</P>'
            f'\n    <P Name="ZOrder">{9000 + sid}</P>{ps}\n  </Block>\n')


def ligne_xml(src, dst):
    return (f'  <Line>\n    <P Name="ZOrder">{abs(hash((src, dst))) % 100000}</P>\n    <P Name="Src">{src}</P>\n'
            f'    <P Name="Dst">{dst}</P>\n  </Line>\n')


def sids(texte):
    return {m.group(1): m.group(2) for m in re.finditer(r'<Block BlockType="[^"]*" Name="([^"]*)" SID="(\d+)"', texte)}


def fabriquer(source, cible, prefixe, code, gains=None, alterer=None):
    """Copie modifiee de source, comme Construire_Modeles_Comparaison.m :
    InitFcn, StopTime, blocs et liaisons d'observation. 'alterer' recoit le
    dictionnaire des fichiers de l'archive pour fabriquer une variante."""
    mdl = os.path.splitext(os.path.basename(cible))[0]
    c = lire(source)
    # InitFcn
    bd = c["simulink/blockdiagram.xml"].decode("utf-8")
    ancien = re.search(r'<P Name="InitFcn">(.*?)</P>', bd, re.S)
    ancien_txt = ancien.group(1).replace("&apos;", "'").replace("&quot;", '"').replace("&lt;", "<") \
        .replace("&gt;", ">").replace("&amp;", "&") if ancien else ""
    nouveau = escape(V.texte_initfcn(mdl, code, ancien_txt), {"'": "&apos;"})
    bd = bd.replace(ancien.group(0), f'<P Name="InitFcn">{nouveau}</P>') if ancien else bd
    c["simulink/blockdiagram.xml"] = bd.encode("utf-8")
    # StopTime
    n = int(round(DUREES[code] / V.TC)) + 1
    cs = c["simulink/configSet0.xml"].decode("utf-8")
    cs = re.sub(r'<P Name="StopTime">[^<]*</P>', f'<P Name="StopTime">{(n - 0.5) * V.TC!r}</P>', cs, count=1)
    c["simulink/configSet0.xml"] = cs.encode("utf-8")
    # Blocs et liaisons d'observation
    rt = c["simulink/systems/system_root.xml"].decode("utf-8")
    S = sids(rt)
    sid = max(int(x) for x in S.values()) + 1
    nom_pwm = "PWM Generator&#xA;(DC-DC)"
    src_pwm = re.search(r'<P Name="Src">(\d+#out:\d+)</P>\s*<P Name="Dst">' + S[nom_pwm] + r'#in:1</P>', rt)
    if src_pwm is None:                           # forme a branches : on cherche la ligne qui arrive au PWM
        for bloc in re.findall(r"<Line>.*?</Line>", rt, re.S):
            if f'<P Name="Dst">{S[nom_pwm]}#in:1</P>' in bloc:
                src_pwm = re.search(r'<P Name="Src">([^<]*)</P>', bloc)
    src_pwm = src_pwm.group(1)
    blocs, lignes = "", ""
    obs = [("Scope", "Observation Vout et consigne", 2, 0, {"SampleTime": TC_TXT},
            [(f"{S['Vout']}#out:1", 1), (f"{S['Somme Consigne']}#out:1", 2)]),
           ("Scope", "Observation iL", 1, 0, {"SampleTime": TC_TXT}, [(f"{S['iL']}#out:1", 1)]),
           ("Scope", "Observation rapport cyclique", 1, 0, {"SampleTime": TC_TXT}, [(src_pwm, 1)])]
    tw = [("Enregistrement Vout", "cmp_vout", f"{S['Vout']}#out:1"), ("Enregistrement iL", "cmp_iL", f"{S['iL']}#out:1"),
          ("Enregistrement rapport cyclique", "cmp_d", src_pwm)]
    if gains:
        g = f"{S[gains]}#out:1"
        sid_gain = sid + 20
        blocs += bloc_xml("Gain", "Observation gains rapportes a ZN", sid_gain, 1, 1,
                          {"Gain": "[1/%.17g, 1/%.17g, 1/%.17g]" % V.K_ZN, "Multiplication": "Element-wise(K.*u)"})
        lignes += ligne_xml(g, f"{sid_gain}#in:1")
        obs.append(("Scope", "Observation gains", 1, 0, {"SampleTime": TC_TXT}, [(f"{sid_gain}#out:1", 1)]))
        tw.append(("Enregistrement gains", "cmp_K", g))
    for type_, nom, n_in, n_out, params, entrees in obs:
        blocs += bloc_xml(type_, nom, sid, n_in, n_out, params)
        for src, port in entrees:
            lignes += ligne_xml(src, f"{sid}#in:{port}")
        sid += 1
    for nom, var, src in tw:
        blocs += bloc_xml("ToWorkspace", nom, sid, 1, 0, {"VariableName": var, "MaxDataPoints": "inf",
                                                          "SaveFormat": "Timeseries", "SampleTime": TC_TXT})
        lignes += ligne_xml(src, f"{sid}#in:1")
        sid += 1
    rt = rt.replace("</System>", blocs + lignes + "</System>")
    c["simulink/systems/system_root.xml"] = rt.encode("utf-8")
    if alterer:
        alterer(c)
    ecrire(cible, c)


def remplacer(c, interne, avant, apres):
    t = c[interne].decode("utf-8")
    if avant not in t:
        raise RuntimeError(f"Motif introuvable dans {interne} : {avant!r}")
    c[interne] = t.replace(avant, apres, 1).encode("utf-8")


def fausse_source_adaptative(cible):
    """Buck_Commun.slx + un bloc MATLAB System "ELM-PID Adaptatif" isole (une sortie)."""
    c = lire(BASE)
    rt = c["simulink/systems/system_root.xml"].decode("utf-8")
    rt = rt.replace("</System>", bloc_xml("MATLABSystem", "ELM-PID Adaptatif", 80, 3, 1,
                                          {"System": "elm_pid_adaptatif"}) + "</System>")
    c["simulink/systems/system_root.xml"] = rt.encode("utf-8")
    ecrire(cible, c)


def verifier(dossier, fichier):
    tampon = io.StringIO()
    with contextlib.redirect_stdout(tampon):
        code = V.main(["--dossier", dossier, fichier])
    return code, tampon.getvalue()


tmp = tempfile.mkdtemp(prefix="test_verif_cmp_")
bilan = []
try:
    def dossier_neuf(nom):
        d = os.path.join(tmp, nom)
        os.makedirs(d)
        shutil.copy(BASE, d)
        shutil.copy(os.path.join(ELM, "scenarios_communs.json"), d)
        fausse_source_adaptative(os.path.join(d, "Buck_Commun_ELM_PID.slx"))
        return d

    # A. Modeles conformes
    d = dossier_neuf("conformes")
    for code in ("S1", "S2", "S3", "S8a", "S10"):
        fabriquer(os.path.join(d, "Buck_Commun.slx"), os.path.join(d, f"ZN_{code}.slx"), "ZN", code)
    for code in ("S2", "S10"):
        fabriquer(os.path.join(d, "Buck_Commun_ELM_PID.slx"), os.path.join(d, f"ELM_PID_{code}.slx"), "ELM_PID", code,
                  gains="ELM-PID Adaptatif")
    for f in sorted(x for x in os.listdir(d) if re.fullmatch(r"(ZN|ELM_PID)_S\w+\.slx", x)):
        code, sortie = verifier(d, f)
        bilan.append(("conforme attendu", f, code == 0))
        print(f"A. {f:18s} -> {'conforme' if code == 0 else 'REJETE'} (attendu : conforme)")
        if code != 0:
            print(sortie)

    # B. Variantes a rejeter
    def ajout_constant(c):
        remplacer(c, "simulink/systems/system_root.xml", "</System>",
                  bloc_xml("Constant", "Observation constante", 95, 0, 1, {"Value": "1"}) + "</System>")

    def renvoi_dans_modele(c):
        t = c["simulink/systems/system_root.xml"].decode("utf-8")
        S = sids(t)
        sid_g = S["Observation gains rapportes a ZN"]
        # le gain d'observation alimente l'entree 2 de "Courant Charge" a la place de Vout
        t = t.replace(f'<P Name="Dst">{S["Courant Charge"]}#in:2</P>', "", 1)
        t = t.replace("</System>", ligne_xml(f"{sid_g}#out:1", f"{S['Courant Charge']}#in:2") + "</System>")
        c["simulink/systems/system_root.xml"] = t.encode("utf-8")

    VARIANTES = [
        ("inductance modifiee", "ZN", "S8a", None,
         lambda c: remplacer(c, "simulink/systems/system_root.xml", '<P Name="Inductance">10e-3</P>',
                             '<P Name="Inductance">11e-3</P>')),
        ("gain P du PID modifie", "ZN", "S3", None,
         lambda c: remplacer(c, "simulink/systems/system_root.xml", '<P Name="P">0.093910</P>', '<P Name="P">0.1</P>')),
        ("StopTime faux", "ZN", "S1", None,
         lambda c: c.__setitem__("simulink/configSet0.xml", re.sub(rb'<P Name="StopTime">[^<]*</P>',
                                                                     b'<P Name="StopTime">0.2</P>',
                                                                     c["simulink/configSet0.xml"], count=1))),
        ("InitFcn d'origine", "ZN", "S2", None,
         lambda c: c.__setitem__("simulink/blockdiagram.xml", lire(BASE)["simulink/blockdiagram.xml"])),
        ("bloc non prevu ajoute", "ZN", "S10", None, ajout_constant),
        ("solveur change", "ZN", "S2", None,
         lambda c: remplacer(c, "simulink/configSet0.xml", '<P Name="StartTime">0.0</P>', '<P Name="StartTime">0.001</P>')),
        ("signal renvoye dans le modele", "ELM_PID", "S10", "ELM-PID Adaptatif", renvoi_dans_modele),
    ]
    for i, (titre, prefixe, code, gains, alterer) in enumerate(VARIANTES):
        d = dossier_neuf(f"variante_{i}")
        source = "Buck_Commun_ELM_PID.slx" if prefixe == "ELM_PID" else "Buck_Commun.slx"
        f = f"{prefixe}_{code}.slx"
        fabriquer(os.path.join(d, source), os.path.join(d, f), prefixe, code, gains=gains, alterer=alterer)
        rc, sortie = verifier(d, f)
        motifs = [x.strip() for x in sortie.splitlines() if "[PROBLEME]" in x]
        bilan.append(("rejet attendu", f"{f} ({titre})", rc != 0))
        print(f"B. {f:14s} {titre:30s} -> {'rejete' if rc != 0 else 'ACCEPTE A TORT'} (attendu : rejete)")
        for x in motifs:
            print("      " + (x if len(x) < 240 else x[:240] + " ..."))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

reussis = sum(ok for _, _, ok in bilan)
print(f"\nBILAN : {reussis} cas sur {len(bilan)} conformes a l'attente "
      f"({sum(1 for a, _, _ in bilan if a == 'conforme attendu')} modeles conformes acceptes attendus, "
      f"{sum(1 for a, _, _ in bilan if a == 'rejet attendu')} variantes rejetees attendues).")
sys.exit(0 if reussis == len(bilan) else 1)
