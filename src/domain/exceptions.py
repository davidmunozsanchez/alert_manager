"""
Excepciones del dominio de negocio
"""

class AlertManagerException(Exception):
    """Excepción base del sistema de alertas"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class AlertNotFoundException(AlertManagerException):
    """Excepción cuando no se encuentra una alerta"""
    def __init__(self, alert_id: int):
        super().__init__(f"Alerta con ID {alert_id} no encontrada", "ALERT_NOT_FOUND")

class InvalidAlertDataException(AlertManagerException):
    """Excepción para datos de alerta inválidos"""
    def __init__(self, field: str, value: str, reason: str):
        super().__init__(f"Campo '{field}' con valor '{value}' es inválido: {reason}", "INVALID_ALERT_DATA")

class AlertExpiredException(AlertManagerException):
    """Excepción cuando una alerta ha expirado"""
    def __init__(self, alert_id: int):
        super().__init__(f"La alerta {alert_id} ha expirado", "ALERT_EXPIRED")

class DuplicateAlertException(AlertManagerException):
    """Excepción cuando se intenta crear una alerta duplicada"""
    def __init__(self, title: str, region: str):
        super().__init__(f"Ya existe una alerta '{title}' en la región '{region}'", "DUPLICATE_ALERT")

class InvalidAlertLevelException(AlertManagerException):
    """Excepción para nivel de alerta inválido"""
    def __init__(self, level: str):
        valid_levels = ["info", "warning", "critical", "emergency"]
        super().__init__(f"Nivel '{level}' inválido. Niveles válidos: {valid_levels}", "INVALID_ALERT_LEVEL")

class InvalidAlertStatusException(AlertManagerException):
    """Excepción para estado de alerta inválido"""
    def __init__(self, status: str):
        valid_statuses = ["active", "resolved", "pending", "cancelled"]
        super().__init__(f"Estado '{status}' inválido. Estados válidos: {valid_statuses}", "INVALID_ALERT_STATUS")

class DataSourceException(AlertManagerException):
    """Excepción para problemas con fuentes de datos automáticas"""
    def __init__(self, source: str, reason: str):
        super().__init__(f"Error en fuente de datos '{source}': {reason}", "DATA_SOURCE_ERROR")

class AirflowTaskException(AlertManagerException):
    """Excepción para problemas con tareas de Airflow"""
    def __init__(self, task_id: str, reason: str):
        super().__init__(f"Error en tarea Airflow '{task_id}': {reason}", "AIRFLOW_TASK_ERROR")