import time
import random
import zlib

class CapaEnlaceDatos:
    def __init__(self, ventana_tamano):
        self.ventana_tamano = ventana_tamano
        self.marcos_enviados = 0
        self.marcos_ack = 0
        self.timeout = 0.5

    def crear_marco(self, datos, secuencia):
        """Crea un marco con los datos y número de secuencia"""
        crc = zlib.crc32(datos.encode('utf-8'))
        return {'secuencia': secuencia, 'datos': datos, 'crc': crc}

    def enviar_marco(self, marco):
        """Simula el envío de un marco"""
        print(f"Enviando marco {marco['secuencia']} con datos: {marco['datos']}")
        if random.random() > 0.9:  # 10% de probabilidad de pérdida
            print(f"Error en la transmisión del marco {marco['secuencia']}")
            return False
        return True

    def recibir_ack(self, marco_secuencia):
        """Simula la recepción de un ACK"""
        if random.random() > 0.9:  # 10% de probabilidad de pérdida de ACK
            print(f"Timeout: No se recibió ACK para el marco {marco_secuencia}")
            return False
        print(f"ACK recibido para el marco {marco_secuencia}")
        return True

    def transmitir(self, datos):
        """Transmite los datos usando ventana deslizante"""
        print(f"\nCapa Enlace: Iniciando transmisión...")
        print(f"→ Ventana de transmisión: {self.ventana_tamano}")
        print(f"→ Datos a transmitir: {datos}")
        
        datos_transmitidos = []
        ventana = []
        secuencia = 0
        
        while secuencia < len(datos):
            # Llenar la ventana
            while len(ventana) < self.ventana_tamano and secuencia < len(datos):
                marco = self.crear_marco(datos[secuencia], secuencia)
                if self.enviar_marco(marco):
                    ventana.append(marco)
                    self.marcos_enviados += 1
                    secuencia += 1
                else:
                    # Si falla el envío, esperamos y reintentamos
                    time.sleep(self.timeout)
                    continue

            # Procesar ACKs
            nuevos_marcos = []
            for marco in ventana:
                if self.recibir_ack(marco['secuencia']):
                    datos_transmitidos.append(marco['datos'])
                    self.marcos_ack += 1
                else:
                    nuevos_marcos.append(marco)
            
            ventana = nuevos_marcos

            # Si la ventana no se vacía, retransmitir
            if len(ventana) > 0:
                time.sleep(self.timeout)

        print("\nTransmisión finalizada")
        print(f"Total de marcos enviados: {self.marcos_enviados}")
        print(f"Total de marcos confirmados: {self.marcos_ack}")
        return datos_transmitidos
