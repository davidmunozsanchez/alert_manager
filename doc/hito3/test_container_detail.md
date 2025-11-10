
### test_01_wait_for_database
Prueba la conectividad y accesibilidad de la base de datos. Verifica que el motor de base de datos pueda ser creado y que una consulta simple (`SELECT 1`) pueda ejecutarse exitosamente. Incluye lógica de reintentos con timeout configurable.

### test_02_wait_for_web_service
Prueba la accesibilidad del servicio web y el endpoint de salud. Verifica que la aplicación web esté ejecutándose y respondiendo con un estado saludable. Incluye manejo especial para entornos de CI con timeouts extendidos y lógica de reintentos adaptativa.

### test_03_seq_logging_platform
Prueba la accesibilidad y funcionalidad de la plataforma de logging centralizada Seq. Verifica que la interfaz web de Seq sea accesible y prueba el endpoint de API enviando una entrada de log de prueba para asegurar que la ingesta de logs funcione correctamente.

### test_04_dozzle_docker_logs_viewer
Prueba la accesibilidad del visor de logs de Docker Dozzle. Verifica que la interfaz web de Dozzle esté ejecutándose y sea accesible para ver logs de contenedores Docker en tiempo real.

### test_05_file_browser_logs_access
Prueba la accesibilidad del File Browser para gestión de archivos de log. Verifica que la interfaz web de File Browser esté ejecutándose y pueda usarse para acceder y gestionar archivos de log a través de una interfaz web.

### test_06_log_integration_test
Prueba la integración de logging de extremo a extremo. Activa la generación de logs de prueba a través del endpoint test-logs del servicio web y verifica que los logs sean escritos correctamente a archivos locales y procesados a través del pipeline de logging.

### test_07_web_service_endpoints
Prueba los endpoints principales de API del servicio web. Verifica que los endpoints principales (root, ping) sean accesibles y respondan correctamente con formatos de respuesta esperados.

### test_08_web_database_integration
Prueba la integración entre el servicio web y la base de datos. Verifica que el servicio web pueda conectarse exitosamente y comunicarse con la base de datos verificando la información de estado de la base de datos del endpoint de salud.

### test_09_web_service_basic_api
Prueba operaciones básicas de API en el endpoint de alertas. Maneja escenarios con y sin autenticación, y soporta tanto respuestas paginadas como directas de lista desde la API.

### test_10_airflow_webserver_health
Prueba la accesibilidad y salud del servidor web de Apache Airflow. Verifica que la interfaz web de Airflow esté ejecutándose y respondiendo, con timeouts extendidos para entornos de CI donde Airflow puede tardar más en iniciar.

### test_11_log_tester_container
Prueba la funcionalidad del contenedor log-tester. Verifica que el contenedor dedicado de generación de logs esté enviando correctamente logs a Seq para probar la funcionalidad del pipeline de logging.

### test_12_all_services_integration
Prueba de integración integral que verifica que todos los servicios estén ejecutándose y puedan comunicarse entre sí. Prueba base de datos, servicio web, Airflow, Seq, Dozzle y File Browser, proporcionando un reporte de estado completo del estado operacional de todo el sistema.