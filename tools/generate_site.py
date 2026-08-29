#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera i file statici del sito (index.html + una pagina per gioco in docs/g/<slug>/index.html)
a partire da docs/js/games-data.json.

Non è un build system a runtime: è un generatore lanciato a mano, una volta,
il cui output sono file HTML statici, vanilla, senza dipendenze — esattamente
come se fossero stati scritti a mano uno per uno. Va rilanciato solo se cambiano
i dati sorgente (tools/build_data.py).
"""
import html
import json

BASE = "/home/damiano/Progetti-Personali/giocainbiblioteca.github.io"

with open(f"{BASE}/docs/js/games-data.json", encoding="utf-8") as f:
    GAMES = json.load(f)

# Unico punto dove il conteggio dei giochi diventa un numero. Ovunque nel
# resto del file (meta description, footer) si legge N_GAMES, mai una cifra
# scritta a mano — la collezione cresce e un numero fisso mentirebbe in
# silenzio. I conteggi sulle porte erano già calcolati dai dati (_conta_porta).
N_GAMES = len(GAMES)

# Un solo catalogo (decisione Damiano 25/08 pomeriggio: "i giochi nel sito
# devono essere trattati tutti alla stessa maniera"). scheda_completa resta
# nel dato solo per sapere QUALI 48 ha donato Damiano (usato in poche frasi
# editoriali, mai per escludere qualcuno da griglia/porte/filtri) — porte e
# gruppi-livello leggono GAMES, il catalogo intero. Chi non ha una porta
# (tag editoriale, solo sui 48) semplicemente non compare in quella porta:
# non se ne inventa una. Chi non ha un livello (30/148, nessuno lo conosce
# ancora abbastanza) finisce nel gruppo "livello non assegnato ancora",
# invece di sparire dalla griglia — vedi build_giochi_section.
GAMES_COMPLETE = [g for g in GAMES if g.get("scheda_completa", True)]
N_GAMES_COMPLETI = len(GAMES_COMPLETE)

# Nomi decisi insieme alla biblioteca il 04/08. Le chiavi (1° elemento di ogni
# tupla) restano quelle di sempre — filtri, CSS, JS le usano ancora — cambia
# solo l'etichetta visibile (3° elemento). Stessa mappa duplicata in
# tools/build_data.py (LEVEL_LABEL), da cui nasce il livello_label per-gioco
# di games-data.json: le due liste vanno tenute a mano in sincronia.
LEGENDA = [
    ("al-volo", "●○○○", "Apri e gioca", "Si spiega in due minuti. Dopo la prima partita ci giocano anche i bambini da soli."),
    ("da-soli", "●●○○", "Leggi e gioca", "Una famiglia legge il regolamento in autonomia, lo capisce e parte."),
    ("con-guida", "●●●○", "Meglio farselo spiegare", "Meglio se qualcuno l'ha già provato e accompagna la prima partita."),
    ("da-serata", "●●●●", "Prenditi la serata", "Regolamento lungo e preparazione corposa. Si mette in conto la serata."),
]


def esc(s):
    return html.escape(s, quote=True)


def dots_markup(dots_str, livello_key):
    """4 pallini, ognuno esplicito on/off — leggibile anche senza colore."""
    spans = []
    for ch in dots_str:
        on = ch == "●"
        cls = "dot dot-on" if on else "dot"
        spans.append(f'<span class="{cls}" aria-hidden="true">{ch}</span>')
    return f'<span class="dots livello-{livello_key}">' + "".join(spans) + "</span>"


def livello_badge(g):
    return (
        f'<span class="livello-badge livello-{g["livello_key"]}">'
        f'{dots_markup(g["livello_dots"], g["livello_key"])} '
        f'<span class="etichetta-livello">{esc(g["livello_label"])}</span>'
        f"</span>"
    )


def stato_badge(g):
    """Pallino + etichetta di stato, stesso principio del badge di livello:
    mai solo colore, sempre testo leggibile accanto."""
    return (
        f'<span class="stato-badge stato-{g["stato_key"]}">'
        f'<span class="stato-pallino" aria-hidden="true"></span>'
        f'{esc(g["stato_label"])}'
        f"</span>"
    )


def stato_ribbon(g):
    """Etichetta di stato sovrapposta alla copertina — versione griglia
    (Direzione A, 26/08 sera, bozze/direzione-a-copertine.html v2): stesso
    dato di stato_badge, markup diverso (nastro sulla copertina invece di
    pillola nella riga meta). Uno dei quattro segnali che distinguono
    «in biblioteca» da «sta arrivando», mai da solo — vedi CSS
    .gioco-card[data-stato]."""
    return f'<span class="gioco-card-ribbon">{esc(g["stato_label"])}</span>'


HEAD = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="stylesheet" href="{css_path}css/fonts.css">
<link rel="stylesheet" href="{css_path}css/style.css">
</head>
<body{body_attrs}>
<a class="skip-link" href="#contenuto">Vai al contenuto</a>
<header class="sito-header">
  <div class="container">
    <a class="sito-header-link" href="{css_path}index.html">
      <svg class="dado-icona" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="4"/>
        <circle cx="8" cy="8" r="1.3" fill="currentColor" stroke="none"/>
        <circle cx="16" cy="8" r="1.3" fill="currentColor" stroke="none"/>
        <circle cx="12" cy="12" r="1.3" fill="currentColor" stroke="none"/>
        <circle cx="8" cy="16" r="1.3" fill="currentColor" stroke="none"/>
        <circle cx="16" cy="16" r="1.3" fill="currentColor" stroke="none"/>
      </svg>
      <h1>Gioca in Biblioteca</h1>
    </a>
    <p class="sito-header-riga2">
      <span class="sito-header-sub">Per scegliere un gioco fra quelli che trovi in biblioteca a Lecco</span>
    </p>
  </div>
</header>
"""
# Sottotitolo H2 (decisione Damiano 28/08): via la riga separata "Biblioteca
# civica di Lecco «Uberto Pozzoli»", il nome della biblioteca entra nella
# frase unica del sottotitolo. Riga condivisa da TUTTE le pagine (HEAD è un
# solo template): non solo la home, coerente su tutto il sito per costruzione.

