#Esercitazione IoT 10/11/2026 - Passo 5: servomotore SG90
#Parte A: acquisizione dei segnali analogici
#Parte B: controllo automatico del LED
#Parte C: controllo del servomotore
#Parte F (in parte): beep di avvio e allarme luminosita' molto bassa

from machine import Pin, ADC, PWM
import time

#================ CLASSI DEI COMPONENTI ================

class SensoreAnalogico:
    #Classe base (superclasse): tutto cio' che e' comune ai sensori letti con l'ADC
    def __init__(self, pin, nome="Sensore"):
        self.adc = ADC(Pin(pin))
        self.adc.atten(ADC.ATTN_11DB)
        #Attenuazione 11dB: misura da 0 a ~3.3V
        self.adc.width(ADC.WIDTH_12BIT)
        #Risoluzione 12 bit: valori 0-4095
        self.nome = nome
        self.valore = 0

    def leggi(self):
        self.valore = self.adc.read()
        return self.valore

    def tensione(self):
        return self.valore * 3.3 / 4095

    def mappa(self, minimo, massimo):
        return minimo + self.valore * (massimo - minimo) // 4095

    def __str__(self):
        return "%s: %d (%.2f V)" % (self.nome, self.valore, self.tensione())


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
    #LED comandato in PWM
    def __init__(self, pin=23, freq=5000):
        self.pwm = PWM(Pin(pin), freq=freq)
        self.pwm.duty(0)
        self.duty_perc = 0

    def imposta(self, percentuale):
        if percentuale != self.duty_perc:
            self.duty_perc = percentuale
            self.pwm.duty(percentuale * 1023 // 100)

    def __str__(self):
        return "LED: %d%%" % self.duty_perc


class Buzzer:
    #Buzzer passivo comandato in PWM, con sequenze di beep NON bloccanti
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

    def occupato(self):
        return self.beep_rimanenti > 0


class Servo:
    #Servomotore SG90 con movimento graduale NON bloccante
    def __init__(self, pin=18, passo=5, intervallo=30, duty_min=26, duty_max=128):
        self.pwm = PWM(Pin(pin), freq=50)
        #Il servo vuole un PWM a 50 Hz (periodo 20 ms)
        self.passo = passo
        #Incremento in gradi a ogni movimento (5 gradi)
        self.intervallo = intervallo
        #Tempo tra un incremento e il successivo (ms)
        self.duty_min = duty_min
        #Duty per 0 gradi   (impulso ~0.5 ms)
        self.duty_max = duty_max
        #Duty per 180 gradi (impulso ~2.5 ms)
        self.angolo = 0
        #Posizione ATTUALE del servo (memorizzata)
        self.obiettivo = 0
        #Posizione RICHIESTA
        self.t_ultimo = time.ticks_ms()
        #Istante dell'ultimo incremento
        self.scrivi_angolo(0)
        #All'avvio il servo si porta a 0 gradi

    def angolo_a_duty(self, angolo):
        return self.duty_min + angolo * (self.duty_max - self.duty_min) // 180
        #Converte l'angolo (0-180) nel duty del PWM (26-128)

    def scrivi_angolo(self, angolo):
        self.pwm.duty(self.angolo_a_duty(angolo))

    def vai_a(self, angolo):
        self.obiettivo = angolo
        #Imposta solo la destinazione: il movimento lo fa aggiorna()

    def in_movimento(self):
        return self.angolo != self.obiettivo

    def aggiorna(self):
        #Da chiamare a ogni giro del while True: muove il servo di un passo alla volta
        if self.angolo == self.obiettivo:
            return
            #Posizione gia' raggiunta: nessun comando
        if time.ticks_diff(time.ticks_ms(), self.t_ultimo) < self.intervallo:
            return
            #Non e' ancora il momento del prossimo passo
        self.t_ultimo = time.ticks_ms()
        if self.angolo < self.obiettivo:
            self.angolo = min(self.angolo + self.passo, self.obiettivo)
            #Sale di 5 gradi senza superare l'obiettivo
        else:
            self.angolo = max(self.angolo - self.passo, self.obiettivo)
            #Scende di 5 gradi senza superare l'obiettivo
        self.scrivi_angolo(self.angolo)

    def __str__(self):
        if self.in_movimento():
            return "Servo: %d gradi -> %d" % (self.angolo, self.obiettivo)
        return "Servo: %d gradi" % self.angolo

#================ OGGETTI ================

ldr = Fotoresistore(34, 500)
pot = Potenziometro(35)
led = Led(23, 5000)
buzzer = Buzzer(27)
servo = Servo(18)

#================ VARIABILI GLOBALI ================

t_stampa = time.ticks_ms()
#Istante dell'ultima stampa sul terminale

buio_in_corso = False
#True se e' in corso un episodio di luminosita' molto bassa
t_buio = 0
#Istante in cui e' iniziato l'episodio di buio
allarme_emesso = False
#True se l'allarme e' gia' stato emesso per questo episodio

#================ FUNZIONI DEL PROGRAMMA ================

def leggi_sensori():
    ldr.leggi()
    pot.leggi()

def controlla_led():
    differenza = pot.soglia - ldr.valore
    #Di quanto la luminosita' e' inferiore alla soglia
    if differenza > 800:
        led.imposta(100)
    elif differenza >= 400:
        led.imposta(70)
    elif differenza >= 100:
        led.imposta(30)
    else:
        led.imposta(0)

def controlla_servo():
    if ldr.valore < pot.soglia:
        servo.vai_a(0)
        #Luminosita' inferiore alla soglia
    elif ldr.valore <= pot.soglia + 500:
        servo.vai_a(45)
        #Luminosita' tra soglia e soglia + 500
    else:
        servo.vai_a(90)
        #Luminosita' superiore a soglia + 500
    servo.aggiorna()
    #Fa avanzare il movimento di un passo, se serve

def gestisci_buzzer():
    global buio_in_corso, t_buio, allarme_emesso
    if ldr.molto_buio():
        if not buio_in_corso:
            buio_in_corso = True
            t_buio = time.ticks_ms()
            allarme_emesso = False
        elif not allarme_emesso:
            if time.ticks_diff(time.ticks_ms(), t_buio) >= 5000:
                buzzer.beep(800, 150, 3)
                allarme_emesso = True
                print("ALLARME: luminosita' molto bassa da 5 secondi")
    else:
        buio_in_corso = False
    buzzer.aggiorna()

def stampa_valori():
    global t_stampa
    if time.ticks_diff(time.ticks_ms(), t_stampa) >= 1000:
        t_stampa = time.ticks_ms()
        print(ldr, " | ", pot, " | ", led, " | ", servo)

#================ PROGRAMMA PRINCIPALE ================

print("Sistema avviato")
buzzer.beep(1000, 200)
#Beep di avvio: 1000 Hz per 200 ms

while True:
    leggi_sensori()
    controlla_led()
    controlla_servo()
    gestisci_buzzer()
    stampa_valori()
