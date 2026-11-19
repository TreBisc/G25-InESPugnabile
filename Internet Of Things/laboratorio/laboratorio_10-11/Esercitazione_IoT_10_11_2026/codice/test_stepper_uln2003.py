#Lab IoT 10/11/2026 - Prova dei collegamenti: ESP32 + MB102 + ULN2003 + 28BYJ-48
#512 half-step in senso orario, 1 s di pausa, 512 in senso antiorario... senza bloccare il loop

from machine import Pin
import time

class Stepper:
    #Motore 28BYJ-48 con driver ULN2003, pilotato in half-step, NON bloccante
    SEQUENZA = [
        [1, 0, 0, 0],
        [1, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 1, 0],
        [0, 0, 1, 1],
        [0, 0, 0, 1],
        [1, 0, 0, 1],
    ]

    def __init__(self, in1=32, in2=33, in3=25, in4=26, intervallo=2):
        self.bobine = [Pin(in1, Pin.OUT), Pin(in2, Pin.OUT),
                       Pin(in3, Pin.OUT), Pin(in4, Pin.OUT)]
        self.intervallo = intervallo
        #Tempo tra un half-step e il successivo (ms)
        self.fase = 0
        self.posizione = 0
        #Posizione ATTUALE in half-step (+ = orario, - = antiorario)
        self.obiettivo = 0
        #Posizione RICHIESTA
        self.t_ultimo = time.ticks_ms()
        self.spegni_bobine()

    def ruota(self, passi):
        self.obiettivo = self.obiettivo + passi

    def in_movimento(self):
        return self.posizione != self.obiettivo

    def scrivi_fase(self):
        valori = Stepper.SEQUENZA[self.fase]
        for i in range(4):
            self.bobine[i].value(valori[i])

    def spegni_bobine(self):
        for bobina in self.bobine:
            bobina.value(0)

    def aggiorna(self):
        if self.posizione == self.obiettivo:
            return
        if time.ticks_diff(time.ticks_ms(), self.t_ultimo) < self.intervallo:
            return
        self.t_ultimo = time.ticks_ms()
        if self.obiettivo > self.posizione:
            direzione = 1
        else:
            direzione = -1
        self.fase = (self.fase + direzione) % 8
        self.scrivi_fase()
        self.posizione = self.posizione + direzione
        if self.posizione == self.obiettivo:
            self.spegni_bobine()

    def __str__(self):
        if self.in_movimento():
            return "Stepper: %d -> %d" % (self.posizione, self.obiettivo)
        return "Stepper: %d" % self.posizione


stepper = Stepper(32, 33, 25, 26)

verso = 1
#1 = prossimo movimento orario, -1 = antiorario
t_fermo = time.ticks_ms()
#Da quando il motore e' fermo
t_stampa = time.ticks_ms()

def controlla_stepper():
    global verso, t_fermo
    if stepper.in_movimento():
        t_fermo = time.ticks_ms()
    elif time.ticks_diff(time.ticks_ms(), t_fermo) >= 1000:
        stepper.ruota(512 * verso)
        #Fermo da 1 s: parte il prossimo movimento
        verso = -verso
    stepper.aggiorna()

def stampa_valori():
    global t_stampa
    if time.ticks_diff(time.ticks_ms(), t_stampa) >= 1000:
        t_stampa = time.ticks_ms()
        print(stepper)

print("Prova stepper avviata")
while True:
    controlla_stepper()
    stampa_valori()
