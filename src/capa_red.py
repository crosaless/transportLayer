import random
import time
from capa_enlace import CapaEnlaceDatos

class CapaRed:
    def __init__(self, modo_servicio):
        self.modo_servicio = modo_servicio  # 'CONEXION' o 'NO_CONEXION'
        self.conexiones_virtuales = {}
        self.id_conexion = 0
        self.tabla_enrutamiento = {}
        self.mtu = 512  # Maximum Transmission Unit
        self.ttl_default = 15  # Time To Live por defecto
        self.id_paquete = 0

    def crear_paquete(self, datos, direccion_origen, direccion_destino):
        """Crea un paquete IP con su cabecera"""
        self.id_paquete += 1
        return {
            'id': self.id_paquete,
            'ttl': self.ttl_default,
            'protocolo': 'TCP' if self.modo_servicio == 'CONEXION' else 'UDP',
            'direccion_origen': direccion_origen,
            'direccion_destino': direccion_destino,
            'datos': datos,
            'fragmentado': False,
            'offset': 0,
            'mas_fragmentos': False
        }

    def fragmentar_paquete(self, paquete):
        """Fragmenta un paquete si supera el MTU"""
        datos = paquete['datos']
        if len(str(datos)) <= self.mtu:
            return [paquete]

        fragmentos = []
        datos_str = str(datos)
        offset = 0

        while datos_str:
            fragmento = datos_str[:self.mtu]
            datos_str = datos_str[self.mtu:]
            
            nuevo_paquete = paquete.copy()
            nuevo_paquete['datos'] = fragmento
            nuevo_paquete['fragmentado'] = True
            nuevo_paquete['offset'] = offset
            nuevo_paquete['mas_fragmentos'] = bool(datos_str)
            
            fragmentos.append(nuevo_paquete)
            offset += len(fragmento)

        print(f"[Capa Red] Paquete fragmentado en {len(fragmentos)} partes")
        return fragmentos

    def establecer_conexion_virtual(self, origen, destino):
        """Establece una conexión virtual para el servicio orientado a conexión"""
        if self.modo_servicio == 'CONEXION':
            print(f"\n[Capa Red] Estableciendo conexión virtual entre {origen} y {destino}")
            try:
                # Simular establecimiento de conexión virtual
                time.sleep(0.3)
                self.id_conexion += 1
                self.conexiones_virtuales[self.id_conexion] = {
                    'origen': origen,
                    'destino': destino,
                    'estado': 'ESTABLECIDA'
                }
                print(f"[Capa Red] Conexión virtual {self.id_conexion} establecida")
                return self.id_conexion
            except Exception as e:
                print(f"[Capa Red] Error al establecer conexión virtual: {e}")
                return None
        return True

    def enviar_paquete(self, paquete):
        """Simula el envío de un paquete a través de la red"""
        # Simular pérdida de paquetes
        if random.random() < 0.1:  # 10% de probabilidad de pérdida
            print(f"[Capa Red] Paquete {paquete['id']} perdido en la red")
            return False

        # Simular degradación del TTL
        paquete['ttl'] -= 1
        if paquete['ttl'] <= 0:
            print(f"[Capa Red] Paquete {paquete['id']} descartado por TTL=0")
            return False

        print(f"[Capa Red] Paquete {paquete['id']} enviado exitosamente")
        return True

    def transmitir_datos(self, datos, direccion_origen, direccion_destino):
        """Proceso principal de transmisión de datos"""
        # Establecer conexión virtual si es necesario
        if self.modo_servicio == 'CONEXION':
            id_conexion = self.establecer_conexion_virtual(direccion_origen, direccion_destino)
            if not id_conexion:
                return False

        # Crear paquete inicial
        paquete = self.crear_paquete(datos, direccion_origen, direccion_destino)
        
        # Fragmentar si es necesario
        paquetes = self.fragmentar_paquete(paquete)
        
        exito = True
        for p in paquetes:
            if not self.enviar_paquete(p):
                exito = False
                if self.modo_servicio == 'CONEXION':
                    print(f"[Capa Red] Reintentando envío del paquete {p['id']}")
                    # En modo conexión, reintentar hasta 3 veces
                    for _ in range(3):
                        if self.enviar_paquete(p):
                            exito = True
                            break
                        time.sleep(0.5)

        if self.modo_servicio == 'CONEXION':
            self.cerrar_conexion_virtual(id_conexion)

        return exito

    def cerrar_conexion_virtual(self, id_conexion):
        """Cierra una conexión virtual"""
        if id_conexion in self.conexiones_virtuales:
            print(f"[Capa Red] Cerrando conexión virtual {id_conexion}")
            del self.conexiones_virtuales[id_conexion]
            return True
        return False

    def actualizar_tabla_enrutamiento(self, destino, siguiente_salto, metrica):
        """Actualiza la tabla de enrutamiento"""
        self.tabla_enrutamiento[destino] = {
            'siguiente_salto': siguiente_salto,
            'metrica': metrica
        }
        print(f"[Capa Red] Ruta actualizada: {destino} -> {siguiente_salto} (métrica: {metrica})")

    def obtener_siguiente_salto(self, destino):
        """Consulta la tabla de enrutamiento"""
        if destino in self.tabla_enrutamiento:
            return self.tabla_enrutamiento[destino]['siguiente_salto']
        return None 