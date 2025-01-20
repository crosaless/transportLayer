import socket
import sys

class Cliente:
    def __init__(self, host, port, protocolo):
        self.host = host
        self.port = port
        self.protocolo = protocolo
        self.sock = None

    def conectar(self):
        if self.protocolo == 'TCP':
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            print(f"Conectado al servidor TCP {self.host}:{self.port}")
        else:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            print(f"Listo para enviar mensajes UDP a {self.host}:{self.port}")

    def enviar_mensaje(self, mensaje):
        try:
            if self.protocolo == 'TCP':
                self.sock.send(mensaje.encode('utf-8'))
            else:
                self.sock.sendto(mensaje.encode('utf-8'), (self.host, self.port))
            
            self.sock.settimeout(5.0)  
            try:
                if self.protocolo == 'TCP':
                    respuesta = self.sock.recv(1024).decode('utf-8')
                else:
                    datos, _ = self.sock.recvfrom(1024)
                    respuesta = datos.decode('utf-8')
                
                if respuesta:
                    print(f"Respuesta del servidor: {respuesta}")
                else:
                    print("No se recibió respuesta del servidor")
            except socket.timeout:
                print("Tiempo de espera agotado esperando respuesta del servidor")
                
        except ConnectionError as e:
            print(f"Error de conexión: {e}")
            if self.protocolo == 'TCP':
                print("Reconectando al servidor...")
                self.conectar()
        except Exception as e:
            print(f"Error inesperado: {e}")

    def cerrar(self):
        if self.sock:
            if self.protocolo == 'TCP':
                try:
                    self.sock.send("CERRAR".encode('utf-8'))
                except:
                    pass
            self.sock.close()

    def mostrar_menu(self):
        while True:
            try:
                print("\nHola, soy el servidor, puedes preguntarme la HORA, los USUARIOS conectados o el número de CONEXIONES")
                print("1. Ver hora actual")
                print("2. Ver número de conexiones")
                print("3. Ver usuarios conectados")
                print("4. Enviar mensaje personalizado")
                print("5. Salir")
                
                opcion = input("Seleccione una opción: ").strip()
                
                if opcion == "5":
                    print("Cerrando conexión...")
                    self.sock.close()
                    break
                    
                if opcion in ["1", "2", "3"]:
                    self.enviar_mensaje(opcion)
                elif opcion == "4":
                    mensaje = input("Ingrese su mensaje: ")
                    self.enviar_mensaje(mensaje)
                else:
                    print("Opción inválida. Por favor, intente de nuevo.")
                    
            except Exception as e:
                print(f"Error en el menú: {e}")
                break

if __name__ == "__main__":
    print("Elija el protocolo:")
    print("1. TCP")
    print("2. UDP")
    opcion = input("Ingrese su opción (1 o 2): ")
    while opcion not in ['1', '2']:
        opcion = input("Opción inválida. Por favor, ingrese 1 para TCP o 2 para UDP: ")
    
    protocolo = 'TCP' if opcion == '1' else 'UDP'
    
    cliente = Cliente('localhost', 8888, protocolo)
    cliente.conectar()
    
    cliente.mostrar_menu()
    
    print("Conexión cerrada. ¡Hasta luego!")
