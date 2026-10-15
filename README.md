# 📊 Monitor Financiero – Proyecto Final

Proyecto final del Bootcamp 4.0 (Devlights), enfocado en el análisis, procesamiento y visualización de datos financieros mediante un pipeline de datos y un dashboard interactivo.
---

## 🎯 Objetivos
- Analizar la evolución de distintos FCI.
- Comparar rendimientos contra inflación y tipo de cambio.
- Construir un pipeline de datos reproducible.
- Visualizar métricas clave en un dashboard interactivo.

## 🛠️ Tecnologías

- **Lenguaje:** Python  
- **Análisis de datos:** Pandas, NumPy  
- **Visualización:** Matplotlib, Seaborn, Plotly, Streamlit  
- **Base de datos:** PostgreSQL (Neon)  
- **Acceso a datos:** SQLAlchemy, psycopg2, Requests  
- **Infraestructura:** Docker, Docker Compose  
- **Control de versiones:** Git & GitHub  
- **Arquitectura:** ETL, consumo de APIs

## 📂 Estructura del proyecto

```text
PROYECTO FINAL/
│
├── .devcontainer/                 # Configuración del entorno de desarrollo (Docker)
|
├── .github/workflows/             # Automatización con GitHub Actions
│   └── etl_process.yml            # Configuración de ejecución diaria de los ETLs
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
├── .gitignore                      # Archivos ignorados por Git
├── backup_finanzas.sql             # Backup de la base de datos
├── docker-compose.yml              # Orquestación de servicios con Docker
├── Dockerfile                      # Imagen del proyecto
├── requirements.txt                # Dependencias del proyecto
└── README.md
```

## 🏗️ Arquitectura del Sistema
<p align="center">
  <img src="screenshots/arquitectura.PNG" width="850">
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

🔗 **Acceso directo al Dashboard**: [![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://monitorfinanciero-tytyevfsnybzcmu5twqtlh.streamlit.app/)

### ✨ Funcionalidades

- 📊 **KPIs en tiempo real**: Inflación, Dólar, Mejor FCI, Estado
- 🔮 **Proyección Simple**: Calcula rendimiento sin aportes adicionales
- 💎 **Proyección con Aportes**: Simula ahorro sistemático mensual
- 📊 **Comparador de Fondos**: Ranking automático con medallas 🥇🥈🥉
- 🎯 **Calculadora de Objetivos**: Calcula aportes para alcanzar tu meta
- 💵 **Cotizaciones en vivo**: Todos los tipos de dólar con spread
- 📈 **Análisis histórico**: Visualización de tendencias pasadas

### 🎮 Controles Interactivos

- **Período**: 7 a 90 días
- **Tipo de Dólar**: Blue, Oficial, MEP, CCL, Cripto, etc.
- **Métrica FCI**: VCP o TNA
- **Comparación**: Selección múltiple de instrumentos

## 📸 Capturas del Dashboard

### 📊 Dashboard principal

![Dashboard principal](screenshots/principal.PNG)

### 🔮 Proyección Simple: Calcula cuánto tendrás en X meses sin aportes
  
![Proyeccion_simple](https://github.com/user-attachments/assets/c77cb694-7111-420c-a158-26812a2b850f)

### 💎 Proyección con Aportes: Simula ahorro sistemático mensual
  
![Proyeccion_aporte](https://github.com/user-attachments/assets/65cf8053-91e8-45dd-9ff0-160cb1cb5fbe)

### 📊 Comparador de Fondos: Ranking automático de todos los FCIs
  
![Comparador_fondo](https://github.com/user-attachments/assets/aef4777c-34fe-4191-af68-e4e8b344b9f9)

### 🎯 Calculadora de Objetivos: Calcula aporte mensual necesario para tu meta

![calculadora_objetivos](https://github.com/user-attachments/assets/7610a7c0-0a68-403b-a1a6-e9848113a776)

---

### 📈 Análisis histórico: Visualización de datos pasados
   
![analicis_historico](https://github.com/user-attachments/assets/042c999d-2102-4b0d-bc10-ad1c6c134b10)

---

### 💵 Cotizaciones: Dólar Blue, Oficial, MEP, CCL, Cripto
  
![dolar_hoy](https://github.com/user-attachments/assets/bed0cc28-0296-41ab-8acc-b44d1be6b70e)

---
## A Futuro . . .

### En desarrollo
- [ ] Análisis de Escenarios (Optimista/Base/Pesimista)
- [ ] Notificaciones y alertas automáticas
- [ ] Exportar reportes en PDF/Excel
- [✓] Automatizar los procesos ETL

### Futuras mejoras
- [ ] Integración con más activos (CEDEARs, Bonos, ...)
- [ ] Machine Learning para predicciones
- [ ] API REST pública


## 🧠 Conclusiones

El proyecto integra análisis e ingeniería de datos en una solución completa, demostrando la capacidad de construir pipelines de datos y visualizaciones orientadas a la toma de decisiones.

## 👤 Autor

**Luciano Riquelme** 

Estudiante de Lic. en Sistemas 
Interés en Data Analytics y Data Engineering

- 🔗 LinkedIn: https://www.linkedin.com/in/luciano-riquelme  
- 📧 Email: luciano.luiz.riquelme@gmail.com

---
## 🙏 Agradecimientos

Bootcamp 4.0 – Devlights, por el acompañamiento y el tiempo brindados.



