# pip install pyfirmata2
# En el Arduino: IDE > File > Examples > Firmata > StandardFirmata

import time, math, sys, datetime
from collections import deque
from pyfirmata2 import Arduino

# ===================== Config =====================
PORT = "COM9"     #AUTODETECT            # o "COM3", "/dev/ttyACM0", etc.
board = Arduino(PORT)

# Entradas con callbacks (NO polling):
a_temp = board.get_pin('a:0:i')      # A0: KY-013 (entrada analógica)
btn    = board.get_pin('d:2:i')      # D2: botón (entrada digital, pull-down externo)

# Salidas:
led_g  = board.get_pin('d:11:o')     # Verde  (baja)
led_b  = board.get_pin('d:12:o')     # Azul   (estable)
led_r  = board.get_pin('d:13:o')     # Rojo   (alza)

# Parámetros
VREF = 5.0
ADC_MAX = 1023.0
R_FIXED = 10000.0
N = 5
Xpct = 5.0
BLINK_S = 0.05
MIN_CYCLE_S, MAX_CYCLE_S = 2.5, 10.0
STOP_S = 1.0
DEBOUNCE_RELEASE_S = 0.05

# ==================== pasaje de los datos a un archivo .txt ====================
sys.stdout = open("salida.txt", "w")

# ===================== Estado =====================
buf = deque(maxlen=N)
cycle_s = 3.5
running = True
last_cycle = time.monotonic()
last_hold_blink = last_cycle
t_btn_press = 0.0
t_last_release = 0.0
btn_held = False

a0_val = None    # actualizado por callback de A0
btn_val = 0      # actualizado por callback de D2
last_trend = "INS"  # para restaurar LED tras “todos”

# ===================== Callbacks =====================
def on_btn(value):     # value es 0/1
    global btn_val
    btn_val = 1 if value else 0

def on_a0(value):      # value es float 0..1
    global a0_val
    a0_val = value

# ---------- Inicialización robusta de reporte ----------
# 1) Configurar intervalo de muestreo analógico
try:
    # Algunas versiones de pyFirmata2
    board.samplingInterval(19)  # 19 ms ≈ 52 Hz
except AttributeError:
    try:
        # Otras versiones
        board.samplingOn(19)
    except AttributeError:
        # Si ninguna existe, seguimos igual (el default suele funcionar)
        pass

# 2) Registrar callbacks y habilitar reporting (entradas)
a_temp.register_callback(on_a0)
a_temp.enable_reporting()
btn.register_callback(on_btn)
btn.enable_reporting()

# 3) Esperar a que lleguen valores de A0
print("t(s),tempC,meanN,trend,cycle_s,running")
t0 = time.monotonic()
while a0_val is None and (time.monotonic() - t0) < 5.0:
    time.sleep(0.02)

if a0_val is None:
    print("ADVERTENCIA: No llegan lecturas de A0. Verifica:")
    print(" - Que cargaste StandardFirmata en el Arduino")
    print(" - Cableado del KY-013 (divisor a 5V y GND, señal a A0)")
    print(" - Que el puerto es correcto")
    # seguimos corriendo igual; cuando lleguen lecturas se activará

# ===================== Helpers LEDs =====================
def leds_all_off():
    led_r.write(0); led_b.write(0); led_g.write(0)

def leds_all_on():
    led_r.write(1); led_b.write(1); led_g.write(1)

def restore_trend_led():
    leds_all_off()
    if   last_trend == "ALZ":    led_r.write(1)
    elif last_trend == "EST": led_b.write(1)
    elif last_trend == "BAJ":    led_g.write(1)

def blink_all_then_restore(duration_s):
    leds_all_on()
    time.sleep(duration_s)
    restore_trend_led()

def set_trend_led(tr):
    global last_trend
    last_trend = tr
    leds_all_off()
    if   tr == "ALZ":    led_r.write(1)
    elif tr == "EST": led_b.write(1)
    elif tr == "BAJ":    led_g.write(1)
    # INS => apagado

# ===================== Cálculos =====================
def push_and_mean(x):
    buf.append(x)
    return sum(buf) / len(buf)

def read_temp_c():
    v_ratio = a0_val
    if v_ratio is None:
        return None
    # proteger extremos (evita div/0)
    v_ratio = min(max(v_ratio, 1.0/ADC_MAX), 1.0 - 1.0/ADC_MAX)
    v = v_ratio * VREF
    r_ntc = (v * R_FIXED) / (VREF - v)
    lnR = math.log(r_ntc)
    invT = 0.001129148 + 0.000234125*lnR + 0.0000000876741*(lnR**3)
    return (1.0 / invT) - 273.15

def trend_from(current, meanN):
    if len(buf) < N:
        return "INS"
    up = meanN * (1.0 + Xpct/100.0)
    dn = meanN * (1.0 - Xpct/100.0)
    if current > up: return "ALZ"
    if current < dn: return "BAJ"
    return "EST"

# ===================== Bucle principal =====================
try:
    btn_prev = btn_val
    while True:
        now = time.monotonic()
        fecha = datetime.now()

        # --- Botón (por callbacks) ---
        if btn_val == 1 and btn_prev == 0:     # flanco subida: presionó
            t_btn_press = now
            last_hold_blink = now
            btn_held = True

        if btn_held and (now - last_hold_blink >= 1.0):  # contador de segundos
            blink_all_then_restore(BLINK_S)
            last_hold_blink += 1.0

        if btn_val == 0 and btn_prev == 1:     # flanco bajada: soltó
            btn_held = False
            if now - t_last_release >= DEBOUNCE_RELEASE_S:  # anti-rebote
                held_s = now - t_btn_press
                if held_s < STOP_S:
                    running = False
                    print("STOP_REQUEST -> running=0")
                else:
                    running = True
                    if held_s < MIN_CYCLE_S:
                        cycle_s = MIN_CYCLE_S
                        print(f"NEW_CYCLE_S(min)={cycle_s}")
                    else:
                        cycle_s = min(held_s, MAX_CYCLE_S)
                        print(f"NEW_CYCLE_S={cycle_s}")
                    last_cycle = now
            t_last_release = now

        btn_prev = btn_val

        # --- Ciclo de monitoreo (no bloqueante) ---
        if running and (not btn_held) and (now - last_cycle >= cycle_s):
            tempC = read_temp_c()
            if tempC is None:
                # Si no hay lectura aún, reintentar pronto (y no clavar el loop)
                time.sleep(0.05)
                # re-pedir reporting por si algo se perdió
                try:
                    a_temp.enable_reporting()
                except Exception:
                    pass
                last_cycle = now  # evita que el ciclo se dispare sin datos
                continue

            meanN = push_and_mean(tempC)
            tr = trend_from(tempC, meanN)

            # 1) fin de ciclo: TODOS breve y restaurar
            blink_all_then_restore(BLINK_S)

            # 2) LED de tendencia fijo si hay suficientes muestras
            if tr != "INS":
                set_trend_led(tr)
            else:
                leds_all_off()
                last_trend = "INS"

            mean_str = f"{meanN:.2f}" if len(buf) else "nan"
            print(f"{fecha.strftime('%d/%m/%Y %H:%M:%S')},{tempC:.2f},{mean_str},{tr},{cycle_s:.2f},{1 if running else 0}")

            last_cycle += cycle_s

        time.sleep(0.002)

except KeyboardInterrupt:
    pass
finally:
    leds_all_off()
    board.exit()

# ==================== cierre del archivo .txt ====================
sys.stdout.close()

# restaurar la salida normal (terminal)
sys.stdout = sys._stdout_