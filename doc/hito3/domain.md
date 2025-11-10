# Capa de dominio - Alert Manager

## Visión general

La **capa de dominio** constituye el corazón arquitectónico de la aplicación Alert Manager, concentrando toda la lógica de negocio en un núcleo independiente de cualquier tecnología específica. Esta capa define las reglas fundamentales del negocio, las entidades principales del sistema y las operaciones que pueden ejecutarse sobre ellas, manteniendo una separación clara entre la lógica empresarial y los detalles de implementación técnica.

## Principios de diseño

La arquitectura de dominio se fundamenta en tres principios esenciales. Primero, la **independencia de frameworks** garantiza que el código no dependa de tecnologías específicas como FastAPI o SQLAlchemy, permitiendo su reutilización en diferentes contextos como aplicaciones web, interfaces de línea de comandos o suites de testing. Segundo, la **testabilidad** se logra mediante lógica pura sin efectos secundarios, facilitando la creación de pruebas unitarias rápidas y confiables. Tercero, la **expresividad** asegura que el código refleje fielmente el lenguaje del negocio, utilizando nombres descriptivos y métodos autoexplicativos que faciliten la comprensión y mantenimiento.

## Estructura y organización

La capa de dominio se organiza en cuatro archivos principales que encapsulan diferentes aspectos de la lógica de negocio. El archivo de entidades define las estructuras de datos centrales y sus comportamientos inherentes. Los servicios implementan operaciones complejas que involucran múltiples entidades. Las interfaces de repositorios establecen contratos para la persistencia de datos. Finalmente, las excepciones proporcionan un manejo de errores específico del dominio que expresa claramente los problemas de negocio.

## Entidades de dominio

El archivo `entities.py` contiene las representaciones centrales del modelo de negocio. La entidad **Alert** constituye el corazón del sistema, encapsulando toda la información relevante de una alerta incluyendo título, descripción, nivel de severidad, tipo, región geográfica, estado actual y metadatos temporales. Esta entidad incorpora métodos de negocio inteligentes que permiten determinar si una alerta ha expirado, si permanece activa, si puede ser resuelta y si requiere atención prioritaria.

Las **enumeraciones** funcionan como objetos de valor que definen vocabularios controlados para el sistema. AlertLevel establece cuatro niveles de severidad con prioridades asociadas, mientras que AlertStatus define los estados posibles de una alerta con transiciones bien definidas. AlertType proporciona una categorización comprensiva que abarca desde eventos meteorológicos hasta emergencias de seguridad.

El objeto de valor **AlertFilter** encapsula criterios de búsqueda complejos, permitiendo filtrar alertas por múltiples dimensiones como nivel, tipo, región, estado y rangos temporales. Su método de coincidencia facilita la implementación de búsquedas flexibles y eficientes.

La entidad **DataSource** representa fuentes automáticas de ingesta de datos, incorporando lógica para determinar cuándo debe verificarse una fuente, registrar verificaciones exitosas o fallidas, y evaluar el estado de salud general de la fuente basándose en patrones de disponibilidad y errores.

## Servicios de dominio

El archivo `services.py` implementa la lógica de negocio compleja que trasciende las responsabilidades de entidades individuales. El **AlertService** coordina operaciones sofisticadas como la creación de alertas con validaciones exhaustivas, el procesamiento automático de alertas expiradas, la gestión de transiciones de estado y la generación de estadísticas operacionales.

Durante la creación de alertas, el servicio aplica múltiples validaciones de negocio incluyendo verificación de longitudes mínimas para textos, validación de coordenadas geográficas dentro de rangos válidos, confirmación de que las fechas de expiración sean futuras y prevención de duplicados en la misma región. El procesamiento de alertas expiradas ejecuta automáticamente la resolución de alertas que han superado su tiempo de vigencia, registrando metadatos apropiados sobre el motivo de la resolución.

El **DataSourceService** gestiona el ciclo de vida de las fuentes de datos automatizadas, implementando lógica para verificar la salud de las fuentes, gestionar intervalos de verificación y mantener estadísticas de confiabilidad a lo largo del tiempo.

## Interfaces de repositorios

El archivo `repositories.py` define contratos abstractos que deben ser implementados por las capas exteriores del sistema. Estas interfaces establecen métodos estándar para persistencia, recuperación, búsqueda y eliminación de entidades, manteniendo la independencia del dominio respecto a tecnologías específicas de almacenamiento.

El patrón Repository abstrae completamente los detalles de persistencia, permitiendo que la lógica de dominio opere con interfaces claras y bien definidas. Esto facilita la implementación de diferentes estrategias de almacenamiento sin afectar el código de negocio central.

## Excepciones de dominio

El archivo `exceptions.py` define un sistema de excepciones específicas que expresan claramente los errores de negocio que pueden ocurrir durante las operaciones del sistema. Estas excepciones proporcionan mensajes descriptivos e información estructurada que facilita el debugging y el manejo apropiado de errores en capas superiores.

Las excepciones relacionadas con alertas cubren escenarios como alertas no encontradas, datos de entrada inválidos, intentos de duplicación y operaciones sobre alertas expiradas. Las excepciones de fuentes de datos abordan problemas de configuración, disponibilidad e integridad de las fuentes automatizadas.

## Reglas de negocio fundamentales

El sistema implementa un conjunto robusto de reglas de negocio que garantizan la integridad operacional. Las alertas están sujetas a restricciones que previenen duplicados activos en la misma región, prohíben modificaciones a alertas expiradas y establecen transiciones válidas entre estados. Las fechas de expiración deben ser futuras y las coordenadas geográficas deben ubicarse dentro de rangos terrestres válidos.

Los niveles de prioridad se organizan jerárquicamente, donde EMERGENCY y CRITICAL constituyen alta prioridad y reciben tratamiento preferencial en ordenamientos y notificaciones. Las fuentes de datos operan bajo intervalos configurables de verificación y mantienen métricas de confiabilidad que informan decisiones automáticas sobre su estado de salud.

## Beneficios arquitectónicos

Esta arquitectura de dominio proporciona ventajas significativas en términos de mantenibilidad, testabilidad y evolución del sistema. La centralización de la lógica de negocio asegura consistencia en toda la aplicación y facilita la implementación de cambios en reglas empresariales. La independencia tecnológica permite migrar entre diferentes frameworks y tecnologías sin afectar el núcleo del sistema.


