#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit dei collegamenti del sito statico (docs/).

Non un controllo "risponde per indirizzo diretto" (quello non distingue il
caso rotto dal caso sano: un file esiste comunque, il difetto è nel LINK che
lo cerca dal posto sbagliato). Questo script fa l'unica cosa che conta
davvero: per ogni pagina/foglio di stile generato, prende ogni riferimento
(href, src, url() nei CSS), lo risolve rispetto alla posizione del file che
lo contiene — non rispetto alla radice — e verifica che il bersaglio esista
per davvero sul disco.

Controlla anche il senso inverso: quali pagine HTML generate non sono
raggiunte da NESSUN link di nessun'altra pagina del sito (pagine orfane).
Alcune sono di servizio per scelta (componenti/, etichetta-scatola/,
cartellino/): lo script le segnala comunque, etichettandole come attese,
così una sorpresa vera non si nasconde in mezzo a quelle note.

Uso:
    python3 tools/audit_links.py

Riusabile: nessun argomento, nessuno stato, funziona ogni volta che il sito
viene rigenerato. Exit code 0 se zero link rotti, 1 altrimenti (per CI/hook
futuri, se mai servissero).
"""
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlsplit

BASE = "/home/damiano/Progetti-Personali/giocainbiblioteca.github.io"
SITO = os.path.join(BASE, "docs")

# Pagine HTML "di servizio" che sappiamo già non essere raggiunte da nessun
# link interno (fogli stampabili A4, non punti di navigazione del sito).
# Qualunque altra pagina orfana che emerga è una sorpresa da segnalare.
ORFANE_ATTESE = {
    "componenti/componenti.html",
    "etichetta-scatola/etichetta-scatola.html",
    "cartellino/cartellino.html",
}

ATTRS_DA_CONTROLLARE = {
    "a": ["href"],
    "link": ["href"],
    "script": ["src"],
    "img": ["src"],
    "source": ["src"],
}


class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []  # lista di (tag, attr, valore)

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        for attr in ATTRS_DA_CONTROLLARE.get(tag, []):
            val = attrs_dict.get(attr)
            if val:
                self.links.append((tag, attr, val))


def is_esterno_o_non_file(url):
    """True per link che non puntano a un file locale da verificare sul
    disco: ancore pure (#...), mailto/tel/javascript, URL assolute http(s)."""
    if not url or url.startswith("#"):
        return True
    scheme = urlsplit(url).scheme
    if scheme in ("http", "https", "mailto", "tel", "javascript", "data"):
        return True
    return False


def strip_query_fragment(url):
    parts = urlsplit(url)
    return parts.path


def find_html_files(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(".html"):
                out.append(os.path.join(dirpath, fn))
    return sorted(out)


def find_css_files(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(".css"):
                out.append(os.path.join(dirpath, fn))
    return sorted(out)


CSS_URL_RE = re.compile(r"url\(\s*['\"]?([^'\")]+)['\"]?\s*\)")


def audit_html_file(path):
    """Ritorna (controllati, rotti) dove rotti è lista di dict con dettagli."""
    with open(path, encoding="utf-8") as f:
        content = f.read()
    parser = LinkExtractor()
    parser.feed(content)

    controllati = 0
    rotti = []
    risolti_locali = []  # per il grafo inverso: solo href verso altri .html

    file_dir = os.path.dirname(path)

    for tag, attr, raw_url in parser.links:
        if is_esterno_o_non_file(raw_url):
            continue
        clean = strip_query_fragment(raw_url)
        if not clean:
            continue
        target = os.path.normpath(os.path.join(file_dir, clean))
        controllati += 1
        esiste = os.path.isfile(target)
        if not esiste:
            rotti.append({
                "file": path,
                "tag": tag,
                "attr": attr,
                "raw": raw_url,
                "risolto": target,
            })
        if tag == "a" and attr == "href" and esiste and target.endswith(".html"):
            risolti_locali.append(target)

    return controllati, rotti, risolti_locali


def audit_css_file(path):
    with open(path, encoding="utf-8") as f:
        content = f.read()
    file_dir = os.path.dirname(path)
    controllati = 0
    rotti = []
    for m in CSS_URL_RE.finditer(content):
        raw_url = m.group(1)
        if is_esterno_o_non_file(raw_url):
            continue
        clean = strip_query_fragment(raw_url)
        target = os.path.normpath(os.path.join(file_dir, clean))
        controllati += 1
        if not os.path.isfile(target):
            rotti.append({
                "file": path,
                "tag": "@font-face/url()",
                "attr": "url",
                "raw": raw_url,
                "risolto": target,
            })
    return controllati, rotti


def main():
    html_files = find_html_files(SITO)
    css_files = find_css_files(SITO)

    totale_controllati = 0
    tutti_rotti = []
    grafo_link_html = set()  # insieme di path assoluti .html raggiunti da un href

    for path in html_files:
        controllati, rotti, risolti_locali = audit_html_file(path)
        totale_controllati += controllati
        tutti_rotti.extend(rotti)
        grafo_link_html.update(risolti_locali)

    for path in css_files:
        controllati, rotti = audit_css_file(path)
        totale_controllati += controllati
        tutti_rotti.extend(rotti)

    # --- Report link rotti ---------------------------------------------
    print(f"Pagine HTML trovate: {len(html_files)}")
    print(f"Fogli CSS trovati:   {len(css_files)}")
    print(f"Collegamenti controllati (href/src/url totali): {totale_controllati}")
    print(f"Collegamenti rotti: {len(tutti_rotti)}")
    print()

    if tutti_rotti:
        print("=== ROTTI ===")
        for r in tutti_rotti:
            rel_file = os.path.relpath(r["file"], BASE)
            print(f"- {rel_file}  <{r['tag']} {r['attr']}=\"{r['raw']}\">  ->  manca: {r['risolto']}")
        print()
    else:
        print("Nessun collegamento rotto.")
        print()

    # --- Pagine orfane (nessun link interno le raggiunge) ---------------
    print("=== PAGINE ORFANE (nessun link interno le raggiunge) ===")
    sorprese = []
    for path in html_files:
        if path not in grafo_link_html:
            rel = os.path.relpath(path, SITO)
            if rel in ORFANE_ATTESE:
                print(f"- {rel}  (attesa: pagina di servizio, non pensata per essere linkata)")
            else:
                sorprese.append(rel)

    if sorprese:
        print()
        print("SORPRESE (orfane non previste, da controllare):")
        for rel in sorprese:
            print(f"- {rel}")
    print()

    ok = (len(tutti_rotti) == 0) and (len(sorprese) == 0)
    print(f"Esito finale: {'OK' if ok else 'DA RIVEDERE'} "
          f"({len(tutti_rotti)} rotti, {len(sorprese)} orfane non attese su {len(html_files)} pagine)")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
