from machine import Pin
import time

led_blue = Pin(25, Pin.OUT)
led_green = Pin(26, Pin.OUT)
led_red = Pin(27, Pin.OUT)
button = Pin(14, Pin.IN, Pin.PULL_UP)

charging = False
level = 0

led_blue.value(0)
led_green.value(0)
led_red.value(0)

while True:
    # Pulsante premuto (con PULL_UP: premuto = 0)
    if button.value() == 0:
        time.sleep(0.3)
        # aspetta che il pulsante venga rilasciato
        while button.value() == 0:
            time.sleep(0.1)

        if charging == False:
            charging = True
        else:
            charging = False
            level = 0
            led_blue.value(0)
            led_green.value(0)
            led_red.value(0)

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

    time.sleep(0.1)