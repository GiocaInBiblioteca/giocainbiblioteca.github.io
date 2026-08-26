#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera docs/etichetta-scatola/etichetta-scatola.html — foglio A4 stampabile
con un'etichetta piccola per ogni gioco (48 giochi + 1 per Spirit of the
Forest: Moonlight, stessa scatola-in-più dei cartellini da scaffale), pensata
per il COPERCHIO della scatola, non per lo scaffale (quella è
tools/generate_cartellini.py, resta invariata, formato diverso per uso diverso).

Contenuto dell'etichetta: titolo del gioco (per non confondere quale
etichetta va su quale scatola, unico rischio irreversibile di questo foglio:
48 etichette quasi identiche), poi la domanda-invito, il QR, la risposta
pratica. Testo di domanda/istruzione di Penna (ratificato Damiano 04/08):
NON riformulare senza passare da Alfred.

Composizione (richiesta esplicita di Damiano 04/08): domanda + QR +
istruzione stanno nella STESSA colonna, larga quanto il QR (24mm, il minimo
sotto cui non scendere senza dirlo) — non testo centrato che galleggia sopra
un quadrato di un'altra misura. Il corpo del carattere della domanda è
calibrato per arrivare quasi al bordo del QR (misurato via rendering reale,
non a occhio: vedi nota su ETICHETTA_DOMANDA_FS più sotto); l'istruzione,
pur restando nella stessa colonna, resta un poco più stretta — a parità di
corpo, i due testi non pesano uguale in pixel nonostante la lunghezza quasi
identica (22 e 20 caratteri contando spazi/punteggiatura), e allargare le
lettere o la spaziatura per farla combaciare al pixel avrebbe fatto rumore
tipografico che Damiano ha esplicitamente chiesto di evitare. Nessun
letter-spacing forzato, nessuna deformazione: è un compromesso dichiarato,
non un errore.
"""
import html
import json
import os

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

# Testo Penna, ratificato Damiano 04/08 — non riformulare senza Alfred.
# Versione lunga valutata e scartata: "Apri la fotocamera e puntala qui" non
# ci sta nella colonna larga quanto il QR (24mm) senza andare a capo o
# rimpicciolire il corpo sotto una soglia leggibile — misurato, non stimato.
ETICHETTA_DOMANDA = "Com'è questo gioco?"
ETICHETTA_ISTRUZIONE = "Puntaci il telefono."


def esc(s):
    return html.escape(s, quote=True)


def build_etichetta(g):
    qr_path = f"../qr/{g['slug']}.png"
    return f"""<li class="etichetta-item">
  <div class="etichetta">
    <p class="etichetta-titolo">{esc(g['titolo'])}</p>
    <div class="etichetta-nucleo">
      <p class="etichetta-domanda">{esc(ETICHETTA_DOMANDA)}</p>
      <img class="etichetta-qr" src="{qr_path}" alt="Codice QR per la scheda di {esc(g['titolo'])}" width="90" height="90" loading="lazy">
      <p class="etichetta-istruzione">{esc(ETICHETTA_ISTRUZIONE)}</p>
    </div>
  </div>
</li>"""


# Stessa eccezione dei cartellini da scaffale: Spirit of the Forest è donato
# in due scatole distinte (base + Moonlight). Stesso slug/QR/scheda della
# base — qui è SOLO una seconda etichetta stampata, non un 49° gioco.
def build_moonlight_etichetta(base_game):
    g = dict(base_game)
    g["titolo"] = "Spirit of the Forest: Moonlight"
    return g


def main():
    base_game = next((g for g in GAMES if g["slug"] == "spirit-of-the-forest"), None)
    if base_game is None:
        raise SystemExit(
            "ATTENZIONE: 'spirit-of-the-forest' non trovato in games-data.json — "
            "impossibile generare l'etichetta Moonlight. Fermo qui."
        )

    etichette_data = []
    for g in GAMES:
        etichette_data.append(g)
        if g["slug"] == "spirit-of-the-forest":
            etichette_data.append(build_moonlight_etichetta(base_game))

    n_attesi = len(GAMES) + 1
    if len(etichette_data) != n_attesi:
        raise SystemExit(
            f"ATTENZIONE: attese {n_attesi} etichette ({len(GAMES)} giochi + 1 Moonlight), "
            f"generate {len(etichette_data)} — fermo qui invece di stampare un foglio sbagliato."
        )

    items = "\n".join(build_etichetta(g) for g in etichette_data)
    html_out = f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Etichette da coperchio stampabili — Gioca in Biblioteca</title>
<link rel="stylesheet" href="etichetta-scatola.css">
</head>
<body>
<div class="barra-schermo no-print">
  <p>Foglio pronto per la stampa: {len(etichette_data)} etichette piccole da coperchio
  ({len(GAMES)} giochi, una in più per Spirit of the Forest: Moonlight, la seconda scatola
  della stessa donazione) — diverse dai cartellini da scaffale (quelli restano dove sono,
  formato più grande). Ogni etichetta porta il titolo del gioco: è l'unico modo per non
  scambiare l'etichetta di una scatola con quella di un'altra mentre si ritaglia. Usi Stampa
  del browser e imposti i margini su "Nessuno" o "Minimi" per il risultato migliore.</p>
</div>
<ul class="griglia-etichette">
{items}
</ul>
</body>
</html>
"""
    outdir = f"{BASE}/docs/etichetta-scatola"
    os.makedirs(outdir, exist_ok=True)
    with open(f"{outdir}/etichetta-scatola.html", "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"OK — generato etichetta-scatola.html con {len(etichette_data)} etichette ({len(GAMES)} giochi + 1 Moonlight)")


if __name__ == "__main__":
    main()
