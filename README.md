# 📊 Monitor Financiero – Proyecto Final

Proyecto final del Bootcamp 4.0 (Devlights), enfocado en el análisis, procesamiento y visualización de datos financieros mediante un pipeline de datos y un dashboard interactivo.
---

## 🎯 Objetivos
- Analizar la evolución de distintos FCI.
- Comparar rendimientos contra inflación y tipo de cambio.
- Construir un pipeline de datos reproducible.
- Visualizar métricas clave en un dashboard interactivo.

## 🛠️ Tecnologías
- Python    
- Pandas
- NumPy
- Matplotlib / Seaborn / plotly
- streamlit
- sqlalchemy / psycopg2
- requests
- Git / GitHub
- Docker
- ETL
- sql / neon
- api

## 📂 Estructura del proyecto

```text
PROYECTO FINAL/
│
├── .devcontainer/                 # Configuración del entorno de desarrollo (Docker)
│
├── Dashboard/
│   └── monitor_financiero.py      # Aplicación de visualización (Streamlit)
│
├── Documentación/
│   └── BASES_DE_DATOS_USADAS.docx # Documentación de las fuentes de datos
│
├── notebooks/
│   └── EDA.ipynb                  # Análisis Exploratorio de Datos (EDA)
│
├── screenshots/                   # Capturas del dashboard
│
├── Script/
│   ├── DOLAR_AHORA_ETL.py          # ETL de cotizaciones actuales de distintos tipos de dólar
│   ├── DOLAR_hist_ETL.py           # ETL histórico de cotizaciones del dólar
│   ├── FCI_api_ETL.py              # ETL de FCI (Ualá, Mercado Pago, Personal Pay)
│   ├── INFLACION_api_ETL.py        # ETL de inflación mensual en Argentina
│   └── plazoFijo_api_ETL.py        # ETL de tasas de plazo fijo (histórico)
│
├── .env.example                    # Ejemplo de variables de entorno
├── .gitignore                      # Archivos ignorados por Git
├── backup_finanzas.sql             # Backup de la base de datos
├── docker-compose.yml              # Orquestación de servicios con Docker
├── Dockerfile                      # Imagen del proyecto
├── requirements.txt                # Dependencias del proyecto
└── README.md
```

## 🏗️ Arquitectura del Sistema
<p align="center">
  <img src="screenshots/arquitectura_sistema.png" width="850">
</p>
La arquitectura del sistema se basa en un flujo ETL donde los datos financieros se obtienen desde distintas APIs públicas, se procesan y almacenan en una base de datos PostgreSQL (Neon) y finalmente se consumen desde un dashboard web desarrollado en Streamlit para su análisis interactivo.

## 💡 Problema que resuelve

El proyecto permite centralizar y analizar información financiera dispersa (FCI, dólar e inflación), facilitando la comparación de rendimientos y el análisis de tendencias económicas de forma visual e interactiva.


## 🔌 Fuentes de datos

- Fondos Comunes de Inversión (FCI)
- Cotización del dólar (actual e histórica)
- Índices de inflación en Argentina
- Tasas de interés de plazos fijos

Las fuentes se consumen mediante APIs públicas y se integran en un pipeline ETL.

## 🌐 Dashboard Web

El dashboard permite:
- Visualizar métricas financieras clave
- Comparar instrumentos de inversión
- Analizar la evolución temporal de variables económicas
- Interactuar mediante filtros dinámicos

🔗 Acceso al dashboard:  
https://monitorfinanciero-tytyevfsnybzcmu5twqtlh.streamlit.app/

## 📸 Capturas del Dashboard
![Dashboard principal](screenshots/principal.PNG)

- 🔮 Proyección Simple: Calcula cuánto tendrás en X meses sin aportes
![Proyeccion_simple](https://github.com/user-attachments/assets/c77cb694-7111-420c-a158-26812a2b850f)

- 💎 Proyección con Aportes: Simula ahorro sistemático mensual
![Proyeccion_aporte](https://github.com/user-attachments/assets/65cf8053-91e8-45dd-9ff0-160cb1cb5fbe)

- 📊 Comparador de Fondos: Ranking automático de todos los FCIs
![Comparador_fondo](https://github.com/user-attachments/assets/aef4777c-34fe-4191-af68-e4e8b344b9f9)

🎯 Calculadora de Objetivos: Calcula aporte mensual necesario para tu meta
![calculadora_objetivos](https://github.com/user-attachments/assets/7610a7c0-0a68-403b-a1a6-e9848113a776)

---

- 📈 Análisis histórico: Visualización de datos pasados 
![analicis_historico](https://github.com/user-attachments/assets/042c999d-2102-4b0d-bc10-ad1c6c134b10)

---

- 💵 Cotizaciones en vivo: Dólar Blue, Oficial, MEP, CCL, Cripto
![dolar_hoy](https://github.com/user-attachments/assets/bed0cc28-0296-41ab-8acc-b44d1be6b70e)

---







