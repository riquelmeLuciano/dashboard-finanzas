import psycopg2
import requests
from psycopg2 import sql
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
import os


load_dotenv() # Carga las variables de un archivo .env

# --- CONFIGURACIÓN BASE DE DATOS ---

DATABASE_URL = os.getenv("DATABASE_URL_NEON")

NOMBRE_TABLA = "rendimientos_fci"

# --- CONFIGURACIÓN DE BILLETERAS Y API ---
DIAS_A_CONSULTAR = 10
BILLETERAS_OBJETIVO = {
    "Ualá": ["ualintec", "uala"],
    "Mercado Pago": ["mercado fondo ahorro - clase b"], # Clase B para evitar duplicados del Clase A
    "Personal Pay": ["delta pesos", "delta ahorro"]
}

# %%


def crear_tabla_postgres():
    conn = None
    try:
        # Conexión a la base de datos
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # SQL para crear la tabla
        # SERIAL es el equivalente a AUTOINCREMENT
        # NUMERIC(18, 6) asegura que guardemos los 6 decimales del VCP con precisión exacta
        query = f"""
        CREATE TABLE IF NOT EXISTS {NOMBRE_TABLA} (
            id SERIAL PRIMARY KEY,
            billetera VARCHAR(50),
            fondo VARCHAR(200),
            fecha DATE,
            vcp NUMERIC(18, 6),
            patrimonio NUMERIC(20, 2),
            horizonte VARCHAR(20),
            tna NUMERIC(10, 4),
            UNIQUE(fondo, fecha)
        );
        """
        
        cur.execute(query)

        # Asegurar que exista la columna 'tna' 
        alter_query = f"ALTER TABLE {NOMBRE_TABLA} ADD COLUMN IF NOT EXISTS tna NUMERIC(10, 4);"
        cur.execute(alter_query)

        conn.commit()

        print("✅ Tabla verificada correctamente.")
        
    except psycopg2.Error as e:
        print(f"❌ Error al conectar o crear tabla: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

def procesar_api_e_insertar():
    """Consulta la API e inserta directamente en PostgreSQL sin pasar por CSV."""
    print("=" * 60)
    print(f"📡 INICIANDO ETL DIRECTO API -> POSTGRES ({DIAS_A_CONSULTAR} DÍAS)")
    print("=" * 60)

    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        fecha_actual = datetime.now()
        nuevos_registros = 0
        
        for i in range(DIAS_A_CONSULTAR):
            fecha_obj = fecha_actual - timedelta(days=i)
            # La API usa formato YYYY/MM/DD
            fecha_str_api = fecha_obj.strftime("%Y/%m/%d")
            # Para la DB usamos formato estándar YYYY-MM-DD
            fecha_str_db = fecha_obj.strftime("%Y-%m-%d")
            
            url = f"https://api.argentinadatos.com/v1/finanzas/fci/mercadoDinero/{fecha_str_api}"
            
            print(f"⏳ Consultando: {fecha_str_api}...", end=" ")
            
            try:
                response = requests.get(url, timeout=10)
                
                if response.status_code == 404:
                    print("❌ Sin datos (Feriado/Finde)")
                    continue
                    
                response.raise_for_status()
                datos_api = response.json()
                
                # Filtrado en memoria
                encontrados_dia = []
                billeteras_procesadas_hoy = set()
                
                for fondo in datos_api:
                    nombre_fondo = fondo.get('fondo', '').lower()
                    
                    for billetera_nombre, patrones in BILLETERAS_OBJETIVO.items():
                        if billetera_nombre not in billeteras_procesadas_hoy:
                            for patron in patrones:
                                if patron in nombre_fondo:
                                    
                                    # Preparar datos para insertar
                                    patrimonio = fondo.get('patrimonio')
                                    if not patrimonio or str(patrimonio).lower() == 'null':
                                        patrimonio = None
                                        
                                    encontrados_dia.append((
                                        billetera_nombre,
                                        fondo.get('fondo'),
                                        fecha_str_db, # Usamos formato DB
                                        float(fondo.get('vcp', 0)),
                                        patrimonio,
                                        fondo.get('horizonte')
                                    ))
                                    billeteras_procesadas_hoy.add(billetera_nombre)
                                    break
                
                # Inserción en DB
                if encontrados_dia:
                    for registro in encontrados_dia:
                        insert_query = sql.SQL("""
                            INSERT INTO {} (billetera, fondo, fecha, vcp, patrimonio, horizonte)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (fondo, fecha) DO NOTHING
                        """).format(sql.Identifier(NOMBRE_TABLA))
                        
                        cur.execute(insert_query, registro)
                        if cur.rowcount > 0:
                            nuevos_registros += 1
                    
                    conn.commit() # Guardar cambios del día
                    print(f"✅ Insertados: {len(encontrados_dia)}")
                else:
                    print("⚠️ Datos vacíos para billeteras objetivo")

            except requests.exceptions.RequestException as e:
                print(f"❌ Error API: {e}")
            
            # Pequeña pausa para no saturar
            time.sleep(0.2)

        print("-" * 60)
        print(f"🚀 Proceso de carga finalizado. Nuevos registros: {nuevos_registros}")

    except psycopg2.Error as e:
        print(f"❌ Error crítico de Base de Datos: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

def actualizar_tna_existentes():
    """Recalcula el TNA para toda la tabla basándose en días reales transcurridos."""
    
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Obtenemos todo ordenado por Fondo y Fecha para poder comparar con el día anterior
        query = f"""
        SELECT id, fondo, fecha, vcp 
        FROM {NOMBRE_TABLA}
        ORDER BY fondo, fecha ASC
        """
        cur.execute(query)
        registros = cur.fetchall()
        
        vcp_anterior_por_fondo = {}
        fecha_anterior_por_fondo = {}
        registros_actualizados = 0
        
        for id_reg, fondo, fecha, vcp_hoy in registros:
            vcp_hoy = float(vcp_hoy)
            vcp_ayer = vcp_anterior_por_fondo.get(fondo)
            fecha_ayer = fecha_anterior_por_fondo.get(fondo)
            
            tna_calculado = None
            
            if vcp_ayer is not None and fecha_ayer is not None:
                # calcular dias reales entre cotizaciones (fines de semana)
                dias_transcurridos = (fecha - fecha_ayer).days
                
                if dias_transcurridos > 0:
                    # Rendimiento del periodo
                    retorno_periodo = (vcp_hoy / vcp_ayer) - 1
                    
                    # Tasa Efectiva Diaria Promedio
                    retorno_diario_promedio = (1 + retorno_periodo)**(1/dias_transcurridos) - 1
                    
                    # Tasa Nominal Anual (TNA)
                    tna_calculado = ((1 + retorno_diario_promedio)**365 - 1) * 100
            
            # Actualizamos si tenemos un cálculo, o dejamos NULL si es el primer registro
            if tna_calculado is not None:
                update_query = f"UPDATE {NOMBRE_TABLA} SET tna = %s WHERE id = %s"
                cur.execute(update_query, (tna_calculado, id_reg))
                registros_actualizados += 1
            
            # Guardamos estado para la siguiente iteración del loop
            vcp_anterior_por_fondo[fondo] = vcp_hoy
            fecha_anterior_por_fondo[fondo] = fecha
        
        conn.commit()
        
    except psycopg2.Error as e:
        print(f"❌ Error al actualizar TNA: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

# --- EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    # 1. Preparar DB
    crear_tabla_postgres()
    
    # 2. Descargar de API e Insertar (Sin CSV)
    procesar_api_e_insertar()
    
    # 3. Calcular matemáticas financieras (TNA)
    actualizar_tna_existentes()


