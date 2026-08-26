#!/usr/bin/env python3
"""
Recupera dal catalogo della biblioteca di Lecco, per ogni gioco:
copertina, giocatori, eta', durata, editore/contributi, anno, lingua.

Fonte: https://lecco.biblioteche.it/opac/detail/view/lc:catalog:<RECORD_ID>
Uso delle copertine autorizzato dalla biblioteca, 25/08/2026.

E' gentile col server: una pausa fra le richieste, e non riscarica cio' che ha gia'.
"""
import json, os, re, html, time, argparse, zipfile, urllib.request

BASE = "https://lecco.biblioteche.it/opac/detail/view/lc:catalog:"
UA   = {"User-Agent": "Mozilla/5.0 (GiocaInBiblioteca/catalogo)"}

def leggi_xlsx(path):
    z = zipfile.ZipFile(path)
    sh = [re.sub(r"<[^>]+>", "", m) for m in
          re.findall(r"<si>(.*?)</si>", z.read("xl/sharedStrings.xml").decode(), re.S)]
    out = []
    for r in re.findall(r"<row[^>]*>(.*?)</row>", z.read("xl/worksheets/sheet1.xml").decode(), re.S):
        c = {}
        for m in re.finditer(r'<c r="([A-Z]+)\d+"(?:[^>]*t="(\w+)")?[^>]*>(?:<v>(.*?)</v>)?</c>', r, re.S):
            col, t, v = m.groups()
            c[col] = sh[int(v)] if (t == "s" and v) else (v or "")
        out.append(c)
    return [{"titolo": r["A"].strip(), "record_id": r["B"], "ean": r["C"],
             "abstract": r.get("D", ""), "a_catalogo": r.get("E", "")}
            for r in out[1:] if r.get("A")]

def _campo(righe, etichetta, multi=False):
    for i, x in enumerate(righe):
        if x.lower().startswith(etichetta.lower()):
            if not multi:
                return righe[i+1].strip() if i+1 < len(righe) else ""
            vals = []
            for j in range(i+1, min(i+8, len(righe))):
                if re.match(r"^[A-ZÀ-Ù][a-zà-ù ]+:$", righe[j]): break
                vals.append(righe[j])
            return " ".join(vals).strip()
    return ""

# La Nota ha forma stabile ma non identica: "Giocatori: 2-8 ; Eta' giocatori 10+; Durata 40 min."
# oppure "Giocatori: 2-4; Eta' giocatori 6+; Durata: ca 20 min." — le varianti si assorbono qui.
def spacchetta_nota(nota):
    g = re.search(r"iocatori\s*:?\s*([0-9]+\s*\+?(?:\s*-\s*[0-9]+)?)", nota)
    e = re.search(r"[EÈ]t[àa]\s*giocatori\s*:?\s*([0-9]+\s*\+?)", nota)
    d = re.search(r"[Dd]urata\s*:?\s*((?:ca\.?\s*)?[0-9]+(?:\s*-\s*[0-9]+)?\s*min\.?)", nota)
    pulisci = lambda m: re.sub(r"\s+", "", m.group(1)) if m else ""
    dur = re.sub(r"\s+", " ", d.group(1)).replace("ca.", "ca").strip() if d else ""
    return pulisci(g), pulisci(e), dur

def scarica_scheda(rid):
    req = urllib.request.Request(BASE + str(rid), headers=UA)
    t = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
    corpo = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
    righe = [x.strip() for x in html.unescape(re.sub(r"<[^>]+>", "\n", corpo)).split("\n") if x.strip()]
    nota = _campo(righe, "Nota:")
    g, e, d = spacchetta_nota(nota)
    imgs = [m for m in re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', t) if "clavisng" in m]
    return {
        "giocatori": g, "eta": e, "durata": d, "nota_grezza": nota,
        "contributi": _campo(righe, "Titolo e contributi:"),
        # "Descrizione fisica" non si chiama componenti ma li contiene, insieme a
        # materiali, misure della scatola e spesso l'EAN in chiaro (Damiano, 25/08)
        "descrizione_fisica": _campo(righe, "Descrizione fisica:", multi=True),
        "anno": _campo(righe, "Pubblicazione:"), "lingua": _campo(righe, "Lingua:"),
        "url_scheda": BASE + str(rid),
        "url_copertina": (imgs[0] if imgs.__len__() else ""),
    }

def salva_copertina(url, dest, lato=500, qualita=82):
    """le originali sono ~170 KB l'una: su 148 giochi sarebbero 25 MB nel repo"""
    from PIL import Image
    import io
    if not url.startswith("http"):
        url = "https://lecco.biblioteche.it/" + url.lstrip("/")
    dati = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
    im = Image.open(io.BytesIO(dati)).convert("RGB")
    if max(im.size) > lato:
        s = lato/max(im.size)
        im = im.resize((round(im.width*s), round(im.height*s)), Image.LANCZOS)
    im.save(dest, "JPEG", quality=qualita, optimize=True)
    return len(dati), os.path.getsize(dest), im.size

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", default="/home/damiano/Scaricati/Giochi con schede catalografiche al 25.08.2026.xlsx")
    ap.add_argument("--out", default="./recupero")
    ap.add_argument("--limite", type=int, default=0, help="0 = tutti")
    ap.add_argument("--pausa", type=float, default=1.5)
    a = ap.parse_args()
    cart_img = os.path.join(a.out, "copertine"); os.makedirs(cart_img, exist_ok=True)
    dati_path = os.path.join(a.out, "schede.json")
    fatti = json.load(open(dati_path)) if os.path.exists(dati_path) else {}

    giochi = leggi_xlsx(a.xlsx)
    if a.limite: giochi = giochi[:a.limite]
    nuovi = tot_prima = tot_dopo = 0
    for i, g in enumerate(giochi, 1):
        rid = g["record_id"]
        if rid in fatti:                       # riprendibile: non rifa' il lavoro gia' fatto
            print(f"  [{i}/{len(giochi)}] {g['titolo'][:30]:32} gia' fatto"); continue
        try:
            sc = scarica_scheda(rid); sc.update(g)
            if sc["url_copertina"]:
                p = os.path.join(cart_img, f"{rid}.jpg")
                pre, post, dim = salva_copertina(sc["url_copertina"], p)
                sc["copertina_file"] = os.path.relpath(p, a.out); sc["copertina_dim"] = list(dim)
                tot_prima += pre; tot_dopo += post
            fatti[rid] = sc; nuovi += 1
            print(f"  [{i}/{len(giochi)}] {g['titolo'][:30]:32} {sc['giocatori'] or '—':>7} | {sc['eta'] or '—':>4} | {sc['durata'] or '—':>10} | {'cop' if sc.get('copertina_file') else 'NO COP'}")
        except Exception as ex:
            print(f"  [{i}/{len(giochi)}] {g['titolo'][:30]:32} ERRORE: {ex}")
        time.sleep(a.pausa)
        json.dump(fatti, open(dati_path, "w"), ensure_ascii=False, indent=1)
    print(f"\nrecuperati ora: {nuovi} | totale in archivio: {len(fatti)}")
    if tot_dopo:
        print(f"copertine: {tot_prima/1024:.0f} KB scaricati -> {tot_dopo/1024:.0f} KB salvati "
              f"(su 148 giochi ~{tot_dopo/max(nuovi,1)*148/1024/1024:.1f} MB)")

if __name__ == "__main__":
    main()
