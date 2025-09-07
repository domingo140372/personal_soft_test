# personal_soft_test

FastAPI Messaging API 💬
Este proyecto es una API fue construida con FastAPI y SQLite que gestiona usuarios y un sistema de mensajería. La aplicación está contenida en un contenedor de Docker para un despliegue y desarrollo sencillos y portátiles.

🚀 Requisitos Previos
Para ejecutar la aplicación, solo necesitas tener Docker instalado en tu sistema.

Instalar Docker

🏁 Guía de Inicio Rápido
Sigue estos pasos para poner la aplicación en funcionamiento en cuestión de minutos.

1. Clonar el Repositorio
Primero, clona este repositorio en tu máquina local.


git clone git@github.com:domingo140372/personal_soft_test.git
cd personal_soft_test/
2. Construir la Imagen de Docker
Desde la raíz del proyecto (donde se encuentra el Dockerfile), ejecuta el siguiente comando para construir la imagen de la aplicación.

´$docker-compose up -- build
Este comando crea una imagen de Docker la cual incluye todas las dependencias y el código de la aplicación.

3. Ejecutar el Contenedor
Ahora, arranca el contenedor de Docker para ejecutar la aplicación.

docker run -d --name test-app-container -p 8000:8000 -v $(pwd):/app personal-test-app
docker run: Ejecuta un nuevo contenedor.

-d: Ejecuta el contenedor en modo detached (en segundo plano).

--name test-app-container: Asigna un nombre fácil de recordar al contenedor.

-p 8000:8000: Mapea el puerto 8000 de tu máquina local al puerto 8000 del contenedor, permitiendo el acceso a la API.

-v $(pwd):/app: Monta el directorio actual de tu máquina al directorio /app del contenedor. Esto es crucial para que el archivo de la base de datos database.db se cree y persista en tu máquina local.

### Nota: Tambien como opcion adicional se puede usar docker-compose
	sudo apt install docker-compose

### Nota: Crea el archivo docker-compose.yml en la raiz del proyecto si no lo tienes:
´´´
	#compose docker
	version: '3.8'

	services:
	  fastapi-app:
	    build: .
	    ports:
	      - "8000:8000"
	    volumes:
	      - .:/app
	    environment:
	      - DB_URL=sqlite:///./database.db # Define la URL de la base de datos
    	command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
´´´ 
Al terminar la instalacion del docker-compose se crea un entorno vistual de python
	cd personal_soft_test/

	@maquina:~/personal_soft_test$ python3 venv venv/
Esto crea una carpeta venv para el entorno virtual

	@maquina:~/personal_soft_test$ source venv/bin/activate
Esto ejecuta el entorno vistual.

	(venv)@maquina:~/personal_soft_test$ docker-compose up --build
Este comando crea el contenedor y lo ejecuta directamente


💻 Uso de la API
Una vez que el contenedor esté en funcionamiento, puedes interactuar con la API a través de la documentación interactiva de Swagger UI.

Abre tu navegador y navega a la siguiente URL:

http://127.0.0.1:8000/docs

Aquí encontrarás todos los endpoints disponibles, con la capacidad de probar las solicitudes directamente.

⚠️ Autenticación: La mayoría de los endpoints están protegidos y requieren un token JWT. Primero, usa la ruta /token para autenticarte y obtener un token, y luego úsalo para autorizar el resto de las solicitudes.

📁 Estructura del Proyecto
El proyecto está organizado siguiendo los principios de arquitectura limpia.

.
├── Dockerfile             # Instrucciones para crear la imagen de Docker
├── requirements.txt       # Dependencias de Python
├── database.db            # Archivo de la base de datos SQLite (generado)
├── app/
│   ├── main.py            # El controlador principal (endpoints de la API)
│   ├── services.py        # La capa de lógica de negocio
│   ├── crud.py            # La capa de repositorio (operaciones con la DB)
│   ├── models.py          # Definiciones de los modelos de datos
│   └── schemas.py         # Esquemas de validación de datos (Pydantic)
🛠️ Solución de Problemas
Si el contenedor no se inicia, puedes revisar los registros para diagnosticar el problema:

´
docker logs my-app-container
Si el puerto 8000 ya está en uso, puedes cambiar el mapeo de puertos en el comando docker run, por ejemplo, usando el puerto 8001 en su lugar:
´ 

🧪 Pruebas con Pytest
El proyecto incluye pruebas unitarias y de integración utilizando **pytest** para garantizar la calidad del código y el correcto funcionamiento de la API.

### Ejecutar las pruebas
1. Activa tu entorno virtual:
  
source venv/bin/activate
Instala las dependencias de pruebas (si aún no lo has hecho):

pip install pytest pytest-mock httpx
Estas librerías permiten ejecutar pruebas, usar mocks para aislar lógica de negocio y simular peticiones HTTP.

Crear el archivo
pytest.ini:
	´´´
		# pytest.ini

		[pytest]
		pythonpath = .
	´´´
Esto asegura que pytest acceda al codigo desde el directorio raiz

Ejecuta pytest desde la raíz del proyecto:

	(venv)@maquina:~/personal_soft_test$ pytest -v
-v muestra más detalle de cada prueba ejecutada.


