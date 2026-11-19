from machine import Pin, disable_irq, enable_irq
import time

led_blue = Pin(25, Pin.OUT)
led_green = Pin(26, Pin.OUT)
led_red = Pin(27, Pin.OUT)
button = Pin(14, Pin.IN, Pin.PULL_UP)

DEBOUNCE_MS = 50        # pressioni più vicine di 50 ms sono rimbalzi
DOUBLE_CLICK_MS = 500   # finestra per riconoscere il doppio clic
NORMAL_DELAY_MS = 2000  # carica normale: un LED ogni 2 s
FAST_DELAY_MS = 1000    # carica rapida: un LED ogni 1 s

charging = False
step_delay = NORMAL_DELAY_MS
level = 0               # quanti LED sono accesi (0..3)
last_step = 0           # quando si è acceso l'ultimo LED

# Variabili scritte dall'interrupt
press_count = 0         # pressioni valide nella finestra corrente
first_press = 0         # tempo della prima pressione della finestra
last_press = 0          # tempo dell'ultima pressione valida (debounce)


def set_leds(n):
    led_blue.value(1 if n >= 1 else 0)
    led_green.value(1 if n >= 2 else 0)
    led_red.value(1 if n >= 3 else 0)


# Interrupt del pulsante: conta solo le pressioni, non decide nulla
def button_pressed(pin):
    global press_count, first_press, last_press

    # Con PULL_UP premuto = 0: se il pin è già a 1 è un rimbalzo del rilascio.
    if pin.value() == 1:
        return

    # Debounce: ignora le pressioni troppo vicine all'ultima valida.
    now = time.ticks_ms()
    if time.ticks_diff(now, last_press) < DEBOUNCE_MS:
        return
    last_press = now

    if press_count == 0:
        first_press = now   # inizia la finestra del doppio clic
    press_count += 1


def start_charging(delay):
    global charging, step_delay, level, last_step
    if not charging:
        level = 1           # alla partenza si accende subito il blu
    charging = True
    step_delay = delay      # se era già in carica cambia solo la velocità
    last_step = time.ticks_ms()
    set_leds(level)


def stop_charging():
    global charging, level
    charging = False
    level = 0
    set_leds(0)


button.irq(trigger=Pin.IRQ_FALLING, handler=button_pressed)
set_leds(0)

while True:
    now = time.ticks_ms()

    # 1) Clic singolo o doppio?
    #    Doppio: la seconda pressione arriva entro 500 ms (si decide subito).
    #    Singolo: passano 500 ms senza una seconda pressione.
    if press_count >= 2 or (press_count == 1 and time.ticks_diff(now, first_press) > DOUBLE_CLICK_MS):
        state = disable_irq()   # legge e azzera il contatore senza interruzioni
        clicks = press_count
        press_count = 0
        enable_irq(state)

        if clicks >= 2:
            start_charging(FAST_DELAY_MS)
            print("Doppio clic: carica rapida (1 s per LED)")
        elif charging:
            stop_charging()
            print("Clic singolo: carica fermata")
        else:
            start_charging(NORMAL_DELAY_MS)
            print("Clic singolo: carica normale (2 s per LED)")

    # 2) Avanza la carica senza bloccare il programma
    if charging and level < 3 and time.ticks_diff(now, last_step) >= step_delay:
        level += 1
        last_step = now
        set_leds(level)
        if level == 3:
            print("Carica completa")

    time.sleep_ms(10)
