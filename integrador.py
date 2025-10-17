# pip install pyfirmata
# Arduino: IDE > File > Examples > Firmata > StandardFirmata (cargarlo en el arduino)
# Si usas PyFirmata viejo: reemplazar getargspec por getfullargspec en el script del pyfirmata
# Driver CH340 si tu placa lo requiere

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
voltaje_referencia = 5.0
val_max_conv_ADC = 1023.0
resistencia_fija = 10000.0

N = 5               # ventana para media móvil
Xpct = 5.0

# ==================== Salida a archivo ====================
sys.stdout = open("salida.txt", "w")

# ====================== Crear socket ==========================
server = socket.socket()
server.bind(("0.0.0.0", 5000))  # Escucha en todas las IP, puerto 5000
server.listen(1)

print("Esperando conexión...")
coneccion, direccion = server.accept()
print("Conectado con", direccion)


# ===================== Estado =====================
buf = deque(maxlen=N)
ciclo = 3.5 #cycle_s
ultimo_ciclo = time.monotonic() # last_cycle
ultimo_parpadeo_presionando= ultimo_ciclo # last_hold_blink
presiona_boton = 0.0 #t_btn_press
suelta_boton = 0.0 #t_last_release
boton_presionado = False #btn_held

boton_valor = 0 #btn_val
ultima_tendencia = "INS" #last_trend

# ===================== Helpers LEDs =====================
def apagar_todos():
    led_r.write(0); led_b.write(0); led_g.write(0)

def prender_todos():
    led_r.write(1); led_b.write(1); led_g.write(1)

def restituir_leds_de_tendencia():
    apagar_todos()
    if   ultima_tendencia == "ALZ": led_r.write(1)
    elif ultima_tendencia == "EST": led_b.write(1)
    elif ultima_tendencia == "BAJ": led_g.write(1)
    elif ultima_tendencia == "INS": prender_todos()

def parpadeo_todos_y_restituir(duration_s):
    prender_todos()
    time.sleep(duration_s)
    restituir_leds_de_tendencia()

def poner_tendencia(tr):
    global ultima_tendencia
    ultima_tendencia = tr
    apagar_todos()
    if   tr == "ALZ": led_r.write(1)
    elif tr == "EST": led_b.write(1)
    elif tr == "BAJ": led_g.write(1)
    elif tr == "INS": prender_todos()

# ===================== Cálculos =====================
def empujar_y_media(x):
    buf.append(x)
    return sum(buf) / len(buf)

def leer_temperatura():
    v_ratio = a0.read()
    v_ratio = min(max(v_ratio, 1.0/val_max_conv_ADC), 1.0 - 1.0/val_max_conv_ADC)
    v = v_ratio * voltaje_referencia
    r_ntc = (v * resistencia_fija) / (voltaje_referencia - v)

    lnR = math.log(r_ntc)
    invT = 0.001129148 + 0.000234125*lnR + 0.0000000876741*(lnR**3)  # Steinhart–Hart
    return (1.0 / invT) - 273.15

def calcular_tendencia(current, meanN):
    if len(buf) < N or current is None or math.isnan(meanN):
        return "INS"
    up = meanN * (1.0 + Xpct/100.0)
    dn = meanN * (1.0 - Xpct/100.0)
    if current > up: return "ALZ"
    if current < dn: return "BAJ"
    return "EST"

# ===================== Bucle principal =====================
header = "fecha y hora, tiempo, temperatura, media móvil, tendencia, ciclo"
print(header)

prender_todos()

try:
    btn_prev = boton_valor

    t0 = time.monotonic()

    while True:
        now = time.monotonic()
        ahora = datetime.now()

        # Leer entradas
        boton_valor = btn.read()

        # --- Botón ---
        if boton_valor == 1 and btn_prev == 0:  # presionado
            presiona_boton = now
            ultimo_parpadeo_presionando = now
            boton_presionado = True

        if boton_presionado and (now - ultimo_parpadeo_presionando >= 1.0):
            parpadeo_todos_y_restituir(0.05)
            ultimo_parpadeo_presionando += 1.0

        if boton_valor == 0 and btn_prev == 1:  # soltado
            boton_presionado = False
            pulso = now - presiona_boton
            # ======== LÓGICA DE AJUSTE DE CICLO ========
            if (pulso <= 0.05):
                # Ignorar toques demasiado cortos
                print(f"TOQUE DEMASIADO CORTO DE {pulso:.2f}s, IGNORADO")
            elif (0.02 < pulso< 1):
                print(f"TOQUE DE {pulso:.2f}s, STOP REQUEST")
                break
            elif 1 <= pulso <= 2.5:
                ciclo = 2.5
                print(f"NUEVO CICLO DE {ciclo:.2f} (PULSACIÓN DE {pulso:.2f}s)")
                ultimo_ciclo = now
            elif pulso >= 10:
                ciclo = 10
                print(f"NUEVO CICLO DE {ciclo:.2f} (PULSACIÓN DE {pulso:.2f}s)")
                ultimo_ciclo = now
            else:
                # Entre 2.5 y 10 s (zona intermedia): dejo el ciclo como está
                ciclo = pulso
                print(f"NUEVO CICLO DE {pulso:.2f}s (PULSACION INTERMEDIA)")
                ultimo_ciclo = now
            # ==================================================

            suelta_boton = now

        btn_prev = boton_valor

        # --- Ciclo de monitoreo ---
        if (not boton_presionado) and (now - ultimo_ciclo >= ciclo):
            tempC = leer_temperatura()

            meanN = empujar_y_media(tempC)
            tr = calcular_tendencia(tempC, meanN)
            if time.monotonic()-suelta_boton >0.01: #se evita que parpadee apenas termina de pulsar
                parpadeo_todos_y_restituir(0.05) #parpadeo de ciclo

            poner_tendencia(tr)

            #guardo la media y la temperatura como string para el caso en que no hay datos
            mean_str = f"{meanN:.2f}" if len(buf) else "nan"
            temp_str = f"{tempC:.2f}" if not (tempC is None) else "nan"
            mensaje = f"{ahora.strftime('%d/%m/%Y %H:%M:%S')},{now-t0:.2f},{temp_str},{mean_str},{tr},{ciclo:.2f}"
            print(mensaje)
            coneccion.send(temp_str.encode()) 
            ultimo_ciclo += ciclo

        time.sleep(0.002)

except KeyboardInterrupt:
    pass
finally:
    apagar_todos()
    board.exit()
    sys.stdout.close()
    sys.stdout = sys.__stdout__

    # ==== cierro el socket =====
    coneccion.close()
    server.close()