FOOTER = """<footer class="sito-footer"></footer>
</body>
</html>
"""
# Nessun testo nel piede per ora (decisione Damiano 04/08, secondo giro Penna
# fermato: "sembra per vantarsi"). La chiusura visiva (linea tricolore, stessa
# del sotto-fascia dell'header) sostituisce il bordo+testo di prima in
# style.css .sito-footer — non un'introduzione a un vuoto. Struttura pronta a
# riaccogliere un <p> dentro <div class="container"> quando la frase ci sarà.

# ---------------------------------------------------------------------------
# INDEX
# ---------------------------------------------------------------------------

# Chiuso di default: la prima schermata deve mostrare che il catalogo è
# semplice, la spiegazione sta sotto per chi la cerca. Titolo dettato da
# Damiano il 04/08 (secondo giro), non riformulare.
INTRO_TESTO = """
<details class="intro">
  <summary>Come sono divisi questi giochi?</summary>
  <div class="intro-corpo">
    <h2>Perché qui non trovi «da 8 anni in su»</h2>
    <p>L'età stampata sulle scatole dice meno di quanto sembra: spesso dipende da quanto sono piccoli i pezzi, non da quanto è difficile il gioco. Un gioco semplicissimo può portare scritto <em>12+</em> solo perché ha componenti minuti — e chi legge quel numero pensa <em>"troppo complicato per noi"</em>, quasi sempre sbagliando.<br>
    Per questo qui trovi un'altra cosa: <strong>quanto aiuto serve per cominciare</strong>.</p>

    <h2>E i minuti?</h2>
    <p>Anche quelli sono un'indicazione larga. La prima partita dura sempre di più, e cambia a seconda di chi hai davanti: se qualcuno conosce già il gioco, se siete in due o in cinque. Un numero preciso darebbe una falsa sicurezza.</p>
  </div>
</details>
"""


LIVELLO_FRASE = {key: frase for key, _, _, frase in LEGENDA}

# ---------------------------------------------------------------------------
# PORTE (ingresso della home)
# ---------------------------------------------------------------------------
# La fascia bianca in HEAD porta già l'identità del sito (dado, titolo,
# biblioteca): niente insegna duplicata qui sotto. Fuori dalla fascia restano
# solo le due righe d'accoglienza, sopra la griglia dei pulsanti.

# (id, filtro, valore, etichetta corta, frase d'arrivo). etichetta/frase con
# {n} sostituito dal conteggio reale calcolato dai dati, mai un numero scritto
# a mano — se i dati cambiano, l'etichetta cambia con loro.
#
# Struttura H2 (Damiano+Penna, 27-28/08): le 4 porte a filtro "livello" sono
# le "grandi" (nomi presi verbatim da LEGENDA — sono la stessa scala, forma
# lunga vs forma corta, vedi giochi-biblioteca/home-porte-penna.md), "tutti"
# è la fascia a sé, le rimanenti sono le "piccole". Chi legge questa lista
# per generare le pagine (build_category_page) non ha bisogno di saperlo:
# quella distinzione la fa solo build_porte_html per la home. L'ordine qui
# sotto è anche l'ordine di lettura in home: scala crescente, fascia, piccole.
PORTE_DEF = [
    ("al-volo", "livello", "al-volo",
     "Apri e gioca",
     "giochi che si spiegano in due minuti: si comincia a giocare quasi subito."),
    ("da-soli", "livello", "da-soli",
     "Leggi e gioca",
     "giochi dove il regolamento si legge in famiglia, e basta quello."),
    ("con-guida", "livello", "con-guida",
     "Meglio farselo spiegare",
     "giochi che vanno meglio se al tavolo c'è qualcuno che ci ha già giocato."),
    ("da-serata", "livello", "da-serata",
     "Prenditi la serata",
     "giochi con regole vere da imparare: si mette in conto la serata."),
    ("tutti", None, None,
     "Fammi vedere tutto",
     None),
    ("solo", "giocatori", "solo",
     "Sono da solo",
     "giochi che funzionano anche senza nessuno accanto."),
    ("tanti", "giocatori", "5-99",
     "Siamo in tanti",
     "giochi che reggono un tavolo affollato, cinque persone o più."),
    ("senza-competere", "tag", "senza-competere",
     "Stiamo dalla stessa parte",
     "giochi dove si vince o si perde tutti insieme, mai uno contro l'altro."),
    ("belli", "tag", "bello-da-vedere",
     "Voglio farci una foto",
     "giochi che a fine partita si fotograferebbero, per come restano in tavola."),
]
# "In due, sul serio" rimossa (Erbottega, 27/08): 125/148 giochi si possono
# comunque giocare in due, il filtro non filtrava — vedi log in
# context/progetti-personali.md.

