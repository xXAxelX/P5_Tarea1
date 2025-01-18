import socket
import os
import threading
import time

CARPETA_SYNC = 'C:\\Users\\Axel\\Desktop\\32'  # Carpeta a sincronizar
PUERTO = 5000  # Puerto utilizado para la comunicación
TIEMPO_ESPERA = 10  # Segundos entre revisiones de archivos
ARCHIVOS_ENVIADOS = set()  # Rastrear archivos enviados

if not os.path.exists(CARPETA_SYNC):
    os.makedirs(CARPETA_SYNC)

def servidor():
    """Función para recibir archivos."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.bind(('0.0.0.0', PUERTO))
        servidor.listen(5)
        print(f"[Servidor] Esperando conexiones en el puerto {PUERTO}...")

        while True:
            conn, addr = servidor.accept()
            print(f"[Servidor] Conexión establecida con {addr}")

            with conn:
                # Recibir el nombre del archivo
                nombre_archivo = conn.recv(1024).decode()
                if not nombre_archivo:
                    continue

                ruta_archivo = os.path.join(CARPETA_SYNC, nombre_archivo)

                # Recibir el contenido del archivo
                with open(ruta_archivo, 'wb') as archivo:
                    while True:
                        datos = conn.recv(1024)
                        if not datos:
                            break
                        archivo.write(datos)

                print(f"[Servidor] Archivo recibido: {ruta_archivo}")

def cliente(ip_destino):
    """Función para enviar archivos."""
    global ARCHIVOS_ENVIADOS

    while True:
        for archivo in os.listdir(CARPETA_SYNC):
            ruta_archivo = os.path.join(CARPETA_SYNC, archivo)

            if archivo not in ARCHIVOS_ENVIADOS and os.path.isfile(ruta_archivo):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
                        cliente.connect((ip_destino, PUERTO))
                        cliente.sendall(archivo.encode())  # Enviar el nombre del archivo

                        # Enviar el contenido del archivo
                        with open(ruta_archivo, 'rb') as f:
                            cliente.sendfile(f)

                    print(f"[Cliente] Archivo enviado: {archivo}")
                    ARCHIVOS_ENVIADOS.add(archivo)

                except Exception as e:
                    print(f"[Cliente] Error al enviar archivo {archivo}: {e}")

        time.sleep(TIEMPO_ESPERA)

def sincronizador(ip_destino):
    """Ejecuta el servidor y el cliente en paralelo."""
    hilo_servidor = threading.Thread(target=servidor, daemon=True)
    hilo_cliente = threading.Thread(target=cliente, args=(ip_destino,), daemon=True)

    hilo_servidor.start()
    hilo_cliente.start()

    hilo_servidor.join()
    hilo_cliente.join()

if __name__ == '__main__':
    ip_destino = input("Introduce la IP de la otra PC: ")
    sincronizador(ip_destino)
