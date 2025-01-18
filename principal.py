import os
import socket
import threading
import time
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog

# Constantes y variables
CARPETA_SYNC = 'C:\\Users\\Axel\\Desktop\\32'  # Carpeta a sincronizar
PUERTO = 5000  # Puerto utilizado para la comunicación
TIEMPO_ESPERA = 10  # Segundos entre revisiones de archivos
ARCHIVOS_ENVIADOS = set()  # Rastrear archivos enviados

if not os.path.exists(CARPETA_SYNC):
    os.makedirs(CARPETA_SYNC)

# Función para guardar el registro
def guardar_registro(archivo):
    if not archivo:
        messagebox.showerror("Error", "Debe seleccionar un archivo.")
        return
    
    # Obtener información
    nombre_usuario = os.getlogin()
    fecha_envio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nombre_archivo = os.path.basename(archivo)
    
    # Guardar en archivo de texto (registro.txt en el directorio del proyecto)
    try:
        with open("registro.txt", "a") as archivo_log:
            archivo_log.write(f"Usuario: {nombre_usuario}, Fecha: {fecha_envio}, Archivo: {nombre_archivo}\n")
        print(f"[Registro] Guardado: Usuario: {nombre_usuario}, Fecha: {fecha_envio}, Archivo: {nombre_archivo}")
    except Exception as e:
        print(f"[Error] No se pudo guardar el registro: {e}")

# Función para sincronizar el archivo
def sincronizar_archivo(ip_destino, archivo):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
            cliente.connect((ip_destino, PUERTO))
            cliente.sendall(archivo.encode())  # Enviar el nombre del archivo

            # Enviar el contenido del archivo
            with open(archivo, 'rb') as f:
                cliente.sendfile(f)
        
        print(f"[Cliente] Archivo enviado: {archivo}")
        ARCHIVOS_ENVIADOS.add(archivo)
        guardar_registro(archivo)  # Guardar el registro después de enviar el archivo

    except Exception as e:
        print(f"[Cliente] Error al enviar archivo {archivo}: {e}")

# Función para la interfaz gráfica de envío
def iniciar_sincronizacion():
    archivo = entrada_archivo.get()
    ip_servidor = entrada_ip.get()
    
    if not archivo:
        messagebox.showerror("Error", "Debe seleccionar un archivo.")
        return
    
    if not ip_servidor:
        messagebox.showerror("Error", "Debe ingresar una dirección IP.")
        return
    
    # Crear hilo para enviar archivo
    cliente_thread = threading.Thread(target=sincronizar_archivo, args=(ip_servidor, archivo))
    cliente_thread.start()

# Función del servidor para recibir archivos
def servidor():
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
                guardar_registro(ruta_archivo)  # Guardar el registro después de recibir el archivo

# Función para abrir un cuadro de diálogo y seleccionar un archivo
def seleccionar_archivo():
    archivo = filedialog.askopenfilename(title="Seleccionar archivo", filetypes=[("Todos los archivos", "*.*")])
    if archivo:
        entrada_archivo.delete(0, tk.END)
        entrada_archivo.insert(0, archivo)

# Función para la interfaz gráfica
def crear_interfaz():
    ventana = tk.Tk()
    ventana.title("Sincronización de Archivos")
    
    # Elementos de la interfaz
    tk.Label(ventana, text="Archivo a sincronizar:").grid(row=0, column=0)
    global entrada_archivo
    entrada_archivo = tk.Entry(ventana, width=50)
    entrada_archivo.grid(row=0, column=1)

    # Botón para seleccionar archivo
    boton_seleccionar = tk.Button(ventana, text="Seleccionar archivo", command=seleccionar_archivo)
    boton_seleccionar.grid(row=0, column=2, padx=10)

    tk.Label(ventana, text="IP del servidor:").grid(row=1, column=0)
    global entrada_ip
    entrada_ip = tk.Entry(ventana, width=50)
    entrada_ip.grid(row=1, column=1)

    boton_enviar = tk.Button(ventana, text="Iniciar sincronización", command=iniciar_sincronizacion)
    boton_enviar.grid(row=2, column=1, pady=10)

    ventana.mainloop()

# Iniciar el servidor y la interfaz gráfica
if __name__ == '__main__':
    # Iniciar servidor en otro hilo
    hilo_servidor = threading.Thread(target=servidor, daemon=True)
    hilo_servidor.start()

    # Crear interfaz gráfica
    crear_interfaz()