# Colore proprio di ciascuna delle 4 porte grandi (palette scelta da Damiano
# 28/08, dopo il giro sui candidati del giallo): smeraldo/blu/ciliegia/viola,
# scritte e segmenti sempre bianchi. Chiave = pid in PORTE_DEF, non il
# livello_key per restare esplicito anche se un domani una porta grande
# cambiasse filtro.
COLORE_PORTA_GRANDE = {
    "al-volo": "smeraldo",
    "da-soli": "blu",
    "con-guida": "ciliegia",
    "da-serata": "viola",
}


# Filtro "giocatori" letto sul catalogo intero: 1 solo gioco (Funky Gallo)
# non ha il dato (buco del catalogo della biblioteca, non nostro — vedi
# messaggio ad Alfred) e va escluso qui invece di far esplodere il
# confronto numerico su un giocatori_min/max che vale None.
def _con_giocatori(giochi):
    return [g for g in giochi if g["giocatori_min"] is not None]


def _conta_porta(filtro, valore):
    return len(_filtra_porta(filtro, valore))


def _filtra_porta(filtro, valore):
    """Legge sempre GAMES (il catalogo intero, 148): le porte a tag restano
    di fatto ancorate ai 48 perché solo loro hanno tags valorizzati — un
    gioco senza porta semplicemente non ci finisce, non lo forziamo."""
    if filtro is None:
        return list(GAMES)
    if filtro == "livello":
        return [g for g in GAMES if g["livello_key"] == valore]
    if filtro == "giocatori":
        candidati = _con_giocatori(GAMES)
        if valore == "solo":
            return [g for g in candidati if g["giocatori_min"] == 1]
        if valore == "due":
            return [g for g in candidati if g["giocatori_max"] == 2]
        lo, hi = (int(x) for x in valore.split("-"))
        return [g for g in candidati if g["giocatori_max"] >= lo and g["giocatori_min"] <= hi]
    if filtro == "tag":
        return [g for g in GAMES if valore in g["tags"]]
    raise ValueError(f"filtro porta sconosciuto: {filtro}")


LIVELLO_DOTS = {key: dots for key, dots, _, _ in LEGENDA}


def _vd_meter_html(dots_str):
    """4 segmenti, ognuno esplicito on/off (currentColor: sulle porte grandi
    diventano bianchi da soli, senza bisogno di una regola a parte) — stessa
    idea dei pallini di dots_markup, markup diverso perché qui vive dentro
    un pulsante a piena tinta invece che accanto a un titolo su sfondo
    chiaro. Validato in bozze/anteprima-home-h2.html."""
    segs = []
    for ch in dots_str:
        cls = "seg on" if ch == "●" else "seg"
        segs.append(f'<span class="{cls}"></span>')
    return f'<span class="vd-meter" aria-hidden="true">' + "".join(segs) + "</span>"


