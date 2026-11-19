#Esercitazione IoT 10/11/2026 - Passo 1 (prima versione, con funzioni): fotoresistore

from machine import Pin, ADC
import time

ldr = ADC(Pin(34))
#Crea un ingresso analogico sul pin GPIO34
ldr.atten(ADC.ATTN_11DB)
#Attenuazione 11dB: misura da 0 a ~3.3V
ldr.width(ADC.WIDTH_12BIT)
#Risoluzione 12 bit: valori 0-4095

luce = 0
#Ultimo valore letto dal fotoresistore (0-4095)
t_stampa = time.ticks_ms()
#Istante dell'ultima stampa sul terminale

def leggi_sensori():
    global luce
    luce = ldr.read()
    #read() restituisce un intero tra 0 e 4095

def stampa_valori():
    global t_stampa
    if time.ticks_diff(time.ticks_ms(), t_stampa) >= 1000:
        t_stampa = time.ticks_ms()
        tensione = luce * 3.3 / 4095
        #Riconverte il valore ADC in volt (solo per verifica)
        print("Luce:", luce, " Tensione:", round(tensione, 2), "V")

while True:
    leggi_sensori()
    stampa_valori()
