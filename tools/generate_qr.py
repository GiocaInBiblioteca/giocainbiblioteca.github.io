#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera i QR code per i 48 giochi, uno per ciascuno, in docs/qr/<slug>.png.

Indirizzo pubblico definitivo: https://giocainbiblioteca.github.io/
(organizzazione GitHub "GiocaInBiblioteca", repo "giocainbiblioteca.github.io").
Un QR è un indirizzo inciso su carta: se l'indirizzo cambia dopo la stampa,
ogni cartellino stampato smette di funzionare in silenzio. Se l'indirizzo
dovesse mai cambiare, questo script va rilanciato e i cartellini rigenerati
(tools/generate_cartellini.py) e ristampati prima di buttare i vecchi.

Uso:
    python3 tools/generate_qr.py --base-url https://giocainbiblioteca.github.io

Libreria necessaria: pacchetto Python "qrcode" (https://pypi.org/project/qrcode/,
licenza BSD, genera immagini in locale, zero chiamate di rete, zero
dipendenza a runtime del sito — serve solo in fase di generazione, qui
sulla macchina di Damiano). Già installata su questa macchina.

Schema URL adottato: {base_url}/g/<slug>/  — stessa cartella già usata
in locale (docs/g/<slug>/index.html), così i link restano identici tra
la copia offline su chiavetta e la pubblicazione su GitHub Pages.
"""
import argparse
import json
import os
import sys

BASE = "/home/damiano/Progetti-Personali/giocainbiblioteca.github.io"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        required=True,
        help="Indirizzo base definitivo, es. https://<utente>.github.io/<repo> (SENZA slash finale)",
    )
    parser.add_argument(
        "--out-dir",
        default=f"{BASE}/docs/qr",
        help="Cartella di output (default: docs/qr)",
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")

    try:
        import qrcode
    except ImportError:
        print(
            "ERRORE: libreria 'qrcode' non installata.\n"
            "Questo script è parametrizzato e pronto, ma la libreria va approvata\n"
            "esplicitamente prima dell'installazione (vedi docstring in testa al file).\n"
            "Se approvata: pip install qrcode[pil]",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(f"{BASE}/docs/js/games-data.json", encoding="utf-8") as f:
        games = json.load(f)

    # Solo i giochi con scheda completa (i 48 di Damiano): quelli della
    # biblioteca non hanno ancora una scheda da far trovare in fondo al QR,
    # e la biblioteca non ha ancora deciso se stamperà per loro.
    _n_prima = len(games)
    games = [g for g in games if g.get("scheda_completa", True)]
    if len(games) != _n_prima:
        print(f"Saltati {_n_prima - len(games)} giochi senza scheda completa (niente QR per loro).")

    os.makedirs(args.out_dir, exist_ok=True)

    for g in games:
        url = f"{base_url}/g/{g['slug']}/"
        img = qrcode.make(url)
        out_path = os.path.join(args.out_dir, f"{g['slug']}.png")
        img.save(out_path)
        print(f"  {g['slug']:35s} -> {url}")

    print(f"OK — generati {len(games)} QR in {args.out_dir}")


if __name__ == "__main__":
    main()
