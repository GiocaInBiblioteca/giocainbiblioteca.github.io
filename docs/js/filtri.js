// Filtro client-side per la home. Vanilla JS, nessuna dipendenza.
// Se questo script non parte per qualunque motivo, la griglia resta
// comunque visibile per intero: è un miglioramento, non un requisito.
(function () {
  "use strict";

  var contenitore = document.getElementById("elenco-giochi");
  if (!contenitore) return;

  var voci = Array.prototype.slice.call(contenitore.querySelectorAll(".gioco-card-wrap"));
  var gruppi = Array.prototype.slice.call(contenitore.querySelectorAll(".livello-gruppo"));
  var contatore = document.getElementById("contatore-risultati");
  var btnReset = document.getElementById("filtro-reset");
  var fraseArrivo = document.getElementById("porta-frase");

  var livelloAttivo = "tutti";
  var giocatoriAttivo = "tutti";
  var tagAttivo = "tutti";

  function parseGiocatoriRange(chiave) {
    var parti = chiave.split("-").map(Number);
    return { min: parti[0], max: parti[1] };
  }

  function okGiocatori(voce) {
    if (giocatoriAttivo === "tutti") return true;
    var gMin = parseInt(voce.dataset.giocatoriMin, 10);
    var gMax = parseInt(voce.dataset.giocatoriMax, 10);
    // "solo"/"due" sono match esatti (porte), non un intervallo che tocca
    // il range come i pulsanti manuali sotto.
    if (giocatoriAttivo === "solo") return gMin === 1;
    if (giocatoriAttivo === "due") return gMax === 2;
    var range = parseGiocatoriRange(giocatoriAttivo);
    return gMax >= range.min && gMin <= range.max;
  }

  function okTag(voce) {
    if (tagAttivo === "tutti") return true;
    var tags = (voce.dataset.tags || "").split(",");
    return tags.indexOf(tagAttivo) !== -1;
  }

  function applicaFiltri() {
    var visibili = 0;

    // conta i visibili per gruppo mentre si scorrono le card, invece di
    // ri-interrogare il DOM sullo stile inline appena scritto (fragile)
    var visibiliPerGruppo = {};

    voci.forEach(function (voce) {
      var okLivello = livelloAttivo === "tutti" || voce.dataset.livello === livelloAttivo;
      var visibile = okLivello && okGiocatori(voce) && okTag(voce);
      voce.style.display = visibile ? "" : "none";
      if (visibile) {
        visibili++;
        var chiaveGruppo = voce.dataset.livello;
        visibiliPerGruppo[chiaveGruppo] = (visibiliPerGruppo[chiaveGruppo] || 0) + 1;
      }
    });

    // un gruppo senza giochi visibili sparisce del tutto, intestazione compresa:
    // un blocco vuoto con scritto "DA SERATA" sotto sarebbe peggio di niente.
    gruppi.forEach(function (gruppo) {
      var haVisibili = (visibiliPerGruppo[gruppo.dataset.livelloGruppo] || 0) > 0;
      gruppo.style.display = haVisibili ? "" : "none";
    });

    if (contatore) {
      contatore.textContent = visibili + " giochi su " + voci.length;
    }
  }

  function aggiornaPressed(gruppoSelector, valore) {
    document.querySelectorAll(gruppoSelector).forEach(function (btn) {
      var attivo = btn.dataset.filtroLivello === valore || btn.dataset.filtroGiocatori === valore;
      btn.setAttribute("aria-pressed", attivo ? "true" : "false");
    });
  }

  function nascondiFrase() {
    if (fraseArrivo) fraseArrivo.textContent = "";
  }

  document.querySelectorAll("[data-filtro-livello]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      livelloAttivo = btn.dataset.filtroLivello;
      aggiornaPressed("[data-filtro-livello]", livelloAttivo);
      nascondiFrase();
      applicaFiltri();
    });
  });

  document.querySelectorAll("[data-filtro-giocatori]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      giocatoriAttivo = btn.dataset.filtroGiocatori;
      aggiornaPressed("[data-filtro-giocatori]", giocatoriAttivo);
      nascondiFrase();
      applicaFiltri();
    });
  });

  if (btnReset) {
    btnReset.addEventListener("click", function () {
      livelloAttivo = "tutti";
      giocatoriAttivo = "tutti";
      tagAttivo = "tutti";
      aggiornaPressed("[data-filtro-livello]", "tutti");
      aggiornaPressed("[data-filtro-giocatori]", "tutti");
      nascondiFrase();
      applicaFiltri();
    });
  }

  // API usata dalle porte (sezione d'ingresso della home, vedi porte.js):
  // ogni porta imposta UN SOLO asse di filtro alla volta e azzera gli altri
  // due — è una vista pulita, non una combinazione con filtri manuali già
  // attivi in precedenza.
  window.Filtri = {
    vaiA: function (opts) {
      livelloAttivo = (opts && opts.livello) || "tutti";
      giocatoriAttivo = (opts && opts.giocatori) || "tutti";
      tagAttivo = (opts && opts.tag) || "tutti";
      aggiornaPressed("[data-filtro-livello]", livelloAttivo);
      aggiornaPressed("[data-filtro-giocatori]", giocatoriAttivo);
      if (fraseArrivo) {
        fraseArrivo.textContent = (opts && opts.frase) || "";
      }
      applicaFiltri();
    }
  };

  applicaFiltri();
})();
