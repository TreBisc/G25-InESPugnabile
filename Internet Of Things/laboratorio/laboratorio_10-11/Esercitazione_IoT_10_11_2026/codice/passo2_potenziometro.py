#Esercitazione IoT 10/11/2026 - Passo 2: fotoresistore + potenziometro
#Parte A: acquisizione dei segnali analogici

from machine import Pin, ADC
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
        #Nome usato nella stampa
        self.valore = 0
        #Ultimo valore letto (0-4095)

    def leggi(self):
        self.valore = self.adc.read()
        return self.valore

    def tensione(self):
        return self.valore * 3.3 / 4095
        #Riconverte il valore ADC in volt

    def mappa(self, minimo, massimo):
        return minimo + self.valore * (massimo - minimo) // 4095
        #Porta il valore dall'intervallo 0-4095 all'intervallo minimo-massimo

    def __str__(self):
        return "%s: %d (%.2f V)" % (self.nome, self.valore, self.tensione())


class Fotoresistore(SensoreAnalogico):
    #Sottoclasse: eredita tutto da SensoreAnalogico
    def __init__(self, pin=34):
        super().__init__(pin, "Luce")
        #Chiama il costruttore della superclasse


class Potenziometro(SensoreAnalogico):
    #Sottoclasse: eredita tutto da SensoreAnalogico e aggiunge la soglia
    def __init__(self, pin=35, soglia_min=1000, soglia_max=3000):
        super().__init__(pin, "Pot")
        self.soglia_min = soglia_min
        self.soglia_max = soglia_max
        self.soglia = soglia_min
        #Soglia attuale, aggiornata a ogni lettura

    def leggi(self):
        #Ridefinisce (override) il metodo leggi() della superclasse
        super().leggi()
        #Prima esegue la lettura normale...
        self.soglia = self.mappa(self.soglia_min, self.soglia_max)
        #...poi calcola la soglia tra 1000 e 3000
        return self.valore

    def __str__(self):
        return super().__str__() + "  Soglia: %d" % self.soglia
        #Aggiunge la soglia al testo della superclasse

#================ OGGETTI ================

ldr = Fotoresistore(34)
pot = Potenziometro(35)

#================ VARIABILI GLOBALI ================

t_stampa = time.ticks_ms()
#Istante dell'ultima stampa sul terminale

#================ FUNZIONI DEL PROGRAMMA ================

def leggi_sensori():
    ldr.leggi()
    pot.leggi()

def stampa_valori():
    global t_stampa
    if time.ticks_diff(time.ticks_ms(), t_stampa) >= 1000:
        t_stampa = time.ticks_ms()
        print(ldr, " | ", pot)

#================ PROGRAMMA PRINCIPALE ================

while True:
    leggi_sensori()
    stampa_valori()
