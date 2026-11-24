# InESPugnabile — Brand Identity

> **Per Claude Code:** leggi questo file per intero prima di creare qualsiasi output per InESPugnabile (interfacce, presentazioni, documenti, video, immagini). Le regole qui sono vincolanti. Usa sempre i file in `assets/` e i valori in `tokens/`: non ridisegnare il logo, non inventare colori o font. Se una regola non copre un caso, scegli l'opzione più semplice e coerente con il resto del file.

## Struttura della cartella

```
brand/
├── BRAND.md                      ← questo file
├── tokens/
│   ├── tokens.css                ← variabili CSS (colori, font, raggi, spaziature)
│   └── tokens.json               ← stessi valori per script (python-pptx, docx, Remotion…)
└── assets/
    ├── logo/
    │   ├── logo-blu.svg                    ← simbolo, versione principale
    │   ├── logo-inchiostro.svg             ← simbolo su fondi chiari, monocromo
    │   ├── logo-bianco.svg                 ← simbolo su fondi scuri o blu
    │   ├── logo-orizzontale.svg            ← simbolo + nome, su chiaro
    │   ├── logo-orizzontale-negativo.svg   ← su Inchiostro
    │   ├── logo-orizzontale-su-blu.svg     ← su Blu Elettrico
    │   ├── app-icon.svg                    ← 512×512, angoli arrotondati
    │   └── favicon.svg                     ← 64×64
    ├── pattern/
    │   ├── onde-concentriche.svg
    │   ├── segnale-ripetuto.svg
    │   ├── monogramma-inchiostro.svg
    │   └── tono-su-tono.svg
    └── mascotte/                 ← immagini di Spy (inserite a mano, vedi §8)
```

I loghi orizzontali contengono il nome come testo SVG in Manrope 800. Se il software non ha Manrope installato, carica il font prima di renderizzare (Google Fonts) oppure converti il testo in tracciati.

---

## 1. Il brand

**InESPugnabile** è uno smart caveau IoT basato su ESP32: tastierino PIN, LCD, motori di apertura, fotocamere interna ed esterna, sensori di luce e umidità, barra LED di stato, interfaccia web sulla scheda e bot Telegram.

- **Concept:** il buco della serratura che trasmette. La sicurezza del caveau e la connessione dell'ESP32 in un solo segno.
- **Personalità:** digitale, netto, affidabile. Tecnologico ma accessibile, mai minaccioso.
- **Tagline:** *Il caveau connesso.*
- **Lingua:** italiano.

### Come si scrive il nome
- Sempre **InESPugnabile**: I maiuscola, **ESP** in maiuscolo, il resto minuscolo.
- "ESP" è il gioco di parole con la scheda ESP32, quindi nel logotipo è sempre evidenziato a colore (vedi §3).
- Non scrivere mai: Inespugnabile, INESPUGNABILE (tranne nelle label in maiuscolo mono e sugli LCD), InEspugnabile, In-ESP-ugnabile.

### Tono di voce
- Frasi brevi, chiare, dirette. Si dà del tu.
- Rassicurante quando tutto è ok, fermo e chiaro quando c'è un problema. Mai allarmista.
- Esempi:
  - Accesso consentito → "Accesso consentito. Bentornato."
  - PIN errato → "PIN errato. Tentativi rimasti: 2."
  - Intrusione → "Accesso negato. Foto inviata al gestore."
  - Stato → "Caveau chiuso · Umidità 48% · Luce 312 lx"

---

## 2. Logo

### Il simbolo
Il buco di una serratura (testa circolare + corpo a trapezio) con sopra **due archi di segnale concentrici**. Il centro dei due archi coincide con il centro della testa della serratura. Gli archi hanno lo stesso spessore, le estremità arrotondate e un'apertura di 52° per lato rispetto alla verticale.

Costruzione (viewBox 0 0 100 100): arco esterno r = 38, arco interno r = 24, spessore archi 6.6, testa della serratura r = 13.7 centrata in (50, 50), corpo da y = 56 a y = 96, larghezza 15.2 in alto e 26.6 in basso. **Non ridisegnarlo:** usa sempre i file SVG.

