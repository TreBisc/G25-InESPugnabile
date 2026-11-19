#Esercitazione IoT 10/11/2026
#Sistema intelligente di controllo ambientale e movimentazione

from machine import Pin, ADC, PWM
import time

#================ CLASSI DEI COMPONENTI ================

class SensoreAnalogico:
    def __init__(self, pin, nome="Sensore"):
        self.adc = ADC(Pin(pin))
        self.adc.atten(ADC.ATTN_11DB)
        self.adc.width(ADC.WIDTH_12BIT)
        self.nome = nome
        self.valore = 0

    def leggi(self):
        self.valore = self.adc.read()
        return self.valore

    def mappa(self, minimo, massimo):
        return minimo + self.valore * (massimo - minimo) // 4095

    def __str__(self):
        return "%s: %d" % (self.nome, self.valore)


class Fotoresistore(SensoreAnalogico):
    def __init__(self, pin=34, soglia_buio=500):
        super().__init__(pin, "Luce")
        self.soglia_buio = soglia_buio

    def molto_buio(self):
        return self.valore < self.soglia_buio


class Potenziometro(SensoreAnalogico):
    def __init__(self, pin=35, soglia_min=1000, soglia_max=3000):
        super().__init__(pin, "Pot")
        self.soglia_min = soglia_min
        self.soglia_max = soglia_max
        self.soglia = soglia_min

    def leggi(self):
        super().leggi()
        self.soglia = self.mappa(self.soglia_min, self.soglia_max)
        return self.valore

    def __str__(self):
        return super().__str__() + "  Soglia: %d" % self.soglia


