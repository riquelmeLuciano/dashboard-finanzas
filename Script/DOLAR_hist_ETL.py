import requests
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

# --- CONFIGURACIÓN DE TU BASE DE DATOS ---
DATABASE_URL = os.getenv("DATABASE_URL_NEON") 

# Tipos de dolar a consultar
TIPOS_DOLAR = ["oficial", "blue", "bolsa", "contadoconliqui", "mayorista", "cripto", "tarjeta"]

def crear_tabla_historica():
    """Crea la tabla de histórico si no existe"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        query = """
        CREATE TABLE IF NOT EXISTS cotizaciones_dolar_hist (
            id SERIAL PRIMARY KEY,
            fecha DATE NOT NULL,
            tipo VARCHAR(50) NOT NULL,
            compra NUMERIC(10, 2),
            venta NUMERIC(10, 2),
            promedio NUMERIC(10, 2),
            UNIQUE(fecha, tipo)
        );
        
        CREATE INDEX IF NOT EXISTS idx_dolar_hist_fecha ON cotizaciones_dolar_hist(fecha);
        CREATE INDEX IF NOT EXISTS idx_dolar_hist_tipo ON cotizaciones_dolar_hist(tipo);
        """
        
        cur.execute(query)
        conn.commit()
        print("✅ Tabla 'cotizaciones_dolar_hist' verificada")
        
    except psycopg2.Error as e:
        print(f"❌ Error al crear tabla histórica: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

def guardar_historial_db():
    try:
        # Conexion a la Base de Datos
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        print("✅ Conexión a la base de datos exitosa.")

        # Recorremos cada tipo de dolar
        for tipo in TIPOS_DOLAR:
            url = f"https://api.argentinadatos.com/v1/cotizaciones/dolares/{tipo}"
            
            response = requests.get(url, timeout=10)
            datos = response.json()

            anio_actual = datetime.now().year

            # Insertamos registro por registro
            registros_nuevos = 0
            for fila in datos:
                # Mapeo de datos
                fecha = fila['fecha']
                if datetime.fromisoformat(fecha).year != anio_actual:
                    continue
                compra = fila['compra']
                venta = fila['venta']
                
                # Calculamos el PROMEDIO
                promedio = (compra + venta) / 2
                
                # Nombre del tipo
                tipo_formateado = tipo.capitalize() 
                if tipo == "contadoconliqui": 
                    tipo_formateado = "Contado con liquidación"

                # SQL de inserción
                query = """
                    INSERT INTO cotizaciones_dolar_hist (fecha, tipo, compra, venta, promedio)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING; 
                """
                
                cur.execute(query, (fecha, tipo_formateado, compra, venta, promedio))
                registros_nuevos += 1

        # Guardar cambios
        conn.commit()
        print(f"🚀 {registros_nuevos} registros históricos guardados")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    crear_tabla_historica()
    guardar_historial_db()