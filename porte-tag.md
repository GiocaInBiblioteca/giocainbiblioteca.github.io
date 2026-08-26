# Porte-tag — le tre etichette mancanti

Data: 2026-08-04
Autrice: Vera

Metodo: per ogni gioco ho incrociato descrizione, `tipologia_tecnico` e `componenti` dal JSON; dove il dubbio riguardava il meccanismo reale (non il tema), ho verificato con fonti esterne (BGG-adjacent, recensioni italiane). Segnalo sotto ogni criterio duro applicato e ogni scarto.

---

## 1. `senza-competere` — «Non voglio litigare con nessuno»

Criterio applicato: cooperativo vero (si vince/perde tutti insieme) o narrativo puro senza avversari. Escluso tutto ciò che è "solitario in compagnia".

1. **Pandemic Reazione Rapida** — cooperativo in tempo reale confermato da fonti esterne: si corre insieme contro la clessidra, non uno contro l'altro.
2. **Yokai** — cooperativo puro: niente comunicazione verbale, si vince o si perde tutti insieme nel riordinare gli spiriti.
3. **Zefiria** — cooperativo: le isole vanno rimesse in fila tutti insieme prima che il tempo scada, poteri diversi ma stesso obiettivo.
4. **Zombie Kidz Evolution** — cooperativo legacy per bambini, confermato: si difende la scuola in squadra, non c'è avversario tra i giocatori.
5. **NobiNobi GDR Spada** — narrativo puro: i ruoli di narratore e protagonista girano a ogni turno, nessuno gioca contro nessuno.
6. **NobiNobi GDR Magia** — stessa struttura di Spada, stesso motivo: nessun avversario al tavolo.

**Totale: 6**

---

## 2. `si-ride` — «Vogliamo ridere»

Criterio applicato: il momento migliore è qualcosa che qualcuno dice o fa, non una mossa. Nel catalogo solo due titoli sono esplicitamente etichettati "Party" nel campo tecnico, e solo questi due reggono davvero il criterio.

1. **CocoRido All'Arrembaggio** — party game puro: si ride delle risposte assurde lette ad alta voce, il divertimento è nella battuta, non nella carta giocata.
2. **Champions!** — party/votazione: si vota il duello più assurdo, conta la battuta e l'istinto del gruppo, non la logica.

**Totale: 2**

⚠️ Vedi nota per Damiano in fondo — questa porta con solo 2 giochi non regge secondo la sua stessa soglia.

---

## 3. `bello-da-vedere` — «Bello da vedere in tavola»

Criterio applicato: il tavolo a fine partita è qualcosa che si fotograferebbe, provato dai componenti (non dall'impressione della copertina).

1. **Aquatica** — 39 miniature di mante (16 addestrate + 23 selvagge) su una plancia oceanica.
2. **Draftosaurus** — dinosauri di legno sagomati e colorati per specie, zoo bifacciale che si riempie visibilmente; recensioni confermano materiali "coloratissimi e curati".
3. **Dungeonology** — miniature di qualità confermata dalle recensioni ("miniature bellissime, grafica ispiratissima"), non solo pedine generiche.
4. **Era Il Medioevo** — città vera in 3D che cresce pezzo su pezzo: fortezze, cattedrali, mura, tutto fisicamente costruito sul tavolo.
5. **Kingdomino** — 4 castelli 3D + torre 3D che si aggiungono al regno di tessere via via composto.
6. **New York Zoo** — pedine animali sagomate e colorate (suricati, fenicotteri, canguri, pinguini, volpi artiche) sopra recinti a incastro tipo puzzle.
7. **Spirit of the Forest** — illustrazioni confermate dalle recensioni come "delight visivo", gemme colorate come segnaposto, tessere spirito riccamente dipinte.
8. **Tang Garden** — tessere dipinte, lanterne, figure personaggio: il giardino si compone visivamente turno dopo turno.

**Totale: 8**

---

## Aperto — da chiedere a Damiano

**Spirit of the Forest e `senza-competere`.** Il gioco base è competitivo (già corretto in sessione precedente). La scatola include però il modulo Moonlight, cooperativo vero, non un'espansione a parte da comprare. Non l'ho incluso nella porta `senza-competere` perché il criterio chiede "cooperativo vero" del gioco come si presenta di default, e di default questo è competitivo. Se Damiano vuole che la porta segnali anche giochi con modulo cooperativo incluso, va detto esplicitamente nella pagina (tipo: "include modulo cooperativo").

**MindUp! — discrepanza nei dati, non decisione mia.** Il campo `tipologia_tecnico` nel JSON lo marca "Cooperativo · Legacy · Tiro di dadi". Ho verificato: la descrizione nel catalogo corrisponde al gioco reale "Mind Up!" di Catch Up Games (carte piazzate in segreto, rivelate insieme, ordinate numericamente) — che secondo le fonti consultate è un gioco **non cooperativo**. Il tag "Cooperativo" sembra un refuso, probabile confusione con "The Mind" (titolo diverso, quello sì cooperativo). Non l'ho incluso in `senza-competere`. Segnalo la correzione per il campo dati, non tocco il JSON.

**`si-ride` — terzo candidato debole.** 21 Giochi Minuti contiene alcuni minigiochi da party nella sua raccolta di 21, ma è un mix eterogeneo (destrezza, memoria, velocità) — non è omogeneamente un gioco "per ridere". L'ho lasciato fuori, ma se Damiano vuole allargare il criterio per arrivare a 3 titoli, è il candidato più prossimo.

**`bello-da-vedere` — due candidati scartati per prudenza.**
- **Sock Monsters** — ha una plancia 3D con un "inserto casa" a stanze chiuse, un gimmick fisico interessante per un gioco da bambini, ma è più giocattolo funzionale che tavolo "fotografabile" nel senso richiesto. Escluso.
- **Momiji** — tema giardino imperiale giapponese, ma componenti (carte, tessere, gettoni) senza prova concreta di resa visiva superiore alla media del catalogo. Escluso per mancanza di prova, non per giudizio negativo.