class Led:
    def __init__(self, pin=23, freq=5000):
        self.pwm = PWM(Pin(pin), freq=freq)
        self.pwm.duty(0)
        self.duty_perc = 0

    def imposta(self, percentuale):
        if percentuale != self.duty_perc:
            self.duty_perc = percentuale
            self.pwm.duty(percentuale * 1023 // 100)
            #Conversione percentuale -> intervallo PWM 0-1023

    def __str__(self):
        return "LED: %d%%" % self.duty_perc


class Buzzer:
    #Sequenze di beep non bloccanti
    def __init__(self, pin=27, pausa=100):
        self.pwm = PWM(Pin(pin), freq=1000)
        self.pwm.duty(0)
        self.pausa = pausa
        self.freq = 1000
        self.durata = 0
        self.beep_rimanenti = 0
        self.suono_attivo = False
        self.t_inizio = 0

    def beep(self, freq, durata, ripetizioni=1):
        self.freq = freq
        self.durata = durata
        self.beep_rimanenti = ripetizioni
        self.accendi_suono()

    def accendi_suono(self):
        self.pwm.freq(self.freq)
        self.pwm.duty(512)
        self.suono_attivo = True
        self.t_inizio = time.ticks_ms()

    def spegni_suono(self):
        self.pwm.duty(0)
        self.suono_attivo = False
        self.t_inizio = time.ticks_ms()
        self.beep_rimanenti = self.beep_rimanenti - 1

    def aggiorna(self):
        if self.beep_rimanenti == 0:
            return
        trascorso = time.ticks_diff(time.ticks_ms(), self.t_inizio)
        if self.suono_attivo:
            if trascorso >= self.durata:
                self.spegni_suono()
        else:
            if trascorso >= self.pausa:
                self.accendi_suono()


class Servo:
    #Movimento graduale di 5 gradi alla volta, non bloccante
    def __init__(self, pin=18, passo=5, intervallo=30, duty_min=26, duty_max=128):
        self.pwm = PWM(Pin(pin), freq=50)
        self.passo = passo
        self.intervallo = intervallo
        self.duty_min = duty_min
        self.duty_max = duty_max
        self.angolo = 0
        self.obiettivo = 0
        self.t_ultimo = time.ticks_ms()
        self.scrivi_angolo(0)

    def scrivi_angolo(self, angolo):
        self.pwm.duty(self.duty_min + angolo * (self.duty_max - self.duty_min) // 180)

    def vai_a(self, angolo):
        self.obiettivo = angolo

    def aggiorna(self):
        if self.angolo == self.obiettivo:
            return
        if time.ticks_diff(time.ticks_ms(), self.t_ultimo) < self.intervallo:
            return
        self.t_ultimo = time.ticks_ms()
        if self.angolo < self.obiettivo:
            self.angolo = min(self.angolo + self.passo, self.obiettivo)
        else:
            self.angolo = max(self.angolo - self.passo, self.obiettivo)
        self.scrivi_angolo(self.angolo)

    def __str__(self):
        return "Servo: %d gradi" % self.angolo


class Stepper:
    #28BYJ-48 + ULN2003 in half-step: un passo per volta, non bloccante
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
        self.fase = 0
        self.posizione = 0
        self.obiettivo = 0
        self.t_ultimo = time.ticks_ms()
        self.spegni_bobine()

    def ruota(self, passi):
        #passi > 0 orario, passi < 0 antiorario
        self.obiettivo = self.obiettivo + passi

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
        return "Stepper: %d" % self.posizione


class Pulsante:
    #Pull-down interno, debouncing non bloccante
    def __init__(self, pin=14, debounce=50):
        self.pin = Pin(pin, Pin.IN, Pin.PULL_DOWN)
        self.debounce = debounce
        self.ultima_lettura = 0
        self.stato_stabile = 0
        self.t_cambio = time.ticks_ms()
        self.pressione = False

    def aggiorna(self):
        lettura = self.pin.value()
        if lettura != self.ultima_lettura:
            self.ultima_lettura = lettura
            self.t_cambio = time.ticks_ms()
        elif lettura != self.stato_stabile:
            if time.ticks_diff(time.ticks_ms(), self.t_cambio) >= self.debounce:
                self.stato_stabile = lettura
                if lettura == 1:
                    self.pressione = True

    def premuto(self):
        if self.pressione:
            self.pressione = False
            return True
        return False

#================ OGGETTI ================

ldr = Fotoresistore(34, 500)
pot = Potenziometro(35)
led = Led(23, 5000)
buzzer = Buzzer(27)
servo = Servo(18)
stepper = Stepper(32, 33, 25, 26)
pulsante = Pulsante(14)

#================ VARIABILI GLOBALI ================

AUTO = "AUTO"
MANUAL = "MANUAL"
modalita = AUTO

t_stampa = time.ticks_ms()

buio_in_corso = False
t_buio = 0
allarme_emesso = False

ISTERESI = 30
stato_stepper = "LUCE"

#================ FUNZIONI DEL PROGRAMMA ================

def leggi_sensori():
    ldr.leggi()
    pot.leggi()

def condizione_luce():
    if ldr.valore < pot.soglia:
        return "BUIO"
    return "LUCE"

def entra_in_manual():
    global modalita
    modalita = MANUAL
    servo.vai_a(90)
    stepper.ruota(256)
    buzzer.beep(2000, 300)
    print(">>> Modalita' MANUAL")

def entra_in_auto():
    global modalita, stato_stepper
    modalita = AUTO
    stato_stepper = condizione_luce()
    buzzer.beep(1500, 100, 2)
    print(">>> Modalita' AUTO")

def gestisci_pulsante():
    pulsante.aggiorna()
    if pulsante.premuto():
        if modalita == AUTO:
            entra_in_manual()
        else:
            entra_in_auto()

def controlla_led():
    if modalita == MANUAL:
        led.imposta(pot.mappa(0, 100))
        return
    differenza = pot.soglia - ldr.valore
    if differenza > 800:
        led.imposta(100)
    elif differenza >= 400:
        led.imposta(70)
    elif differenza >= 100:
        led.imposta(30)
    else:
        led.imposta(0)

def controlla_servo():
    if modalita == AUTO:
        if ldr.valore < pot.soglia:
            servo.vai_a(0)
        elif ldr.valore <= pot.soglia + 500:
            servo.vai_a(45)
        else:
            servo.vai_a(90)
    servo.aggiorna()

def controlla_stepper():
    global stato_stepper
    if modalita == AUTO:
        if stato_stepper == "LUCE" and ldr.valore < pot.soglia - ISTERESI:
            stato_stepper = "BUIO"
            stepper.ruota(512)
        elif stato_stepper == "BUIO" and ldr.valore > pot.soglia + ISTERESI:
            stato_stepper = "LUCE"
            stepper.ruota(-512)
    stepper.aggiorna()

def gestisci_buzzer():
    global buio_in_corso, t_buio, allarme_emesso
    if ldr.molto_buio():
        if not buio_in_corso:
            buio_in_corso = True
            t_buio = time.ticks_ms()
            allarme_emesso = False
        elif not allarme_emesso and time.ticks_diff(time.ticks_ms(), t_buio) >= 5000:
            buzzer.beep(800, 150, 3)
            allarme_emesso = True
            print("ALLARME: luminosita' molto bassa")
    else:
        buio_in_corso = False
    buzzer.aggiorna()

def stampa_valori():
    global t_stampa
    if time.ticks_diff(time.ticks_ms(), t_stampa) >= 1000:
        t_stampa = time.ticks_ms()
        print("[%s]" % modalita, ldr, "|", pot, "|", led, "|", servo, "|", stepper)

#================ PROGRAMMA PRINCIPALE ================

print("Sistema avviato")
buzzer.beep(1000, 200)
leggi_sensori()
stato_stepper = condizione_luce()

while True:
    leggi_sensori()
    gestisci_pulsante()
    controlla_led()
    controlla_servo()
    controlla_stepper()
    gestisci_buzzer()
    stampa_valori()
