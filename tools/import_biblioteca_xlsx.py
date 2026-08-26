#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Importa il foglio Excel che la biblioteca manda periodicamente (titolo,
RECORD_ID, EAN, abstract, stato catalogazione) e produce/aggiorna
biblioteca-nuovi.csv — la fonte da cui tools/build_data.py legge i giochi
"scarni" (senza descrizione/livello/componenti, quelli scritti da Damiano).

Non usa openpyxl (non installato, non è nel novero delle dipendenze
ammesse): l'xlsx è un file zip con XML dentro, letto con la sola libreria
standard (zipfile + xml.etree).

Uso:
    python3 tools/import_biblioteca_xlsx.py "/percorso/al/file.xlsx"

Regola di sicurezza: se un titolo del foglio Excel esiste già in
giochi-originale.csv (il catalogo di Damiano), lo script NON lo scrive
in biblioteca-nuovi.csv e stampa un avviso — non decide da solo come
unificare due schede sullo stesso gioco (è già successo una volta con
Kingdomino: la scelta su quale riga tenere e come è stata umana, non
automatica, e resta tale ogni volta che ricapita).
"""
import csv
import re
import sys
import unicodedata
import zipfile
from xml.etree import ElementTree as ET

BASE = "/home/damiano/Progetti-Personali/giocainbiblioteca.github.io"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

STATO_MAP = {
    "già a catalogo": "in biblioteca",
    "gia' a catalogo": "in biblioteca",
    "in arrivo": "in arrivo",
}


def norm_title_key(t):
    """Stessa normalizzazione usata per confrontare titoli fra fonti diverse:
    minuscolo, senza parentesi, spazi ridotti — non deve essere identica
    carattere per carattere per contare come lo stesso gioco."""
    t = re.sub(r"\s*\(.*?\)\s*", " ", t)
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode("ascii")
    t = re.sub(r"\s+", " ", t).strip().lower()
    return t


def leggi_xlsx(path):
    z = zipfile.ZipFile(path)
    ss_root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    shared = []
    for si in ss_root.findall("m:si", NS):
        texts = si.findall(".//m:t", NS)
        shared.append("".join(t.text or "" for t in texts))

    root = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))

    def col_letter(cellref):
        m = re.match(r"([A-Z]+)(\d+)", cellref)
        return m.group(1)

    rows = []
    for row in root.findall(".//m:row", NS):
        rowvals = {}
        for c in row.findall("m:c", NS):
            col = col_letter(c.get("r"))
            t = c.get("t")
            v = c.find("m:v", NS)
            val = v.text if v is not None else None
            if t == "s" and val is not None:
                val = shared[int(val)]
            rowvals[col] = val
        rows.append(rowvals)
    return rows


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python3 tools/import_biblioteca_xlsx.py <percorso.xlsx>")
    xlsx_path = sys.argv[1]

    rows = leggi_xlsx(xlsx_path)
    header = rows[0]
    attese = {"A": "TITOLO", "B": "RECORD_ID", "C": "EAN", "D": "ABSTRACT", "E": "A CATALOGO"}
    for col, nome in attese.items():
        if (header.get(col) or "").strip() != nome:
            raise SystemExit(
                f"ATTENZIONE: intestazione colonna {col} attesa '{nome}', trovata "
                f"'{header.get(col)}' — il foglio della biblioteca è cambiato di forma, "
                f"fermo qui invece di importare alla cieca."
            )
    data = rows[1:]

    # titoli già presenti nel catalogo di Damiano (per rilevare sovrapposizioni)
    with open(f"{BASE}/giochi-originale.csv", newline="", encoding="utf-8") as f:
        csv_rows = list(csv.reader(f))
    titoli_originali = {
        norm_title_key(r[0]) for r in csv_rows[1:49] if r and r[0].strip()
    }

    scritte = []
    saltate_sovrapposte = []
    saltate_incomplete = []
    for r in data:
        titolo = (r.get("A") or "").strip()
        record_id = (r.get("B") or "").strip()
        ean = (r.get("C") or "").strip()
        abstract = (r.get("D") or "").strip()
        stato_raw = (r.get("E") or "").strip().lower()

        if not titolo:
            continue
        if not record_id or not ean:
            saltate_incomplete.append(titolo)
            continue
        if norm_title_key(titolo) in titoli_originali:
            saltate_sovrapposte.append(titolo)
            continue
        stato = STATO_MAP.get(stato_raw)
        if stato is None:
            raise SystemExit(
                f"ATTENZIONE: stato '{r.get('E')}' per '{titolo}' non riconosciuto "
                f"(atteso 'Già a catalogo' o 'In arrivo') — fermo qui."
            )
        scritte.append([titolo, record_id, ean, abstract, stato])

    out_path = f"{BASE}/biblioteca-nuovi.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["TITOLO", "RECORD_ID", "EAN", "ABSTRACT", "STATO"])
        w.writerows(scritte)

    print(f"OK — {len(scritte)} giochi scritti in {out_path}")
    if saltate_sovrapposte:
        print(f"SALTATI (già nel catalogo di Damiano, gestione manuale come Kingdomino): {saltate_sovrapposte}")
    if saltate_incomplete:
        print(f"SALTATI (senza RECORD_ID o EAN, non collegabili al catalogo online): {saltate_incomplete}")


if __name__ == "__main__":
    main()
