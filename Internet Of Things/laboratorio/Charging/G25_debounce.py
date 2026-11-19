from machine import Pin
import time

led_blue = Pin(25, Pin.OUT)
led_green = Pin(26, Pin.OUT)
led_red = Pin(27, Pin.OUT)
button = Pin(14, Pin.IN, Pin.PULL_UP)

charging = False
level = 0

# Debounce: memorizza il tempo (in ms) dell'ultima pressione valida.
last_press = 0

led_blue.value(0)
led_green.value(0)
led_red.value(0)

# Interrupt del pulsante: avvia o ferma la carica
def toggle_charging(pin):
    global charging
    global last_press

    # Con PULL_UP premuto = 0: se il pin è già tornato a 1 è un rimbalzo del rilascio.
    if pin.value() == 1:
        return

    # Debounce: ignora le pressioni arrivate meno di 200 ms dopo l'ultima valida.
    time_ms = time.ticks_ms()
    delay = time.ticks_diff(time_ms, last_press)
    if delay < 200:
        return

    last_press = time_ms
    charging = not charging   # inverte lo stato: avvia / ferma la carica

button.irq(trigger=Pin.IRQ_FALLING, handler=toggle_charging)

while True:
    # Simulazione della carica
    if charging == True:
        if level < 100:
            level = level + 1

        if level <= 33:
            led_blue.value(1)
        elif level <= 66:
            led_blue.value(1)
            led_green.value(1)
        else:
            led_blue.value(1)
            led_green.value(1)
            led_red.value(1)
    else:
        # Carica ferma: azzera il livello e spegne i LED
        level = 0
        led_blue.value(0)
        led_green.value(0)
        led_red.value(0)

    time.sleep(0.1)
