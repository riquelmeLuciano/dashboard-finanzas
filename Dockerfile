# Usa una imagen base de Python
FROM python:3.11-slim

# Establece el directorio de trabajo
WORKDIR /app

# CONFIGURAR LOCALES Y UTF-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONIOENCODING=utf-8

# Instala dependencias del sistema necesarias para psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia el archivo de dependencias
COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el código del proyecto
COPY . .

# Expone el puerto de Streamlit (por defecto 8501)
EXPOSE 8501

# Comando para ejecutar la aplicación
CMD ["streamlit", "run", "Dashboard/monitor_financiero.py", "--server.address", "0.0.0.0"]