def build_porte_html():
    """Struttura H2 (Damiano+Penna, 27-28/08): 4 porte grandi (scala "quanto
    aiuto serve", una per livello) + una fascia larga a sé ("tutti", l'unica
    via per i 30 giochi senza livello) + 4 porte piccole ("per come giocate").
    Le grandi e le piccole restano link veri verso docs/c/<pid>/, come da
    04/08 — cambia solo il markup e i colori, non lo schema di indirizzi."""
    grandi = [p for p in PORTE_DEF if p[1] == "livello"]
    fascia = next(p for p in PORTE_DEF if p[0] == "tutti")
    piccole = [p for p in PORTE_DEF if p[1] != "livello" and p[0] != "tutti"]

    voci_grandi = []
    for pid, filtro, valore, etichetta, frase_tpl in grandi:
        n = _conta_porta(filtro, valore)
        colore = COLORE_PORTA_GRANDE[pid]
        dots = LIVELLO_DOTS[valore]
        voci_grandi.append(
            f'<li><a class="porta-grande-link porta-grande--{colore}" href="c/{pid}/index.html">'
            f'{_vd_meter_html(dots)}'
            f'<span class="pg-titolo">{esc(etichetta)}</span>'
            f'<span class="pg-numero">· {n}</span></a></li>'
        )
    grandi_html = f"""<section class="blocco-grandi" aria-label="Quanto aiuto ti serve per cominciare">
  <p class="blocco-titolo">Quanto aiuto ti serve per cominciare?</p>
  <p class="blocco-sottotitolo">Più segmenti pieni, più regole da imparare prima di partire.</p>
  <ul class="porte-grandi-griglia">
{chr(10).join(voci_grandi)}
  </ul>
</section>
"""

    pid_t, _, _, etichetta_t, _ = fascia
    n_t = _conta_porta(None, None)
    fascia_html = (
        f'<a class="fascia-tutti" href="c/{pid_t}/index.html">'
        f'<span class="fascia-tutti-titolo">{esc(etichetta_t)}</span>'
        f'<span class="fascia-tutti-numero">· {n_t}</span></a>\n'
    )

    voci_piccole = []
    for pid, filtro, valore, etichetta, frase_tpl in piccole:
        n = _conta_porta(filtro, valore)
        # Etichetta e numero dentro un unico span (non due figli diretti del
        # flex .porta-btn): con l'etichetta nuova più lunga ("Stiamo dalla
        # stessa parte") due flex-item separati si spaccavano a metà,
        # lasciando il numero a galleggiare da solo sulla riga sbagliata —
        # bug trovato a schermata vera, non a leggere il codice. Un solo
        # span avvolge tutto: va a capo come un unico blocco di testo.
        voci_piccole.append(
            f'<li><a class="porta-btn" href="c/{pid}/index.html">'
            f'<span class="porta-btn-testo">{esc(etichetta)} <span class="porta-numero">· {n}</span></span></a></li>'
        )
    piccole_html = f"""<section class="blocco-piccole" aria-label="Oppure cerca per occasione">
  <p class="blocco-sottotitolo">O cerca per come giocate:</p>
  <ul class="porte-piccole-griglia">
{chr(10).join(voci_piccole)}
  </ul>
</section>
"""

    return grandi_html + fascia_html + piccole_html


def build_accoglienza_html():
    """Struttura H2 (decisione Damiano 28/08): due paragrafi, sopra la
    griglia dei pulsanti, fuori dalla fascia bianca. Il primo (verbatim di
    Damiano, non riformulare) dice cos'è il catalogo; il secondo è
    l'istruzione già dettata il 04/08 (quarto giro), passata al «tu» lo
    stesso giorno sera (Penna, registro-tu-penna.md) — non riformulare
    nemmeno questo.

    La citazione finale pesca l'etichetta del pulsante 'al-volo' da
    PORTE_DEF: se quell'etichetta cambia, la citazione cambia con lei — mai
    una citazione scritta a mano che può marcire.
    """
    etichetta_al_volo = next(et for pid, _, _, et, _ in PORTE_DEF if pid == "al-volo")
    return f"""<section class="accoglienza" aria-label="Introduzione">
  <p class="corpo">Qui trovi i giochi da tavolo della biblioteca civica di Lecco. Alcuni sono già sullo scaffale, altri stanno arrivando.</p>
  <p class="istruzione">Non sai che gioco scegliere? I pulsanti qui sotto ti aiutano: cliccane uno. Se è la prima volta che giochi, clicca su «{esc(etichetta_al_volo)}».</p>
</section>
"""


def build_livello_group(key, dots, label, frase, giochi_del_livello, card_path):
    """Un blocco per livello: intestazione (pallini+nome) + frase della legenda
    spiegata lì dove serve, poi solo i giochi di quel livello. Se il gruppo
    non ha giochi visibili dopo un filtro, il JS nasconde l'intera <section>,
    intestazione compresa — mai un blocco vuoto in pagina."""
    cards = "\n".join(build_card(g, card_path) for g in giochi_del_livello)
    return f"""<section class="livello-gruppo" data-livello-gruppo="{key}">
  <div class="livello-gruppo-intestazione">
    {dots_markup(dots, key)}
    <h2 class="livello-gruppo-titolo">{esc(label)}</h2>
  </div>
  <p class="livello-gruppo-frase">{esc(frase)}</p>
  <ul class="griglia-giochi">
{cards}
  </ul>
</section>"""


