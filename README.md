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
│   ├── FCI_api_ETL.py              # ETL de Fondos Comunes de Inversión (Ualá, Mercado Pago, Personal Pay)
│   ├── INFLACION_api_ETL.py        # ETL de datos mensuales de inflación en Argentina
│   └── plazoFijo_api_ETL.py        # ETL de tasas de plazo fijo (registro histórico)
│
├── .env.example                    # Ejemplo de variables de entorno
├── .gitignore                     # Archivos ignorados por Git
├── backup_finanzas.sql             # Backup de la base de datos
├── docker-compose.yml              # Orquestación de servicios con Docker
├── Dockerfile                      # Imagen del proyecto
├── requirements.txt                # Dependencias del proyecto
└── README.md




