import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import numpy as np
from dotenv import load_dotenv
import os


load_dotenv()
# --------------------------------------------------CONFIGURACIÓN DE LA PÁGINA--------------------------------------------------
st.set_page_config(
    page_title="Monitor Financiero Argentina",
    page_icon="💸",
    layout="wide"
)

# --------------------------------------------------ESTILOS CSS PERSONALIZADOS--------------------------------------------------
st.markdown("""
<style>
    /* ==================== ELIMINAR RECUADRO DE FONDO ==================== */
    div[data-testid="column"] > div {
        background-color: transparent !important;  /* ← Cambiado a transparente */
        padding: 0px !important;  /* ← Sin padding */
        border-radius: 0px !important;  /* ← Sin bordes redondeados */
        border: none !important;  /* ← Sin borde */
        backdrop-filter: none !important;  /* ← Sin efecto blur */
    }
    /* ==================== MÉTRICAS (KPIs) ==================== */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a7b 100%) !important;
        padding: 25px !important;
        border-radius: 12px !important;
        border: 2px solid rgba(74, 85, 104, 0.4) !important;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.5) !important;
    }
    /* Título de las métricas */
    div[data-testid="stMetric"] label {
        color: #e0e0e0 !important;
        font-weight: 600 !important;
        font-size: 0.90rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.0px !important;
    }
    
    /* Valor principal de las métricas */
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #00ff88 !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
        text-shadow: 0 2px 4px rgba(0, 255, 136, 0.3) !important;
    }
    
    /* ==================== TABS (Pestañas) ==================== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px !important;
        background-color: transparent !important;
        padding: 10px 0 !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #1e2130 0%, #2d3748 100%) !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
        border: 2px solid #2d3748 !important;
        color: #a0aec0 !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2) !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border-color: #667eea !important;
        color: #ffffff !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4) !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border-color: #667eea !important;
        color: #ffffff !important;
        box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5) !important;
    }
    
    /* ==================== BOTONES ==================== */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(102, 126, 234, 0.5) !important;
    }
    
    /* ==================== EXPANDER ==================== */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a7b 100%) !important;
        border-radius: 10px !important;
        border: 2px solid rgba(74, 85, 104, 0.4) !important;
        font-weight: 600 !important;
    }
    
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------CONEXION A LA BASE DE DATOS --------------------------------------------------
# para usar una BD local, descomentar y modificar la siguiente línea:
# @st.cache_resource
# def get_connection():
#     DB_URL = (
#         f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
#         f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
#     )
#     return create_engine(DB_URL)

# NUEVA CONEXIÓN PARA NEON + STREAMLIT CLOUD
conn = st.connection("neon", type="sql")



# --------------------------------------------------FUNCIONES DE CARGA---------------------------------------------------------
def cargar_inflacion_real(conn, fecha_inicio, fecha_fin):
    """
    Obtiene la inflación mensual desde la base de datos y la transforma 
    en una curva de inflación diaria acumulada (índice).

    Logica:
    Toma el dato mensual (ej: 4% en enero), lo convierte a una tasa diaria equivalente
    y genera una curva acumulada para poder compararla día a día con otros activos.

    Args:
        conn: Conexión a la base de datos (SQLAlchemy).
        fecha_inicio (datetime): Fecha desde donde arranca la serie diaria.
        fecha_fin (datetime): Fecha hasta donde llega la serie diaria.

    Returns:
        pd.DataFrame: DataFrame con columnas ['fecha', 'inflacion_acumulada'].
    """
    # 1. Obtener datos mensuales de inflación
    query = "SELECT fecha, valor FROM inflacion ORDER BY fecha ASC"
    df_inf = conn.query(query)
    df_inf['fecha'] = pd.to_datetime(df_inf['fecha'])
    
    # Crear columna 'anio_mes' para hacer el cruce
    df_inf['anio_mes'] = df_inf['fecha'].dt.to_period('M')
    
    #2. Generar rango de fechas diario completo
    rango_dias = pd.date_range(start=fecha_inicio, end=fecha_fin, freq='D')
    df_diario = pd.DataFrame({'fecha': rango_dias})
    df_diario['anio_mes'] = df_diario['fecha'].dt.to_period('M')
    
    #3. Unir datos mensuales al calendario diario
    df_merged = pd.merge(df_diario, df_inf[['anio_mes', 'valor']], on='anio_mes', how='left')

    # Rellenar datos faltantes: 
    # 'ffill' propaga el último valor conocido. 
    # 'fillna(3.0)' asume un 3% mensual si no hay datos históricos ni previos
    df_merged['valor'] = df_merged['valor'].ffill().fillna(3.0) 
    
    #4. Calculo financiero: Desagregación mensual a diaria
    tasa_mensual = df_merged['valor'] / 100

    # Formula de interes compuesto: (1 + TasaMensual)^(1/30) = TasaDiaria
    df_merged['factor_diario'] = (1 + tasa_mensual) ** (1/30)

    # Multiplicar los factores diarios acumulativamente para crear el índice
    df_merged['inflacion_acumulada'] = df_merged['factor_diario'].cumprod()
    
    return df_merged[['fecha', 'inflacion_acumulada']]

@st.cache_data(ttl=3600) # -->Cachear (guardar en memoria) el resultado por 1 hora para optimizar velocidad


def obtener_datos_consolidados(metrica_fci='vcp'):
    """
    Descarga, procesa y unifica datos de FCIs, Dólar e Inflación en un solo DataFrame.

    Args:
        metrica_fci (str): 
            - 'vcp': Usa el Valor de Cuotaparte (precio real).
            - 'tna': Usa la Tasa Nominal Anual y simula el rendimiento acumulado.

    Returns:
        pd.DataFrame: Tabla con fechas como índice y columnas para cada activo 
                    (Billeteras, Tipos de Dólar, Inflación).
    """
    conn = st.connection("neon", type="sql")
    
    # ---------------------------------------------------------
    # 1. CARGA Y PROCESAMIENTO DE FCI (Billeteras)
    # ---------------------------------------------------------
    q_fci = f"""
    SELECT fecha, billetera, vcp, tna 
    FROM rendimientos_fci 
    WHERE billetera IN ('Mercado Pago', 'Ualá', 'Personal Pay')
    ORDER BY fecha ASC
    """
    df_fci = conn.query(q_fci, ttl="10m")
    df_fci['fecha'] = pd.to_datetime(df_fci['fecha'])
    
    #logica condicional según qué métrica quiere ver el usuario
    if metrica_fci == 'tna':
        # Convertir TNA (anual %) a rendimiento acumulado
        # TNA es anual, lo dividimos por 365 para tasa diaria
        # Luego acumulamos día a día por billetera
        
        df_fci['tna'] = df_fci['tna'].fillna(0)  # Rellenar NaN con 0 (Limpieza de nulos)

        #Convertir TNA (Anual) a factor diario: (1 + Tasa / 100 / 365)
        df_fci['tasa_diaria'] = (1 + df_fci['tna'] / 100 / 365)
        
        # Calcular el crecimiento compuesto acumulado por cada billetera
        df_fci = df_fci.sort_values(['billetera', 'fecha'])
        df_fci['rendimiento_acumulado'] = df_fci.groupby('billetera')['tasa_diaria'].cumprod()
        
        # NORMALIZACIÓN (Base 100):
        # Hace que todas las curvas empiecen en 100 el primer día para poder compararlas visualmente
        for billetera in df_fci['billetera'].unique():
            mask = df_fci['billetera'] == billetera

            # Tomamos el primer valor de la serie
            primer_valor = df_fci.loc[mask, 'rendimiento_acumulado'].iloc[0]

            # re-escalamos toda la serie dividiendo por el primer valor
            df_fci.loc[mask, 'rendimiento_acumulado'] = (
                df_fci.loc[mask, 'rendimiento_acumulado'] / primer_valor * 100
            )
        
        # Pivotear: Convertir billeteras de filas a columnas
        df_fci_pivot = df_fci.pivot_table(
            index='fecha', 
            columns='billetera', 
            values='rendimiento_acumulado'
        )
    else:
        # CASO VCP: Usar el valor de cuotaparte directo --> (ya es acumulativo)
        df_fci_pivot = df_fci.pivot_table(
            index='fecha', 
            columns='billetera', 
            values='vcp'
        )
    
    # ---------------------------------------------------------
    # 2. CARGA Y PROCESAMIENTO DE DOLAR
    # ---------------------------------------------------------
    try:
        q_dolar = """
        SELECT fecha, tipo, venta 
        FROM cotizaciones_dolar_hist 
        ORDER BY fecha ASC
        """
        df_dolar = conn.query(q_dolar, ttl="10m")
        df_dolar['fecha'] = pd.to_datetime(df_dolar['fecha'])
        
        # Agrupar por día y tipo para obtener promedio (evita duplicados o zig-zag)
        df_dolar = df_dolar.groupby(['fecha', 'tipo'])['venta'].mean().reset_index()
        
        # Pivotear tipos de dolar a columnas (Blue, Oficial, MEP, etc.)
        df_dolar_pivot = df_dolar.pivot_table(
            index='fecha', 
            columns='tipo', 
            values='venta'
        )
        
        # Renombrar columnas para que sean mas claras
        df_dolar_pivot.columns = [f'Dólar {col}' for col in df_dolar_pivot.columns]
        
    except Exception as e:
        # Manejo de errores si falla la DB o la tabla no existe
        st.warning(f"No se pudo cargar el dólar: {e}. Usando simulado.")
        #Crea un dato para que no rompa el gráfico
        df_dolar_pivot = pd.DataFrame({'Dólar Blue': 1200}, index=df_fci_pivot.index)
    

    # ---------------------------------------------------------
    # 3. UNIFICACION FINAL (FCI + Dolar + Inflacion)
    # ---------------------------------------------------------

    # Unir FCI y Dólar por fecha (outer join para no perder días si faltan datos en uno)
    df_cons = df_fci_pivot.join(df_dolar_pivot, how='outer')
    df_cons = df_cons.ffill().dropna() # --> Rellenar huecos hacia adelante (si no hay cotización fin de semana, usa la del viernes)
    
    # Calcular Inflacion para el rango de fechas resultante
    df_inf = cargar_inflacion_real(conn, df_cons.index.min(), df_cons.index.max())

    # Unir Inflacion al consolidado
    df_cons = df_cons.join(df_inf.set_index('fecha'), how='left')
    
    # Renombrar para visualizacion
    if 'inflacion_acumulada' in df_cons.columns:
        df_cons = df_cons.rename(columns={'inflacion_acumulada': 'Inflación'})
        
    return df_cons

# --------------------------------------------------SIDEBAR (PRIMERO - antes de cargar datos)--------------------------------------------------
st.sidebar.header("⚙️ Configuración")

# SELECTOR DE MÉTRICA (debe estar antes de obtener_datos_consolidados)
metrica_seleccionada = st.sidebar.radio(
    "Métrica de FCI:",
    options=['vcp', 'tna'],
    format_func=lambda x: 'VCP (Valor Cuota Parte)' if x == 'vcp' else 'TNA (Tasa Nominal Anual)',
    help="VCP: valor acumulado del fondo | TNA: tasa de rendimiento anualizada"
)

# OTROS CONTROLES DEL SIDEBAR --> (dias a visualizar)
dias_filtro = st.sidebar.slider("Días a visualizar", 7 , 30, 90)


try:
    df = obtener_datos_consolidados(metrica_fci=metrica_seleccionada)
    
    # Obtener tipos de dólar disponibles
    tipos_dolar = [col for col in df.columns if col.startswith('Dólar')]
    
    # Selector de tipo de dólar (después de cargar datos)
    if tipos_dolar:
        tipo_dolar_seleccionado = st.sidebar.selectbox(
            "Tipo de Dólar:",
            options=tipos_dolar,
            index=0,  # Selecciona el primero por defecto
            help="Selecciona qué cotización de dólar usar para comparar"
        )
    else:
        tipo_dolar_seleccionado = None
        st.sidebar.warning("No se encontraron tipos de dólar en la BD")
        
except Exception as e:
    st.error(f"Error conectando a la base de datos: {e}")
    st.stop()

# Selector de instrumentos (después de tener df)
# filtra para no mostrar todos los tipos de dólar, solo el seleccionado
instrumentos_disponibles = [c for c in df.columns if c != 'Inflación']
# remueve todos los tipos de dolar excepto el seleccionado
instrumentos_disponibles = [c for c in instrumentos_disponibles if not c.startswith('Dólar') or c == tipo_dolar_seleccionado]

# Default: seleccionar Mercado Pago y el dolar elegido
default_instrumentos = ['Mercado Pago']
if tipo_dolar_seleccionado:
    default_instrumentos.append(tipo_dolar_seleccionado)

instrumentos = st.sidebar.multiselect(
    "Comparar (Análicis histórico):", 
    options=instrumentos_disponibles,
    default=default_instrumentos
)


# INFORMACION IMPORTANTE
with st.sidebar:
    st.header("Información IMPORTANTE")
    st.warning("La proyección asume TNA constante. Los rendimientos pasados no garantizan futuros.")
    st.markdown("---")

# ----------------------------------------------------- UI DE LA APLICACIÓN --------------------------------------------------
st.title("📊 Análisis Financiero Argentino")

if metrica_seleccionada == 'tna':
    st.markdown("Comparación en tiempo real de **FCI (TNA convertido) vs Dólar vs Inflación**.")
    st.info("📊 **Nota**: El TNA se ha convertido a rendimiento acumulado para poder compararlo con el dólar y la inflación.")
else:
    st.markdown("Comparación en tiempo real de **FCI vs Dólar vs Inflación**.")


# Filtrar por días
fecha_corte = df.index.max() - pd.Timedelta(days=dias_filtro)
df_filtrado = df[df.index >= fecha_corte].copy()

# -------------------------------------------------- NORMALIZACIÓN DINÁMICA (Base 100) --------------------------------------------------

df_norm = (df_filtrado / df_filtrado.iloc[0]) * 100

# ---------------------------------------------------------KPIS---------------------------------------------------------------------------------

# CSS solo para el fondo de los KPIs
st.markdown("""
<style>
    /* Fondo sutil para las columnas de métricas */
    div[data-testid="column"] > div {
        background-color: rgba(38, 39, 48, 0.5);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid rgba(74, 85, 104, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# --------------------------CALCULOS DE RENDIMIENTO--------------------------
# Fórmula de rendimiento: Valor Final - 100 = % Variación.
# Dividimos la pantalla en 4 columnas de igual ancho para los 4 indicadores
col1, col2, col3, col4 = st.columns(4)

# A. Inflación
# Tomamos el último valor (.iloc[-1]) de la columna Inflación y restamos la base.
rend_infla = df_norm['Inflación'].iloc[-1] - 100

# B. Dólar
rend_dolar = df_norm[tipo_dolar_seleccionado].iloc[-1] - 100 if tipo_dolar_seleccionado and tipo_dolar_seleccionado in df_norm else 0

# C. Mejor FCI (Billetera)
# Filtramos las columnas para excluir Inflación y Dólares, quedándonos solo con las Billeteras
fci_cols = [c for c in df_norm.columns if c not in ['Inflación', 'dolar_blue']]
mejor_fci_nombre = df_norm[fci_cols].iloc[-1].idxmax() #.idxmax() devuelve el NOMBRE de la columna con el valor más alto en la última fila

# Obtenemos el valor numérico de ese mejor rendimiento.
mejor_fci_val = df_norm[mejor_fci_nombre].iloc[-1] - 100

#---VISUALIZACIÓN DE KPIS---

# KPI 1: INFLACIÓN
#Muestra cuánto subieron los precios en el periodo seleccionado.
col1.metric("Inflación del Periodo", f"{rend_infla:.2f}%", delta=f"{dias_filtro} días")

# KPI 2: DÓLAR
# Compara el rendimiento del dólar contra la inflacion.
# El 'delta' aquí muestra la GANANCIA REAL (Dólar - Inflación).
col2.metric(tipo_dolar_seleccionado or "Dólar", f"{rend_dolar:.2f}%", delta=f"{rend_dolar - rend_infla:.2f}% vs Infla")

# KPI 3: MEJOR BILLETERA
# Muestra cul fue la ganadora y su rendimiento real vs inflacion.
col3.metric(f"Mejor: {mejor_fci_nombre}", f"{mejor_fci_val:.2f}%", delta=f"{mejor_fci_val - rend_infla:.2f}% vs Infla")

# KPI 4: PODER DE COMPRA ---> (CONCLUSION)
#Determina si el mejor FCI logró ganarle a la inflación.
resultado_real = mejor_fci_val - rend_infla
estado = "Ganando" if resultado_real > 0 else "Perdiendo"
icono = "🟢" if resultado_real > 0 else "🔴"
col4.metric("Estado Poder de Compra", estado, icono)


# ----------------------------------------------- GRAFICOS CON PESTAÑAS -----------------------------------------------------------------------
#creamos las 4 pestañas principales
tab1, tab2, tab3, tab4 = st.tabs([
    "🔮 Proyección Simple", 
    "💎 Proyección con Aportes", 
    "📊 Comparador de Fondos", 
    "🎯 Calculadora de Objetivos"
])

# ==============================================================================
# PESTAÑA 1: PROYECCIÓN SIMPLE (Interes Compuesto sin aportes)
# ==============================================================================
with tab1:
    st.subheader("🔮 Proyección a Futuro")
    st.markdown("Calcula cuánto tendrías en el futuro **sin realizar aportes adicionales**")
    
    # ----------------------- 1. CONTROLES (INPUTS) -----------------------
    col_proy1, col_proy2, col_proy3 = st.columns(3)
    
    with col_proy1:
        # Input numérico para el dinero inicial
        capital_inicial = st.number_input(
            "💰 Capital Inicial ($)", 
            value=100000, 
            step=10000,
            min_value=1000,
            help="¿Con cuánto dinero empiezas?"
        )
    
    with col_proy2:
        # Filtramos las columnas del DF para mostrar solo los FCI.
        # Excluimos 'Inflación' y cualquier columna que empiece con 'Dólar'.
        fcis_disponibles = [c for c in df.columns if c not in ['Inflación'] and not c.startswith('Dólar')]
        
        fci_proyeccion = st.selectbox(
            "📊 Selecciona el FCI",
            options=fcis_disponibles,
            index=0 if fcis_disponibles else None, # ---> Selecciona el primero por defecto si hay datos
            help="¿En qué fondo quieres invertir?"
        )
    
    with col_proy3:
        # Slider para elegir la duración de la inversión
        meses_proyeccion = st.slider(
            "📅 Plazo (meses)",
            min_value=1,
            max_value=36,
            value=12,
            help="¿Por cuánto tiempo?"
        )
    
    # ----------------------- 2. LOGICA DE CÁLCULO -----------------------
    if fci_proyeccion:
        # A. ESTIMACION DE LA TASA (TNA)
        # obtine TNA promedio de los últimos 30 días del FCI seleccionado
        try:
            # Filtrar últimos 30 días para calcular TNA promedio reciente
            fecha_limite = df.index.max() - pd.Timedelta(days=30)
            # Filtramos el DF para quedarnos solo con el último mes
            df_reciente = df[df.index >= fecha_limite]
            
            # Calcular TNA a partir del VCP o datos disponibles
            # Aproximamos TNA observando el crecimiento diario
            valores_fci = df_reciente[fci_proyeccion].dropna()
            
            if len(valores_fci) > 1:
                # CALCULO DE RENDIMIENTO DIARIO PROMEDIO --->(Geométrico)
                # Fórmula: (ValorFinal / ValorInicial) ^ (1 / cantidad_dias) - 1
                rendimiento_diario = (valores_fci.iloc[-1] / valores_fci.iloc[0]) ** (1/len(valores_fci)) - 1
                # Anualizamos la tasa diaria para obtener la TNA (Tasa Nominal Anual)
                tna_estimada = rendimiento_diario * 365 * 100
            else:
                tna_estimada = 35.0  # ---->Default conservador si no hay suficientes datos
            
            # CLAMPING (Límites de seguridad):
            # Forzamos a que la tasa esté entre 20% y 60% para evitar proyecciones irreales
            # si el fondo tuvo una semana muy buena o muy mala.
            tna_estimada = max(20, min(tna_estimada, 60))
            
        except:
            tna_estimada = 35.0  # Default de seguridad ante errores
        
        
        # Mostrar TNA estimada
        st.info(f"📊 **TNA estimada del fondo:** {tna_estimada:.2f}% anual (basada en rendimiento reciente)")
        
        # PROYECCIÓN MES A MES (Interés Compuesto)
        proyeccion_meses = []
        capital_actual = capital_inicial

        # Convertimos TNA a Tasa Mensual Efectiva para el bucle
        tasa_mensual = tna_estimada / 100 / 12 
        
        # Bucle para simular el paso del tiempo
        for mes in range(meses_proyeccion + 1):
            proyeccion_meses.append({
                'Mes': mes,
                'Capital': capital_actual,
                'Ganancia Acumulada': capital_actual - capital_inicial
            })
            #formula de interés compuesto: Capital * (1 + tasa)
            capital_actual = capital_actual * (1 + tasa_mensual)
        
        #Convertimos la lista de diccionarios en DataFrame para graficar fácil
        df_proyeccion = pd.DataFrame(proyeccion_meses)
        
        # ----------------------- 3. RESULTADOS (KPIs) -----------------------
        capital_final = df_proyeccion['Capital'].iloc[-1]
        ganancia_total = capital_final - capital_inicial
        rentabilidad_porcentual = (ganancia_total / capital_inicial) * 100

        col_res1, col_res2, col_res3 = st.columns(3)
        
        col_res1.metric(
            "💵 Capital Final",
            f"${capital_final:,.0f}", # ---> Formato moneda sin decimales
            delta=f"+${ganancia_total:,.0f}" # --->Ganancia en plata
        )
        
        col_res2.metric(
            "📈 Rentabilidad Total",
            f"{rentabilidad_porcentual:.2f}%",
            delta=f"{rentabilidad_porcentual/meses_proyeccion:.2f}% mensual" # ---> Promedio simple mensual
        )
        
        col_res3.metric(
            "💰 Ganancia Neta",
            f"${ganancia_total:,.0f}",
            delta=f"TNA {tna_estimada:.1f}%"
        )
        
        # ----------------------- 4. GRAFICO (Plotly) -----------------------
        st.markdown("---")
        st.markdown("### 📊 Evolución Proyectada")
        
        fig_proyeccion = go.Figure()
        
        # Trazo 1: La curva de crecimiento (Capital Proyectado)
        fig_proyeccion.add_trace(go.Scatter(
            x=df_proyeccion['Mes'],
            y=df_proyeccion['Capital'],
            mode='lines+markers',
            name='Capital Proyectado',
            line=dict(color='#00d4ff', width=3),
            marker=dict(size=8)
        ))
        
        # Trazo 2: Línea base (Capital Inicial) para ver cuanto crecio visualmente
        fig_proyeccion.add_trace(go.Scatter(
            x=[0, meses_proyeccion],
            y=[capital_inicial, capital_inicial],
            mode='lines',
            name='Capital Inicial',
            line=dict(color='gray', width=2, dash='dash')
        ))
        
        fig_proyeccion.update_layout(
            title=f"Proyección de ${capital_inicial:,.0f} en {fci_proyeccion}",
            xaxis_title="Meses",
            yaxis_title="Capital ($)",
            hovermode='x unified', # ---->Muestra todos los datos al pasar el mouse
            template='plotly_dark'
        )
        
        st.plotly_chart(fig_proyeccion, use_container_width=True)
        
        # ----------------------- 5. TABLA DE DATOS -----------------------
        with st.expander("📋 Ver tabla detallada mes a mes"):
            df_proyeccion_display = df_proyeccion.copy()
            df_proyeccion_display['Capital'] = df_proyeccion_display['Capital'].apply(lambda x: f"${x:,.0f}")
            df_proyeccion_display['Ganancia Acumulada'] = df_proyeccion_display['Ganancia Acumulada'].apply(lambda x: f"${x:,.0f}")
            st.dataframe(df_proyeccion_display, use_container_width=True)
        
    
    else:
        st.warning("No hay FCIs disponibles para proyectar")

# ==============================================================================
# PESTAÑA 2: PROYECCIÓN CON APORTES (Ahorro Recurrente)
# ==============================================================================
with tab2:
    st.subheader("💎 Proyección con Aportes Mensuales")
    st.markdown("Calcula cuánto tendrías realizando **aportes periódicos** cada mes")
    
    # ----------------------- 1. CONTROLES (INPUTS) -----------------------
    # Dividimos en 4 columnas para que entre todo ordenado
    col_ap1, col_ap2, col_ap3, col_ap4 = st.columns(4)
    
    with col_ap1:
        # nota: Usamos el parametro 'key' (ej: key="capital_aportes") porque Streamlit 
        # no permite dos inputs con el mismo nombre en pestañas diferentes sin un ID unico.
        capital_inicial_ap = st.number_input(
            "💰 Capital Inicial ($)", 
            value=100000, 
            step=10000,
            min_value=0,
            key="capital_aportes",
            help="¿Con cuánto dinero empiezas?"
        )
    
    with col_ap2:
        # Input exclusivo de esta pestaña: Cuánto agrega el usuario por mes
        aporte_mensual = st.number_input(
            "💵 Aporte Mensual ($)",
            value=10000,
            step=1000,
            min_value=0,
            key="aporte_mensual",
            help="¿Cuánto vas a agregar cada mes?"
        )
    
    with col_ap3:
        # Obtener lista de FCIs disponibles (Reutilizamos la lógica de filtrar columnas para mostrar solo FCIs)
        fcis_disponibles_ap = [c for c in df.columns if c not in ['Inflación'] and not c.startswith('Dólar')]
        
        fci_proyeccion_ap = st.selectbox(
            "📊 Selecciona el FCI",
            options=fcis_disponibles_ap,
            index=0 if fcis_disponibles_ap else None,
            key="fci_aportes",
            help="¿En qué fondo quieres invertir?"
        )
    
    with col_ap4:
        meses_proyeccion_ap = st.slider(
            "📅 Plazo (meses)",
            min_value=1,
            max_value=36,
            value=12,
            key="meses_aportes",
            help="¿Por cuánto tiempo?"
        )
    
    # ----------------------- 2. CALCULO DE LA PROYECCIÓN -----------------------
    if fci_proyeccion_ap:
        # A. ESTIMACIÓN DE LA TASA
        # Se calcula la TNA basándose en los últimos 30 días del fondo seleccionado (osea misma logica que proyeccion simple)
        try:
            fecha_limite_ap = df.index.max() - pd.Timedelta(days=30)
            df_reciente_ap = df[df.index >= fecha_limite_ap]
            valores_fci_ap = df_reciente_ap[fci_proyeccion_ap].dropna()
            
            if len(valores_fci_ap) > 1:
                rendimiento_diario_ap = (valores_fci_ap.iloc[-1] / valores_fci_ap.iloc[0]) ** (1/len(valores_fci_ap)) - 1
                tna_estimada_ap = rendimiento_diario_ap * 365 * 100
            else:
                tna_estimada_ap = 35.0
            
            # Limitar tasa entre 20% y 60% para realismo
            tna_estimada_ap = max(20, min(tna_estimada_ap, 60))
            
        except:
            tna_estimada_ap = 35.0
        
        # Mostrar TNA estimada
        st.info(f"📊 **TNA estimada del fondo:** {tna_estimada_ap:.2f}% anual (basada en rendimiento reciente)")
        
        #B. BUCLE DE ACUMULACIÓN (Interés Compuesto + Flujo de Fondos)
        proyeccion_aportes = []

        capital_actual_ap = capital_inicial_ap

        #convertimos TNA anual a tasa mensual efectiva
        tasa_mensual_ap = tna_estimada_ap / 100 / 12

        #variable para rastrear cuanto dinero salio del bolsillo del usuario
        total_aportado = capital_inicial_ap
        
        for mes in range(meses_proyeccion_ap + 1):
            # Ganancia = Dinero Total en Cuenta - Dinero que puse de mi bolsillo
            ganancia_acumulada = capital_actual_ap - total_aportado
            
            proyeccion_aportes.append({
                'Mes': mes,
                'Capital Total': capital_actual_ap,
                'Total Aportado': total_aportado,
                'Ganancia por Interés': ganancia_acumulada
            })
            
            # proyeccion hacia el mes siguiente
            if mes < meses_proyeccion_ap:
                # 1. El dinero crece por intereses este mes
                capital_actual_ap = capital_actual_ap * (1 + tasa_mensual_ap)
                # 2. Se inyecta el nuevo aporte (Fin de mes)
                capital_actual_ap += aporte_mensual
                # 3. Actualizamos el contador de dinero invertido
                total_aportado += aporte_mensual
        
        df_proyeccion_ap = pd.DataFrame(proyeccion_aportes)
        
        # ----------------------- 3. RESULTADOS Y KPIs -----------------------
        capital_final_ap = df_proyeccion_ap['Capital Total'].iloc[-1]
        total_aportado_final = df_proyeccion_ap['Total Aportado'].iloc[-1]
        ganancia_interes = df_proyeccion_ap['Ganancia por Interés'].iloc[-1]
        
        # Rentabilidad real sobre el dinero puesto
        rentabilidad_sobre_aportes = (ganancia_interes / total_aportado_final) * 100
        ganancia_mensual_promedio = ganancia_interes / meses_proyeccion_ap if meses_proyeccion_ap > 0 else 0
        
        # KPIs de proyección con aportes
        st.markdown("---")
        col_res_ap1, col_res_ap2, col_res_ap3, col_res_ap4 = st.columns(4)
        
        # KPI 1: Cuánto tengo en total
        col_res_ap1.metric(
            "💵 Capital Final",
            f"${capital_final_ap:,.0f}",
            delta=f"+${ganancia_interes:,.0f} de interés"
        )
        # KPI 2: Cuánto esfuerzo hice (ahorro puro)
        col_res_ap2.metric(
            "📥 Total Aportado",
            f"${total_aportado_final:,.0f}",
            delta=f"{meses_proyeccion_ap} aportes"
        )
        # KPI 3: Dinero "gratis" generado por el sistema
        col_res_ap3.metric(
            "💰 Ganancia por Interés",
            f"${ganancia_interes:,.0f}",
            delta=f"{rentabilidad_sobre_aportes:.2f}% sobre aportes"
        )
        # KPI 4: Ingreso pasivo promedio mensual
        col_res_ap4.metric(
            "📈 Ganancia Mensual Promedio",
            f"${ganancia_mensual_promedio:,.0f}",
            delta=f"promedio por mes"
        )
        
        # ----------------------- 4. GRÁFICO COMPARATIVO (Invertir vs Guardar) -----------------------
        st.markdown("---")
        st.markdown("### 📊 Comparacion: Invertir vs Solo Guardar")
        
        # Escenario: ¿Qué pasa si guardo la plata bajo el colchón? (Sin interés)
        solo_aportes = [capital_inicial_ap + (aporte_mensual * mes) for mes in range(meses_proyeccion_ap + 1)]
        
        fig_aportes = go.Figure()
        
        # # Línea A: Crecimiento Exponencial ---> (Inversión)
        fig_aportes.add_trace(go.Scatter(
            x=df_proyeccion_ap['Mes'],
            y=df_proyeccion_ap['Capital Total'],
            mode='lines+markers',
            name='Con Inversión en FCI',
            line=dict(color='#00ff88', width=3),
            marker=dict(size=8),
            fill='tonexty'
        ))
        
        # Línea B: Crecimiento Lineal (Ahorro sin tasa)
        fig_aportes.add_trace(go.Scatter(
            x=df_proyeccion_ap['Mes'],
            y=solo_aportes,
            mode='lines',
            name='Solo Guardando (sin invertir)',
            line=dict(color='#ff6b6b', width=2, dash='dash')
        ))
        
        # Línea C: Solo para mostrar el area de ganancia en el gráfico (Feedback visual)
        fig_aportes.add_trace(go.Scatter(
            x=df_proyeccion_ap['Mes'],
            y=df_proyeccion_ap['Ganancia por Interés'],
            mode='lines',
            name='Ganancia por Interés',
            line=dict(color='#ffd700', width=2),
            fill='tozeroy',
            fillcolor='rgba(255, 215, 0, 0.2)'
        ))
        
        fig_aportes.update_layout(
            title=f"Evolución con aportes de ${aporte_mensual:,.0f} mensuales en {fci_proyeccion_ap}",
            xaxis_title="Meses",
            yaxis_title="Capital ($)",
            hovermode='x unified',
            template='plotly_dark',
            legend=dict(
                orientation="h", # ---> Leyenda horizontal arriba para ahorrar espacio
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig_aportes, use_container_width=True)
        
        # Destacar el beneficio
        st.success(f"🎉 **¡Ganaste ${ganancia_interes:,.0f} extra por invertir en lugar de solo guardar el dinero!**")
        
        # ----------------------- 5. TABLA RESUMEN -----------------------
        with st.expander("📋 Ver tabla detallada mes a mes"):
            df_proyeccion_ap_display = df_proyeccion_ap.copy()
            
            # Agregamos columnas calculadas para la tabla
            df_proyeccion_ap_display['Solo Aportes (sin invertir)'] = solo_aportes
            df_proyeccion_ap_display['Ventaja de Invertir'] = df_proyeccion_ap_display['Capital Total'] - df_proyeccion_ap_display['Solo Aportes (sin invertir)']
            
            # Formatear columnas
            for col in ['Capital Total', 'Total Aportado', 'Ganancia por Interés', 'Solo Aportes (sin invertir)', 'Ventaja de Invertir']:
                df_proyeccion_ap_display[col] = df_proyeccion_ap_display[col].apply(lambda x: f"${x:,.0f}")
            
            st.dataframe(df_proyeccion_ap_display, use_container_width=True)
        
    
    else:
        st.warning("No hay FCIs disponibles para proyectar")

# ==============================================================================
# PESTAÑA 3: COMPARADOR DE FONDOS (Ranking Competitivo)
# ==============================================================================
with tab3:
    st.subheader("📊 Comparador de Fondos")
    st.markdown("Compara el rendimiento de diferentes FCIs con **el mismo capital e inversión**")
    
    # ----------------------- 1. CONTROLES (INPUTS) -----------------------
    col_comp1, col_comp2 = st.columns(2)
    
    with col_comp1:
        # Nota: Usamos keys unicas para evitar conflictos con inputs de otras pestañas
        capital_comparador = st.number_input(
            "💰 Capital a invertir ($)",
            value=100000,
            step=10000,
            min_value=1000,
            key="capital_comparador",
            help="¿Cuánto dinero quieres comparar?"
        )
    
    with col_comp2:
        meses_comparador = st.slider(
            "📅 Plazo (meses)",
            min_value=1,
            max_value=36,
            value=12,
            key="meses_comparador",
            help="¿En qué plazo quieres comparar?"
        )
    
    # ----------------------- 2. LOGICA DE COMPARACION -----------------------
    # Detectamos automáticamente todos los fondos disponibles en el DF
    fcis_para_comparar = [c for c in df.columns if c not in ['Inflación'] and not c.startswith('Dólar')]
    
    if len(fcis_para_comparar) > 0:
        st.markdown("---")
        st.markdown(f"### 🏆 Resultados para ${capital_comparador:,.0f} en {meses_comparador} meses")
        
        # Lista para almacenar los resultados de cada iteración
        resultados_comparacion = []
        
        # BUCLE PRINCIPAL: Iteramos por CADA fondo disponible
        for fci in fcis_para_comparar:
            try:
                # A. CALCULAR TNA INDIVIDUAL
                # Usamos la misma lógica de "últimos 30 días" para ser justos con todos
                fecha_limite_comp = df.index.max() - pd.Timedelta(days=30)
                df_reciente_comp = df[df.index >= fecha_limite_comp]
                valores_fci_comp = df_reciente_comp[fci].dropna()
                
                if len(valores_fci_comp) > 1:
                    # Rendimiento geometrico diario
                    rendimiento_diario_comp = (valores_fci_comp.iloc[-1] / valores_fci_comp.iloc[0]) ** (1/len(valores_fci_comp)) - 1
                    tna_fci = rendimiento_diario_comp * 365 * 100
                else:
                    tna_fci = 35.0 # --->Fallback seguro
                
                #Normalizacion de tasas
                tna_fci = max(20, min(tna_fci, 60))
                
                # B. PROYECCIÓN INDIVIDUAL
                tasa_mensual_comp = tna_fci / 100 / 12

                # Fórmula directa de interés compuesto para el plazo total (sin aportes intermedios)
                capital_final_comp = capital_comparador * ((1 + tasa_mensual_comp) ** meses_comparador)
                ganancia_comp = capital_final_comp - capital_comparador
                rentabilidad_comp = (ganancia_comp / capital_comparador) * 100
                
                #guardamos la "Ficha Técnica" de este fondo en la lista
                resultados_comparacion.append({
                    'FCI': fci,
                    'TNA': tna_fci,
                    'Capital Final': capital_final_comp,
                    'Ganancia': ganancia_comp,
                    'Rentabilidad %': rentabilidad_comp
                })
                
            except Exception as e:
                # Si un fondo falla, lo saltamos y seguimos con el siguiente
                continue
        
        # ----------------------- 3. ORDENAMIENTO Y RANKING -----------------------
        # Ordenamos la lista de diccionarios: El que tenga mayor 'Capital Final' va primero
        resultados_comparacion = sorted(resultados_comparacion, key=lambda x: x['Capital Final'], reverse=True)
        
        if len(resultados_comparacion) > 0:
            # Crear DataFrame para visualización
            df_comparacion = pd.DataFrame(resultados_comparacion)
            
            # Asignar medallas
            medallas = []
            for i in range(len(df_comparacion)):
                if i == 0:
                    medallas.append('🥇')
                elif i == 1:
                    medallas.append('🥈')
                elif i == 2:
                    medallas.append('🥉')
                else:
                    medallas.append('')
            
            df_comparacion['Ranking'] = medallas
            
            # CÁLCULO (Diferencia entre el mejor y el peor)
            mejor_fondo = resultados_comparacion[0]
            peor_fondo = resultados_comparacion[-1]
            diferencia = mejor_fondo['Capital Final'] - peor_fondo['Capital Final']
            
            # ----------------------- 4. KPIs DESTACADOS -----------------------
            col_best1, col_best2, col_best3, col_best4 = st.columns(4)
            
            # Quién ganó
            col_best1.metric(
                "🥇 Mejor Fondo",
                mejor_fondo['FCI'],
                delta=f"TNA {mejor_fondo['TNA']:.2f}%"
            )
            
            # Cuánto ganó
            col_best2.metric(
                "💰 Ganarías",
                f"${mejor_fondo['Ganancia']:,.0f}",
                delta=f"{mejor_fondo['Rentabilidad %']:.2f}%"
            )
            
            # Resultado final
            col_best3.metric(
                "📊 Capital Final",
                f"${mejor_fondo['Capital Final']:,.0f}",
                delta="El más alto"
            )
            
            # Costo de oportunidad (cuánto pierdes si eliges mal)
            col_best4.metric(
                "🔥 Ventaja sobre el peor",
                f"+${diferencia:,.0f}",
                delta=f"{len(resultados_comparacion)} fondos comparados"
            )
            
            # ----------------------- 5. GRÁFICOS COMPARATIVOS -----------------------
            st.markdown("---")
            st.markdown("### 📊 Comparación Visual")
            
            fig_comparador = go.Figure()
            
            # Logica de colores condicionales: Oro, Plata, Bronce, y Azul para el resto
            colores = ['#FFD700' if i == 0 else '#C0C0C0' if i == 1 else '#CD7F32' if i == 2 else '#4A90E2' 
                       for i in range(len(df_comparacion))]
            
            # GRÁFICO 1: Capital Total
            fig_comparador.add_trace(go.Bar(
                x=df_comparacion['FCI'],
                y=df_comparacion['Capital Final'],
                text=[f"${val:,.0f}" for val in df_comparacion['Capital Final']],
                textposition='outside',
                marker_color=colores,
                name='Capital Final',
                hovertemplate='<b>%{x}</b><br>Capital Final: $%{y:,.0f}<extra></extra>'
            ))
            
            # Línea de referencia (Capital Inicial) para ver el crecimiento real
            fig_comparador.add_hline(
                y=capital_comparador,
                line_dash="dash",
                line_color="gray",
                annotation_text=f"Capital Inicial: ${capital_comparador:,.0f}",
                annotation_position="right"
            )
            
            fig_comparador.update_layout(
                title=f"Capital Final por Fondo ({meses_comparador} meses)",
                xaxis_title="Fondo de Inversión",
                yaxis_title="Capital Final ($)",
                template='plotly_dark',
                showlegend=False,
                height=500
            )
            
            st.plotly_chart(fig_comparador, use_container_width=True)
            
            # GRÁFICO 2: Solo Ganancias
            st.markdown("### 💰 Ganancia Neta por Fondo")
            
            fig_ganancia = go.Figure()
            
            fig_ganancia.add_trace(go.Bar(
                x=df_comparacion['FCI'],
                y=df_comparacion['Ganancia'],
                # Etiqueta compuesta: Dinero + Porcentaje
                text=[f"${val:,.0f}<br>({df_comparacion.iloc[i]['Rentabilidad %']:.1f}%)" 
                      for i, val in enumerate(df_comparacion['Ganancia'])],
                textposition='outside',
                marker_color=colores,
                name='Ganancia',
                hovertemplate='<b>%{x}</b><br>Ganancia: $%{y:,.0f}<extra></extra>'
            ))
            
            max_ganancia = df_comparacion['Ganancia'].max()

            fig_ganancia.update_layout(
                title=f"Ganancia Neta por Fondo",
                xaxis_title="Fondo de Inversión",
                yaxis_title="Ganancia ($)",
                template='plotly_dark',
                showlegend=False,
                height=400,
                yaxis_range=[0, max_ganancia * 1.25]
            )
            
            st.plotly_chart(fig_ganancia, use_container_width=True)
            
            # ----------------------- 6. TABLA FINAL -----------------------
            with st.expander("📋 Ver tabla comparativa detallada"):
                df_comparacion_display = df_comparacion.copy()
                # Seleccionamos y ordenamos columnas limpia
                df_comparacion_display = df_comparacion_display[['Ranking', 'FCI', 'TNA', 'Capital Final', 'Ganancia', 'Rentabilidad %']]
                
                # Formatear columnas
                df_comparacion_display['TNA'] = df_comparacion_display['TNA'].apply(lambda x: f"{x:.2f}%")
                df_comparacion_display['Capital Final'] = df_comparacion_display['Capital Final'].apply(lambda x: f"${x:,.0f}")
                df_comparacion_display['Ganancia'] = df_comparacion_display['Ganancia'].apply(lambda x: f"${x:,.0f}")
                df_comparacion_display['Rentabilidad %'] = df_comparacion_display['Rentabilidad %'].apply(lambda x: f"{x:.2f}%")
                
                st.dataframe(df_comparacion_display, use_container_width=True, hide_index=True)
            
            # Observacion final
            st.success(f"💡 Observacion: Según los datos actuales, **{mejor_fondo['FCI']}** es la mejor opción con una ganancia proyectada de **${mejor_fondo['Ganancia']:,.0f}** en {meses_comparador} meses.")
            
            # Advertencia
            st.warning("⚠️ NOTA: Esta comparación se basa en el rendimiento reciente de cada fondo.")
        
        else:
            st.error("No se pudieron calcular las proyecciones para ningún fondo.")
    
    else:
        st.warning("No hay FCIs disponibles para comparar.")

# ==============================================================================
# PESTAÑA 4: CALCULADORA DE OBJETIVOS (Ingeniería Inversa)
# ==============================================================================
with tab4:
    st.subheader("🎯 Calculadora de Objetivos")
    st.markdown("Calcula **cuánto debes aportar mensualmente** para alcanzar tu meta financiera.")
    
    # ----------------------- 1. CONTROLES (INPUTS) -----------------------
    col_obj1, col_obj2, col_obj3, col_obj4 = st.columns(4)
    
    with col_obj1:
        capital_inicial_obj = st.number_input(
            "💰 Capital Inicial ($)",
            value=100000,
            step=10000,
            min_value=0,
            key="capital_objetivo", # Key única para diferenciar de las otras pestañas
            help="¿Con cuánto dinero empiezas?"
        )
    
    with col_obj2:
        # Input exclusivo de esta pestaña: La Meta Financiera
        objetivo_final = st.number_input(
            "🎯 Meta a Alcanzar ($)",
            value=500000,
            step=50000,
            min_value=1000,
            key="meta_objetivo",
            help="¿Cuánto dinero quieres tener?"
        )
    
    with col_obj3:
        fcis_objetivo = [c for c in df.columns if c not in ['Inflación'] and not c.startswith('Dólar')]
        
        fci_objetivo = st.selectbox(
            "📊 Selecciona el FCI",
            options=fcis_objetivo,
            index=0 if fcis_objetivo else None,
            key="fci_objetivo",
            help="¿En qué fondo vas a invertir?"
        )
    
    with col_obj4:
        meses_objetivo = st.slider(
            "📅 Plazo (meses)",
            min_value=1,
            max_value=60, # Hasta 5 años
            value=24,
            key="meses_objetivo",
            help="¿En cuánto tiempo quieres lograrlo?"
        )
    
    # ----------------------- 2. VALIDACIÓN Y MATEMÁTICA FINANCIERA -----------------------
    
    # Validación A: La meta debe ser lógica (mayor a lo que ya tengo)
    if objetivo_final <= capital_inicial_obj:
        st.error("⚠️ Tu meta debe ser mayor que tu capital inicial")
        
    elif fci_objetivo:
        # A. ESTIMACIÓN DE TASA (Igual a pestañas anteriores)
        try:
            fecha_limite_obj = df.index.max() - pd.Timedelta(days=30)
            df_reciente_obj = df[df.index >= fecha_limite_obj]
            valores_fci_obj = df_reciente_obj[fci_objetivo].dropna()
            
            if len(valores_fci_obj) > 1:
                rendimiento_diario_obj = (valores_fci_obj.iloc[-1] / valores_fci_obj.iloc[0]) ** (1/len(valores_fci_obj)) - 1
                tna_objetivo = rendimiento_diario_obj * 365 * 100
            else:
                tna_objetivo = 35.0
            
            tna_objetivo = max(20, min(tna_objetivo, 60))
            
        except:
            tna_objetivo = 35.0
        
        st.info(f"📊 **TNA estimada del fondo:** {tna_objetivo:.2f}% anual")
        
        # B. CÁLCULO DEL APORTE NECESARIO (PMT)
        # Objetivo: Despejar 'Aporte Mensual' de la fórmula de valor futuro.
        
        tasa_mensual_obj = tna_objetivo / 100 / 12
        
        # Paso 1: Calcular cuánto valdrá mi dinero actual si no hago nada más.
        # Fórmula: Capital * (1 + i)^n
        valor_futuro_capital_inicial = capital_inicial_obj * ((1 + tasa_mensual_obj) ** meses_objetivo)
        
        if tasa_mensual_obj > 0:
            # Paso 2: Calcular cuánto dinero me falta para llegar a la meta
            diferencia_a_cubrir = objetivo_final - valor_futuro_capital_inicial
            
            # Paso 3: Calcular el "Factor de Capitalización de una Serie"
            # Esto nos dice en cuánto se convierte $1 depositado mensualmente.
            # Fórmula: ((1+i)^n - 1) / i
            factor_anualidad = ((1 + tasa_mensual_obj) ** meses_objetivo - 1) / tasa_mensual_obj
            
            # Paso 4: División final para obtener la cuota mensual
            aporte_necesario = diferencia_a_cubrir / factor_anualidad if factor_anualidad != 0 else 0
        else:
            # Si la tasa es 0%, es una división simple
            aporte_necesario = (objetivo_final - capital_inicial_obj) / meses_objetivo
        
        # ----------------------- 3. VALIDACIÓN DE RESULTADOS -----------------------
        
        # Caso 1: El interés compuesto hizo todo el trabajo (No hace falta aportar)
        if aporte_necesario < 0:
            st.success("🎉 **¡Felicitaciones!** Tu capital inicial con los intereses ya supera tu meta. No necesitas hacer aportes adicionales.")
            aporte_necesario = 0
            es_alcanzable = True
            
        # Caso 2: Meta imposible (números astronómicos)
        elif aporte_necesario > 10000000: 
            st.error(f"⚠️ **Meta muy ambiciosa:** Necesitarías aportar ${aporte_necesario:,.0f} mensuales, lo cual puede no ser realista.")
            es_alcanzable = False
        else:
            es_alcanzable = True
        
        # ----------------------- 4. VISUALIZACIÓN DE RESULTADOS -----------------------
        if es_alcanzable and aporte_necesario >= 0:
            st.markdown("---")
            
            # A. KPIs PRINCIPALES
            col_res_obj1, col_res_obj2, col_res_obj3, col_res_obj4 = st.columns(4)
            
            total_a_aportar = aporte_necesario * meses_objetivo
            total_invertido = capital_inicial_obj + total_a_aportar
            # La diferencia es el dinero "gratis" ganado por interés
            intereses_ganados = objetivo_final - total_invertido
            
            col_res_obj1.metric("💵 Aporte Mensual Necesario", f"${aporte_necesario:,.0f}", delta=f"durante {meses_objetivo} meses")
            col_res_obj2.metric("📥 Total a Aportar", f"${total_a_aportar:,.0f}", delta=f"{meses_objetivo} cuotas")
            col_res_obj3.metric("🎯 Meta Final", f"${objetivo_final:,.0f}", delta=f"Capital + Aportes + Interés")
            col_res_obj4.metric("💰 Intereses que Ganarás", f"${intereses_ganados:,.0f}", delta=f"TNA {tna_objetivo:.1f}%")
            
            # B. SIMULACIÓN MES A MES (Para el gráfico de línea)
            st.markdown("---")
            st.markdown("### 📊 Proyección hacia tu Objetivo")
            
            simulacion_objetivo = []
            capital_simulado = capital_inicial_obj
            
            for mes in range(meses_objetivo + 1):
                simulacion_objetivo.append({
                    'Mes': mes,
                    'Capital Acumulado': capital_simulado,
                    # Calculamos cuánto falta, sin bajar de 0
                    'Falta para Meta': max(0, objetivo_final - capital_simulado)
                })
                
                if mes < meses_objetivo:
                    capital_simulado = capital_simulado * (1 + tasa_mensual_obj) # Crece el dinero
                    capital_simulado += aporte_necesario                        # Entra el aporte
            
            df_simulacion_obj = pd.DataFrame(simulacion_objetivo)
            
            # GRÁFICO 1: LÍNEA DE PROGRESO
            fig_objetivo = go.Figure()
            
            # Curva de crecimiento
            fig_objetivo.add_trace(go.Scatter(
                x=df_simulacion_obj['Mes'],
                y=df_simulacion_obj['Capital Acumulado'],
                mode='lines+markers',
                name='Tu Progreso',
                line=dict(color='#00ff88', width=3),
                fill='tozeroy', # Relleno verde debajo de la curva
                fillcolor='rgba(0, 255, 136, 0.2)'
            ))
            
            # Línea horizontal de la Meta
            fig_objetivo.add_trace(go.Scatter(
                x=[0, meses_objetivo],
                y=[objetivo_final, objetivo_final],
                mode='lines',
                name=f'Meta: ${objetivo_final:,.0f}',
                line=dict(color='#FFD700', width=3, dash='dash') # Dorada punteada
            ))
            
            # Línea horizontal del Capital Inicial
            fig_objetivo.add_hline(
                y=capital_inicial_obj,
                line_dash="dot",
                line_color="gray",
                annotation_text=f"Capital Inicial: ${capital_inicial_obj:,.0f}",
                annotation_position="top left"
            )
            
            fig_objetivo.update_layout(
                title=f"Camino a tu meta de ${objetivo_final:,.0f} con aportes de ${aporte_necesario:,.0f}/mes",
                xaxis_title="Meses",
                yaxis_title="Capital ($)",
                template='plotly_dark',
                height=500
            )
            
            st.plotly_chart(fig_objetivo, use_container_width=True)
            
            # C. DESGLOSE VISUAL (GRÁFICO DE TORTA)
            # Muestra qué parte de la meta la pone el usuario y qué parte el mercado.
            st.markdown("### 🔍 Composición de tu Meta")
            
            col_pie1, col_pie2 = st.columns(2)
            
            with col_pie1:
                fig_pie = go.Figure(data=[go.Pie(
                    labels=['Capital Inicial', 'Aportes Mensuales', 'Intereses Ganados'],
                    values=[capital_inicial_obj, total_a_aportar, intereses_ganados],
                    marker=dict(colors=['#4A90E2', '#00ff88', '#FFD700']), # Azul, Verde, Oro
                    hole=0.4, # Donut chart
                    textinfo='label+percent',
                    textposition='outside'
                )])
                
                fig_pie.update_layout(title="¿De dónde viene tu meta?", template='plotly_dark', height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col_pie2:
                # Explicación en texto para reforzar el concepto
                st.markdown("#### 💡 Resumen de tu Plan")
                st.markdown(f"""
                Para alcanzar tu meta de **${objetivo_final:,.0f}** en **{meses_objetivo} meses**:
                
                **📋 Plan de acción:**
                1. Invertir capital inicial: **${capital_inicial_obj:,.0f}**
                2. Aportar **${aporte_necesario:,.0f}** cada mes
                3. Dejar que el interés trabaje por ti
                
                **🔥 El poder del interés compuesto:**
                ¡Los intereses aportarán **${intereses_ganados:,.0f}** sin esfuerzo adicional!
                Representan el **{(intereses_ganados/objetivo_final*100):.1f}%** de tu meta.
                """)
            
            # D. ANÁLISIS DE SENSIBILIDAD (¿QUÉ PASA SI CAMBIO EL PLAZO?)
            st.markdown("---")
            st.markdown("### 🔄 ¿Y si cambio el plazo?")
            
            # Generamos 3 escenarios: Menos tiempo, Tiempo actual, Más tiempo
            plazos_alternativos = [max(6, meses_objetivo-12), meses_objetivo, min(60, meses_objetivo+12)]
            escenarios_plazo = []
            
            for plazo_alt in plazos_alternativos:
                if plazo_alt > 0:
                    # Recalculamos PMT para cada plazo alternativo
                    vf_cap_alt = capital_inicial_obj * ((1 + tasa_mensual_obj) ** plazo_alt)
                    num_alt = objetivo_final - vf_cap_alt
                    den_alt = ((1 + tasa_mensual_obj) ** plazo_alt - 1) / tasa_mensual_obj if tasa_mensual_obj > 0 else plazo_alt
                    aporte_alt = num_alt / den_alt if den_alt != 0 else 0
                    
                    escenarios_plazo.append({
                        'Plazo': f"{plazo_alt} meses",
                        'Aporte Mensual': aporte_alt,
                        'Total a Aportar': aporte_alt * plazo_alt
                    })
            
            df_escenarios = pd.DataFrame(escenarios_plazo)
            
            fig_escenarios = go.Figure()
            
            fig_escenarios.add_trace(go.Bar(
                x=df_escenarios['Plazo'],
                y=df_escenarios['Aporte Mensual'],
                text=[f"${val:,.0f}/mes" for val in df_escenarios['Aporte Mensual']],
                textposition='outside',
                marker_color=['#4A90E2', '#00ff88', '#FFD700'], # Colores distintos para diferenciar
                name='Aporte Mensual'
            ))
            
            max_valor = df_escenarios['Aporte Mensual'].max()

            fig_escenarios.update_layout(
                title="Aporte mensual necesario según el plazo elegido",
                xaxis_title="Plazo",
                yaxis_title="Aporte Mensual ($)",
                template='plotly_dark',
                showlegend=False,
                height=400,
                yaxis_range=[0, max_valor * 1.2] 
            )
            
            st.plotly_chart(fig_escenarios, use_container_width=True)
            
            # Insight automático: Muestra cuánto ahorras mensualmente si esperas más tiempo
            ahorro_mensual = aporte_necesario - escenarios_plazo[2]['Aporte Mensual']
            st.info(f"💡 **Tip:** Si extiendes el plazo a {plazos_alternativos[2]} meses, tu cuota baja en **${ahorro_mensual:,.0f}/mes**.")
            
            # E. TABLA DETALLADA
            with st.expander("📋 Ver evolución mes a mes"):
                df_simulacion_display = df_simulacion_obj.copy()
                df_simulacion_display['Capital Acumulado'] = df_simulacion_display['Capital Acumulado'].apply(lambda x: f"${x:,.0f}")
                df_simulacion_display['Falta para Meta'] = df_simulacion_display['Falta para Meta'].apply(lambda x: f"${x:,.0f}")
                # Barra de progreso textual
                df_simulacion_display['% Completado'] = [(i/meses_objetivo*100) for i in range(len(df_simulacion_display))]
                df_simulacion_display['% Completado'] = df_simulacion_display['% Completado'].apply(lambda x: f"{x:.1f}%")
                
                st.dataframe(df_simulacion_display, use_container_width=True)
            
            st.success(f"🎉 **¡Tu meta es alcanzable!** Con disciplina y aportes constantes de **${aporte_necesario:,.0f}** mensuales, llegarás a **${objetivo_final:,.0f}** en {meses_objetivo} meses.")
            
    else:
        st.warning("No hay FCIs disponibles para calcular objetivos.")

# -------------------------------------------------------ANALISIS HISTORICO(SECCIÓN OCULTA) -------------------------------------------------

st.divider() #--> Separador visual

# Usamos st.expander para ocultar esta sección por defecto (expanded=False).
# El usuario puede expandirla si desea ver el análisis histórico detallado.
with st.expander("📈 Ver Análisis Histórico ", expanded=False):
    st.markdown("### Análisis de datos históricos")
    st.caption("Esta sección muestra el comportamiento pasado de los instrumentos. Recuerda que rendimientos pasados no garantizan rendimientos futuros.")
    
    # Creamos sub-pestañas internas para organizar las dos vistas históricas
    hist_tab1, hist_tab2 = st.tabs(["📈 Carrera Nominal", "🧠 Rendimiento Real"])

    # ==============================================================================
    # SUB-PESTAÑA 1: CARRERA NOMINAL (Crecimiento Base 100)
    # ==============================================================================
    with hist_tab1:
        st.subheader("Evolución de $100 invertidos")

        # Definimos qué columnas graficar: Los instrumentos seleccionados + La referencia (Inflación)
        cols_to_plot = instrumentos + ['Inflación']

        # Grafico de Líneas con Plotly Express
        # Usa el DF 'df_norm' que ya tiene todos los valores empezando en 100.
        fig = px.line(
            df_norm, 
            y=cols_to_plot, 
            labels={"value": "Base 100", "fecha": "Fecha", "variable": "Instrumento"},
            color_discrete_map={"Inflación": "red"}
        )

        #PERSONALIZACIÓN DE PLOTLY:
        # Modificamos solo la línea de 'Inflación' para que sea punteada ('dot') y más gruesa.
        # Esto ayuda visualmente a diferenciar el benchmark de los activos
        fig.update_traces(patch={"line": {"dash": "dot", "width": 3}}, selector={"legendgroup": "Inflación"})
        st.plotly_chart(fig, use_container_width=True)
    
    # ==============================================================================
    # SUB-PESTAÑA 2: RENDIMIENTO REAL (Ajustado por Inflación)
    # ==============================================================================
    with hist_tab2:
        st.subheader("Ganancia/Pérdida Real (Ajustado por Inflación)")
        
        #1. CALCULO DEL TASA REAL
        # Queremos saber cuanto ganamos *por encima* de la inflacion.
        # Copiamos el DF para no alterar el original.
        df_real = df_norm.copy()

        #Iteramos por cada columna y le restamos la curva de inflación.
        # Si el resultado es positivo, ganamos poder de compra. Si es negativo, perdimos.
        for c in df_real.columns:
            df_real[c] = df_real[c] - df_norm['Inflación']
        
        # Eliminamos la columna 'Inflación' porque sería una línea plana en 0 (Inflación - Inflación = 0)
        df_real = df_real.drop(columns=['Inflación'])

        # Filtramos solo los instrumentos activos para el gráfico
        df_real = df_real[instrumentos]
        
        #2. GRAFICACION
        fig_real = px.line(
            df_real,
            labels={"value": "Ganancia/Pérdida % vs Inflación", "fecha": "Fecha"},
        )

        #3. LINEA DE REFERENCIA (CERO)
        # Agregamos una línea blanca horizontal en el 0.
        # Todo lo que esté arriba de esta línea significa que le gano a la inflacion.
        fig_real.add_hline(y=0, line_dash="dash", line_color="white", annotation_text="Empate Inflación")
        
        st.plotly_chart(fig_real, use_container_width=True)




# --------------------------------------------------DOLAR HOY--------------------------------------------------
st.divider() #--> Separador visual

# Usamos st.expander para ocultar esta sección por defecto (expanded=False).
# El usuario puede expandirla si desea ver el cotizaciones del  Dólar Hoy.
with st.expander("💵 Cotizaciones del  Dólar Hoy ", expanded=False):
    conn = st.connection("neon", type="sql")

    

    # ----------------------- 1. CONSULTA SQL INTELIGENTE -----------------------
    try:
        #Nota sobre la Query:
        # usamos una sentencia CASE en el ORDER BY.
        # Esto ordena por "Relevancia".
        # Queremos que el Oficial, Blue y MEP salgan siempre primero, sin importar su nombre.
        query_cotizaciones = """
        SELECT tipo, compra, venta, promedio, fecha
        FROM cotizaciones_dolar
        ORDER BY 
            CASE tipo
                WHEN 'Oficial' THEN 1
                WHEN 'Blue' THEN 2
                WHEN 'MEP' THEN 3
                WHEN 'CCL' THEN 4
                WHEN 'Cripto' THEN 5
                ELSE 6
            END
        """
        df_cotizaciones = conn.query(query_cotizaciones, ttl="10m")
    
        # ----------------------- 2. VISUALIZACION DE TARJETAS (METRICS) -----------------------
        #Filtramos solo los dolares mas relevantes para las tarjetas principales
        tipos_principales = ['Oficial', 'Blue', 'MEP', 'CCL', 'Cripto']
        #creamos un sub-dataframe solo con esos tipos y limitamos a 5
        df_principales = df_cotizaciones[df_cotizaciones['tipo'].isin(tipos_principales)].head(5)

        #creamos dinamicamente tantas columnas como tipos de dolar hayamos encontrado
        num_cols = len(df_principales)
        cols = st.columns(num_cols)
    
        #iteramos sobre el DF para crear una tarjeta por cada dolar
        for idx, (_, row) in enumerate(df_principales.iterrows()):
            with cols[idx]:
                # Spread: Diferencia entre punta compradora y vendedora (ganancia de la casa de cambio)
                spread = row['venta'] - row['compra']
            
                #diccionario de Emojis para darle identidad visual a cada tipo
                emoji_map = {
                    'Oficial': '🏦',  # Banco
                    'Blue': '💵',     # Billete físico
                    'MEP': '📊',      # Bolsa/Gráfico
                    'CCL': '💼',      # Maletín (Negocios exterior)
                    'Cripto': '₿',     # Bitcoin
                    'Bolsa': '📈',
                    'Mayorista': '🏭',
                    'Tarjeta': '💳'
                }
                # .get() busca el tipo, y si no lo encuentra usa '💱' por defecto
                emoji = emoji_map.get(row['tipo'], '💱')

                # Mostramos la métrica
                st.metric(
                    f"{emoji} {row['tipo']}", 
                    f"${row['venta']:,.2f}",
                    delta=f"diferencia: ${spread:,.2f}",
                    delta_color="off",
                    help=f"Compra: ${row['compra']:,.2f} | Venta: ${row['venta']:,.2f} | diferencia entre la compra y venta"
                )
    
        # ----------------------- 3. TABLA DETALLADA (OPCIONAL) -----------------------
        # Checkbox para mostrar/ocultar la tabla completa
        if st.checkbox("📋 Ver todas las cotizaciones (Tabla completa)"):
            # Trabajamos sobre una copia para no romper el DF original
            df_tabla = df_cotizaciones.copy()
        
            # Calcular diferencia
            df_tabla['diferencia'] = df_tabla['venta'] - df_tabla['compra']
            # Calculo de porcentaje de diferencia
            df_tabla['diferencia %'] = ((df_tabla['diferencia'] / df_tabla['compra']) * 100).round(2)
        
            # Renombrar columnas (Mayusculas)
            df_tabla = df_tabla.rename(columns={
                'tipo': 'Tipo',
                'compra': 'Compra',
                'venta': 'Venta',
                'promedio': 'Promedio'
            })
        
            #Formateo de Strings ($):
            # Convertimos los números a texto con signo '$'. 
            # NOTA: Una vez hecho esto, ya no se pueden hacer cálculos matemáticos con estas columnas.
            for col in ['Compra', 'Venta', 'Promedio', 'diferencia']:
                df_tabla[col] = df_tabla[col].apply(lambda x: f"${x:,.2f}")
            df_tabla['diferencia %'] = df_tabla['diferencia %'].apply(lambda x: f"{x:.2f}%")

        
            # Seleccionamos y reordenamos las columnas finales
            df_tabla = df_tabla[['Tipo', 'Compra', 'Venta', 'Promedio', 'diferencia', 'diferencia %']]
        
            # Renderizamos la tabla sin el índice numérico de Pandas --->(hide_index=True)
            st.dataframe(df_tabla, use_container_width=True, hide_index=True)
        
            #Mostramos cuando fue la ultima vez que la base de datos se actualizó
            fecha_actualizacion = pd.to_datetime(df_cotizaciones['fecha'].iloc[0])
            st.caption(f"🕒 Actualizado: {fecha_actualizacion.strftime('%d/%m/%Y %H:%M')}")

    except Exception as e:
        #manejo de errores: Si falla la conexion o la query, mostramos el error sin romper la app
        st.error(f"Error cargando cotizaciones: {e}")

    st.divider()