def build_filtri_html(mostra_livello=True):
    """Barra compatta, non due riquadri grandi: deve leggersi a colpo
    d'occhio come 'sono filtri', non come una sezione di contenuto.
    mostra_livello=False sulle pagine-porta che SONO già un livello
    (al-volo, da-serata): lì il filtro per livello non ha senso, resta
    solo quello dei giocatori."""
    gruppi = []

    if mostra_livello:
        livello_btns = ['<button type="button" class="filtro-btn" data-filtro-livello="tutti" aria-pressed="true">Tutti</button>']
        for key, dots, label, _ in LEGENDA:
            livello_btns.append(
                f'<button type="button" class="filtro-btn" data-filtro-livello="{key}" aria-pressed="false">{dots} {esc(label)}</button>'
            )
        gruppi.append(
            f'<div class="filtri-gruppo" role="group" aria-label="Livello">'
            f'<span class="filtri-etichetta">Livello</span>'
            f'<div class="filtri-opzioni">{"".join(livello_btns)}</div></div>'
        )

    giocatori_ranges = [("tutti", "Tutti"), ("1-2", "1–2"), ("3-4", "3–4"), ("5-99", "5 o più")]
    giocatori_btns = []
    for key, label in giocatori_ranges:
        pressed = "true" if key == "tutti" else "false"
        giocatori_btns.append(
            f'<button type="button" class="filtro-btn" data-filtro-giocatori="{key}" aria-pressed="{pressed}">{esc(label)}</button>'
        )
    gruppi.append(
        f'<div class="filtri-gruppo" role="group" aria-label="Numero di giocatori">'
        f'<span class="filtri-etichetta">Numero di giocatori</span>'
        f'<div class="filtri-opzioni">{"".join(giocatori_btns)}</div></div>'
    )

    return f"""
<div class="filtri" aria-label="Filtra i giochi">
  {''.join(gruppi)}
  <button type="button" class="filtro-reset" id="filtro-reset">Azzera i filtri</button>
</div>
<p class="contatore-risultati" id="contatore-risultati" role="status" aria-live="polite"></p>
"""


def build_card_copertina_html(g):
    """Cella fissa con la copertina intera dentro (Direzione A, 26/08 sera):
    la scatola ha già il titolo stampato sopra, object-fit:contain non la
    ritaglia mai — l'altezza della cella è fissa in CSS, uguale per tutte,
    non segue l'aspect-ratio dell'immagine (33/148 non sono quadrate).
    Il nastro di stato sta sovrapposto alla copertina, non più nella riga
    meta sotto. Segnaposto discreto per copertine assenti: non più un caso
    vivo (148/148 coperte dal 26/08), resta come rete di sicurezza."""
    ribbon_html = stato_ribbon(g)
    if g.get("copertina"):
        return (
            f'<span class="gioco-card-copertina">'
            f'<img src="{{card_path}}{esc(g["copertina"])}" alt="" loading="lazy">'
            f'{ribbon_html}'
            f'</span>'
        )
    return (
        f'<span class="gioco-card-copertina gioco-card-copertina--assente">'
        f'{ribbon_html}'
        f'</span>'
    )


def build_card(g, card_path="../../"):
    """card_path è il prefisso relativo dal file che contiene la card fino
    alla radice del sito — stesso principio di css_path in HEAD, perché la
    stessa card_wrap va incollata a profondità diverse. Oggi le card vivono
    solo dentro docs/c/<pid>/index.html (profondità 2, prefisso "../../"),
    ma il parametro resta esplicito e non implicito per non ripetere il bug
    del link fisso "g/..." che presumeva la home come unico chiamante.

    Direzione A (26/08 sera, bozze/direzione-a-copertine.html v2): la
    copertina è protagonista, cella fissa uguale per tutte. La descrizione
    è uscita dalla griglia — si legge nella scheda, dov'era già. Le
    etichette (vocabolario di Penna) NON entrano in griglia (Damiano,
    26/08). Restano in meta-riga solo i pallini di livello e il numero di
    giocatori; lo stato passa dal badge alla copertina (vedi
    build_card_copertina_html/stato_ribbon). Nessun campo assente mostra
    un vuoto o un "non disponibile"."""
    tags_attr = ",".join(g.get("tags", []))
    copertina_html = build_card_copertina_html(g).replace("{card_path}", esc(card_path))
    giocatori_html = f'<span class="gioco-card-giocatori">{esc(g["giocatori"])} giocatori</span>' if g.get("giocatori") else ""
    dots_html = dots_markup(g["livello_dots"], g["livello_key"]) if g.get("livello_key") else ""
    # giocatori_min/max possono essere None (1 gioco su 148, Funky Gallo:
    # buco nel catalogo della biblioteca) — "" nell'attributo, mai "None"
    # scritto in chiaro nell'HTML.
    gmin_attr = g["giocatori_min"] if g["giocatori_min"] is not None else ""
    gmax_attr = g["giocatori_max"] if g["giocatori_max"] is not None else ""
    return f"""<li class="gioco-card-wrap" data-slug="{esc(g['slug'])}" data-livello="{g['livello_key']}" data-giocatori-min="{gmin_attr}" data-giocatori-max="{gmax_attr}" data-tags="{esc(tags_attr)}">
  <a class="gioco-card" data-stato="{g['stato_key']}" href="{card_path}g/{g['slug']}/index.html">
    {copertina_html}
    <div class="gioco-card-corpo">
      <h3>{esc(g['titolo'])}</h3>
      <div class="meta-riga">
        {dots_html}
        {giocatori_html}
      </div>
    </div>
  </a>
</li>"""


