#!/usr/bin/env python3
import socket
import os
import sys
import time
import threading

# Colores para terminal
RED = "\033[91m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# Banner
def banner():
    print(f"""{CYAN}
    ===========================
       UDPCAT v1.2 by OIHEC
    ===========================
    {RESET}""")

# Validar IP
def validar_ip(ip):
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

# Chat UDP
def udp_chat():
    ip = input("IP destino: ")
    port = int(input("Puerto destino: "))
    if not validar_ip(ip):
        print(RED + "IP inválida." + RESET)
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(GREEN + "[+] Escribe 'exit' para salir del chat." + RESET)

    def escuchar():
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                print(f"{YELLOW}[{addr[0]}:{addr[1]}]{RESET} {data.decode()}")
            except:
                break

    t = threading.Thread(target=escuchar, daemon=True)
    t.start()

    while True:
        msg = input("> ")
        if msg.lower() == "exit":
            break
        sock.sendto(msg.encode(), (ip, port))
    sock.close()

# Enviar archivo UDP
def enviar_archivo():
    ip = input("IP destino: ")
    port = int(input("Puerto destino: "))
    archivo = input("Ruta del archivo: ")

    if not os.path.isfile(archivo):
        print(RED + "Archivo no encontrado." + RESET)
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    with open(archivo, "rb") as f:
        data = f.read(1024)
        while data:
            sock.sendto(data, (ip, port))
            data = f.read(1024)
    sock.close()
    print(GREEN + "[+] Archivo enviado con éxito." + RESET)

# Escuchar mensajes UDP
def escuchar_udp():
    port = int(input("Puerto a escuchar: "))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", port))
    print(GREEN + f"[+] Escuchando en puerto {port}..." + RESET)
    while True:
        data, addr = sock.recvfrom(4096)
        print(f"{YELLOW}[{addr[0]}:{addr[1]}]{RESET} {data.decode(errors='ignore')}")

# Escaneo de puertos UDP
def escanear_udp():
    ip = input("IP objetivo: ")
    if not validar_ip(ip):
        print(RED + "IP inválida." + RESET)
        return
    start_port = int(input("Puerto inicial: "))
    end_port = int(input("Puerto final: "))

    print(GREEN + f"[+] Escaneando {ip} puertos {start_port}-{end_port}..." + RESET)
    for port in range(start_port, end_port + 1):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(0.5)
            sock.sendto(b"ping", (ip, port))
            data, _ = sock.recvfrom(1024)
            print(f"{CYAN}[OPEN]{RESET} {port} -> {data}")
        except socket.timeout:
            pass
        except:
            pass
    print(GREEN + "[+] Escaneo finalizado." + RESET)

# Ping UDP
def ping_udp():
    ip = input("IP destino: ")
    port = int(input("Puerto destino: "))
    cantidad = int(input("Cantidad de paquetes: "))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for i in range(cantidad):
        mensaje = f"ping {i}".encode()
        sock.sendto(mensaje, (ip, port))
        print(f"Paquete {i+1} enviado.")
        time.sleep(0.2)
    sock.close()

# UDP Flood (pruebas de carga)
def udp_flood():
    ip = input("IP destino: ")
    port = int(input("Puerto destino: "))
    tamaño = int(input("Tamaño del paquete (bytes): "))
    cantidad = int(input("Cantidad de paquetes: "))

    data = os.urandom(tamaño)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for i in range(cantidad):
        sock.sendto(data, (ip, port))
        print(f"Paquete {i+1} enviado.")
    sock.close()

# Menú principal
def menu():
    while True:
        banner()
        print(f"""{YELLOW}
        1. Modo chat UDP
        2. Enviar archivo
        3. Escuchar mensajes UDP
        4. Escanear puertos UDP
        5. Ping UDP
        6. UDP Flood (pruebas de carga)
        7. Salir
        {RESET}""")

        opcion = input("Selecciona una opción: ")
        if opcion == "1":
            udp_chat()
        elif opcion == "2":
            enviar_archivo()
        elif opcion == "3":
            escuchar_udp()
        elif opcion == "4":
            escanear_udp()
        elif opcion == "5":
            ping_udp()
        elif opcion == "6":
            udp_flood()
        elif opcion == "7":
            sys.exit(0)
        else:
            print(RED + "Opción inválida." + RESET)

if __name__ == "__main__":
    menu()
