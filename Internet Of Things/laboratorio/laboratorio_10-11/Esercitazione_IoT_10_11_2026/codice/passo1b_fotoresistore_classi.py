#Esercitazione IoT 10/11/2026 - Passo 1: fotoresistore (versione a classi)

from machine import Pin, ADC
import time

#================ CLASSI DEI COMPONENTI ================

class Fotoresistore:
    def __init__(self, pin=34):
        self.adc = ADC(Pin(pin))
        #Crea l'ingresso analogico sul pin indicato
        self.adc.atten(ADC.ATTN_11DB)
        #Attenuazione 11dB: misura da 0 a ~3.3V
        self.adc.width(ADC.WIDTH_12BIT)
        #Risoluzione 12 bit: valori 0-4095
        self.valore = 0
        #Ultimo valore letto

    def leggi(self):
        self.valore = self.adc.read()
        #Legge l'ADC e salva il risultato nell'oggetto
        return self.valore

    def tensione(self):
        return self.valore * 3.3 / 4095
        #Riconverte il valore ADC in volt

    def __str__(self):
        return "Luce: %d  Tensione: %.2f V" % (self.valore, self.tensione())
        #Testo stampato quando si fa print(oggetto)

#================ OGGETTI ================

ldr = Fotoresistore(34)

#================ VARIABILI GLOBALI ================

t_stampa = time.ticks_ms()
#Istante dell'ultima stampa sul terminale

#================ FUNZIONI DEL PROGRAMMA ================

def leggi_sensori():
    ldr.leggi()

def stampa_valori():
    global t_stampa
    if time.ticks_diff(time.ticks_ms(), t_stampa) >= 1000:
        t_stampa = time.ticks_ms()
        print(ldr)

#================ PROGRAMMA PRINCIPALE ================

while True:
    leggi_sensori()
    stampa_valori()
