import requests
import psycopg2
from datetime import datetime
import json
from dotenv import load_dotenv
import os

# %%

# Cargar variables de entorno
load_dotenv()

# --- CONFIGURACIÓN BASE DE DATOS ---

DATABASE_URL = os.getenv("DATABASE_URL_NEON") 

# EXTRAER DATOS

class ExtractorDolar:
    """Extrae cotizaciones del dólar desde APIs públicas"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def obtener_cotizaciones(self) -> dict:
        """
        Obtiene todas las cotizaciones del dólar
        
        Returns:
            dict: Diccionario con todas las cotizaciones
            {
                'Oficial': {'compra': 850, 'venta': 890, 'fecha': '2025-11-28T...'},
                'Blue': {'compra': 1400, 'venta': 1450, 'fecha': '2025-11-28T...'},
                ...
            }
        """
        try:
            print("🔄 Consultando API de DolarAPI.com...")
            
            url = "https://dolarapi.com/v1/dolares"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            datos_api = response.json()
            
            # Procesar y estructurar los datos
            cotizaciones = {}
            for dolar in datos_api:
                nombre = dolar['nombre']
                cotizaciones[nombre] = {
                    'compra': float(dolar['compra']),
                    'venta': float(dolar['venta']),
                    'fecha_actualizacion': dolar['fechaActualizacion']
                }
            
            print(f"✅ Cotizaciones obtenidas: {len(cotizaciones)} tipos de dólar")
            return cotizaciones
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Error al decodificar JSON: {e}")
            return {}
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return {}
    
    
    def crear_tabla_db(self):
        """Crea la tabla en PostgreSQL --> si no existe"""
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            
            query = """
            CREATE TABLE IF NOT EXISTS cotizaciones_dolar (
                id SERIAL PRIMARY KEY,
                fecha TIMESTAMP NOT NULL,
                tipo VARCHAR(50) NOT NULL,
                compra NUMERIC(10, 2) NOT NULL,
                venta NUMERIC(10, 2) NOT NULL,
                promedio NUMERIC(10, 2),
                UNIQUE(fecha, tipo)
            );
            
            CREATE INDEX IF NOT EXISTS idx_dolar_fecha ON cotizaciones_dolar(fecha);
            CREATE INDEX IF NOT EXISTS idx_dolar_tipo ON cotizaciones_dolar(tipo);
            """
            
            cur.execute(query)
            conn.commit()
            
            print("✅ Tabla 'cotizaciones_dolar' verificada en PostgreSQL")
            
        except psycopg2.Error as e:
            print(f"❌ Error al crear tabla: {e}")
        finally:
            if 'conn' in locals() and conn:
                cur.close()
                conn.close()
    
    def guardar_en_db(self, cotizaciones: dict) -> int:
        """
        Guarda las cotizaciones en PostgreSQL
        ESTRATEGIA: Borra todo (Truncate) e inserta lo nuevo para mantener solo lo actual.
        

        Returns:
            int: Cantidad de registros guardados
        """
        if not cotizaciones:
            print("⚠️  No hay cotizaciones para guardar")
            return 0
        
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            
            # 1. BORRAR DATOS VIEJOS
            # Usamos TRUNCATE para vaciar la tabla completamente antes de guardar lo nuevo
            cur.execute("TRUNCATE TABLE cotizaciones_dolar RESTART IDENTITY;")

            fecha_actual = datetime.now()
            registros_guardados = 0
            
            # 2. INSERTAR DATOS NUEVOS
            for tipo, valores in cotizaciones.items():
                compra = valores['compra']
                venta = valores['venta']
                promedio = (compra + venta) / 2
                
                # Insert simple (ya no necesitamos ON CONFLICT porque la tabla está vacía)
                query = """
                INSERT INTO cotizaciones_dolar (fecha, tipo, compra, venta, promedio)
                VALUES (%s, %s, %s, %s, %s)
                """
                
                cur.execute(query, (fecha_actual, tipo, compra, venta, promedio))
                registros_guardados += 1
            
            conn.commit()
            
            return registros_guardados
            
        except psycopg2.Error as e:
            print(f"❌ Error de Base de Datos: {e}")
            if 'conn' in locals():
                conn.rollback()
            return 0
        finally:
            if 'conn' in locals() and conn:
                cur.close()
                conn.close()
    
    
# ==================== FUNCIONES DE UTILIDAD ====================

def ejecutar_extraccion_completa():
    
    extractor = ExtractorDolar()
    
    # 1. Crear tabla si no existe
    extractor.crear_tabla_db()
    
    # 2. Obtener cotizaciones
    cotizaciones = extractor.obtener_cotizaciones()
    
    if not cotizaciones:
        print("\n❌ No se pudieron obtener cotizaciones")
        return
    
    # 4. Guardar en base de datos
    print("\n💾 Guardando en PostgreSQL...")
    registros = extractor.guardar_en_db(cotizaciones)
    
    
    print("✅ EXTRACCIÓN COMPLETADA")
    




# ==================== EJECUCIÓN ====================

if __name__ == "__main__":
    
    # Opción 1: Extracción completa (recomendado)
    ejecutar_extraccion_completa()

