import requests
import psycopg2
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os


# Cargar variables de entorno
load_dotenv()

# --- CONFIGURACIÓN BASE DE DATOS ---

DATABASE_URL = os.getenv("DATABASE_URL_NEON")

class ExtractorInflacion:
    """Extrae historial de inflacion desde APIs públicas"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def obtener_datos_inflacion(self) -> list:
        """
        Obtiene todas las fechas del inflacion
        
        Repueta:
            Devuelve una lista de índices de inflación
            {
                'fecha': "string",
                'valor': "0"
            }
        """
        try:
            print("🔄 Consultando API...")
            
            url = "https://api.argentinadatos.com/v1/finanzas/indices/inflacion"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            datos_api = response.json()
            
            # Procesar y estructurar los datos
            inflacion = []
            fecha_limite = datetime.now() - timedelta(days=365)  # Hace 12 meses

            for dato in datos_api:
                fecha_dato = datetime.strptime(dato['fecha'], '%Y-%m-%d')
    
                # Filtrar solo los datos del último año
                if fecha_dato >= fecha_limite:
                    inflacion.append({
                        'fecha': dato['fecha'],
                        'valor': float(dato['valor'])
                    })
            
            return inflacion
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Error al decodificar JSON: {e}")
            return []
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return []
    
    def crear_tabla_db(self):
        """Crea la tabla en PostgreSQL --> si no existe"""
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            
            query = """
            CREATE TABLE IF NOT EXISTS inflacion (
                id SERIAL PRIMARY KEY,
                fecha DATE NOT NULL UNIQUE,
                valor DECIMAL(10, 2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Índice para búsquedas rápidas por fecha
            CREATE INDEX IF NOT EXISTS idx_inflacion_fecha ON inflacion(fecha DESC);
            """
            
            cur.execute(query)
            conn.commit()
            
            
        except psycopg2.Error as e:
            print(f"❌ Error al crear tabla: {e}")
        finally:
            if 'conn' in locals() and conn:
                cur.close()
                conn.close()
    
    def guardar_en_db(self, inflacion: list) -> int:
        """
        Returns:
            int: Cantidad de registros guardados
        """
        if not inflacion:
            print("⚠️  No hay datos de inflacion para guardar")
            return 0
        
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()

            registros_guardados = 0
            
            # INSERTAR DATOS NUEVOS
            for dato in inflacion:
                fecha = dato['fecha']
                valor = dato['valor']
                
                query = """
                INSERT INTO inflacion (fecha, valor)
                VALUES (%s, %s)
                ON CONFLICT (fecha) DO UPDATE 
                SET valor = EXCLUDED.valor, updated_at = CURRENT_TIMESTAMP
                """
                
                cur.execute(query, (fecha, valor))
                registros_guardados += 1
            
            conn.commit()
            print(f"✅ {registros_guardados} registros de inflación guardados en PostgreSQL")
            
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

if __name__ == "__main__":
    extractor = ExtractorInflacion()
    extractor.crear_tabla_db()
    datos = extractor.obtener_datos_inflacion()
    extractor.guardar_en_db(datos)



