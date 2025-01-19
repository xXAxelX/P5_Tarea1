import os
import socket
import threading
import time
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog
from plyer import notification  # Importar plyer para notificaciones

# Ruta predeterminada
CARPETA_SYNC = 'C:\\Users\\Axel\\Desktop\\32'  # Carpeta a sincronizar
PUERTO = 5000  # Puerto utilizado para la comunicación
TIEMPO_ESPERA = 10  # Segundos entre revisiones de archivos
ARCHIVOS_ENVIADOS = set()  # Rastrear archivos enviados
PAUSADO = False  # Estado de la sincronización
RUTA_DESTINO = CARPETA_SYNC  # Ruta de destino inicial

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
                # Recibir el nombre del archivo
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

# Función para la interfaz gráfica
def crear_interfaz():
    ventana = tk.Tk()
    ventana.title("Sincronización de Archivos")
    
    # Configuración de la ventana
    ventana.geometry("500x350")
    
    # Elementos de la interfaz
    tk.Label(ventana, text="Archivo a sincronizar:").grid(row=0, column=0, padx=10, pady=10)
    global entrada_archivo
    entrada_archivo = tk.Entry(ventana, width=50)
    entrada_archivo.grid(row=0, column=1, padx=10, pady=10)

    tk.Label(ventana, text="IP del servidor:").grid(row=1, column=0, padx=10, pady=10)
    global entrada_ip
    entrada_ip = tk.Entry(ventana, width=50)
    entrada_ip.grid(row=1, column=1, padx=10, pady=10)

    # Botones para seleccionar carpeta y enviar archivo en la misma fila
    boton_seleccionar_carpeta = tk.Button(ventana, text="Seleccionar carpeta de destino", command=seleccionar_carpeta)
    boton_seleccionar_carpeta.grid(row=2, column=0, padx=10, pady=10)

    boton_enviar = tk.Button(ventana, text="Enviar archivo", command=iniciar_sincronizacion)
    boton_enviar.grid(row=2, column=1, padx=10, pady=10)

    # Botones para pausar y reanudar sincronización en la misma fila
    boton_pausar = tk.Button(ventana, text="Pausar sincronización", command=pausar_sincronizacion)
    boton_pausar.grid(row=3, column=0, padx=10, pady=10)

    boton_reanudar = tk.Button(ventana, text="Reanudar sincronización", command=reanudar_sincronizacion)
    boton_reanudar.grid(row=3, column=1, padx=10, pady=10)

    # Botón para seleccionar archivo centrado en la siguiente fila
    boton_seleccionar_archivo = tk.Button(ventana, text="Seleccionar archivo", command=seleccionar_archivo)
    boton_seleccionar_archivo.grid(row=4, column=1, padx=10, pady=10, columnspan=2)  # Centrado en la columna 1

    ventana.mainloop()

# Función cliente para enviar archivos continuamente
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

# Ejecutar servidor y cliente
if __name__ == "__main__":
    servidor_thread = threading.Thread(target=servidor)
    servidor_thread.start()
    
    # Para que el cliente envíe archivos de forma continua, agrega la dirección IP de destino
    cliente_thread = threading.Thread(target=cliente, args=("192.168.1.13",))
    cliente_thread.start()
    
    # Crear la interfaz gráfica
    crear_interfaz()
