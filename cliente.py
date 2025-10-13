# pip install matplotlib

import socket
import matplotlib.pyplot as plt

server_ip = "127.0.0.1"   # si es la misma PC
port = 5000

s = socket.socket()
s.connect((server_ip, port))
print("Conectado al servidor\n")

x = []
lista = []

plt.ion()   # 🔹 ① modo interactivo: permite actualizar el gráfico en tiempo real

i = 0

while True:
    data = s.recv(1024)
    if not data:
        break
    valor = data.decode().strip()   # 🔹 ② guardar texto decodificado
    print(valor)

    try:
        lista.append(float(valor))  # 🔹 ③ convertir el texto a número
    except ValueError:
        continue                    # si llega algo que no es número, lo ignora

    x.append(i)

    plt.clf()                       # borrar gráfico anterior
    plt.title("Temperatura en tiempo real")
    plt.xlabel("Lectura")
    plt.ylabel("Temperatura (°C)")
    plt.plot(x, lista, 'r-o')

    plt.pause(0.1)   # 🔹 ④ deja actualizar la ventana

    i += 1

s.close()
plt.ioff()   # 🔹 ⑤ deja la ventana fija al terminar
plt.show()