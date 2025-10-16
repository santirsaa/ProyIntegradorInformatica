# pip install matplotlib

import socket
import matplotlib.pyplot as plt
# comentario 2
server_ip = "10.65.3.89"   # IP del servidor
port = 5000 

s = socket.socket() # crear socket
print("Conectando al servidor...")
s.connect((server_ip, port)) # conectar al servidor
print("Conectado al servidor\n") 

x = []
lista = []

plt.ion()   # modo interactivo: permite actualizar el gráfico en tiempo real

i = 0

while True: 
    data = s.recv(1024) # recibir datos del servidor 
    if not data:
        break
    valor = data.decode().strip()   # guardar texto decodificado
    print(valor)

    try:
        lista.append(float(valor))  # convertir el texto a número
    except ValueError:
        continue                    # si llega algo que no es número, lo ignora

    x.append(i)

    plt.clf()                       # borrar gráfico anterior
    plt.plot(x, lista, 'r-o') # gráfico de puntos rojos
    plt.title("Temperatura en tiempo real")
    plt.xlabel("Lectura")
    plt.ylabel("Temperatura (°C)")
    plt.pause(0.1)   # pausa el while, para que se actualice la interfaz gráfica

    i += 1

s.close()
plt.ioff()   # deja la ventana fija al terminar
plt.show()