### Varianti e quando usarle
| Variante | File | Quando |
|---|---|---|
| Simbolo blu | `logo-blu.svg` | Uso principale su Carta o bianco |
| Simbolo bianco | `logo-bianco.svg` | Su Blu Elettrico, su Inchiostro, su foto scure |
| Simbolo inchiostro | `logo-inchiostro.svg` | Stampa monocromatica, timbri, documenti in bianco e nero |
| Orizzontale | `logo-orizzontale.svg` | Intestazioni, slide, siti, su chiaro |
| Orizzontale negativo | `logo-orizzontale-negativo.svg` | Su Inchiostro |
| Orizzontale su blu | `logo-orizzontale-su-blu.svg` | Su Blu Elettrico |
| App icon | `app-icon.svg` | Icona app, avatar del bot Telegram, profilo social |
| Favicon | `favicon.svg` | Browser e interfaccia web dell'ESP32 |

### Regole
- **Area di rispetto:** intorno al logo lascia uno spazio libero pari almeno al diametro della testa della serratura.
- **Dimensioni minime:** simbolo da 20 px di altezza su schermo (8 mm in stampa); logo orizzontale da 120 px di larghezza (30 mm).
- **Vietato:** deformarlo o ruotarlo, cambiarne i colori fuori palette, aggiungere ombre, contorni, gradienti o effetti 3D, separare gli archi dalla serratura, cambiare il numero degli archi, metterlo su fondi a basso contrasto (es. blu su Nebbia, bianco su Carta).

---

## 3. Logotipo

- Font **Manrope 800**, crenatura (letter-spacing) **−0,045 em**, su una riga sola.
- **"ESP" evidenziato** secondo il fondo:
  - su Carta o bianco: testo Inchiostro `#111214`, "ESP" in Blu Elettrico `#1F4BFF`;
  - su Inchiostro: testo bianco, "ESP" in `#6F8BFF`;
  - su Blu Elettrico: tutto bianco, "ESP" sottolineato (spessore 0,08 em, distanza 0,12 em);
  - monocromo: tutto in un colore, "ESP" sottolineato.
- Composizione orizzontale: simbolo a sinistra, alto circa quanto il testo più un 40%, distanza simbolo-testo pari a circa ¼ dell'altezza del simbolo.

---

## 4. Colori

| Nome | HEX | Ruolo |
|---|---|---|
| **Blu Elettrico** | `#1F4BFF` | Colore di marca: logo, pulsanti principali, link, accenti, copertine |
| **Inchiostro** | `#111214` | Testo principale, fondi scuri, interfaccia notturna |
| **Carta** | `#F4F4F2` | Fondo chiaro principale |
| **Nebbia** | `#D9DAD6` | Linee, bordi, separatori, fondi secondari |
| **Rosso Allarme** | `#E5484D` | **Solo** errori, PIN errato, intrusione, allarme |
| Bianco | `#FFFFFF` | Card, superfici su Carta, testo su blu e su inchiostro |
| Blu chiaro su scuro | `#6F8BFF` | "ESP" e link su fondo Inchiostro |
| Testo secondario | `#55585C` | Didascalie e label su fondi chiari |

**Proporzioni indicative:** 60% Carta/Bianco, 25% Inchiostro, 12% Blu Elettrico, 3% Rosso (solo dove serve).

### Abbinamenti ammessi (contrasto ≥ 4,5:1)
- Inchiostro su Carta o bianco · Blu Elettrico su Carta o bianco · Bianco su Blu Elettrico · Bianco su Inchiostro · `#6F8BFF` su Inchiostro · `#55585C` su Carta.

### Abbinamenti vietati
- Blu Elettrico su Inchiostro per il testo (troppo scuro: usa `#6F8BFF`) · Rosso su Blu · Nebbia come colore del testo · bianco su Carta o Nebbia · gradienti tra i colori del brand.

Il **Rosso Allarme** non è decorativo: non usarlo per titoli, sfondi o accenti estetici.

---

## 5. Tipografia

