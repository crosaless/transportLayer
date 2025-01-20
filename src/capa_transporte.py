import random
import time
from capa_red import CapaRed

class CapaTransporte:
    def __init__(self, protocolo):
        self.protocolo = protocolo  # 'TCP' o 'UDP'
        self.conexiones = {}
        self.numero_secuencia = 0
        self.buffer_recepcion = {}
        self.ventana_congestion = 1
        self.timeout = 1.0
        self.capa_red = CapaRed('CONEXION' if protocolo == 'TCP' else 'NO_CONEXION')

    def establecer_conexion(self, origen, destino):
        """Simula el establecimiento de conexión TCP (3 pasos handshake)"""
        if self.protocolo == 'TCP':
            print(f"\n[Capa Transporte] Iniciando 3 pasos handshake")
            try:
                # Establecer conexión virtual en la capa de red
                id_conexion_red = self.capa_red.establecer_conexion_virtual(origen, destino)
                if not id_conexion_red:
                    print("[Capa Transporte] Error: No se pudo establecer conexión virtual en capa de red")
                    return None

                # Simulamos 3 pasos handshake
                print("[Capa Transporte] SYN recibido")
                time.sleep(0.2)
                print("[Capa Transporte] SYN-ACK enviado")
                time.sleep(0.2)
                print("[Capa Transporte] ACK recibido")
                
                conexion_id = len(self.conexiones) + 1
                self.conexiones[conexion_id] = {
                    'origen': origen,
                    'destino': destino,
                    'estado': 'ESTABLECIDA',
                    'ventana_congestion': self.ventana_congestion,
                    'id_conexion_red': id_conexion_red
                }
                print(f"[Capa Transporte] Conexión {conexion_id} establecida exitosamente")
                return conexion_id
            except Exception as e:
                print(f"[Capa Transporte] Error en establecimiento de conexión: {e}")
                return None
        else:
            # UDP no establece conexión
            return True

    def enviar_datos(self, datos, origen, destino, conexion_id=None):
        """Envía datos usando TCP o UDP"""
        print(f"\nCapa Transporte: Enviando datos...")
        print(f"→ Origen: {origen}")
        print(f"→ Destino: {destino}")
        print(f"→ Datos: {datos}")
        if self.protocolo == 'TCP':
            return self._enviar_tcp(datos, origen, destino, conexion_id)
        else:
            return self._enviar_udp(datos, origen, destino)

    def _enviar_tcp(self, datos, origen, destino, conexion_id):
        """Implementa envío confiable con control de flujo y congestión"""
        if conexion_id not in self.conexiones:
            print("[Capa Transporte] Error: No existe la conexión TCP")
            return False

        segmentos = self._segmentar_datos(datos)
        for segmento in segmentos:
            enviado = False
            intentos = 0
            while not enviado and intentos < 3:
                print(f"[Capa Transporte] Enviando segmento TCP {self.numero_secuencia}")
                
                # Usar la capa de red para transmitir el segmento
                exito = self.capa_red.transmitir_datos(
                    segmento,
                    origen,
                    destino
                )

                if exito:
                    self.numero_secuencia += 1
                    enviado = True
                    print(f"[Capa Transporte] ACK recibido para segmento {self.numero_secuencia}")
                else:
                    print(f"[Capa Transporte] Timeout, retransmitiendo...")
                    intentos += 1
                    time.sleep(self.timeout)
                    # Implementar backoff exponencial
                    self.timeout *= 2

            if not enviado:
                print("[Capa Transporte] Error: Máximo de intentos alcanzado")
                return False

        return True

    def _enviar_udp(self, datos, origen, destino):
        """Implementa envío no confiable de datagramas"""
        print("[Capa Transporte] Enviando datagrama UDP")
        
        # Usar la capa de red para transmitir el datagrama
        exito = self.capa_red.transmitir_datos(
            datos,
            origen,
            destino
        )

        if exito:
            print("[Capa Transporte] Datagrama UDP enviado exitosamente")
        else:
            print("[Capa Transporte] Datagrama UDP posiblemente perdido (comportamiento normal en UDP)")
        
        # En UDP, siempre retornamos True porque no hay garantía de entrega
        return True

    def _segmentar_datos(self, datos):
        """Divide los datos en segmentos más pequeños"""
        tamano_segmento = 1024
        return [datos[i:i+tamano_segmento] for i in range(0, len(datos), tamano_segmento)]

    def cerrar_conexion(self, conexion_id):
        """Cierra una conexión TCP (4 pasos handshake)"""
        if self.protocolo == 'TCP' and conexion_id in self.conexiones:
            print("\n[Capa Transporte] Iniciando cierre de conexión TCP")
            
            # Cerrar conexión virtual en la capa de red
            id_conexion_red = self.conexiones[conexion_id]['id_conexion_red']
            self.capa_red.cerrar_conexion_virtual(id_conexion_red)
            
            print("[Capa Transporte] FIN recibido")
            time.sleep(0.2)
            print("[Capa Transporte] ACK enviado")
            time.sleep(0.2)
            print("[Capa Transporte] FIN enviado")
            time.sleep(0.2)
            print("[Capa Transporte] ACK recibido")
            del self.conexiones[conexion_id]
            return True
        return False