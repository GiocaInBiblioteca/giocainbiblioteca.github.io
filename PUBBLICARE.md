# Pubblicare il catalogo su GitHub Pages

Questo foglio sostituisce quello vecchio (`giochi-biblioteca/PUBBLICARE.md`,
ora superato — lasciato lì solo con un rimando a questo). Dal 25/08 non ci
sono più due repository: uno solo, questo, contiene sia il progetto (dati,
script) sia il sito pubblicato (`docs/`). Leggilo dall'inizio anche se pensi
di ricordarti la procedura.

**Dati fissi del progetto:**

- Repo (unico, lavoro e pubblicazione insieme): `/home/damiano/Progetti-Personali/giocainbiblioteca.github.io/`
- Remote GitHub: `https://github.com/GiocaInBiblioteca/giocainbiblioteca.github.io.git`
- Indirizzo pubblico del sito: `https://giocainbiblioteca.github.io/`
- GitHub Pages serve dalla cartella `docs/` del branch `main` — NON dalla
  radice del repo (che ora ospita anche i CSV e `tools/`). Vedi Passo 0bis,
  da fare una volta sola.
- Alla radice: `giochi-originale.csv` (i 48 giochi di Damiano),
  `biblioteca-nuovi.csv` (i giochi della biblioteca, prodotto da
  `tools/import_biblioteca_xlsx.py`), `revisione-livelli-DAMIANO.csv`,
  `descrizioni-v2.md`, `tools/` (gli script), `da-stampare/` (i PDF già
  pronti per la stampa). `docs/` è tutto generato da questi — non si tocca
  a mano dentro `docs/`, si tocca la fonte e si rigenera.

---

## Cambiare lo stato di un gioco (in arrivo / in biblioteca)

Il gesto che farai più spesso, su segnalazione della biblioteca. Costa una
parola in una cella, poi due comandi:

1. Apri il CSV giusto: `giochi-originale.csv` se è uno dei 48 di Damiano,
   `biblioteca-nuovi.csv` se è uno dei giochi della biblioteca. Cambia la
   colonna `STATO` in `in arrivo` o `in biblioteca` (parole esatte, minuscole).
2. Rigenera:
   ```
   cd /home/damiano/Progetti-Personali/giocainbiblioteca.github.io
   python3 tools/build_data.py && python3 tools/generate_site.py
   ```
3. Guarda cosa è cambiato (`git status` — deve toccare solo `docs/js/games-data.*`
   e la scheda del gioco in questione), poi commit + push (Passo 3-4 sotto).

## Aggiungere nuovi giochi segnalati dalla biblioteca

Quando la biblioteca manda un nuovo foglio Excel (stesse 5 colonne:
TITOLO, RECORD_ID, EAN, ABSTRACT, A CATALOGO):

```
cd /home/damiano/Progetti-Personali/giocainbiblioteca.github.io
python3 tools/import_biblioteca_xlsx.py "/percorso/al/nuovo/foglio.xlsx"
```

