import requests
import psycopg2
from psycopg2 import sql
from datetime import datetime
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# --- CONFIGURACIÓN BASE DE DATOS ---

DATABASE_URL = os.getenv("DATABASE_URL_NEON")

if not DATABASE_URL:
    raise ValueError("❌ Error: No se encontró la variable DATABASE_URL_NEON en el archivo .env")

NOMBRE_TABLA_PF = "historial_plazos_fijos"
URL_API_PF = "https://api.argentinadatos.com/v1/finanzas/tasas/plazoFijo"

def inicializar_tabla_pf():
    """Crea la tabla para historial de Plazos Fijos si no existe."""
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Estructura: Banco, Fecha, y Tasa Nominal Anual (TNA)
        query = f"""
        CREATE TABLE IF NOT EXISTS {NOMBRE_TABLA_PF} (
            id SERIAL PRIMARY KEY,
            entidad VARCHAR(150),
            fecha DATE,
            tna_clientes NUMERIC(10, 4),
            tna_no_clientes NUMERIC(10, 4),
            UNIQUE(entidad, fecha)
        );
        """
        cur.execute(query)
        conn.commit()
        
    except psycopg2.Error as e:
        print(f"❌ Error al crear tabla: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

def guardar_tasas_plazo_fijo():
    
    conn = None
    try:
        response = requests.get(URL_API_PF, timeout=10)
        response.raise_for_status()
        datos = response.json()
        
        # Fecha de registro = Hoy (ya que esta API da el valor 'actual')
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        
        # Conectar a DB
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        nuevos = 0
        actualizados = 0
        
        # Procesar cada banco
        for banco in datos:
            entidad = banco.get("entidad", "Desconocido")
            tna_clientes = banco.get("tnaClientes")
            tna_no_clientes = banco.get("tnaNoClientes")
            
            # Limpieza de datos (si viene null)
            if tna_clientes is None: tna_clientes = 0
            if tna_no_clientes is None: tna_no_clientes = 0
            
            # SQL Upsert:
            # - Intenta Insertar
            # - Si ya existe (mismo banco, misma fecha) -> Actualiza los valores
            query = sql.SQL("""
                INSERT INTO {} (entidad, fecha, tna_clientes, tna_no_clientes)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (entidad, fecha) 
                DO UPDATE SET 
                    tna_clientes = EXCLUDED.tna_clientes,
                    tna_no_clientes = EXCLUDED.tna_no_clientes;
            """).format(sql.Identifier(NOMBRE_TABLA_PF))
            
            cur.execute(query, (entidad, fecha_hoy, tna_clientes, tna_no_clientes))
            
            # Verificar que paso (insert o update)
            nuevos += 1

        conn.commit()
        print(f"🚀 Datos guardados en PostgreSQL.")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión con la API: {e}")
    except psycopg2.Error as e:
        print(f"❌ Error de Base de Datos: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    inicializar_tabla_pf()
    guardar_tasas_plazo_fijo()