| Ruolo | Font | Pesi | Note |
|---|---|---|---|
| Logo e titoli | **Manrope** | 800 (500 per i sottotitoli) | Crenatura −0,035 em nei titoli, −0,045 em nel logotipo |
| Testo, interfaccia | **Inter** | 400, 600 | Interlinea 1,5–1,6 |
| Dati, label, LCD, codice | **JetBrains Mono** | 400, 500 | Label in MAIUSCOLO, spaziatura +0,13 em, 12–13 px |

Google Fonts: `https://fonts.googleapis.com/css2?family=Manrope:wght@500;800&family=Inter:wght@400;600&family=JetBrains+Mono:wght@400;500&display=swap`

Ripiego se i font non sono disponibili (es. PowerPoint su un PC senza i font): Manrope → Arial Black / Segoe UI Black; Inter → Arial / Segoe UI; JetBrains Mono → Consolas. Quando possibile, incorpora i font.

**Scala web (px):** display 76 · h1 56 · h2 36 · h3 24 · corpo 16 · piccolo 14 · label 13.
**Scala slide (pt):** titolo copertina 54–66 · titolo slide 32–40 · sottotitolo 20–24 · corpo 16–20 (mai sotto 14) · label 11–12.
**Scala documenti (pt):** titolo 26 · H1 18 · H2 14 · corpo 11 · note 9.

---

## 6. Forme, spaziatura, griglia

