#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera docs/cartellino/cartellino.html — foglio A4 stampabile con 8 cartellini
per pagina (2 colonne x 4 righe), uno per ciascuno dei 48 giochi.

Ogni cartellino: titolo, giocatori, livello (pallini), descrizione breve, QR.
Niente gergo tecnico sul cartellino: chi lo legge è in piedi davanti allo scaffale.

Il QR punta a ../qr/<slug>.png. Le immagini si generano con
tools/generate_qr.py --base-url <indirizzo definitivo>: vanno rigenerate
(e questo script rilanciato) ogni volta che l'indirizzo pubblico cambia.
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


def esc(s):
    return html.escape(s, quote=True)


def dots_markup(dots_str, livello_key):
    spans = []
    for ch in dots_str:
        cls = "dot dot-on" if ch == "●" else "dot"
        spans.append(f'<span class="{cls}" aria-hidden="true">{ch}</span>')
    return f'<span class="dots livello-{livello_key}">' + "".join(spans) + "</span>"


def build_cartellino(g):
    qr_path = f"../qr/{g['slug']}.png"
    return f"""<li class="cartellino-item">
  <div class="cartellino">
    <div class="cartellino-testo">
      <h2 class="cartellino-titolo">{esc(g['titolo'])}</h2>
      <div class="cartellino-meta">
        <span class="giocatori-badge">{esc(g['giocatori'])} giocatori</span>
        <span class="livello-badge livello-{g['livello_key']}">{dots_markup(g['livello_dots'], g['livello_key'])} <span class="etichetta-livello">{esc(g['livello_label'])}</span></span>
      </div>
      <p class="cartellino-desc">{esc(g['descrizione'])}</p>
    </div>
    <div class="cartellino-qr">
      <img src="{qr_path}" alt="Codice QR per la scheda di {esc(g['titolo'])}" width="120" height="120" loading="lazy">
    </div>
  </div>
</li>"""


# Spirit of the Forest è donato in due scatole distinte (base + Moonlight, vedi
# spirit-correzione.md). Il catalogo resta di 48 giochi — Moonlight non è una
# voce nuova né in home né nelle porte né nei conteggi, non ha una scheda sua —
# ma sullo scaffale è una scatola a sé, e senza un proprio cartellino è quella
# che nessuno prende in mano. Stesso slug/QR/scheda della base: qui è SOLO un
# secondo cartellino stampato, non un 49° gioco.
def build_moonlight_cartellino(base_game):
    g = dict(base_game)
    g["titolo"] = "Spirit of the Forest: Moonlight"
    g["descrizione"] = (
        "Il modulo notturno di Spirit of the Forest, per giocare in cooperazione "
        "o in solitario. Sono due scatole: prendile insieme."
    )
    # slug invariato (eredita quello della base): stesso QR, stessa scheda.
    return g


def main():
    base_game = next((g for g in GAMES if g["slug"] == "spirit-of-the-forest"), None)
    if base_game is None:
        raise SystemExit(
            "ATTENZIONE: 'spirit-of-the-forest' non trovato in games-data.json — "
            "impossibile generare il cartellino Moonlight. Fermo qui."
        )

    cartellini_data = []
    for g in GAMES:
        cartellini_data.append(g)
        if g["slug"] == "spirit-of-the-forest":
            cartellini_data.append(build_moonlight_cartellino(base_game))

    n_attesi = len(GAMES) + 1
    if len(cartellini_data) != n_attesi:
        raise SystemExit(
            f"ATTENZIONE: attesi {n_attesi} cartellini ({len(GAMES)} giochi + 1 Moonlight), "
            f"generati {len(cartellini_data)} — fermo qui invece di stampare un foglio sbagliato."
        )

    items = "\n".join(build_cartellino(g) for g in cartellini_data)
    html_out = f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cartellini stampabili — Gioca in Biblioteca</title>
<link rel="stylesheet" href="cartellino.css">
</head>
<body>
<div class="barra-schermo no-print">
  <p>Foglio pronto per la stampa: 8 cartellini per pagina A4 (2 colonne &times; 4 righe), {len(cartellini_data)} cartellini in tutto
  ({len(GAMES)} giochi, un cartellino in più per Spirit of the Forest: Moonlight, la seconda scatola della stessa donazione).
  Usi Stampa del browser e imposti i margini su "Nessuno" o "Minimi" per il risultato migliore.</p>
</div>
<ul class="griglia-cartellini">
{items}
</ul>
</body>
</html>
"""
    with open(f"{BASE}/docs/cartellino/cartellino.html", "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"OK — generato cartellino.html con {len(cartellini_data)} cartellini ({len(GAMES)} giochi + 1 Moonlight)")


if __name__ == "__main__":
    main()
