#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera docs/componenti/componenti.html — foglio A4 stampabile con l'elenco
componenti di ogni gioco, un blocco per gioco, in ordine alfabetico per
titolo, ciascuna voce con una casella da spuntare.

Non è vetrina: è lo strumento con cui un bibliotecario controlla che una
scatola sia completa (dopo una partita in sede, o al rientro da un prestito).
I componenti vengono spezzati sul separatore "·" già presente nel campo
"componenti" di games-data.json — una voce per riga, una casella per voce.

I componenti sono stati raccolti da fonti esterne, gioco per gioco: NON sono
l'inventario ufficiale dell'editore. Ogni blocco ha in fondo uno spazio
"Note" per segnare a mano differenze trovate nella scatola reale.
"""
import html
import json

BASE = "/home/damiano/Progetti-Personali/giocainbiblioteca.github.io"

with open(f"{BASE}/docs/js/games-data.json", encoding="utf-8") as f:
    GAMES = json.load(f)

# Le stampe (cartellini/etichette/componenti/QR) valgono solo per i giochi con
# scheda completa (i 48 di Damiano): i giochi della biblioteca non hanno
# ancora componenti/livello/descrizione da stampare, e la biblioteca non ha
# ancora deciso se stamperà per loro. Si saltano qui, un punto solo, invece
# di far fallire lo script su un campo mancante.
_n_prima = len(GAMES)
GAMES = [g for g in GAMES if g.get("scheda_completa", True)]
if len(GAMES) != _n_prima:
    print(f"Saltati {_n_prima - len(GAMES)} giochi senza scheda completa (dati insufficienti per la stampa).")


def esc(s):
    return html.escape(s, quote=True)


def build_blocco(g):
    voci = [v.strip() for v in g["componenti"].split("·") if v.strip()]
    righe = "\n".join(
        f'      <li class="voce-componente"><span class="checkbox" aria-hidden="true"></span><span>{esc(v)}</span></li>'
        for v in voci
    )
    return f"""<li class="gioco-blocco">
  <h2 class="gioco-titolo">{esc(g['titolo'])}</h2>
  <ul class="lista-componenti">
{righe}
  </ul>
  <p class="nota-riga"><span class="nota-etichetta">Note:</span><span class="nota-spazio"></span></p>
</li>"""


def main():
    giochi_ordinati = sorted(GAMES, key=lambda g: g["titolo"].lower())

    if len(giochi_ordinati) != len(GAMES):
        raise SystemExit("ATTENZIONE: l'ordinamento ha perso o duplicato giochi — fermo qui.")

    blocchi = "\n".join(build_blocco(g) for g in giochi_ordinati)
    html_out = f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Elenco componenti — Gioca in Biblioteca</title>
<link rel="stylesheet" href="componenti.css">
</head>
<body>
<div class="barra-schermo no-print">
  <p>Foglio di controllo scatole: un blocco per gioco (ordine alfabetico, {len(giochi_ordinati)} giochi in tutto),
  con una casella da spuntare per ogni componente elencato. L'elenco è stato raccolto da fonti esterne,
  gioco per gioco: non è l'inventario ufficiale dell'editore. Usa lo spazio "Note" in fondo a ogni blocco
  per segnare a mano cosa manca o cosa c'è in più nella scatola reale.
  Usi Stampa del browser e imposti i margini su "Nessuno" o "Minimi" per il risultato migliore.</p>
</div>
<ul class="griglia-componenti">
{blocchi}
</ul>
</body>
</html>
"""
    with open(f"{BASE}/docs/componenti/componenti.html", "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"OK — generato componenti.html con {len(giochi_ordinati)} blocchi gioco")


if __name__ == "__main__":
    main()
