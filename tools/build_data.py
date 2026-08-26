#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consolida le fonti (giochi-originale.csv, revisione-livelli-DAMIANO.csv,
descrizioni-proposte.md/v2, biblioteca-nuovi.csv) in un unico
games-data.json, applicando le correzioni esplicite di Damiano
(Zefiro->Zefiria, tipologie sbagliate di Once Upon a Castle e Spirit of
the Forest).

Due popolazioni di giochi, stesso file di output, schema condiviso:
- i 48 di Damiano (giochi-originale.csv) — scheda_completa=True, passano
  per tutte le guardie di editoriale/livello/componenti qui sotto;
- i giochi della biblioteca (biblioteca-nuovi.csv) — scheda_completa=False,
  niente descrizione/livello/componenti (non inventati: li scriverà Penna),
  solo titolo/stato/collegamento al catalogo online.
Cambiare lo STATO di un gioco (in arrivo <-> in biblioteca) è una parola
sola in una cella di uno dei due CSV, poi si rilancia questo script +
generate_site.py — mai altro.

Non è un build system del sito: è uno script di preparazione dati, lanciato
a mano una volta. L'output (games-data.json + games-data.js) è statico e viene
committato/servito come file vanilla, senza dipendenze a runtime.
"""
import csv
import html
import json
import os
import re
import shutil
import unicodedata

BASE = "/home/damiano/Progetti-Personali/giocainbiblioteca.github.io"

# Unico punto di verità per il collegamento al catalogo online della
# biblioteca — se il dominio o lo schema URL cambiano, si tocca questa
# riga sola, mai le 148 righe di dati.
LINK_CATALOGO_TEMPLATE = "https://lecco.biblioteche.it/opac/detail/view/lc:catalog:{record_id}"

STATO_LABEL = {
    # "Sta arrivando" preferita da Damiano a "In arrivo" (25/08 pomeriggio),
    # da usare ovunque sul sito: la chiave sorgente resta "in arrivo" nei
    # CSV (non si tocca la fonte), cambia solo l'etichetta che il lettore
    # vede — stessa logica di LEVEL_LABEL qui sotto.
    "in arrivo": "Sta arrivando",
    "in biblioteca": "In biblioteca",
}
STATO_KEY = {
    "in arrivo": "in-arrivo",
    "in biblioteca": "in-biblioteca",
}


def stato_fields(stato_raw, record_id="", ean=""):
    stato_raw = stato_raw.strip().lower()
    if stato_raw not in STATO_LABEL:
        raise SystemExit(f"ATTENZIONE: stato '{stato_raw}' non riconosciuto (atteso 'in arrivo' o 'in biblioteca') — fermo qui.")
    link = LINK_CATALOGO_TEMPLATE.format(record_id=record_id) if record_id else ""
    return {
        "stato_key": STATO_KEY[stato_raw],
        "stato_label": STATO_LABEL[stato_raw],
        "record_id": record_id,
        "ean": ean,
        "link_catalogo": link,
    }


# ---------- 1. Leggi la fonte grezza (giochi-originale.csv) ----------
with open(f"{BASE}/giochi-originale.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))

header = rows[0]
data_rows = [r for r in rows[1:49]]  # 48 giochi (righe 1..48)

# ---------- 2. Leggi i livelli definitivi (revisione-livelli-DAMIANO.csv) ----------
with open(f"{BASE}/revisione-livelli-DAMIANO.csv", newline="", encoding="utf-8-sig") as f:
    lv_rows = list(csv.reader(f))[1:]


def norm_title(t):
    t = re.sub(r"\s*\(.*?\)", "", t)  # rimuove parentesi es. "(Meeple Land)"
    return t.strip()


levels = {}
for r in lv_rows:
    title = norm_title(r[0])
    level_raw = r[2].strip().rstrip("*")  # CocoRido ha un asterisco, tolto
    levels[title] = level_raw

LEVEL_KEY = {
    "AL VOLO": "al-volo",
    "DA SOLI": "da-soli",
    "CON UNA GUIDA": "con-guida",
    "DA SERATA": "da-serata",
}

# Nomi visibili dei quattro livelli (decisione presa insieme alla biblioteca, 04/08).
# Le chiavi (LEVEL_KEY, sopra) restano quelle di sempre — filtri, CSS, JS le
# usano ancora — qui cambia solo l'etichetta che il lettore vede. games-data.json
# (livello_label) nasce da questa mappa, non più dal testo grezzo del CSV.
# Stessa mappa duplicata in tools/generate_site.py (LEGENDA), per l'intestazione
# di gruppo e i pulsanti filtro: le due liste vanno tenute a mano in sincronia
# finché non c'è un unico punto di verità condiviso tra i due script.
LEVEL_LABEL = {
    "al-volo": "Apri e gioca",
    "da-soli": "Leggi e gioca",
    "con-guida": "Meglio farselo spiegare",
    "da-serata": "Prenditi la serata",
}


def level_key(level_str):
    for label, key in LEVEL_KEY.items():
        if label in level_str:
            return key
    raise ValueError(f"livello non riconosciuto: {level_str}")


def level_dots(level_str):
    return level_str.split(" ")[0]


def level_label(level_str):
    return LEVEL_LABEL[level_key(level_str)]


# ---------- 3. Editoriale: IN CHIARO / TECNICO (da descrizioni-proposte.md, versione finale Parte 4) ----------
# tecnico = None significa "usa la TIPOLOGIA della riga CSV originale, invariata"
EDITORIALE = {
    "Bloom Town": ("Si scelgono tessere da un gruppo comune, come lo scambio di figurine, e si piazzano per costruire pezzo dopo pezzo la propria città.", None),
    "Meepleland": ("Si piazzano attrazioni sulla propria mappa e si tengono i conti dei soldi, un po' come costruire il proprio piccolo luna park.", None),
    "Tang Garden": ("Si compone un giardino piazzando tessere e si fanno gruppi di decorazioni uguali, come una raccolta di figurine; più le zone create sono grandi, più valgono.", None),
    "Hippocrates": ("Si mandano i propri dottori a occupare i posti disponibili prima degli altri — come essere i primi della fila — gestendo le scorte dell'ospedale.", None),
    "Rune Stones": ("Si scelgono carte da un gruppo comune e si costruisce nel tempo una combinazione che produce sempre più risorse, come una catena di montaggio che cresce.", None),
    "Visconti del Regno Occidentale": ("Si mandano i propri aiutanti a occupare i posti disponibili prima degli altri — come essere i primi della fila — allargando la propria influenza sulla mappa.", None),
    "Dungeonology": ("Si esplora un dungeon muovendosi sulla mappa e gestendo le carte in mano, come una piccola spedizione da studiosi.", None),
    "New York Zoo": ("Si incastrano pezzi di forme diverse, come nel Tetris, scegliendoli a turno da un gruppo comune.", None),
    "The Hunger": ("Si scelgono carte da un gruppo comune e si decide, turno dopo turno, se continuare a rischiare o fermarsi e tenere quello che si ha.", None),
    "Woodcraft": ("Si aggiustano i dadi lanciati per ottenere il risultato che serve, e si mandano i propri artigiani a occupare i posti disponibili prima degli altri — come essere i primi della fila.", None),
    "Sock Monsters": ("Un gioco di memoria, come il classico Memory, dove ci si muove su una griglia di stanze.", None),
    "Railroad Ink Rosso": ("Si lanciano i dadi e ognuno disegna sul proprio foglio, cercando di collegare le strade come quando si uniscono i puntini.", None),
    "Railroad Ink Blu": ("Si lanciano i dadi e ognuno disegna sul proprio foglio, cercando di collegare le strade come quando si uniscono i puntini.", None),
    "Lo Scatto Perfetto": ("Si piazzano carte per fotografare animali e si raccolgono le foto per tipo, come una raccolta di figurine.", None),
    "MindUp!": ("Tutti giocano una carta nello stesso momento, non a turni, come nella morra cinese (sasso-carta-forbici) — o come le mini-sfide simultanee di certi party game ai videogiochi (tipo Mario Party).", None),
    "Hats": ("Si scambiano carte con gli altri per completare la propria collezione di cappelli, come una raccolta di figurine.", None),
    "Sobek 2 giocatori": ("Si scelgono tessere di merce dal mercato comune per fare le collezioni più ricche, come una raccolta di figurine.", None),
    "Gasha": ("Si può continuare a rischiare per un premio migliore, o fermarsi e tenere quello che si ha già, come con gli ovetti a sorpresa: non sai mai cosa esce finché non lo apri — lo stesso brivido delle loot box nei videogiochi, che di questi distributori sono in realtà le eredi dirette.", None),
    "Corinth": ("Si scelgono dadi da un gruppo comune per costruire rotte commerciali, come quando si uniscono i puntini su una mappa.", None),
    "Orbis": ("Si scelgono e si piazzano tessere di territorio, come lo scambio di figurine, gestendo i propri seguaci come una piccola scorta da amministrare.", None),
    "Conspiracy": ("Si gestiscono le carte in mano e si finge di avere alleanze che non si hanno, come quando si bluffa giocando a carte.", None),
    "Yokai": ("Si gioca tutti insieme per vincere o perdere insieme, ma senza poter parlare: ci si deve capire con gli sguardi, come nel mimo.", None),
    "Wild Space": ("Si scelgono carte da un gruppo comune per costruire, turno dopo turno, un equipaggio sempre più forte, come una catena di montaggio che cresce.", None),
    "Zefiro": ("Si collabora per rimettere in ordine le isole numerate prima che il tempo scada, un po' come riordinare in fila le carte di un mazzo numerato che qualcuno ha mischiato.", "Cooperativo · Puzzle logico · Contro il tempo"),
    "Pandemic Reazione Rapida": ("Si gioca tutti insieme contro il gioco, con la clessidra che corre, un po' come nel gioco di carta e penna 'Città, Fiumi, Monti' quando il tempo sta per scadere.", None),
    "CocoRido All'Arrembaggio": ("Un gioco da fare in gruppo per ridere insieme, dove si gioca una carta tutti nello stesso momento.", None),
    "Spirit of the Forest": ("Si scelgono tessere spirito da un gruppo comune per fare le collezioni più ricche, come una raccolta di figurine.", "Piazzamento tessere · Punteggio di area · Competitivo (con modulo cooperativo Moonlight incluso nella scatola)"),
    "Draftosaurus": ("Si sceglie a turno un dinosauro da un sacchetto comune e lo si piazza nel proprio zoo.", None),
    "Welcome to New Las Vegas": ("Si girano carte al posto di lanciare i dadi, e ognuno segna sul proprio foglio quello che gli serve — un po' come alla Tombola, ma con le carte al posto dei numeri estratti.", None),
    "Villagers": ("Si scelgono carte da un gruppo comune e si costruisce davanti a sé una fila di paesani che si aiutano a vicenda, come una catena di montaggio che cresce.", None),
    "21 Giochi Minuti": ("Una scatola con 21 piccoli giochi diversi, ognuno spiegabile e giocabile in circa un minuto.", None),
    "Once Upon a Castle": ("Si lanciano i dadi e si disegna il proprio castello sul foglio, ognuno per sé: gara a chi lo fa più bello.", "Tiro di dadi · Disegno su foglio (roll-and-write) · Competitivo"),
    "NobiNobi GDR Spada": ("Si inventa una storia insieme, come quando da bambini si giocava a \"facciamo finta che\", aiutandosi con carte e dadi.", None),
    "NobiNobi GDR Magia": ("Si inventa una storia insieme, come quando da bambini si giocava a \"facciamo finta che\", aiutandosi con carte e dadi.", None),
    "Machi Koro": ("Si lanciano i dadi e si comprano edifici che fanno guadagnare soldi ogni turno, un po' come in Monopoli — solo che qui ognuno costruisce la propria città per conto suo, senza girare sul tabellone.", None),
    "Florenza Dice Game": ("Si lanciano i dadi e si decide dove piazzare ciascuno, un po' come nello Yahtzee, ma per costruire palazzi e commissionare opere d'arte invece di fare punteggio.", None),
    "Azul Summer Pavillion": ("Si scelgono tessere colorate da vassoi comuni e si compone un disegno geometrico sul proprio pannello, come un mosaico.", None),
    "Oddville": ("Si scelgono carte da un gruppo comune per costruire, edificio dopo edificio, una città bizzarra.", None),
    "Era Il Medioevo": ("Si lanciano i dadi per ottenere materiali e si costruisce fisicamente il proprio villaggio con pezzi tridimensionali, come con i mattoncini.", None),
    "Santiago De Cuba": ("Si muove una pedina su una ruota di azioni per commerciare merci e costruire rotte, come le lancette di un orologio che indicano cosa si può fare in quel momento.", None),
    "Aquatica": ("Si gestiscono carte e risorse sottomarine per fare le collezioni più ricche, come una raccolta di figurine.", None),
    "Meeples and Monsters": ("Si esplora un dungeon mandando i propri eroi a occupare i posti disponibili prima degli altri — come essere i primi della fila — e si combatte contro i mostri.", None),
    "Watergate": ("Un duello di carte in cui i due giocatori hanno ruoli e regole diverse tra loro, come nel gioco del gatto e del topo — o come nei videogiochi multigiocatore asimmetrici, dove uno caccia e gli altri si nascondono — per collegare o rompere una rete di prove.", None),
    "Zombie Kidz Evolution": ("Si gioca tutti insieme contro gli zombie, e il gioco stesso cambia e si trasforma partita dopo partita, come un album di figurine che si riempie col tempo — o, per chi preferisce, come un videogioco che salva i progressi e sblocca cose nuove a ogni partita.", "Cooperativo · Legacy · Tiro di dadi"),
    "Champions!": ("Un gioco da fare in gruppo dove si vota chi vincerà ogni sfida, un po' come un piccolo torneo a indovinare, stile Indovina Chi — o come votare il proprio preferito in un talent show.", "Party · Votazione · Deduzione"),
    "Momiji": ("Si gestiscono le carte in mano e se ne scelgono altre da un gruppo comune, per fare le collezioni di foglie più ricche, come una raccolta di figurine.", "Gestione mano · Drafting · Raccolta set"),
    "Kingdomino": ("Si scelgono tessere a domino da un gruppo comune e si compone, pezzo dopo pezzo, il proprio regno.", "Drafting di tessere · Piazzamento · Costruzione regno"),
    "Snow Time": ("Tutti scelgono la propria mossa nello stesso momento, senza sapere cosa faranno gli altri, un po' come alla morra cinese — o come le mini-sfide simultanee di party game da console (tipo Mario Party).", "Azione simultanea · Bluff · Dadi"),
}

# Guardia sugli override di tipologia tecnica — CAUSA RADICE del bug MindUp!
# (04/08, segnalato da Damiano): 'MindUp!' aveva un tecnico_override col testo
# IDENTICO, carattere per carattere, a quello di 'Zombie Kidz Evolution' più
# sotto in questo stesso dizionario — un refuso di trascrizione, non una
# decisione. Il dizionario è scritto a mano (a differenza delle descrizioni,
# che ora si parsano da descrizioni-v2.md, vedi sezione 4): un valore sbagliato
# non aveva alcun controllo che lo intercettasse, perché lo script si fidava
# ciecamente di ogni override presente.
#
# Un tecnico_override è legittimo per una sola di due ragioni:
#   (a) il CSV originale ha quella colonna TIPOLOGIA vuota per quel titolo
#       (senza override lo script si fermerebbe più sotto su "tipologia
#       tecnica vuota") — non è una correzione, è un riempimento necessario;
#   (b) è una correzione ESPLICITA di un valore CSV sbagliato, confermata da
#       Damiano (Zefiro/Zefiria, Spirit of the Forest, Once Upon a Castle —
#       vedi descrizioni-proposte.md righe 214/217/222).
# Fuori da questi due casi, un override è quasi certamente un copia-incolla
# finito nella riga sbagliata: la guardia sotto lo intercetta al prossimo
# giro, invece di lasciarlo propagare in silenzio come stavolta.
CORREZIONI_TIPOLOGIA_CONFERMATE = {"Zefiro", "Spirit of the Forest", "Once Upon a Castle"}

# ---------- 4. Descrizioni (fonte unica: descrizioni-v2.md, colonna "Nuova") ----------
# Non è una copia a mano: il markdown è parsato a ogni build, quindi un ritocco
# al file sorgente si riflette qui senza dover ricordarsi di aggiornare una
# seconda copia. Tracciabilità: descrizioni-v2.md, Vera, 2026-08-04.
#
# Alias = casi noti dove il titolo nel markdown diverge dal titolo grezzo nel
# CSV sorgente (stessa lista dei 3 correttivi già confermati da Damiano):
#   Zefiria (md, nome corretto)              -> Zefiro (titolo grezzo nel CSV)
#   Conspiracy (Abyss Universe) (md, esteso)  -> Conspiracy (titolo grezzo nel CSV)
DESCRIZIONI_MD_PATH = f"{BASE}/descrizioni-v2.md"
DESCRIZIONI_ALIAS = {
    "Zefiria": "Zefiro",
    "Conspiracy (Abyss Universe)": "Conspiracy",
}


def load_descrizioni_v2():
    """Parsa descrizioni-v2.md ed estrae, per ognuno dei 48 giochi numerati,
    il testo della colonna 'Nuova'. Ritorna un dict {titolo_csv: descrizione}.
    Si ferma con errore esplicito se non trova esattamente 48 voci, o se una
    voce non ha corrispondenza nei titoli del CSV — meglio fermarsi che
    procedere con una sostituzione parziale invisibile."""
    with open(DESCRIZIONI_MD_PATH, encoding="utf-8") as f:
        text = f.read()

    header_pat = re.compile(r"^## (\d+)\.\s+(.+?)\s+—\s+.+$", re.M)
    headers = [m for m in header_pat.finditer(text) if m.group(1).isdigit()]
    if len(headers) != 48:
        raise SystemExit(
            f"ATTENZIONE: attese 48 intestazioni numerate in descrizioni-v2.md, trovate {len(headers)} — fermo qui."
        )

    nuova_pat = re.compile(r"\*\*Nuova:\*\*\s*(.+?)(?=\n\n|\Z)", re.S)
    trovate = {}
    mancanti = []
    for i, h in enumerate(headers):
        raw_title = h.group(2).strip()
        title_noparen = re.sub(r"\s*\(.*?\)\s*", "", raw_title).strip()
        start = h.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        section = text[start:end]
        m = nuova_pat.search(section)
        if not m:
            mancanti.append(raw_title)
            continue
        csv_title = DESCRIZIONI_ALIAS.get(title_noparen, title_noparen)
        trovate[csv_title] = m.group(1).strip()

    if mancanti:
        raise SystemExit(f"ATTENZIONE: nessuna colonna 'Nuova' trovata per: {mancanti} — fermo qui.")
    if len(trovate) != 48:
        raise SystemExit(f"ATTENZIONE: attese 48 descrizioni distinte, trovate {len(trovate)} — fermo qui.")

    return trovate


DESCRIZIONI_OVERRIDE = load_descrizioni_v2()

# ---------- 4quater. Tag delle "porte" (porte-tag.md, Vera, 2026-08-04) — solo
# 2 dei 3 elenchi: si-ride scartato (2 giochi soli, sotto la soglia di Damiano).
# Copiati verbatim, stessa disciplina di guardia delle altre fonti a mano. ----------
TAG_SENZA_COMPETERE = [
    "Pandemic Reazione Rapida", "Yokai", "Zefiro", "Zombie Kidz Evolution",
    "NobiNobi GDR Spada", "NobiNobi GDR Magia",
]
TAG_BELLO_DA_VEDERE = [
    "Aquatica", "Draftosaurus", "Dungeonology", "Era Il Medioevo", "Kingdomino",
    "New York Zoo", "Spirit of the Forest", "Tang Garden",
]

if len(TAG_SENZA_COMPETERE) != 6:
    raise SystemExit(f"ATTENZIONE: attesi 6 titoli in TAG_SENZA_COMPETERE, trovati {len(TAG_SENZA_COMPETERE)} — fermo qui.")
if len(TAG_BELLO_DA_VEDERE) != 8:
    raise SystemExit(f"ATTENZIONE: attesi 8 titoli in TAG_BELLO_DA_VEDERE, trovati {len(TAG_BELLO_DA_VEDERE)} — fermo qui.")
for _t in TAG_SENZA_COMPETERE + TAG_BELLO_DA_VEDERE:
    if _t not in levels:
        raise SystemExit(f"ATTENZIONE: tag-porta per '{_t}' non aggancia nessun gioco reale — fermo qui.")

# ---------- 4quinquies. Nota "due scatole distinte" — SOLO Spirit of the Forest
# (chiarito da Damiano 04/08: non è un modulo dentro la stessa scatola, sono
# due oggetti separati sullo scaffale — il gioco base e Moonlight). Non tocca
# la descrizione esistente (vincolo esplicito): è un'aggiunta a parte. ----------
NOTA_DUE_SCATOLE = {
    "Spirit of the Forest": "Sono due scatole distinte: Spirit of the Forest (base, competitivo, si gioca da sé) e Spirit of the Forest: Moonlight (l'espansione notturna). Moonlight richiede sempre la scatola base per essere giocata — non funziona da sola sullo scaffale. Chi cerca il cooperativo (o la variante in solitario) prende entrambe le scatole insieme.",
}
if len(NOTA_DUE_SCATOLE) != 1:
    raise SystemExit(f"ATTENZIONE: attesa esattamente 1 nota due-scatole, trovate {len(NOTA_DUE_SCATOLE)} — fermo qui.")
for _t in NOTA_DUE_SCATOLE:
    if _t not in levels:
        raise SystemExit(f"ATTENZIONE: nota due-scatole per '{_t}' non aggancia nessun gioco reale — fermo qui.")

# ---------- 4bis. Titolo corretto (Zefiro -> Zefiria, confermato da Damiano; il titolo grezzo
# nelle fonti CSV resta "Zefiro" — la correzione si applica solo in uscita: titolo, slug) ----------
TITOLO_OVERRIDE = {
    "Zefiro": "Zefiria",
}


def slugify(title):
    t = title.lower()
    t = t.replace("'", "-").replace("!", "")
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode("ascii")
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t


def clean_giocatori(raw):
    return raw.split("\n")[0].strip()


def parse_giocatori_range(giocatori_str):
    """Es. '2 – 4' -> (2,4); '2+' -> (2,99); '2' -> (2,2); '1 – 100' -> (1,100)."""
    nums = re.findall(r"\d+", giocatori_str)
    if not nums:
        raise SystemExit(f"ATTENZIONE: impossibile leggere il numero giocatori da '{giocatori_str}'")
    if "+" in giocatori_str and len(nums) == 1:
        return int(nums[0]), 99
    if len(nums) == 1:
        return int(nums[0]), int(nums[0])
    return int(nums[0]), int(nums[-1])


games = []
for r in data_rows:
    titolo_raw = r[0].strip()
    titolo = norm_title(titolo_raw)
    giocatori = clean_giocatori(r[1])
    descrizione_csv = r[3].strip()
    tipologia_csv = r[4].strip()
    componenti = r[5].strip()
    stato_raw = r[6].strip() if len(r) > 6 else "in arrivo"
    record_id_raw = r[7].strip() if len(r) > 7 else ""
    ean_raw = r[8].strip() if len(r) > 8 else ""

    if titolo not in levels:
        raise SystemExit(f"ATTENZIONE: nessun livello trovato per '{titolo}' — fermo qui, verificare a mano.")
    level_str = levels[titolo]

    in_chiaro, tecnico_override = EDITORIALE.get(titolo, (None, None))
    if in_chiaro is None:
        raise SystemExit(f"ATTENZIONE: nessuna tipologia IN CHIARO per '{titolo}' — fermo qui.")

    if tecnico_override is not None:
        csv_vuoto = not tipologia_csv
        correzione_confermata = titolo in CORREZIONI_TIPOLOGIA_CONFERMATE
        if not csv_vuoto and not correzione_confermata:
            raise SystemExit(
                f"ATTENZIONE: '{titolo}' ha un tecnico_override in EDITORIALE ma il CSV originale "
                f"non è vuoto ('{tipologia_csv}') e il titolo non è nella lista delle correzioni "
                f"confermate da Damiano ({sorted(CORREZIONI_TIPOLOGIA_CONFERMATE)}) — probabile "
                f"refuso di trascrizione (lo stesso tipo di bug del caso MindUp!/Zombie Kidz "
                f"Evolution, 04/08). Fermo qui invece di propagarlo in silenzio."
            )
    tecnico = tecnico_override if tecnico_override is not None else tipologia_csv
    if titolo not in DESCRIZIONI_OVERRIDE:
        raise SystemExit(
            f"ATTENZIONE: nessuna descrizione v2 trovata per '{titolo}' — fermo qui, "
            f"invece di lasciarlo con la vecchia descrizione senza dirlo."
        )
    descrizione = DESCRIZIONI_OVERRIDE.pop(titolo)

    if not descrizione:
        raise SystemExit(f"ATTENZIONE: descrizione vuota per '{titolo}' — fermo qui.")
    if not tecnico:
        raise SystemExit(f"ATTENZIONE: tipologia tecnica vuota per '{titolo}' — fermo qui.")
    if not componenti:
        raise SystemExit(f"ATTENZIONE: componenti vuoti per '{titolo}' — fermo qui.")

    g_min, g_max = parse_giocatori_range(giocatori)

    titolo_output = TITOLO_OVERRIDE.get(titolo, titolo)
    nota_due_scatole = NOTA_DUE_SCATOLE.pop(titolo, "")

    tags = []
    if titolo in TAG_SENZA_COMPETERE:
        tags.append("senza-competere")
    if titolo in TAG_BELLO_DA_VEDERE:
        tags.append("bello-da-vedere")

    game = {
        "slug": slugify(titolo_output),
        "titolo": titolo_output,
        "giocatori": giocatori,
        "giocatori_min": g_min,
        "giocatori_max": g_max,
        "livello_dots": level_dots(level_str),
        "livello_label": level_label(level_str),
        "livello_key": level_key(level_str),
        "descrizione": descrizione,
        "tipologia_chiaro": in_chiaro,
        "tipologia_tecnico": tecnico,
        "componenti": componenti,
        "tags": tags,
        "nota_due_scatole": nota_due_scatole,
        "abstract": "",
        "scheda_completa": True,
    }
    game.update(stato_fields(stato_raw, record_id_raw, ean_raw))
    games.append(game)

N_GAMES_COMPLETI = len(games)
assert N_GAMES_COMPLETI == 48, f"attesi 48 giochi completi (Damiano), trovati {N_GAMES_COMPLETI}"
assert not DESCRIZIONI_OVERRIDE, (
    f"descrizioni v2 avanzate senza corrispondenza in un gioco reale: {list(DESCRIZIONI_OVERRIDE)} — "
    f"probabile disallineamento di titolo tra descrizioni-v2.md e giochi-originale.csv."
)
assert not NOTA_DUE_SCATOLE, (
    f"nota due-scatole avanzata senza corrispondenza in un gioco reale: {list(NOTA_DUE_SCATOLE)} — "
    f"probabile disallineamento di titolo."
)
_n_senza_competere = sum(1 for g in games if "senza-competere" in g["tags"])
_n_bello = sum(1 for g in games if "bello-da-vedere" in g["tags"])
if _n_senza_competere != 6:
    raise SystemExit(f"ATTENZIONE: attesi 6 giochi con tag senza-competere, applicati {_n_senza_competere} — fermo qui.")
if _n_bello != 8:
    raise SystemExit(f"ATTENZIONE: attesi 8 giochi con tag bello-da-vedere, applicati {_n_bello} — fermo qui.")
_n_due_scatole = sum(1 for g in games if g["nota_due_scatole"])
if _n_due_scatole != 1:
    raise SystemExit(f"ATTENZIONE: attesa esattamente 1 scheda con nota due-scatole, applicate {_n_due_scatole} — fermo qui.")

# controllo slug duplicati (solo i 48, prima di unire i giochi scarni)
slugs = [g["slug"] for g in games]
assert len(slugs) == len(set(slugs)), f"slug duplicati: {[s for s in slugs if slugs.count(s) > 1]}"

# ---------- 5. Giochi della biblioteca (biblioteca-nuovi.csv) — scheda scarna ----------
# Prodotto da tools/import_biblioteca_xlsx.py. Niente livello, tipologia,
# componenti: non li inventiamo, li assegnerà Damiano nei prossimi mesi.
# La descrizione invece arriva a lotti da Penna (giochi-biblioteca/lotti/) —
# vedi load_descrizioni_lotto qui sotto — quando un gioco non è ancora
# coperto da un lotto resta "" e il sito mostra l'abstract del catalogo.
# vedi build_card_scarsa/generate_game_page_scarsa in generate_site.py.
with open(f"{BASE}/biblioteca-nuovi.csv", newline="", encoding="utf-8") as f:
    bib_rows = list(csv.reader(f))[1:]

# ---------- 5bis. Descrizioni dei giochi scarni, a lotti (giochi-biblioteca/lotti/) ----------
# Stessa logica di load_descrizioni_v2 (sezione 4) ma su un formato di
# intestazione più semplice ("## N. Titolo", senza suffisso em-dash) e senza
# vincolo sul numero totale di giochi coperti: un lotto copre solo una parte
# dei 100 scarni, gli altri restano "" finché Penna non li scrive.
GIOCHI_BIBLIOTECA_DIR = "/home/damiano/Progetti-Personali/giochi-biblioteca"

# Alias = casi noti dove il titolo scritto nel markdown del lotto (corretto,
# leggibile) diverge dal titolo grezzo in biblioteca-nuovi.csv (refuso della
# biblioteca, non nostro da correggere). Stesso pattern di DESCRIZIONI_ALIAS
# (sezione 4) per i 48 giochi completi.
#   Lotto 2, voce 3: a catalogo l'accento di "città" è perso e c'è un doppio
#   spazio ("La citt  meccanica") — refuso già segnalato alla biblioteca,
#   non corretto qui. Il testo installato non cita comunque il titolo.
DESCRIZIONI_SCARNI_ALIAS = {
    "Destini Infiniti. La città meccanica": "Destini Infiniti. La citt  meccanica",
}

LOTTI_DESCRIZIONI = [
    (f"{GIOCHI_BIBLIOTECA_DIR}/lotti/lotto-01-descrizioni-penna.md", 20, {}),
    (f"{GIOCHI_BIBLIOTECA_DIR}/lotti/lotto-02-descrizioni-penna.md", 20, DESCRIZIONI_SCARNI_ALIAS),
]


def load_descrizioni_lotto(path, n_expected, alias=None):
    """Parsa un file lotto-NN-descrizioni-penna.md ed estrae, per ognuno dei
    giochi numerati nel corpo (non nella sezione 'Aperto' di commento), il
    testo della colonna 'Nuova'. Ritorna un dict {titolo_csv: descrizione}.
    Si ferma con errore esplicito se non trova esattamente n_expected voci.
    `alias` mappa titolo-nel-md -> titolo-grezzo-nel-CSV per i casi noti di
    refuso a catalogo (mai una sostituzione silenziosa: dichiarata sopra)."""
    alias = alias or {}
    with open(path, encoding="utf-8") as f:
        text = f.read()

    # La sezione "Aperto" in coda è commento editoriale (note su fonti/dubbi),
    # non contiene descrizioni da installare: si taglia via prima di parsare,
    # altrimenti gli eventuali "## " o riferimenti numerati lì dentro
    # potrebbero confondersi con le intestazioni vere.
    aperto_pat = re.search(r"^## Aperto\s*$", text, re.M)
    if aperto_pat:
        text = text[: aperto_pat.start()]

    header_pat = re.compile(r"^## (\d+)\.\s+(.+?)\s*$", re.M)
    headers = list(header_pat.finditer(text))
    if len(headers) != n_expected:
        raise SystemExit(
            f"ATTENZIONE: attese {n_expected} intestazioni numerate in {path}, trovate {len(headers)} — fermo qui."
        )

    nuova_pat = re.compile(r"\*\*Nuova:\*\*\s*(.+?)(?=\n\n|\Z)", re.S)
    trovate = {}
    mancanti = []
    for i, h in enumerate(headers):
        raw_title = h.group(2).strip()
        start = h.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        section = text[start:end]
        m = nuova_pat.search(section)
        if not m:
            mancanti.append(raw_title)
            continue
        csv_title = alias.get(raw_title, raw_title)
        trovate[csv_title] = m.group(1).strip()

    if mancanti:
        raise SystemExit(f"ATTENZIONE: nessuna colonna 'Nuova' trovata per: {mancanti} in {path} — fermo qui.")
    if len(trovate) != n_expected:
        raise SystemExit(f"ATTENZIONE: attese {n_expected} descrizioni distinte in {path}, trovate {len(trovate)} — fermo qui.")

    return trovate


DESCRIZIONI_SCARNI_OVERRIDE = {}
for _lotto_path, _lotto_n, _lotto_alias in LOTTI_DESCRIZIONI:
    DESCRIZIONI_SCARNI_OVERRIDE.update(load_descrizioni_lotto(_lotto_path, _lotto_n, _lotto_alias))

games_scarni = []
for r in bib_rows:
    if not r or not r[0].strip():
        continue
    titolo, record_id, ean, abstract, stato_raw = r[0].strip(), r[1].strip(), r[2].strip(), r[3].strip(), r[4].strip()
    game = {
        "slug": slugify(titolo),
        "titolo": titolo,
        "giocatori": "",
        "giocatori_min": None,
        "giocatori_max": None,
        "livello_dots": "",
        "livello_label": "",
        "livello_key": "",
        "descrizione": DESCRIZIONI_SCARNI_OVERRIDE.pop(titolo, ""),
        "tipologia_chiaro": "",
        "tipologia_tecnico": "",
        "componenti": "",
        "tags": [],
        "nota_due_scatole": "",
        "abstract": abstract,
        "scheda_completa": False,
    }
    game.update(stato_fields(stato_raw, record_id, ean))
    games_scarni.append(game)

N_GAMES_SCARNI = len(games_scarni)
if N_GAMES_SCARNI != 100:
    raise SystemExit(f"ATTENZIONE: attesi 100 giochi scarni dalla biblioteca, trovati {N_GAMES_SCARNI} — fermo qui.")

assert not DESCRIZIONI_SCARNI_OVERRIDE, (
    f"descrizioni di lotto avanzate senza corrispondenza in un gioco scarno reale: {list(DESCRIZIONI_SCARNI_OVERRIDE)} — "
    f"probabile disallineamento di titolo tra il file lotto e biblioteca-nuovi.csv."
)

games = games + games_scarni

# controllo slug duplicati sull'unione (i 48 + i 100): uno slug ripetuto
# sovrascriverebbe silenziosamente una pagina con un'altra in docs/g/<slug>/
slugs = [g["slug"] for g in games]
assert len(slugs) == len(set(slugs)), f"slug duplicati fra i due cataloghi: {[s for s in slugs if slugs.count(s) > 1]}"

N_GAMES_TOTALE = len(games)
if N_GAMES_TOTALE != 148:
    raise SystemExit(f"ATTENZIONE: attesi 148 giochi in totale (48+100), trovati {N_GAMES_TOTALE} — fermo qui.")

games.sort(key=lambda g: g["titolo"].lower())

# ---------- 6. Arricchimento schede (25/08, modello di scheda approvato) ----------
# Tre fonti nuove in dati-catalogo/, lette qui e mai a mano:
#   - schede-biblioteca.json (101, chiave record_id): giocatori/durata/
#     componenti dal catalogo della biblioteca. Copre i 100 giochi scarni +
#     Kingdomino (uno dei 48— i suoi campi restano quelli di Damiano, non si
#     toccano: la fonte qui serve solo per la copertina di Kingdomino).
#   - livelli-damiano.json (71, chiave titolo grezzo con eventuali entità
#     HTML tipo "&amp;"): livello assegnato da Damiano ai giochi che conosce.
#     Copre 70 giochi scarni + Kingdomino (idem, non si tocca).
#   - copertine-extra/_registro.json (72 voci, 66 con file valido): copertine
#     procurate a mano per i giochi che il catalogo non copre.
# Where un campo manca, resta "" — mai inventato, mai dedotto.
with open(f"{BASE}/dati-catalogo/schede-biblioteca.json", encoding="utf-8") as f:
    SCHEDE_BIB = json.load(f)

with open(f"{BASE}/dati-catalogo/livelli-damiano.json", encoding="utf-8") as f:
    _livelli_raw = json.load(f)
LIVELLI_DAMIANO = {html.unescape(k): v for k, v in _livelli_raw.items()}

with open(f"{BASE}/dati-catalogo/copertine-extra/_registro.json", encoding="utf-8") as f:
    _registro_raw = json.load(f)
COPERTINE_EXTRA = {html.unescape(k): v for k, v in _registro_raw.items() if v.get("file")}

DOTS_BY_KEY = {
    "al-volo": "●○○○",
    "da-soli": "●●○○",
    "con-guida": "●●●○",
    "da-serata": "●●●●",
}


def estrai_componenti(descrizione_fisica):
    """Isola il testo fra la prima parentesi e la sua chiusura bilanciata.
    Alcune schede del catalogo hanno la parentesi esterna mai richiusa prima
    di 'EAN:' (refuso del catalogo, es. Pandemic Zona Rossa Europa): in quel
    caso si prende tutto il resto fino a 'EAN:' invece di restituire vuoto."""
    testo = descrizione_fisica.split("EAN:")[0]
    start = testo.find("(")
    if start == -1:
        return ""
    depth = 0
    for i in range(start, len(testo)):
        if testo[i] == "(":
            depth += 1
        elif testo[i] == ")":
            depth -= 1
            if depth == 0:
                return testo[start + 1:i].strip()
    return testo[start + 1:].strip().rstrip(";").strip()


def normalizza_durata(durata_raw):
    """'ca 10-15 min' -> '10-15 min'; '40 min.' -> '40 min'. Non tocca i
    numeri, solo la punteggiatura del catalogo."""
    d = durata_raw.strip()
    if d.lower().startswith("ca "):
        d = d[3:].strip()
    d = d.replace("min.", "min").strip()
    return d


COPERTINE_DIR_OUT = f"{BASE}/docs/copertine"
os.makedirs(COPERTINE_DIR_OUT, exist_ok=True)

_n_copertina_catalogo = 0
_n_copertina_extra = 0
_n_arricchiti_scarni = 0

for g in games:
    # --- copertina: prima il catalogo (per record_id), poi la extra (per titolo) ---
    sorgente_copertina = None
    scheda_bib = SCHEDE_BIB.get(g.get("record_id", ""))
    if scheda_bib and scheda_bib.get("copertina_file"):
        sorgente_copertina = f"{BASE}/dati-catalogo/{scheda_bib['copertina_file']}"
        _n_copertina_catalogo += 1
    elif g["titolo"] in COPERTINE_EXTRA:
        sorgente_copertina = f"{BASE}/dati-catalogo/copertine-extra/{COPERTINE_EXTRA[g['titolo']]['file']}"
        _n_copertina_extra += 1

    if sorgente_copertina:
        dest = f"{COPERTINE_DIR_OUT}/{g['slug']}.jpg"
        shutil.copyfile(sorgente_copertina, dest)
        g["copertina"] = f"copertine/{g['slug']}.jpg"
    else:
        g["copertina"] = ""

    # --- arricchimento SOLO delle schede scarne (i 48 di Damiano non si toccano) ---
    if g["scheda_completa"]:
        g["durata"] = ""
        continue

    g["durata"] = ""
    if scheda_bib:
        giocatori_raw = scheda_bib.get("giocatori", "").strip()
        if giocatori_raw:
            try:
                g_min, g_max = parse_giocatori_range(giocatori_raw)
                g["giocatori"] = giocatori_raw
                g["giocatori_min"] = g_min
                g["giocatori_max"] = g_max
            except SystemExit:
                pass  # formato non riconosciuto: resta senza giocatori, non si inventa

        durata_raw = scheda_bib.get("durata", "").strip()
        if durata_raw:
            g["durata"] = normalizza_durata(durata_raw)

        componenti = estrai_componenti(scheda_bib.get("descrizione_fisica", ""))
        if componenti:
            g["componenti"] = componenti

        _n_arricchiti_scarni += 1

    if g["titolo"] in LIVELLI_DAMIANO:
        level_key = LIVELLI_DAMIANO[g["titolo"]]
        if level_key not in DOTS_BY_KEY:
            raise SystemExit(f"ATTENZIONE: livello '{level_key}' per '{g['titolo']}' non riconosciuto — fermo qui.")
        g["livello_key"] = level_key
        g["livello_dots"] = DOTS_BY_KEY[level_key]
        g["livello_label"] = LEVEL_LABEL[level_key]

print(
    f"Arricchimento schede — copertine: {_n_copertina_catalogo} dal catalogo + {_n_copertina_extra} extra "
    f"= {_n_copertina_catalogo + _n_copertina_extra} su {len(games)}; "
    f"giochi scarni con dati dal catalogo (giocatori/durata/componenti): {_n_arricchiti_scarni}; "
    f"giochi scarni con livello di Damiano: {sum(1 for g in games if not g['scheda_completa'] and g['livello_key'])}"
)

with open(f"{BASE}/docs/js/games-data.json", "w", encoding="utf-8") as f:
    json.dump(games, f, ensure_ascii=False, indent=2)

# games-data.js: stesso contenuto del json, come const globale — caricato da index.html
# via <script src="js/games-data.js">, prima di filtri.js.
with open(f"{BASE}/docs/js/games-data.js", "w", encoding="utf-8") as f:
    f.write("// Dati generati da tools/build_data.py — non modificare a mano, rigenerare dallo script.\n")
    f.write("const GAMES = ")
    json.dump(games, f, ensure_ascii=False, indent=2)
    f.write(";\n")

_n_in_arrivo = sum(1 for g in games if g["stato_key"] == "in-arrivo")
_n_in_biblioteca = sum(1 for g in games if g["stato_key"] == "in-biblioteca")
print(
    f"OK — {len(games)} giochi consolidati in docs/js/games-data.json + games-data.js "
    f"({N_GAMES_COMPLETI} schede complete + {N_GAMES_SCARNI} scarne; "
    f"per stato: {_n_in_arrivo} in arrivo, {_n_in_biblioteca} in biblioteca)"
)
for g in games:
    completo = "completa" if g["scheda_completa"] else "scarna  "
    print(f"  {g['slug']:35s} {completo} {g['stato_key']:15s} {g['titolo']}")
