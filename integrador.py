# pip install pyfirmata
# Arduino: IDE > File > Examples > Firmata > StandardFirmata (cargarlo en el arduino)
# Si usas PyFirmata viejo: reemplazar getargspec por getfullargspec en el script del pyfirmata
# Driver CH340 si tu placa lo requiere
#comentario
import time, math, sys, socket
from datetime import datetime
from collections import deque
from pyfirmata import Arduino, util

# ===================== Config =====================
PORT = 'COM8'  # Cambiar por tu puerto
board = Arduino(PORT)

# Iterator para lecturas analógicas
it = util.Iterator(board)
it.start()

# Entradas
a0  = board.get_pin('a:0:i')   # A0: KY-013
btn = board.get_pin('d:2:i')   # D2: botón (usar pull-down externo 10k a GND)

# Salidas
led_g = board.get_pin('d:11:o')
led_b = board.get_pin('d:12:o')
led_r = board.get_pin('d:13:o')

# ===================== Parámetros =====================
VREF = 5.0
ADC_MAX = 1023.0
R_FIXED = 10000.0

N = 5               # ventana para media móvil
Xpct = 5.0

# ==================== Salida a archivo ====================
sys.stdout = open("salida.txt", "w")

# ====================== Crear socket ==========================
server = socket.socket()
server.bind(("0.0.0.0", 5000))  # Escucha en todas las IP, puerto 5000
server.listen(1)

print("Esperando conexión...")
conn, addr = server.accept()
print("Conectado con", addr)


# ===================== Estado =====================
buf = deque(maxlen=N)
cycle_s = 3.5
last_cycle = time.monotonic()
last_hold_blink = last_cycle
t_btn_press = 0.0
t_last_release = 0.0
btn_held = False

btn_val = 0
last_trend = "INS"

# ===================== Helpers LEDs =====================
def leds_all_off():
    led_r.write(0); led_b.write(0); led_g.write(0)

def leds_all_on():
    led_r.write(1); led_b.write(1); led_g.write(1)

def restituir_leds_de_tendencia():
    leds_all_off()
    if   last_trend == "ALZ": led_r.write(1)
    elif last_trend == "EST": led_b.write(1)
    elif last_trend == "BAJ": led_g.write(1)
    elif last_trend == "INS": leds_all_on()

def parpadeo_todos_y_restituir(duration_s):
    leds_all_on()
    time.sleep(duration_s)
    restituir_leds_de_tendencia()

def set_trend_led(tr):
    global last_trend
    last_trend = tr
    leds_all_off()
    if   tr == "ALZ": led_r.write(1)
    elif tr == "EST": led_b.write(1)
    elif tr == "BAJ": led_g.write(1)
    elif tr == "INS": leds_all_on()

# ===================== Cálculos =====================
def push_and_mean(x):
    buf.append(x)
    return sum(buf) / len(buf)

def read_temp_c():
    v_ratio = a0.read()
    v_ratio = min(max(v_ratio, 1.0/ADC_MAX), 1.0 - 1.0/ADC_MAX)
    v = v_ratio * VREF
    r_ntc = (v * R_FIXED) / (VREF - v)

    lnR = math.log(r_ntc)
    invT = 0.001129148 + 0.000234125*lnR + 0.0000000876741*(lnR**3)  # Steinhart–Hart
    return (1.0 / invT) - 273.15

def trend_from(current, meanN):
    if len(buf) < N or current is None or math.isnan(meanN):
        return "INS"
    up = meanN * (1.0 + Xpct/100.0)
    dn = meanN * (1.0 - Xpct/100.0)
    if current > up: return "ALZ"
    if current < dn: return "BAJ"
    return "EST"

# ===================== Bucle principal =====================
header = "fecha,t,tempC,meanN,trend,cycle_s"
print(header)

leds_all_on()

try:
    btn_prev = btn_val

    t0 = time.monotonic()

    while True:
        now = time.monotonic()
        ahora = datetime.now()

        # Leer entradas
        btn_val = btn.read()

        # --- Botón ---
        if btn_val == 1 and btn_prev == 0:  # presionado
            t_btn_press = now
            last_hold_blink = now
            btn_held = True

        if btn_held and (now - last_hold_blink >= 1.0):
            parpadeo_todos_y_restituir(0.05)
            last_hold_blink += 1.0

        if btn_val == 0 and btn_prev == 1:  # soltado
            btn_held = False
            held_s = now - t_btn_press
            # ======== LÓGICA DE AJUSTE DE CICLO ========
            if (held_s <= 0.05):
                # Ignorar toques demasiado cortos
                print(f"TOQUE DEMASIADO CORTO DE {held_s:.2f}s, IGNORADO")
            elif (0.02 < held_s< 1):
                print(f"TOQUE DE {held_s:.2f}s, STOP REQUEST")
                break
            elif 1 <= held_s <= 2.5:
                cycle_s = 2.5
                print(f"NUEVO CICLO DE {cycle_s:.2f} (PULSACIÓN DE {held_s:.2f}s)")
                last_cycle = now
            elif held_s >= 10:
                cycle_s = 10
                print(f"NUEVO CICLO DE {cycle_s:.2f} (PULSACIÓN DE {held_s:.2f}s)")
                last_cycle = now
            else:
                # Entre 2.5 y 10 s (zona intermedia): dejo el ciclo como está
                cycle_s = held_s
                print(f"NUEVO CICLO DE {held_s:.2f}s (PULSACION INTERMEDIA)")
                last_cycle = now
            # ==================================================

            t_last_release = now

        btn_prev = btn_val

        # --- Ciclo de monitoreo ---
        if (not btn_held) and (now - last_cycle >= cycle_s):
            tempC = read_temp_c()

            meanN = push_and_mean(tempC)
            tr = trend_from(tempC, meanN)
            if time.monotonic()-t_last_release >0.01: #se evita que parpadee apenas termina de pulsar
                parpadeo_todos_y_restituir(0.05) #parpadeo de ciclo

            set_trend_led(tr)

            #guardo la media y la temperatura como string para el caso en que no hay datos
            mean_str = f"{meanN:.2f}" if len(buf) else "nan"
            temp_str = f"{tempC:.2f}" if not (tempC is None) else "nan"
            mensaje = f"{ahora.strftime('%d/%m/%Y %H:%M:%S')},{now-t0:.2f},{temp_str},{mean_str},{tr},{cycle_s:.2f}"
            print(mensaje)
            conn.send(temp_str.encode()) 
            last_cycle += cycle_s

        time.sleep(0.002)

except KeyboardInterrupt:
    pass
finally:
    leds_all_off()
    board.exit()
    sys.stdout.close()
    sys.stdout = sys.__stdout__

    # ==== cierro el socket =====
    conn.close()
    server.close()