# 148 giochi, un solo catalogo (25/08): "48 donati" resta vero (sono
# davvero i 48 di Damiano), il resto della frase parlava di TUTTO il
# catalogo come se fosse solo quei 48 — corretto qui, non riscritto:
# stesso impianto, numero e soggetto giusti.
INDEX_DESCRIPTION = (
    f"{N_GAMES} giochi da tavolo del catalogo della biblioteca di Lecco, {N_GAMES_COMPLETI} donati da Damiano, "
    "con una scheda per ciascuno: quanto aiuto serve per cominciare, quanti giocatori, quanto dura."
)


def generate_index():
    """La home è solo l'ingresso: identità, accoglienza, le otto porte,
    il richiudibile 'come sono divisi'. Niente elenco, niente filtri —
    quelli vivono ora nelle pagine di ogni porta (build_category_page)."""
    body = (
        HEAD.format(
            title="Gioca in Biblioteca",
            description=INDEX_DESCRIPTION,
            css_path="",
            body_attrs="",
        )
        + f'<main id="contenuto"><div class="container">'
        + build_accoglienza_html()
        + build_porte_html()
        + INTRO_TESTO
        + "</div></main>"
        + FOOTER
    )
    with open(f"{BASE}/docs/index.html", "w", encoding="utf-8") as f:
        f.write(body)


# ---------------------------------------------------------------------------
# PAGINA DI OGNI PORTA (docs/c/<pid>/index.html)
# ---------------------------------------------------------------------------
# Otto pagine, una per porta: i giochi di quella porta raggruppati per
# livello (come in home ieri), la frase d'arrivo già scritta in PORTE_DEF,
# il filtro dei giocatori (+ livello dove ha senso), una via di ritorno.
# Il filtro per livello sparisce sulle due porte che SONO già un livello
# (al-volo, da-serata: filtro == "livello") — mostrarlo lì sarebbe un filtro
# che filtra dentro un insieme già ristretto a un solo valore possibile.

def build_senza_livello_group(giochi, card_path):
    """Gruppo per chi non ha un livello assegnato (30/148, dal 25/08:
    nessuno li conosce ancora abbastanza per dirlo). data-livello-gruppo=""
    per restare agganciato allo stesso data-livello="" che le card già
    portano — filtri.js non ha bisogno di sapere che questo gruppo esiste,
    lo tratta come uno qualunque."""
    cards = "\n".join(build_card(g, card_path) for g in giochi)
    return f"""<section class="livello-gruppo" data-livello-gruppo="">
  <div class="livello-gruppo-intestazione">
    <h2 class="livello-gruppo-titolo">Livello non assegnato ancora</h2>
  </div>
  <p class="livello-gruppo-frase">Nessuno li ha ancora provati abbastanza per dire quanto aiuto serve.</p>
  <ul class="griglia-giochi">
{cards}
  </ul>
</section>"""


def build_giochi_section(subset, raggruppa_per_livello, card_path="../../"):
    """Con più livelli nel sottoinsieme, raggruppa come in home (intestazione
    + frase per livello, gruppi vuoti mai generati). Chi nel sottoinsieme
    non ha un livello finisce in un gruppo a parte (mai perso dalla
    griglia solo perché manca un campo — vedi build_senza_livello_group).
    Sulle porte-livello il sottoinsieme è già un solo livello: niente
    intestazione ripetuta, solo la griglia. card_path: vedi build_card —
    qui chiamato solo dalle pagine porta (docs/c/<pid>/), profondità 2."""
    if raggruppa_per_livello:
        gruppi = []
        for key, dots, label, frase in LEGENDA:
            giochi_del_livello = [g for g in subset if g["livello_key"] == key]
            if giochi_del_livello:
                gruppi.append(build_livello_group(key, dots, label, frase, giochi_del_livello, card_path))
        senza_livello = [g for g in subset if not g["livello_key"]]
        if senza_livello:
            gruppi.append(build_senza_livello_group(senza_livello, card_path))
        return '<div id="elenco-giochi">\n' + "\n".join(gruppi) + "\n</div>"
    cards = "\n".join(build_card(g, card_path) for g in subset)
    return f'<div id="elenco-giochi">\n<ul class="griglia-giochi">\n{cards}\n</ul>\n</div>'


