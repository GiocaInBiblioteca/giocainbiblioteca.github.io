#!/usr/bin/env python3
"""
Copertine mancanti, cercate su uplay.it per nome del gioco.

Serve per i giochi che il catalogo della biblioteca non copre:
i 48 donati da Damiano (non ancora catalogati) e i 24 gia' a catalogo ma senza immagine.

REGOLA CHE TIENE ONESTO LO STRUMENTO
Il negozio distingue le edizioni nel nome del file: `woodcraft`, `woodcraft-edizione-inglese`,
`woodcraft-us-version`. Prendiamo SOLO il nome esatto — l'edizione italiana base, quella
che sta sullo scaffale. Se il nome esatto non c'e', lo strumento NON sceglie il piu' simile:
mette il gioco nella lista da guardare a mano. Una copertina sbagliata e' peggio di una mancante,
perche' nessuno la ricontrolla piu'.

USO:  python3 tools/recupera_copertine.py --titoli lista.txt --out dati-catalogo/copertine-extra
"""
import argparse, io, json, os, re, time, unicodedata, urllib.parse, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120"}
RICERCA = "https://www.uplay.it/it/search?query="

def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def pulisci_titolo(t):
    """i titoli del catalogo hanno code da bibliotecari: 'Just one : a te la scelta...'"""
    t = re.split(r"\s*[:;]\s", t)[0]
    return re.sub(r"\s+", " ", t).strip()

def cerca(titolo):
    u = RICERCA + urllib.parse.quote(titolo)
    t = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read().decode("utf-8", "ignore")
    trovati = re.findall(r'(https://www\.uplay\.it/storage/\d+/conversions/([a-z0-9\-]+)-listing\.webp)', t)
    return list(dict.fromkeys(trovati))

def scegli(trovati, atteso):
    """Ordine di fiducia. Sotto queste regole non si sceglie: si chiede a un umano."""
    # 1. nome identico
    for u, s in trovati:
        if s == atteso: return (u, s), "esatto"
    # 2. edizione italiana dichiarata: e' quella che sta sullo scaffale
    for u, s in trovati:
        if s == atteso + "-edizione-italiana": return (u, s), "edizione italiana"
    # 3. la "&" del titolo diventa "amp" nei nomi del negozio
    amp = atteso.replace("-e-", "-amp-")
    for u, s in trovati:
        if s in (amp, amp + "-edizione-italiana"): return (u, s), "e commerciale"
    # 4. stesse parole, stesso ordine, solo un plurale di differenza (forest/forests)
    import difflib
    for u, s in trovati:
        if difflib.SequenceMatcher(None, s, atteso).ratio() >= 0.94: return (u, s), "quasi identico"
    return None, "da guardare"

def scarica(url, dest, lato=500):
    from PIL import Image
    d = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
    im = Image.open(io.BytesIO(d)).convert("RGB")
    if max(im.size) > lato:
        k = lato / max(im.size)
        im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    im.save(dest, "JPEG", quality=85, optimize=True)
    return im.size, os.path.getsize(dest)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--titoli", required=True, help="file di testo, un titolo per riga")
    ap.add_argument("--out", default="./copertine-extra")
    ap.add_argument("--pausa", type=float, default=2.0)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    reg_path = os.path.join(a.out, "_registro.json")
    reg = json.load(open(reg_path)) if os.path.exists(reg_path) else {}

    titoli = [x.strip() for x in open(a.titoli, encoding="utf-8") if x.strip()]
    a_mano = []
    for i, t in enumerate(titoli, 1):
        if t in reg and reg[t].get("file"):
            print(f"  [{i}/{len(titoli)}] {t[:34]:36} già fatto"); continue
        breve = pulisci_titolo(t)
        try:
            trovati = cerca(breve)
            scelta, come = scegli(trovati, slug(breve))
            if scelta:
                url, s = scelta
                p = os.path.join(a.out, f"{s}.jpg")
                dim, peso = scarica(url, p)
                reg[t] = {"file": os.path.basename(p), "slug": s, "url": url, "dim": list(dim), "come": come}
                print(f"  [{i}/{len(titoli)}] {t[:34]:36} ✓ {s[:34]:36} [{come}]")
            else:
                vicini = [s for _, s in trovati[:4]]
                reg[t] = {"file": None, "candidati": vicini}
                a_mano.append((t, vicini))
                print(f"  [{i}/{len(titoli)}] {t[:34]:36} — da guardare  {vicini[:3]}")
        except Exception as e:
            reg[t] = {"file": None, "errore": str(e)}
            a_mano.append((t, []))
            print(f"  [{i}/{len(titoli)}] {t[:34]:36} ERRORE {e}")
        json.dump(reg, open(reg_path, "w"), ensure_ascii=False, indent=1)
        time.sleep(a.pausa)

    fatti = sum(1 for v in reg.values() if v.get("file"))
    print(f"\ntrovate {fatti} su {len(titoli)}")
    if a_mano:
        print(f"\nDA GUARDARE A MANO ({len(a_mano)}) — nessuna copertina inventata:")
        for t, cand in a_mano:
            print(f"  • {t}")
            if cand: print(f"      possibili: {', '.join(cand[:4])}")

if __name__ == "__main__":
    main()
