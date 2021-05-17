# OSBEX: Open Source BORME Explorer
Plataforma OpenSource de explotación de datos del BORME (Boletín Oficial del Registro Mercantil)
## Propósito
OSBEX se crea con la finalidad de cubrir una alternativa Open Source a las existentes soluciones cerradas para la exploración de información del BORME ofreciendo una base para que cualquiera que lo desea pueda utilizar / mejorar / ampliar las funcionalidades del mismo, además de colaborar en la evolución del proyecto

## Estado del proyecto y TODO
Actualmente el proyecto es una __prueba de concepto__ que ya se puede utilizar por cualquier usuario que lo necesite, aunque si el proyecto progresa será sin duda necesario mejorar el empaquetado de la aplicación y tecnologías, además de otra línea de presentación.

## Flujo del funcionamiento de OSBEX

### Diagrama
![alt text](https://lh3.googleusercontent.com/fife/ABSRlIoGhtXZacSw50p4jUt3StnvOJYFrAiMNEtSWsGPOhtNQMijehri4MHo2MS6jk5hG87wkgq-uTaUmmn-jxVpc99bCtJB6bjDrk4kqrIAqXJwOKhwFzqBBJOvmq-5aH9Xi2j41lFEWfFOcaY6hqmNLhuD8B8ywl7tO-arQnPkyFFeGX9D7meBBFy9YHry_17eHiv3nx-HX4s4sEOr1cn7RHwDkK1NriCB9AAPrle7JYBUecbaNNrTM5Km84lin8nqDpsZu-_b_C_SJLcN_ZxqAP58GHvwHPAXc5FdWTSaCG9pdlew5grPsxMztPYEmR-k8f-PQasddXdBMOSWUlJzgQHa1Avee9pIsKqJaUm2SxE2QsPxSd8iY-eP3ZfM1kQBtpymX7Y3ZLtMKhOb5MYCAfHncS6GYbCe75EJ8pkqWuf-xPFPQljqQ3JTPKehjuw9-Zy5Gcynmie8LxJIPmvdy1UKg1WdDNiPEJ6fq8dpTsqn6vq799Ue1dCWeW8ist1AFDDqR6ak0zxgsQLm2JfDKsl8cXzbsAI3PivJ5HEyzKDIKL6sA8r9tmbuGe5z53en7cdnX_lLGfU9erOw3zZfO0gJ31TpC2pEjcE1cX1w_fQKLA1kyRlC7iQ3a7zKxcInK50vbhRLdaUPkJisecx_WvDKAwZ2OvBIYyCfz0mthAGDhKQ5CvC2CcIvj_2_uZQC9jhZYMBCllegtQ5WPBmMoqndPR_3SyxjdA=w1280-h608-ft)

### Descripción
La aplicación se presenta como un entorno de varios contenedores docker y conjuntado con docker-compose. Una vez se levante la infraestructura, se habrán creado 5 componentes:
+ **borme-extractor**: Es el componente encargado de comunicarse con el BORME (escrito en Python). Según la configuración que hayamos establecido para cada provincia, comenzará a solicitarle los XML y los boletines en formato PDF y realizará lectura de los mismos para convertirlos en formato entendible (JSON) y preformateado para logstash (siguiente componente) (**1.**). Una vez realizada la conversión de un boletín, lo enviará mediante HTTP (POST) a logstash (**2.**).
+ **logstash-oss**: Logstash es un componente del stack de Elastic que permite realizar ingestión de datos desde muchas fuentes, realizar procesado y enviarselo a distintos desstinos. En esta implementación se ocupa de recibir los boletines en formato JSON manteniéndose siempre a la escucha con un servidor HTTP levantado en su parte. Una vez reciba un boletín, realiza múltiples transformaciones y cortes para estructurar los datos correctamente de cara a optimizar y ingestarle los datos a OpenDistro también mediante HTTP (**3.**).
+ **opendistro** (Elasticsearch): Es una base de datos no relacional optimizada para el almacenamiento de datos en series temporales. Almacena los datos documentos que a su vez se guardan en índices de Elastic, que le permite buscar / encontrar información de manera muy ágil. Una vez recibidos los datos de logstash permanecen guardados y estructurados a la espera de consulta.
+ **grafana**: Permite crear completas visualizaciones gráficas y de representación de la información desde distintas fuentes. En este caso realiza consultas a opendistro (**4.**) cada vez que un usuario visualiza un cuadro de mandos (**5.**).
--
+ **kibana**: Aunque en este caso no pertenece al flujo de datos de OSBEX, este componente también es parte del stack de elastic y permite realizar múltiples operaciones contra elasticsearch para la gestión de los índices, visualizar los datos almacenados "en crudo" además de poder crear también visualizaciones más complejas.

## Escenarios de actuación

Dependencias: Docker y docker-compose instalados

### Configuración de la extracción por provincias
Antes de empezar a recolectar/ingestar es necesario establecer para cada provincia desde qué fecha queremos ingestar datos del BORME. Consultar en https://www.boe.es/diario_borme/calendarios.php para cada provincia cual es la fecha mínima.

+ Para configurar la extracción es necesario editar el YAML checker.yml ubicado en `borme-extractor-app/config/checker.yml` en la sección zones, por ejemplo:
```
zones:
  A CORUÑA:
    last_checked: '2020-01-01'
  LUGO:
    last_checked: '2020-01-01'
  PONTEVEDRA:
    last_checked: '2020-01-01'
```
Le estamos indicando que queremos ingestar solamente las provincias de A Coruña, Pontevedra y Lugo con las fechas establecidas. Simplemente añadir a continuación las provicincias necesarias respectando el formato YAML. Las provincias se deben de anotar tal y como aparecen en boe.es/borme_diario.

Este fichero se actualizará según se vayan descargando boletines.
### Levantar OSBEX
Ubicarse en una shell al directorio del proyecto y levantar el entorno de docker con **`docker-compose up -d`**. Comenzará a construir / descargar las imágenes de los contenedores y levantarlos. Una vez todo esté operativo borme-extractor comenzará automáticamente a descargarse los boletines y a ingestarlos.

### Parar OSBEX
Ubicarse en una shell al directorio del proyecto y parar el entorno de docker con **`docker-compose stop`**. Esto únicamente detendrá los contenedores y se podrán volver a levantar con la instrucción de levantamiento según sea necesario.

### Eliminar OSBEX
Primeramente parar OSBEX. Ubicarse en una shell al directorio del proyecto y eliminar completamente el entorno de docker con **`docker-compose rm -f`**. 
Esto eliminará todo el entorno aunque los datos de OSBEX permanecen en el volumen. Para eliminar todos los volúmenes inutilizados, ejecutar: `docker volume prune`.
Esto eliminará DEFINITIVAMENTE todos los recursos de OSBEX, incluidos los datos descargados del BORME.

### Visualizar el estado de la ingestión
Una vez levantado el entorno, abrir grafana en un navegador con http://localhost:3000 y las credenciales por defecto (admin/admin) y ubicarse en el dashboard "ESTADO INGESTION BORME" (http://localhost:3000/d/a0kcurXGk/estado-ingestion-borme?orgId=1)

## Configuraciones avanzadas

Observando el [diagrama de flujo](#diagrama) podemos ver todos los archivos de configuración implicados. 
Las cajas con forma de carpetas son la ubicación dentro del repositorio local mientras que las rutas descritas abajo de las cajas son las rutas dentro de los contenedores.

Todo esto está descrito en `docker-compose.yml` dónde podemos observar para cada componente su definición (imagen de docker a utilizar, volúmenes, rutas, configuraciones, etc.)

