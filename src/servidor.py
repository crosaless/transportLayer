import socket
import threading
import time
import signal
import sys
import random
from capa_transporte import CapaTransporte
from capa_enlace import CapaEnlaceDatos

class Servidor:
    def __init__(self, host, port, protocolo):
        self.host = host
        self.port = port
        self.protocolo = protocolo
        self.sock = None
        self.clientes_conectados = set()
        self.contador_conexiones = 0
        self.ejecutando = False
        self.threads = []
        self.capa_transporte = CapaTransporte(protocolo)
        self.capa_enlace = CapaEnlaceDatos(ventana_tamano=3)
        self.conexiones_transporte = {}  

    def iniciar(self):
        if self.protocolo == 'TCP':
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.sock.bind((self.host, self.port))
        self.ejecutando = True
        
        if self.protocolo == 'TCP':
            self.iniciar_tcp()
        else:
            self.iniciar_udp()

    def iniciar_tcp(self):
        self.sock.listen(5)
        self.sock.settimeout(1)
        print(f"Servidor TCP escuchando en {self.host}:{self.port}")
        while self.ejecutando:
            try:
                cliente, direccion = self.sock.accept()
                self.contador_conexiones += 1
                self.clientes_conectados.add(direccion)
                print(f"Nueva conexión TCP desde {direccion}")
                thread = threading.Thread(target=self.manejar_cliente_tcp, args=(cliente, direccion))
                thread.start()
                self.threads.append(thread)
            except socket.timeout:
                continue
            except Exception as e:
                if self.ejecutando:
                    print(f"Error al aceptar conexión TCP: {e}")

    def iniciar_udp(self):
        self.sock.settimeout(1)
        print(f"Servidor UDP escuchando en {self.host}:{self.port}")
        while self.ejecutando:
            try:
                datos, direccion = self.sock.recvfrom(1024)
                self.contador_conexiones += 1
                self.clientes_conectados.add(direccion)
                print(f"Mensaje UDP recibido desde {direccion}")
                self.manejar_cliente_udp(datos, direccion)
            except socket.timeout:
                continue
            except Exception as e:
                if self.ejecutando:
                    print(f"Error al recibir mensaje UDP: {e}")

    def manejar_cliente_tcp(self, cliente, direccion):
        try:
            self.clientes_conectados.add(direccion)
            self.contador_conexiones += 1
            conexion_id = f"{direccion[0]}:{direccion[1]}"
            print(f"Nueva conexión TCP desde {conexion_id}")
            
            # Establecer conexión en la capa de transporte
            print("\n=== Estableciendo conexión en la capa de transporte ===")
            conexion_transporte = self.capa_transporte.establecer_conexion(self.host, direccion[0])
            if not conexion_transporte:
                print("✗ Error al establecer conexión en la capa de transporte")
                return
            
            self.conexiones_transporte[conexion_id] = conexion_transporte
            print("✓ Conexión establecida en la capa de transporte")
            
            while self.ejecutando:
                try:
                    mensaje = cliente.recv(1024).decode('utf-8')
                    if not mensaje:
                        print(f"Cliente {conexion_id} desconectado")
                        break

                    print(f"\n=== Nueva solicitud TCP de {direccion} ===")
                    respuesta = self.procesar_mensaje(mensaje, direccion)
                    
                    if not respuesta:
                        respuesta = "Error: No se pudo procesar el mensaje"

                    print("\n=== Iniciando proceso de envío a través de las capas ===")
                    
                    # Usar la conexión establecida para enviar datos
                    print("\n--- Procesamiento en Capa de Transporte ---")
                    exito_transporte = self.capa_transporte.enviar_datos(
                        respuesta,
                        self.host,
                        direccion[0],
                        self.conexiones_transporte[conexion_id]
                    )

                    if exito_transporte:
                        print("\n--- Procesamiento en Capa de Enlace ---")
                        datos_a_enviar = respuesta.split()
                        datos_transmitidos = self.capa_enlace.transmitir(datos_a_enviar)
                        respuesta_final = ' '.join(datos_transmitidos) if datos_transmitidos else respuesta

                        try:
                            cliente.send(respuesta_final.encode('utf-8'))
                            print(f"\n✓ Mensaje enviado exitosamente al cliente: {respuesta_final}")
                        except Exception as e:
                            print(f"✗ Error al enviar respuesta al cliente: {e}")
                    else:
                        print(f"✗ Error en la capa de transporte al procesar datos para {direccion}")
                        cliente.send("Error en el procesamiento del mensaje".encode('utf-8'))

                except ConnectionError as e:
                    print(f"Error de conexión con {conexion_id}: {e}")
                    break
                except Exception as e:
                    print(f"Error inesperado con {conexion_id}: {e}")
                    break
                    
        finally:
            # Cerrar la conexión en la capa de transporte
            if conexion_id in self.conexiones_transporte:
                self.capa_transporte.cerrar_conexion(self.conexiones_transporte[conexion_id])
                del self.conexiones_transporte[conexion_id]
            
            cliente.close()
            self.clientes_conectados.remove(direccion)
            print(f"Conexión cerrada con {conexion_id}")

    def manejar_cliente_udp(self, datos, direccion):
        try:
            mensaje = datos.decode('utf-8')
            print(f"\n=== Nueva solicitud UDP de {direccion} ===")
            respuesta = self.procesar_mensaje(mensaje, direccion)
            
            if not respuesta:
                respuesta = "Error: No se pudo procesar el mensaje"

            print("\n=== Iniciando proceso de envío UDP a través de las capas ===")
            
            # 1. Procesamiento en la capa de transporte
            print("\n--- Procesamiento en Capa de Transporte ---")
            exito_transporte = self.capa_transporte.enviar_datos(
                respuesta,
                self.host,
                direccion[0]
            )

            if exito_transporte:
                # 2. Procesamiento en la capa de enlace
                print("\n--- Procesamiento en Capa de Enlace ---")
                datos_a_enviar = respuesta.split()
                datos_transmitidos = self.capa_enlace.transmitir(datos_a_enviar)
                respuesta_final = ' '.join(datos_transmitidos) if datos_transmitidos else respuesta

                try:
                    self.sock.sendto(respuesta_final.encode('utf-8'), direccion)
                    print(f"\n✓ Mensaje UDP enviado exitosamente: {respuesta_final}")
                except Exception as e:
                    print(f"✗ Error al enviar respuesta UDP: {e}")
            else:
                print(f"✗ Error en la capa de transporte al procesar datos UDP para {direccion}")
                self.sock.sendto("Error en el procesamiento del mensaje".encode('utf-8'), direccion)
                
        except Exception as e:
            print(f"Error en el manejo de cliente UDP: {e}")
            try:
                self.sock.sendto("Error en el servidor".encode('utf-8'), direccion)
            except:
                pass

    def procesar_mensaje(self, mensaje, direccion):
        # Primero imprimimos el comando recibido
        print(f"Comando recibido de {direccion}: {mensaje}")
        
        respuesta = None
        if mensaje == "1":
            respuesta = f"La hora actual es: {time.strftime('%H:%M:%S')}"
        elif mensaje == "2":
            respuesta = f"Número de conexiones: {self.contador_conexiones}"
        elif mensaje == "3":
            usuarios = [f"{addr[0]}:{addr[1]}" for addr in self.clientes_conectados]
            respuesta = f"Usuarios conectados ({len(usuarios)}): {', '.join(usuarios)}"
        else:
            respuesta = f"Mensaje recibido: {mensaje}"
        
        # Imprimimos la respuesta que vamos a enviar
        print(f"Enviando respuesta a {direccion}: {respuesta}")
        return respuesta

    def detener(self):
        print("Deteniendo el servidor...")
        self.ejecutando = False
        if self.sock:
            self.sock.close()
        for thread in self.threads:
            thread.join()
        print("Servidor detenido.")

def signal_handler(signum, frame):
    print("\nSeñal de interrupción recibida. Deteniendo el servidor...")
    servidor.detener()
    sys.exit(0)

if __name__ == "__main__":
    print("Elija el protocolo:")
    print("1. TCP")
    print("2. UDP")
    opcion = input("Ingrese su opción (1 o 2): ")
    while opcion not in ['1', '2']:
        opcion = input("Opción inválida. Por favor, ingrese 1 para TCP o 2 para UDP: ")
    
    protocolo = 'TCP' if opcion == '1' else 'UDP'
    
    servidor = Servidor('localhost', 8888, protocolo)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        servidor.iniciar()
    except KeyboardInterrupt:
        print("\nInterrupción de teclado detectada. Deteniendo el servidor...")
    finally:
        servidor.detener()
