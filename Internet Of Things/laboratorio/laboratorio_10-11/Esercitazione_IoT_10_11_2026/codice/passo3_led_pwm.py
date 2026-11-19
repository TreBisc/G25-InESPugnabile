#Esercitazione IoT 10/11/2026 - Passo 3: LED con PWM
#Parte A: acquisizione dei segnali analogici
#Parte B: controllo automatico del LED

from machine import Pin, ADC, PWM
import time

#================ CLASSI DEI COMPONENTI ================

class SensoreAnalogico:
    #Classe base (superclasse): tutto cio' che e' comune ai sensori letti con l'ADC
    def __init__(self, pin, nome="Sensore"):
        self.adc = ADC(Pin(pin))
        #Crea l'ingresso analogico sul pin indicato
        self.adc.atten(ADC.ATTN_11DB)
        #Attenuazione 11dB: misura da 0 a ~3.3V
        self.adc.width(ADC.WIDTH_12BIT)
        #Risoluzione 12 bit: valori 0-4095
        self.nome = nome
        self.valore = 0
        #Ultimo valore letto (0-4095)

    def leggi(self):
        self.valore = self.adc.read()
        return self.valore

    def tensione(self):
        return self.valore * 3.3 / 4095

    def mappa(self, minimo, massimo):
        return minimo + self.valore * (massimo - minimo) // 4095
        #Porta il valore dall'intervallo 0-4095 all'intervallo minimo-massimo

    def __str__(self):
        return "%s: %d (%.2f V)" % (self.nome, self.valore, self.tensione())


class Fotoresistore(SensoreAnalogico):
    def __init__(self, pin=34):
        super().__init__(pin, "Luce")


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
        #Crea il PWM sul pin indicato alla frequenza indicata (5000 Hz)
        self.pwm.duty(0)
        #All'avvio il LED e' spento
        self.duty_perc = 0
        #Duty cycle attuale in percentuale (0-100): memorizza lo stato

    def imposta(self, percentuale):
        if percentuale != self.duty_perc:
            #Esegue il comando solo se il valore e' cambiato
            self.duty_perc = percentuale
            self.pwm.duty(percentuale * 1023 // 100)
            #Converte la percentuale nell'intervallo del PWM (0-1023)

    def __str__(self):
        return "LED: %d%%" % self.duty_perc
        #%% stampa il simbolo %

#================ OGGETTI ================

ldr = Fotoresistore(34)
pot = Potenziometro(35)
led = Led(23, 5000)

#================ VARIABILI GLOBALI ================

t_stampa = time.ticks_ms()
#Istante dell'ultima stampa sul terminale

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
        #Luminosita' uguale o superiore alla soglia (o inferiore di meno di 100)

def stampa_valori():
    global t_stampa
    if time.ticks_diff(time.ticks_ms(), t_stampa) >= 1000:
        t_stampa = time.ticks_ms()
        print(ldr, " | ", pot, " | ", led)

#================ PROGRAMMA PRINCIPALE ================

while True:
    leggi_sensori()
    controlla_led()
    stampa_valori()