- **Raggi degli angoli:** 8 (piccoli elementi, input), 14 (pulsanti, chip), 20 (card, riquadri), 28 (contenitori grandi, app icon proporzionale).
- **Spaziatura:** base 8 → 4, 8, 12, 16, 24, 32, 48, 64, 96.
- **Linee:** 1 px Nebbia su chiaro, 1 px `#2A2B2E` su scuro.
- **Stile generale:** forme piene e geometriche, superfici piatte. Niente ombre pesanti (al massimo un'ombra morbida molto leggera sulle card in UI), niente gradienti, niente glassmorphism, niente emoji.
- **Icone:** stile a linea, tratto 2 px, estremità arrotondate (es. Lucide). Colore Inchiostro o Blu Elettrico; rosso solo per gli stati di allarme.

---

## 7. Pattern e sfondi

### Pattern (`assets/pattern/`)
| File | Aspetto | Uso |
|---|---|---|
| `onde-concentriche.svg` | Cerchi bianchi su blu, dal basso, come un segnale che si propaga | Copertine, slide di sezione, intro dei video |
| `segnale-ripetuto.svg` | Piccoli doppi archi blu su Carta | Fondi decorativi chiari, bordi di pagina, packaging |
| `monogramma-inchiostro.svg` | Simbolo bianco ripetuto e sfalsato su Inchiostro | Slide di chiusura, retro dei biglietti, schermate di caricamento |
| `tono-su-tono.svg` | Simbolo Nebbia su Carta | Fondo discreto per documenti e moduli |

Non mettere testo lungo sopra i pattern: sopra un pattern vanno al massimo titolo e logo, su un riquadro pieno se serve leggibilità.

### Sfondi predefiniti
1. **Blu:** fondo Blu Elettrico, simbolo bianco gigante tagliato in un angolo con opacità 14%, testo bianco. Per copertine, slide e web.
2. **Carta:** fondo Carta con righe orizzontali Nebbia da 2 px ogni 22 px, logo blu. Per documenti.
3. **Inchiostro:** fondo Inchiostro, logotipo bianco con "ESP" `#6F8BFF`, tagline in label mono. Per chiusure e copertine scure.

---

## 8. Mascotte — Spy

**Spy** è il guardiano del caveau: un buco della serratura vivente con la stessa silhouette del logo, corpo Blu Elettrico, occhi grandi bianchi con pupille Inchiostro, guance rosa tenue e due archi di segnale sopra la testa che reagiscono alle emozioni. Simpatico ma protettivo, mai infantile.

### File attesi in `assets/mascotte/`
Le immagini sono inserite a mano. Usa questi nomi; se un file manca, **non disegnare né generare la mascotte**: usa il simbolo del logo al suo posto.

| File | Posa | Usala per |
|---|---|---|
| `spy-frontale.png` | Frontale, neutra | Presentazione del progetto, pagina "chi siamo", README |
| `spy-saluto.png` | Saluta, archi luminosi | Benvenuto, prima slide, onboarding, messaggio iniziale del bot |
| `spy-chiave.png` | Tiene la chiave | Spiegazione del PIN e dell'apertura, tutorial |
| `spy-accesso-negato.png` | Braccia incrociate, archi rossi | PIN errato, intrusione, errori |
| `spy-accesso-consentito.png` | Salto felice | Apertura riuscita, conferme, esito positivo |
| `spy-standby.png` | Occhi chiusi, archi grigi | Caveau in standby, schermate vuote, caricamento |
| `spy-icona.png` | Solo testa in un quadrato arrotondato | Avatar del bot Telegram, sticker, icone |

Le immagini vanno in PNG con fondo trasparente, almeno 1024 px sul lato lungo.

### Regole d'uso
- Al massimo **una mascotte per schermata o slide**, mai più grande di circa 40% dell'area.
- Non deformarla, non ricolorarla, non ritagliarla in modo da perdere gli archi.
- La mascotte accompagna i contenuti, non li sostituisce: il logo resta sempre presente altrove nella pagina o nella slide.
- Nei documenti tecnici e formali (relazione d'esame, specifiche) usala solo in copertina o non usarla.

---

## 9. Applicazioni

### 9.1 Interfacce (web ESP32, dashboard, pagine, app)
- Importa `tokens/tokens.css` e usa sempre le variabili, non valori scritti a mano.
- **Tema chiaro (predefinito):** fondo Carta, card bianche con bordo 1 px Nebbia e raggio 20, testo Inchiostro.
- **Tema scuro (notte/LCD):** fondo Inchiostro, card `#1A1B1E` con bordo `#2A2B2E`, testo bianco, link `#6F8BFF`.
- **Header:** logo orizzontale a sinistra (altezza 28–32 px), azioni a destra.
- **Pulsanti:** principale con fondo Blu Elettrico e testo bianco Inter 600; secondario con bordo Inchiostro e fondo trasparente; pericoloso con fondo Rosso Allarme e testo bianco, solo per azioni distruttive. Raggio 14, altezza minima 44 px.
- **Stati del caveau** (sempre con colore + icona + testo, mai solo colore):
  - CHIUSO → Inchiostro, icona lucchetto chiuso.
  - APERTO → Blu Elettrico, icona lucchetto aperto.
  - ALLARME / PIN ERRATO → Rosso Allarme, icona di avviso.
  - STANDBY → `#55585C`.
- **Dati dei sensori** (umidità, luce, tentativi) in JetBrains Mono; etichette in label mono maiuscola.
- **Messaggi LCD 16×2:** solo MAIUSCOLO, niente accenti (UMIDITA, non UMIDITÀ), massimo 16 caratteri per riga. Es.: `INESPUGNABILE` / `PIN: ***_`.
- **Bot Telegram:** avatar `app-icon.svg` (o `spy-icona.png`), messaggi brevi nel tono del §1, stati con il testo in grassetto all'inizio ("**Accesso negato.** Foto inviata.").
- Le interfacce devono funzionare anche da telefono (layout responsivo, target di tocco ≥ 44 px).

### 9.2 Presentazioni (PowerPoint / slide)
- Formato **16:9** (13,33 × 7,5 in). Margini 0,6 in. Griglia a 12 colonne.
- Con python-pptx: leggi colori e font da `tokens/tokens.json`; inserisci i loghi convertendo gli SVG in PNG ad alta risoluzione se il software non supporta gli SVG.
- **Layout:**
  1. **Copertina:** fondo Blu Elettrico + pattern `onde-concentriche` dal basso, logo orizzontale su blu, titolo Manrope 800 bianco, sottotitolo Inter. Opzionale: `spy-saluto.png` a destra.
  2. **Sezione:** fondo Inchiostro, numero della sezione in JetBrains Mono `#6F8BFF`, titolo bianco grande.
  3. **Contenuto:** fondo Carta, titolo Inchiostro in alto a sinistra, label mono blu sopra il titolo, massimo 5 punti o un visual principale. Logo piccolo (simbolo blu) in basso a destra.
  4. **Dati/architettura:** fondo bianco, schemi con riquadri a raggio 20, linee Inchiostro 2 px, componenti chiave in blu, solo il punto critico in rosso.
  5. **Chiusura:** fondo `monogramma-inchiostro`, riquadro Inchiostro pieno con logo e contatti, oppure `spy-frontale.png`.
- Una sola idea per slide. Niente clip art, foto generiche, animazioni vistose: al massimo dissolvenze e comparse dal basso di 0,3 s.

### 9.3 Documenti (Word, PDF, relazioni)
- **A4**, margini 2,5 cm. Corpo Inter 11 pt, interlinea 1,5, testo Inchiostro.
- Titoli Manrope 800 (H1 18 pt Inchiostro, H2 14 pt Blu Elettrico). Label e didascalie in JetBrains Mono 9 pt maiuscolo `#55585C`.
- **Copertina:** fondo Blu Elettrico pieno o Carta con `tono-su-tono`, logo orizzontale, titolo, sottotitolo, data e autore.
- **Intestazione:** simbolo blu a sinistra (8 mm) + nome del documento in label mono. **Piè di pagina:** "InESPugnabile · Progetto IoT" a sinistra, numero di pagina a destra.
- **Tabelle:** intestazione Inchiostro con testo bianco, righe alternate bianco/Carta, bordi Nebbia 0,5 pt.
- **Codice:** JetBrains Mono 9,5 pt su fondo Carta, bordo sinistro assente, raggio 8.
- **Box di avviso:** fondo bianco, bordo 1 pt Nebbia, titolo in blu (info) o rosso (attenzione).

### 9.4 Video (reel, demo, presentazione del progetto)
- **Formati:** verticale 1080×1920 (reel, storie), orizzontale 1920×1080 (demo, presentazione). 30 fps.
- **Zone sicure** nel verticale: lascia libero il 12% in alto e il 18% in basso (interfaccia dei social).
- **Intro (1,5–2 s):** fondo Blu Elettrico; appare la serratura (scala da 90% a 100%, 0,3 s), poi l'arco interno e subito dopo quello esterno (0,15 s ciascuno, come un segnale che parte), poi entra il logotipo bianco. Easing morbido (ease-out), nessun rimbalzo eccessivo.
- **Sottotitoli:** Inter 600, bianco su riquadro Inchiostro all'85% con raggio 14, oppure Inchiostro su riquadro bianco. Massimo 2 righe, parole chiave in Blu Elettrico (`#6F8BFF` su scuro).
- **Titoli in sovrimpressione:** Manrope 800, label mono sopra il titolo.
- **Cambi scena:** tagli netti oppure il pattern `onde-concentriche` che si espande dal basso (0,4 s).
- **Stati del caveau nel video:** quando il caveau si apre usa un lampo blu sul bordo; quando c'è un PIN errato un lampo rosso breve (0,2 s), mai lampeggiante più di 2 volte.
- **Mascotte:** solo in intro o outro, oppure per reagire a un evento (accesso consentito / negato) con l'immagine corrispondente del §8.
- **Outro (2–3 s):** fondo Inchiostro, logo orizzontale negativo al centro, tagline "Il caveau connesso." in label mono sotto.
- Con Remotion o ffmpeg leggi colori e font da `tokens/tokens.json`. Per la qualità in H.264 usa `-preset veryfast` salvo richieste diverse.

---

## 10. Checklist prima di consegnare

- [ ] Il logo è uno dei file in `assets/logo/`, non è deformato e ha l'area di rispetto.
- [ ] "InESPugnabile" è scritto correttamente, con "ESP" evidenziato secondo il fondo.
- [ ] Sono usati solo i colori della palette e il rosso compare solo negli stati di errore/allarme.
- [ ] Font: Manrope 800 per titoli/logo, Inter per testo, JetBrains Mono per dati e label.
- [ ] Ogni testo ha un contrasto di almeno 4,5:1 (3:1 sopra i 24 px).
- [ ] Niente gradienti, ombre pesanti, emoji o effetti 3D.
- [ ] La mascotte compare solo se il file esiste in `assets/mascotte/`, al massimo una per schermata.
- [ ] Tono di voce: frasi brevi, si dà del tu, italiano corretto.
