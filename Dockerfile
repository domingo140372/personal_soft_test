# Usa una imagen base de Python optimizada.
FROM python:3.12-slim

# Establece el directorio de trabajo.
WORKDIR /app

# Copia los requisitos e instálalos.
# Esto reduce el tamaño de la imagen final.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de tu código al contenedor.
COPY ./app /app/app
COPY .env .

# Expone el puerto por defecto de Uvicorn.
EXPOSE 8000

# Comando para ejecutar la aplicación cuando se inicie el contenedor.
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]