Questo riscrive `biblioteca-nuovi.csv` da capo con TUTTO il contenuto del
foglio — se la biblioteca manda un elenco cumulativo (i vecchi giochi più i
nuovi), va bene così. Se un titolo del foglio esiste già in
`giochi-originale.csv`, lo script lo salta e lo stampa a schermo (è già
successo con Kingdomino, il 25/08: due schede per lo stesso gioco vanno
unificate a mano, non è un'operazione automatica). Poi rigenera come sopra.

---

## Passo 0 — Il lavoro è pulito?

```
cd /home/damiano/Progetti-Personali/giocainbiblioteca.github.io && git status
```

Deve rispondere "niente da committare, albero di lavoro pulito" (o mostrare
solo le modifiche che ti aspetti di aver fatto tu). Se non lo è, capisci
perché prima di andare avanti.

## Passo 0bis — GitHub Pages serve da `docs/` (una volta sola)

Dal 25/08 il repo ha sia il progetto sia il sito: Pages deve sapere di
servire solo `docs/`, non la radice. Vale una volta sola, poi salta questo
passo alle pubblicazioni successive.

1. Apri `https://github.com/GiocaInBiblioteca/giocainbiblioteca.github.io/settings/pages`
2. Sotto "Build and deployment", "Source" → "Deploy from a branch".
3. Branch: `main`, cartella: `/docs` (non `/ (root)`).
4. Salva.

## Passo 1 — Rigenera se hai toccato i dati

```
cd /home/damiano/Progetti-Personali/giocainbiblioteca.github.io
python3 tools/build_data.py && python3 tools/generate_site.py
```

(Salta questo passo se hai toccato solo `tools/` o file di progetto che non
producono `docs/`.)

## Passo 2 — Guarda cosa sta per cambiare

```
cd /home/damiano/Progetti-Personali/giocainbiblioteca.github.io && git status
```

Leggi l'elenco. Deve avere senso rispetto a quello che hai davvero cambiato.
Se vedi file che non ti aspettavi, fermati e capisci perché.

## Passo 3 — Commit e push (li esegui tu, mai un agent)

```
cd /home/damiano/Progetti-Personali/giocainbiblioteca.github.io && git add -A
```

```
cd /home/damiano/Progetti-Personali/giocainbiblioteca.github.io && git commit -m "Aggiorna catalogo"
```

```
cd /home/damiano/Progetti-Personali/giocainbiblioteca.github.io && git push origin main
```

## Passo 4 — Verifica che conta, non "dovrebbe funzionare"

Il deploy dopo un push può richiedere un minuto o due. Poi lancia questo
controllo: scarica l'elenco reale dal sito online e prova a raggiungere ogni
scheda, contando quante rispondono davvero (HTTP 200).

```
total=$(curl -s https://giocainbiblioteca.github.io/js/games-data.json | jq -r '.[].slug' | wc -l); ok=0; for slug in $(curl -s https://giocainbiblioteca.github.io/js/games-data.json | jq -r '.[].slug'); do code=$(curl -s -o /dev/null -w "%{http_code}" "https://giocainbiblioteca.github.io/g/$slug/"); if [ "$code" = "200" ]; then ok=$((ok+1)); else echo "FALLITA: $slug ($code)"; fi; done; echo "$ok / $total schede online"
```

Il risultato atteso oggi è `148 / 148 schede online` e nessuna riga "FALLITA".
Se il numero è più basso, il deploy potrebbe non essere ancora finito
(riprova tra un minuto) oppure qualcosa nella pubblicazione è andato storto.

Controlla anche la home a occhio, aprendo `https://giocainbiblioteca.github.io/`
nel browser.

---

## La prima pubblicazione (si fa una volta sola)

Il repo su GitHub oggi ha dentro solo il vecchio sito. Adesso ci mettiamo anche il
progetto — dati, strumenti, materiali — e ripartiamo con una cronologia pulita:
il lavoro locale di questi mesi resta sul tuo computer, online va il progetto come
e' oggi.

**Prima**: apri `git status` e guarda cosa c'e' nella radice. Devi vedere `docs/`,
`tools/`, `dati-catalogo/`, i CSV, `da-stampare/`, `PUBBLICARE.md`. Se vedi altro,
fermati e chiedi.

Poi, uno alla volta:

```
cd /home/damiano/Progetti-Personali/giocainbiblioteca.github.io
git checkout --orphan pubblico
git add -A
git commit -m "Il catalogo e il progetto, insieme"
git branch -D main
git branch -m main
git push origin main --force
```

**Poi, una volta sola, su GitHub**: Settings → Pages → Source: `main`, cartella `/docs`.
Da quel momento il sito si aggiorna da solo a ogni push.

**Controlla che sia andata**: apri https://giocainbiblioteca.github.io/ e conta i giochi.
Devono essere 148. Se ne vedi 48, Pages sta ancora servendo dalla vecchia cartella:
ricontrolla l'impostazione qui sopra.

Il `--force` cancella da GitHub i tre commit vecchi. E' voluto: e' il modo per non
portare online una cronologia di lavoro che non c'e' mai stata.
