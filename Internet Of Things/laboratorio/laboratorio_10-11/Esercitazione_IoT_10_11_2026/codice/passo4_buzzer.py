#Esercitazione IoT 10/11/2026 - Passo 4: buzzer passivo
#Parte A: acquisizione dei segnali analogici
#Parte B: controllo automatico del LED
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
        #Sotto questo valore la luminosita' e' "molto bassa"

    def molto_buio(self):
        return self.valore < self.soglia_buio
        #Restituisce True oppure False


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
        #Duty cycle attuale in percentuale (0-100)

    def imposta(self, percentuale):
        if percentuale != self.duty_perc:
            #Esegue il comando solo se il valore e' cambiato
            self.duty_perc = percentuale
            self.pwm.duty(percentuale * 1023 // 100)
            #Converte la percentuale nell'intervallo del PWM (0-1023)

    def __str__(self):
        return "LED: %d%%" % self.duty_perc


class Buzzer:
    #Buzzer passivo comandato in PWM, con sequenze di beep NON bloccanti
    def __init__(self, pin=27, pausa=100):
        self.pwm = PWM(Pin(pin), freq=1000)
        self.pwm.duty(0)
        #All'avvio il buzzer e' muto
        self.pausa = pausa
        #Silenzio tra un beep e l'altro (ms)
        self.freq = 1000
        #Frequenza (nota) del beep in corso (Hz)
        self.durata = 0
        #Durata di ogni beep (ms)
        self.beep_rimanenti = 0
        #Quanti beep mancano: 0 = nessuna sequenza in corso
        self.suono_attivo = False
        #Stato: True = sta suonando, False = e' in pausa
        self.t_inizio = 0
        #Istante in cui e' iniziato il beep o la pausa attuale

    def beep(self, freq, durata, ripetizioni=1):
        #Avvia una sequenza di beep e ritorna subito (non aspetta la fine)
        self.freq = freq
        self.durata = durata
        self.beep_rimanenti = ripetizioni
        self.accendi_suono()

    def accendi_suono(self):
        self.pwm.freq(self.freq)
        self.pwm.duty(512)
        #Duty 50%: onda quadra, volume massimo
        self.suono_attivo = True
        self.t_inizio = time.ticks_ms()

    def spegni_suono(self):
        self.pwm.duty(0)
        self.suono_attivo = False
        self.t_inizio = time.ticks_ms()
        self.beep_rimanenti = self.beep_rimanenti - 1
        #Un beep e' terminato

    def aggiorna(self):
        #Da chiamare a ogni giro del while True: fa avanzare la sequenza
        if self.beep_rimanenti == 0:
            return
            #Nessuna sequenza in corso: non c'e' niente da fare
        trascorso = time.ticks_diff(time.ticks_ms(), self.t_inizio)
        if self.suono_attivo:
            if trascorso >= self.durata:
                self.spegni_suono()
        else:
            if trascorso >= self.pausa:
                self.accendi_suono()

    def occupato(self):
        return self.beep_rimanenti > 0

#================ OGGETTI ================

ldr = Fotoresistore(34, 500)
pot = Potenziometro(35)
led = Led(23, 5000)
buzzer = Buzzer(27)

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

def gestisci_buzzer():
    global buio_in_corso, t_buio, allarme_emesso
    if ldr.molto_buio():
        if not buio_in_corso:
            #Inizia un nuovo episodio di buio
            buio_in_corso = True
            t_buio = time.ticks_ms()
            allarme_emesso = False
        elif not allarme_emesso:
            if time.ticks_diff(time.ticks_ms(), t_buio) >= 5000:
                #Buio da almeno 5 secondi consecutivi
                buzzer.beep(800, 150, 3)
                allarme_emesso = True
                print("ALLARME: luminosita' molto bassa da 5 secondi")
    else:
        buio_in_corso = False
        #La luce e' tornata: l'episodio e' finito
    buzzer.aggiorna()
    #Fa avanzare l'eventuale sequenza di beep in corso

def stampa_valori():
    global t_stampa
    if time.ticks_diff(time.ticks_ms(), t_stampa) >= 1000:
        t_stampa = time.ticks_ms()
        print(ldr, " | ", pot, " | ", led)

#================ PROGRAMMA PRINCIPALE ================

print("Sistema avviato")
buzzer.beep(1000, 200)
#Beep di avvio: 1000 Hz per 200 ms

while True:
    leggi_sensori()
    controlla_led()
    gestisci_buzzer()
    stampa_valori()
