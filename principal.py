import os
import socket
import threading
import time
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog
import json
import logging
from plyer import notification  # Importar plyer para notificaciones

# Cargar configuración desde archivo JSON
with open("config.json", "r") as config_file:
    CONFIG = json.load(config_file)

# Ruta predeterminada
CARPETA_SYNC = CONFIG["carpeta_sync"]  # Carpeta a sincronizar
PUERTO = CONFIG["puerto"]  # Puerto utilizado para la comunicación
TIEMPO_ESPERA = CONFIG["tiempo_espera"]  # Segundos entre revisiones de archivos
ARCHIVOS_ENVIADOS = set()  # Rastrear archivos enviados
PAUSADO = False  # Estado de la sincronización
RUTA_DESTINO = CARPETA_SYNC  # Ruta de destino inicial
IP = CONFIG["ip_destino"]

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
    
    # Guardar en archivo de texto
    with open("registro.txt", "a") as archivo_log:
        archivo_log.write(f"Usuario: {nombre_usuario}, Fecha: {fecha_envio}, Archivo: {nombre_archivo}\n")
    
    print(f"[Registro] Guardado: Usuario: {nombre_usuario}, Fecha: {fecha_envio}, Archivo: {nombre_archivo}")
    # Configuración básica de logs
logging.basicConfig(
    filename="sincronizacion.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
# Función para sincronizar el archivo
def sincronizar_archivo(ip_destino, archivo):
    global PAUSADO, RUTA_DESTINO
    
    try:
        # Pausar la sincronización si está en pausa
        while PAUSADO:
            time.sleep(1)
        
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
        logging.error(f"Error en el servidor: {e}")
        messagebox.showerror("Error","Ha ocurrido un error modificando la configuración, intente de nuevo")
# Función para la interfaz gráfica de envío
def iniciar_sincronizacion():
    archivo = entrada_archivo.get()
    ip_servidor = IP
    
    if not archivo:
        messagebox.showerror("Error", "Debe seleccionar un archivo.")
        return
    
    if not ip_servidor:
        messagebox.showerror("Error", "Debe ingresar una dirección IP.")
        return
    
    # Crear hilo para enviar archivo
    cliente_thread = threading.Thread(target=sincronizar_archivo, args=(ip_servidor, archivo))
    cliente_thread.start()
    
    # Mensaje de inicio de sincronización (mensaje emergente)
    messagebox.showinfo("Sincronización Iniciada", "Se ha iniciado la sincronización.")
    print("Se ha iniciado la sincronización.")

# Función para seleccionar archivo
def seleccionar_archivo():
    archivo_seleccionado = filedialog.askopenfilename(initialdir=CARPETA_SYNC, title="Seleccionar archivo a enviar")
    if archivo_seleccionado:
        entrada_archivo.delete(0, tk.END)  # Limpiar campo actual
        entrada_archivo.insert(0, archivo_seleccionado)  # Insertar archivo seleccionado
        print(f"Archivo seleccionado: {archivo_seleccionado}")

# Función para seleccionar carpeta
def seleccionar_carpeta():
    global RUTA_DESTINO
    carpeta_seleccionada = filedialog.askdirectory(initialdir=RUTA_DESTINO)
    if carpeta_seleccionada:
        RUTA_DESTINO = carpeta_seleccionada
        # Mostrar mensaje cuando se seleccione una carpeta
        messagebox.showinfo("Carpeta Seleccionada", f"Carpeta de destino seleccionada: {RUTA_DESTINO}")
        print(f"Carpeta de destino seleccionada: {RUTA_DESTINO}")
    else:
        # Si no se selecciona ninguna carpeta, mantener la ruta predeterminada
        print(f"No se seleccionó ninguna carpeta, se mantiene la ruta predeterminada: {RUTA_DESTINO}")

# Función del servidor para recibir archivos
def servidor():
    global RUTA_DESTINO
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.bind(('0.0.0.0', PUERTO))
        servidor.listen(5)
        print(f"[Servidor] Esperando conexiones en el puerto {PUERTO}...")

        while True:
            conn, addr = servidor.accept()
            print(f"[Servidor] Conexión establecida con {addr}")

            with conn:

            # Mientras esté en pausa, espera a que se reanude
                while  PAUSADO:
                    print("[Servidor] Sincronización pausada, esperando reanudación...")
                    time.sleep(1)  # El servidor "duerme" hasta que la sincronización se reanude
                # Recibir el nombre del archivos
                nombre_archivo = conn.recv(1024).decode()
                if not nombre_archivo:
                    continue

                ruta_archivo = os.path.join(RUTA_DESTINO, nombre_archivo)

                # Recibir el contenido del archivo
                with open(ruta_archivo, 'wb') as archivo:
                    while True:
                        datos = conn.recv(1024)
                        if not datos:
                            break
                        archivo.write(datos)

                print(f"[Servidor] Archivo recibido: {ruta_archivo}")
                guardar_registro(ruta_archivo)  # Guardar el registro después de recibir el archivo
                
                # Mostrar notificación con plyer cuando se recibe un archivo
                notification.notify(
                    title="Archivo Recibido",
                    message=f"Se ha agregado el nuevo archivo: {ruta_archivo}",
                    timeout=10  # La notificación desaparece después de 10 segundos
                )
                
                # Mensaje cuando se recibe un archivo nuevo
                print(f"Se ha agregado el nuevo archivo: {ruta_archivo}")
# Función del cliente
def cliente():

    while True:
        for archivo in os.listdir(CARPETA_SYNC):
            ruta_archivo = os.path.join(CARPETA_SYNC, archivo)
            # Mientras esté en pausa, espera a que se reanude
            while  PAUSADO:
                print("[Cliente] Sincronización pausada, esperando reanudación...")
                time.sleep(1)  # El cliente "duerme" hasta que la sincronización se reanude
            if archivo not in ARCHIVOS_ENVIADOS and os.path.isfile(ruta_archivo):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
                        cliente.connect((IP, PUERTO))
                        cliente.sendall(archivo.encode())  # Enviar el nombre del archivo

                        # Enviar el contenido del archivo
                        with open(ruta_archivo, 'rb') as f:
                            cliente.sendfile(f)

                    print(f"[Cliente] Archivo enviado: {archivo}")
                    ARCHIVOS_ENVIADOS.add(archivo)

                except Exception as e:
                    print(f"[Cliente] Error al enviar archivo {archivo}: {e}")
                    logging.error(f"Error en el servidor: {e}")
                    messagebox.showerror("Error","Ha ocurrido un error modificando la configuración, intente de nuevo")
        time.sleep(TIEMPO_ESPERA)
# Función para pausar la sincronización
def pausar_sincronizacion():
    global PAUSADO
    PAUSADO = True
    # Mensaje de pausa (ventana emergente)
    messagebox.showinfo("Sincronización Pausada", "Se ha detenido la sincronización.")
    print("Se ha detenido la sincronización.")

# Función para reanudar la sincronización
def reanudar_sincronizacion():
    global PAUSADO
    PAUSADO = False
    # Mensaje de reanudación (ventana emergente)
    messagebox.showinfo("Sincronización Reanudada", "Se ha iniciado la sincronización.")
    print("Se ha iniciado la sincronización.")

def crear_interfaz():
    # Configuración de la ventana principal
    ventana = tk.Tk()
    ventana.title("Gestión de Sincronización de Archivos")
    ventana.geometry("600x400")
    ventana.configure(bg="#f3f4f6")  # Fondo moderno

    # Título de la aplicación
    label_titulo = tk.Label(
        ventana,
        text="Sincronización de Archivos",
        font=("Helvetica", 20, "bold"),
        bg="#f3f4f6",
        fg="#333",
    )
    label_titulo.pack(pady=20)

    # Marco para contener los botones
    frame_botones = tk.Frame(ventana, bg="#f3f4f6")
    frame_botones.pack(pady=20)

    # Estilo común para los botones
    boton_config = {
        "font": ("Helvetica", 12),
        "width": 25,
        "height": 2,
        "relief": "flat",
        "highlightthickness": 0,
    }

    # Botón de seleccionar carpeta
    boton_seleccionar_carpeta = tk.Button(
        frame_botones,
        text="Seleccionar Carpeta de Destino",
        bg="#4caf50",
        fg="white",
        activebackground="#45a049",
        activeforeground="white",
        command=seleccionar_carpeta,
        **boton_config
    )
    boton_seleccionar_carpeta.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

    # Botón para pausar sincronización
    boton_pausar = tk.Button(
        frame_botones,
        text="Pausar Sincronización",
        bg="#ff9800",
        fg="white",
        activebackground="#e68900",
        activeforeground="white",
        command=pausar_sincronizacion,
        **boton_config
    )
    boton_pausar.grid(row=1, column=0, padx=10, pady=10)

    # Botón para reanudar sincronización
    boton_reanudar = tk.Button(
        frame_botones,
        text="Reanudar Sincronización",
        bg="#2196f3",
        fg="white",
        activebackground="#1e88e5",
        activeforeground="white",
        command=reanudar_sincronizacion,
        **boton_config
    )
    boton_reanudar.grid(row=1, column=1, padx=10, pady=10)

    ventana.mainloop()

# Iniciar el servidor y la interfaz gráfica
if __name__ == '__main__':
    # Iniciar servidor en otro hilo
    hilo_servidor = threading.Thread(target=servidor, daemon=True)
    hilo_servidor.start()
    cliente_thread = threading.Thread(target=cliente)
    cliente_thread.start()

    # Crear interfaz gráfica
    crear_interfaz()
