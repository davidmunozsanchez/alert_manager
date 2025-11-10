"""
Interfaces (contratos) para repositorios del dominio
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from .entities import Alert, AlertFilter, AlertStatus, DataSource

class AlertRepository(ABC):
    """Interfaz para el repositorio de alertas"""
    
    @abstractmethod
    def save(self, alert: Alert) -> Alert:
        """Guarda una alerta"""
        pass
    
    @abstractmethod
    def find_by_id(self, alert_id: int) -> Optional[Alert]:
        """Busca una alerta por ID"""
        pass
    
    @abstractmethod
    def find_all(self, filter: Optional[AlertFilter] = None) -> List[Alert]:
        """Busca todas las alertas con filtros opcionales"""
        pass
    
    @abstractmethod
    def delete(self, alert_id: int) -> bool:
        """Elimina una alerta"""
        pass
    
    @abstractmethod
    def exists_by_title_and_region(self, title: str, region: str) -> bool:
        """Verifica si existe una alerta con título y región específicos"""
        pass
    
    @abstractmethod
    def count_by_status(self, status: AlertStatus) -> int:
        """Cuenta alertas por estado"""
        pass
    
    @abstractmethod
    def find_expired_active_alerts(self) -> List[Alert]:
        """Encuentra alertas activas que han expirado"""
        pass

class DataSourceRepository(ABC):
    """Interfaz para el repositorio de fuentes de datos"""
    
    @abstractmethod
    def save(self, data_source: DataSource) -> DataSource:
        """Guarda una fuente de datos"""
        pass
    
    @abstractmethod
    def find_by_id(self, source_id: int) -> Optional[DataSource]:
        """Busca una fuente de datos por ID"""
        pass
    
    @abstractmethod
    def find_all_active(self) -> List[DataSource]:
        """Busca todas las fuentes de datos activas"""
        pass
    
    @abstractmethod
    def find_ready_for_check(self) -> List[DataSource]:
        """Busca fuentes de datos listas para verificar"""
        pass