# Stampa — Monolite (proposta A)

Cassaforte stampabile in 3D, versione **Monolite**: corpo nero, porta bianca a battente aperta dallo
stepper, simbolo nero centrato sulla porta, fascia comandi fissa in alto con semaforo, display, buzzer,
PIR e tastierino. Alimentata a batteria 9V. L'elenco dei componenti con foto e funzione è in
[`../hardware/componenti.html`](../hardware/componenti.html). Le proposte di partenza sono in
[`proposte-modello-3d.html`](proposte-modello-3d.html).

Questa è la **prima versione (v1)**: è completa e passa i controlli di collisione, ma le quote dei
componenti sono nominali. Prima di stampare il corpo vanno misurati i pezzi veri (vedi
[Da misurare col calibro](#da-misurare-col-calibro)).

## Rigenerare il modello

Tutto il modello nasce da uno script parametrico: ogni quota è una variabile in cima al file.

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --python stampa/cad/genera_monolite.py
```

Lo script produce:

| File | Cosa contiene |
|---|---|
| `cad/monolite.blend` | Modello assemblato, con i componenti elettronici di riferimento |
| `stl/*.stl` | Una parte per file, già orientata per la stampa |
| `cad/render/*.png` | Render di controllo (assemblato, fronte, porta aperta, sezione, retro, esploso) |

In console stampa anche un **controllo collisioni**: per ogni coppia di parti calcola il volume che
si sovrappone, e controlla la porta aperta a 0°, 20°, 45°, 70° e 90°. Tutte le righe devono dire `OK`.

## Parti

Ogni parte è di un solo colore: niente stampa multimateriale. I grammi sono stimati dallo script
(2 perimetri, strati pieni, riempimento 15%): lo slicer darà il valore esatto.

| Parte | Colore | Ingombro di stampa (mm) | Sul piatto | Grammi stimati |
|---|---|---|---|---|
| `corpo` | nero | 180 × 210 × 150 | faccia frontale | 336 g |
| `paratia` | nero | 176 × 206 × 50 | lato caveau | 78 g |
| `coperchio_posteriore` | nero | 176 × 206 × 7 | faccia esterna | 53 g |
| `porta` | bianco | 146 × 100 × 33 | faccia frontale | 52 g |
| `pannello_interfaccia` | nero | 146 × 89 × 17 | faccia frontale | 33 g |
| `staffa_stepper` | nero | 37 × 38 × 21 | capovolta | 10 g |
| `simbolo` | nero | 32 × 40 × 4 | piastrina, rilievi in alto | 3 g |
| `sportello_batteria` | nero | 54 × 21 × 1,6 | faccia esterna | 2 g |
| `chiavistello` | nero | 27 × 12 × 4 | piatto | 1 g |

Totale circa **565 g** (606 g con brim, supporti e scarti): 515 g di nero e 52 g di bianco.

**Supporti:** servono solo sotto la faccia frontale della colonna del servo, dentro il corpo (un
piano di 15 × 45 mm a 32 mm dal piatto). Il resto si stampa senza supporti.

## Costo

Con PLA a circa 20 €/kg il materiale usato costa **circa 12 €** (da 9 a 15 € tra marche economiche e
di fascia alta). La corrente aggiunge circa 1 € per 15–30 ore di stampa, secondo la stampante.

La spesa vera dipende dalle bobine che dovete comprare, perché si comprano intere:

| Scelta | Bobine | Spesa iniziale indicativa |
|---|---|---|
| Nero + bianco (scelta attuale, simbolo nero) | 2 | circa 40 € |
| Nero da 1 kg + bianco in bobina piccola da 250 g | 2 | circa 30 € |
| Con il simbolo blu (`SIMBOLO_COLORE = "blu"`) | 3 | circa 55–60 € |

Il simbolo nero su porta bianca è la variante monocroma del brand (`logo-inchiostro`). Le bobine
avanzano per i provini e per ristampare i pezzi piccoli.

### Cosa è stato alleggerito

Rispetto alla v1 (circa 645 g) il modello pesa il 15% in meno:

- pareti del corpo da 1,6 mm (4 linee con ugello da 0,4), fondo da 2 mm, soffitto del caveau da 2 mm;
- profondità da 170 a 150 mm: il caveau resta profondo circa 80 mm e largo 172 mm all'interno;
- porta con pelle e pareti da 1,6 mm e nervature meno profonde;
- paratia da 1,6 mm, ingrossata solo attorno al DHT22;
- coperchio posteriore da 1,6 mm con 36 feritoie, che ventilano anche il vano;
- porta più bassa (96 mm) per far posto a tastierino e PIR nella fascia, senza allungare la scatola;
- colonna del servo solo attorno al servo, con una canalina per il cavo.

Altre leve, se serve risparmiare ancora: una versione più piccola in larghezza e altezza (circa 160 × 190)
toglierebbe altri 60–70 g, ma riduce il caveau. Le misure sono parametri (`W`, `H`, `D`) ma alcune
posizioni interne vanno ricalcolate.

## Viteria

Un solo formato, **M3**:

- 6 viti M3 × 10 a testa cilindrica (ISO 4762): 4 sul coperchio posteriore, 2 sulla staffa dello stepper;
- 6 dadi M3, inseriti di lato in sedi esagonali stampate.

Lo sportello della batteria si toglie senza attrezzi: entra a scatto e si apre con l'unghia.

Tutto il resto si monta senza viti: pannello a scatto, schedine su pioli stampati, simbolo inserito da dietro nella
porta, servo in una slitta a T, ESP32 su breadboard (adesivo) e driver su pioli, paratia tenuta dalle
colonnine del coperchio. Le viti fornite con servo e display non servono.

## Fronte

Il pannello interfaccia (146 × 88 mm) è diviso in due colonne:

- **sinistra**, dall'alto: il modulo semaforo con le icone incise sopra i LED; il display OLED accanto alla
  griglia ad archi del buzzer; in basso la cupola del PIR;
- **destra**, lo spazio piano per il tastierino a membrana 4×4 adesivo (69 × 77 mm). Il flat passa in
  un'asola nascosta sotto il bordo basso del tastierino.

| LED | Icona | Significato |
|---|---|---|
| Verde | lucchetto aperto | cassaforte aperta |
| Giallo | ingranaggio | si sta aprendo, oppure problema meccanico |
| Rosso | lucchetto chiuso | cassaforte chiusa |

Il modulo semaforo ha i LED in ordine rosso, giallo, verde: va montato **ruotato di 180°** (connettore a
sinistra, visto da davanti) per leggere verde, giallo, rosso. I LED sporgono dal pannello di circa 3 mm.

Il caveau è largo 172 mm, profondo circa 80 mm e alto circa 100 mm (apertura della porta 96 mm).

## Dove va ogni componente

| Componente | Posizione |
|---|---|
| Modulo semaforo | Pannello in alto a sinistra, su 2 distanziali con piolo |
| OLED 0,96" | Pannello, colonna sinistra, finestra 24 × 13 mm, PCB su 4 pioli |
| Buzzer Ø12 | Pannello, dietro la griglia ad archi accanto al display |
| PIR HC-SR501 | Pannello in basso a sinistra: cupola nel foro Ø23,5, scheda su 2 distanziali |
| Tastierino 4×4 | Pannello, metà destra; il flat entra nella fascia |
| Stepper 28BYJ-48 | Fascia, in alto a sinistra: il suo albero è l'asse della cerniera |
| Servo SG90 | Colonna nel montante destro del caveau; il chiavistello entra nel riscontro sul retro della porta |
| Sensore Hall HW-484 | Schedina nella culla della fascia; il sensore 49E passa dal foro nel soffitto, con la faccia verso il magnete (a 3–4 mm dal suo bordo) |
| Magnete Ø18 × 4 | Nella porta, angolo in alto a destra, appoggiato alla pelle frontale |
| IR HW-201 n.1 | Fine corsa porta aperta: spalla sinistra, guide verticali dietro la cornice; i LED vanno piegati in avanti dentro i 2 fori inclinati |
| IR HW-201 n.2 | Oggetto nel caveau: paratia in basso, lato vano, LED nei fori verso il caveau (portata sotto i 7 cm) |
| DHT22 | Paratia, con griglia verso il caveau |
| TSL2561 (GY-2561) | Paratia, lato vano, sensore rivolto alla finestra verso il caveau |
| MPU-6050 (GY-521) | Paratia, lato vano, su 2 pioli (rigido col corpo) |
| EVA-ZM1 + HW-131 | Sulla breadboard da 830 punti, in alto sulla paratia; foro nel coperchio davanti all'interruttore dell'HW-131 |
| ULN2003 | Paratia, lato vano, su 4 pioli |
| Batteria 9V | Fondo del vano, su due slitte, dietro lo sportello |
| Pulsante di reset | Sede incassata nel coperchio, si preme con una punta dal foro Ø3,5 |

I cavi non passano mai dalla porta: sulla porta c'è solo il magnete. I cavi della fascia arrivano al
vano dalla finestra in alto nella paratia; quello dell'IR n.1 dal foro in basso a sinistra.

**Batteria:** una 9V alcalina con ESP32 in Wi-Fi, stepper e servo dura poche ore. Nel firmware conviene
togliere corrente alle bobine dello stepper quando è fermo. Il regolatore dell'HW-131 scalda passando
da 9 a 5 V. Con lo stesso vano si può usare una 9V ricaricabile al litio.

## Montaggio

1. Paratia: DHT22, TSL2561, IR n.2, MPU-6050 e ULN2003 nelle loro sedi; breadboard con EVA-ZM1 e HW-131.
2. Servo nella slitta a T dal lato caveau, poi il chiavistello sulla squadretta. Il cavo sale nel canale della colonna.
3. IR n.1 nelle guide della spalla sinistra, LED piegati nei fori inclinati.
4. Porta: magnete nell'anello, simbolo nero inserito da dietro (una goccia di colla se serve).
5. Porta nel vano: il perno inferiore entra nell'asola dal davanti.
6. Stepper dall'alto: l'albero entra nella sede a D della porta. Poi la staffa con 2 viti M3.
7. Sensore Hall nella sua culla, pannello con semaforo, OLED, buzzer e PIR a scatto nel fronte;
   tastierino incollato sul pannello col flat nell'asola.
8. Paratia dal retro contro le battute, cablaggio, coperchio posteriore con 4 viti M3.
9. Batteria sulle slitte, sportello a scatto.

Per togliere il pannello si spingono i 4 ganci dall'interno, passando dal vano posteriore.

## Cosa è cambiato rispetto alla proposta A

- **Fotoresistenza e DHT22 dentro il caveau**, sulla paratia: nessun cavo attraversa la cerniera.
- **Fascia più alta con il tastierino**, porta più bassa; LED verde, giallo, rosso in alto a sinistra.
- **Simbolo nero centrato** sulla porta.
- **Componenti reali:** modulo semaforo al posto dei LED sciolti (niente più pezzo dei diffusori),
  TSL2561 al posto della fotoresistenza, sensore Hall con magnete al posto del contatto MC-38,
  PIR sul fronte, 2 IR, MPU-6050, batteria 9V con sportello, pulsante di reset. L'HC-SR04 non si usa.
- **Paratia alta fino al cielo**, con finestra per i cavi della fascia.
- **Porta 146 mm** (più stretta della bozza): le orecchie dello stepper devono stare dentro la parete.
- **Lato cerniera a spigolo vivo** con smusso a 45° e retro arrotondato. Gli angoli tondi da quel lato
  bloccavano la rotazione; il lato maniglia resta con raggio 8.
- **Apertura massima 90°**: oltre, la porta tocca il telaio. Va impostata come fine corsa nel firmware.
- **Pareti da 1,6 mm** e profondità di 150 mm per risparmiare filamento (vedi [Costo](#costo)).

## Da misurare col calibro

Le quote sono parametri in cima a `cad/genera_monolite.py`. Quelle da verificare per prime:

| Parametro | Cosa misurare | Valore attuale |
|---|---|---|
| `TL_*` | Semaforo: diametro e passo dei LED, scheda, fori della croce | LED Ø8, passo 12, barra 40 × 12,5 |
| `PIR_*` | HC-SR501: scheda, cupola, interasse fori | 32 × 24, Ø23, fori a 28 |
| `MAG_D`, `MAG_T` | Magnete | Ø18 × 4 |
| `HALL_PCB` | Schedina HW-484 | 15 × 36 |
| `IR_PCB`, `IR_LED_DZ` | Schedina HW-201 e distanza dei LED | 31 × 14, LED a ±4 |
| `TSL`, `MPU` | GY-2561 e GY-521, con posizione dei fori | 19 × 13,5 · 21 × 16 |
| `HW_SW` | Posizione dell'interruttore dell'HW-131 vista dal retro | (66, 142) |
| `BB` | Breadboard (830 o 400 punti) | 165 × 55 |
| `RESET_POS` | Pulsante di reset (sede per un 6 × 6) | 6 × 6 |
| `OLED_PCB`, `OLED_HOLES` | Scheda OLED e interasse dei fori | 27,3 × 27,8 · 23,5 × 23,8 |
| `OLED_AA_DZ`, `OLED_PCB_DZ` | Posizione dei pixel e della scheda rispetto al vetro | +2,5 · −0,6 |
| `SV_*`, `ST_*` | Servo e stepper | 22,8 × 12,2 × 22,7 · albero 10 |
| `ULN_HOLES`, `DHT` | Fori del driver, DHT22 | 29,5 × 26,5 · 25,1 × 15,1 × 7,7 |

Prima del corpo conviene stampare dei provini (incastri, sede del dado, gancio del pannello, perno e
asola, sportello della batteria) per tarare i giochi sulla vostra stampante.