def build_category_page(porta):
    pid, filtro, valore, etichetta, frase_tpl = porta
    subset = _filtra_porta(filtro, valore)
    n = len(subset)
    mostra_livello = filtro != "livello"

    if frase_tpl:
        frase = f"{n} {frase_tpl}"
        intro_html = f'<p class="categoria-intro">{esc(frase)}</p>\n'
        description = esc(frase[0].upper() + frase[1:])
    else:
        # Solo "tutti": nessuna frase d'arrivo in PORTE_DEF (frase_tpl=None),
        # non ne invento una — vedi build_accoglienza_html per lo stesso
        # criterio applicato altrove in questo file.
        intro_html = ""
        description = INDEX_DESCRIPTION

    body = (
        HEAD.format(
            title=f"{esc(etichetta)} — Gioca in Biblioteca",
            description=description,
            css_path="../../",
            # Tinta di pagina (29/08/2026): il colore della propria porta
            # su titolo/filtri/link, vedi body[data-porta] in style.css —
            # unico punto che scrive questo attributo, pid = data-porta.
            body_attrs=f' data-porta="{pid}"',
        )
        + f"""<main id="contenuto"><div class="container">
  <p class="breadcrumb"><a href="../../index.html">&larr; Torna al catalogo</a></p>
  <header class="categoria-intestazione">
    <h2 class="categoria-titolo">{esc(etichetta)}</h2>
{intro_html}  </header>
"""
        + build_filtri_html(mostra_livello=mostra_livello)
        + build_giochi_section(subset, raggruppa_per_livello=mostra_livello)
        + "</div></main>"
        + FOOTER
        + '<script src="../../js/filtri.js"></script>\n'
    )
    import os
    outdir = f"{BASE}/docs/c/{pid}"
    os.makedirs(outdir, exist_ok=True)
    with open(f"{outdir}/index.html", "w", encoding="utf-8") as f:
        f.write(body)


# ---------------------------------------------------------------------------
# SCHEDA GIOCO
# ---------------------------------------------------------------------------

def build_due_scatole_html(g):
    """Nota 'due scatole distinte' — solo su Spirit of the Forest. Affianca la
    descrizione, non la sostituisce (vincolo: non toccare le descrizioni)."""
    nota = g.get("nota_due_scatole", "")
    if not nota:
        return ""
    return f"""    <div class="scheda-due-scatole">
      <p><strong>Attenzione:</strong> {esc(nota)}</p>
    </div>
"""


def build_link_catalogo_html(g):
    if not g.get("link_catalogo"):
        return ""
    return f'    <p class="scheda-link-catalogo"><a href="{esc(g["link_catalogo"])}">Vedi la scheda nel catalogo della biblioteca &rarr;</a></p>\n'


# Modello di scheda approvato da Damiano il 25/08 (schede-campione.html,
# scheda di Bloom Town), applicato qui a tutti i 148 giochi — non più due
# template separati per le due popolazioni. Un solo generatore, campi
# assenti che semplicemente non generano il loro blocco (vincolo: nessun
# "non disponibile", nessun trattino, nessun div vuoto).
#
# I due stati (in biblioteca / sta arrivando) si distinguono su quattro
# segnali insieme (mai su uno solo): classe sull'<article> (bordo pieno vs
# tratteggiato, sfondo), l'etichetta colorata, l'opacità della copertina
# (in CSS) e la frase di stato qui sotto.
NOTA_STATO = {
    "in-biblioteca": "Puoi venire a giocarci in biblioteca.",
    "in-arrivo": "La biblioteca lo sta catalogando. Fra poco sarà sullo scaffale.",
}


def build_copertina_html(g, path_prefix):
    """Dal 26/08/2026 le copertine sono 148 su 148 (le ultime sei mandate
    da Stefano della biblioteca): questo ramo non scatta piu'. Resta come
    rete di sicurezza per un gioco nuovo senza copertina — niente
    placeholder grigio, il corpo della scheda occupa tutta la larghezza,
    vedi .scheda-layout in style.css.
    Fino al 25/08 il commento qui diceva "assente per 6/148": era vero
    quando fu scritto, ed e' rimasto falso senza che nulla fallisse."""
    if not g.get("copertina"):
        return ""
    return (
        f'  <div class="scheda-copertina">'
        f'<img src="{path_prefix}{esc(g["copertina"])}" alt="" loading="lazy"></div>\n'
    )


def build_dati_riga_html(g):
    """Giocatori e minuti, mai l'età (dice la stessa cosa del livello, ma
    peggio — decisione Damiano 25/08). Ogni valore assente non genera la
    sua voce, mai un segnaposto."""
    voci = []
    if g.get("giocatori"):
        voci.append(f'<li><b>{esc(g["giocatori"])}</b><span>giocatori</span></li>')
    if g.get("durata"):
        voci.append(f'<li><b>{esc(g["durata"])}</b><span>minuti</span></li>')
    if not voci:
        return ""
    return f'    <ul class="scheda-dati">{"".join(voci)}</ul>\n'


def build_livello_scheda_html(g):
    """Pallini + nome del livello + frase esplicativa, insieme — solo per
    i giochi che hanno un livello (119/148: i 48 di Damiano + i 70 che
    conosce fra i giochi della biblioteca). Nessun livello dedotto per i
    restanti 29: quella scelta non si inventa."""
    if not g.get("livello_key"):
        return ""
    return f"""    <div class="scheda-livello">
      {dots_markup(g['livello_dots'], g['livello_key'])}
      <b class="scheda-livello-nome">{esc(g['livello_label'])}</b>
      <p class="scheda-livello-frase">{esc(LIVELLO_FRASE[g['livello_key']])}</p>
    </div>
"""


