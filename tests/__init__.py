"""
Test Suite para Alert Manager

Configuración y utilities para testing:
- conftest.py: Fixtures compartidos
- test_*.py: Tests organizados por funcionalidad
"""

import sys
from pathlib import Path

# Asegurar que src está en el path para todos los tests
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configuración de testing
TEST_CONFIG = {
    "database_url": "sqlite:///./test_alerts.db",
    "test_environment": "testing"
}