def build_descrizione_html(g):
    """La descrizione vera (di Penna) quando c'è — solo sui 48 di Damiano
    per ora. Altrimenti la riga discreta in corsivo: non un vuoto che
    sembra un guasto, un'informazione ('non è ancora pronta')."""
    if g.get("descrizione"):
        return f'    <p class="scheda-descrizione">{esc(g["descrizione"])}</p>\n'
    return '    <p class="scheda-descrizione scheda-descrizione--mancante">La descrizione di questo gioco non è ancora pronta.</p>\n'


def build_dettagli_tecnici_html(g):
    """Tipologia (solo i 48, unica popolazione che la ha) e componenti
    (tutti e 148, dal CSV di Damiano o dal catalogo della biblioteca).
    Se mancano entrambi il <details> intero non esiste — mai un
    richiudibile vuoto da aprire per scoprire che non c'è niente dentro."""
    righe = []
    if g.get("tipologia_tecnico"):
        righe.append(f'      <h3>Tipologia</h3>\n      <p class="tipologia-tecnica">{esc(g["tipologia_tecnico"])}</p>\n')
    if g.get("componenti"):
        righe.append(f'      <h3>Cosa c\'è nella scatola</h3>\n      <p class="componenti">{esc(g["componenti"])}</p>\n')
    if not righe:
        return ""
    return f"""    <details class="dettagli-tecnici">
      <summary>Per chi vuole saperne di più</summary>
{"".join(righe)}    </details>

"""


def generate_game_page(g):
    """Titolo dettato dalla struttura approvata (schede-campione.html):
    copertina, etichetta di stato, titolo, riga dati, frase di stato,
    livello, descrizione, «per chi vuole saperne di più», link al
    catalogo — in quest'ordine, sempre, con o senza scheda editoriale."""
    stato_key = g["stato_key"]
    classe_stato = "scheda-gioco--qui" if stato_key == "in-biblioteca" else "scheda-gioco--arrivo"

    # Descrizione della pagina (SEO): la descrizione di Penna se c'è, altrimenti
    # una frase minima di cornice — mai l'abstract del catalogo (decisione
    # Damiano 25/08: quel testo non compare in pagina, in nessuna forma).
    description = g["descrizione"] if g.get("descrizione") else f"{g['titolo']}: {g['stato_label'].lower()} nel catalogo della biblioteca."

    body = (
        HEAD.format(
            title=f"{esc(g['titolo'])} — Gioca in Biblioteca",
            description=esc(description),
            css_path="../../",
            body_attrs="",
        )
        + f"""<main id="contenuto"><div class="container">
  <p class="breadcrumb"><a href="../../index.html">&larr; Torna al catalogo</a></p>
  <article class="scheda-gioco {classe_stato}">
{build_copertina_html(g, "../../")}  <div class="scheda-corpo">
    {stato_badge(g)}
    <h2 class="scheda-titolo">{esc(g['titolo'])}</h2>
{build_dati_riga_html(g)}    <p class="scheda-nota-stato scheda-nota-stato--{stato_key}">{esc(NOTA_STATO[stato_key])}</p>
{build_livello_scheda_html(g)}{build_descrizione_html(g)}{build_due_scatole_html(g)}"""
        + (f"""    <div class="tipologia-chiaro">
      <p>{esc(g['tipologia_chiaro'])}</p>
    </div>

""" if g.get("tipologia_chiaro") else "")
        + build_dettagli_tecnici_html(g)
        + build_link_catalogo_html(g)
        + f"""    <a class="link-torna" href="../../index.html">&larr; Torna al catalogo</a>
  </div>
  </article>
</div></main>"""
        + FOOTER
    )
    import os
    outdir = f"{BASE}/docs/g/{g['slug']}"
    os.makedirs(outdir, exist_ok=True)
    with open(f"{outdir}/index.html", "w", encoding="utf-8") as f:
        f.write(body)


def main():
    generate_index()
    for g in GAMES:
        generate_game_page(g)
    for porta in PORTE_DEF:
        build_category_page(porta)
    # docs/novita/ non esiste più (25/08): un solo catalogo, niente pagina
    # a parte per i giochi della biblioteca — se un vecchio output resta
    # su disco da una build precedente, lo si toglie a mano una volta sola.
    print(
        f"OK — generati index.html + {len(GAMES)} schede in docs/g/<slug>/index.html "
        f"({N_GAMES_COMPLETI} donati da Damiano, {N_GAMES - N_GAMES_COMPLETI} dal catalogo della biblioteca) "
        f"+ {len(PORTE_DEF)} pagine porta in docs/c/<pid>/index.html"
    )


if __name__ == "__main__":
    main()
