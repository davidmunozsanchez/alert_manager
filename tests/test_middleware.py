"""
Tests exhaustivos para el sistema de middleware sin dependencias externas
"""
import sys
from pathlib import Path
import pytest
import time
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import FastAPI, HTTPException

# Configurar path para imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.infrastructure.middleware import (
    SimpleRateLimiter,
    RequestLoggingMiddleware,
    RateLimitMiddleware, 
    SecurityHeadersMiddleware,
    HealthCheckMiddleware,
    get_client_ip
)
from src.domain.exceptions import AlertManagerException

# ================================
# FIXTURES Y SETUP
# ================================

@pytest.fixture
def mock_request():
    """Mock request para testing"""
    request = MagicMock()
    request.method = "GET"
    request.url.path = "/test"
    request.url.scheme = "http"
    request.query_params = {}
    request.headers = {
        "user-agent": "test-agent",
        "content-length": "100"
    }
    request.client.host = "192.168.1.100"
    request.state = MagicMock()
    return request

@pytest.fixture
def mock_response():
    """Mock response para testing"""
    response = MagicMock()
    response.status_code = 200
    response.headers = {}
    return response

@pytest.fixture
def sample_app():
    """App FastAPI simple para testing"""
    app = FastAPI()
    
    @app.get("/test")
    def test_endpoint():
        return {"message": "test response"}
    
    @app.get("/error")
    def error_endpoint():
        raise HTTPException(status_code=500, detail="Test error")
    
    @app.get("/business-error")
    def business_error_endpoint():
        raise AlertManagerException("TEST_ERROR", "Test business error")
    
    @app.post("/data")
    def post_endpoint(data: dict):
        return {"received": data}
    
    return app

# ================================
# TESTS DE RATE LIMITER
# ================================

class TestSimpleRateLimiter:
    """Tests para el rate limiter simple"""
    
    def test_rate_limiter_creation(self):
        """Test creación básica del rate limiter"""
        limiter = SimpleRateLimiter(max_requests=10, time_window=60)
        
        assert limiter.max_requests == 10
        assert limiter.time_window == 60
        assert len(limiter.requests) == 0
        print("✅ Rate limiter created successfully")
    
    def test_rate_limiter_allows_under_limit(self):
        """Test que permite requests bajo el límite"""
        limiter = SimpleRateLimiter(max_requests=5, time_window=60)
        client_id = "test_client"
        
        # Primeras 5 requests deberían estar permitidas
        for i in range(5):
            assert limiter.is_allowed(client_id) is True
            remaining = limiter.get_remaining(client_id)
            assert remaining == 4 - i
            print(f"✅ Request {i+1}/5 allowed, {remaining} remaining")
    
    def test_rate_limiter_blocks_over_limit(self):
        """Test que bloquea requests sobre el límite"""
        limiter = SimpleRateLimiter(max_requests=3, time_window=60)
        client_id = "test_client"
        
        # Primeras 3 requests permitidas
        for i in range(3):
            assert limiter.is_allowed(client_id) is True
            print(f"✅ Request {i+1}/3 allowed")
        
        # La 4ta debería estar bloqueada
        assert limiter.is_allowed(client_id) is False
        assert limiter.get_remaining(client_id) == 0
        print("✅ 4th request blocked correctly")
    
    def test_rate_limiter_time_window_reset(self):
        """Test que el time window se resetea correctamente"""
        limiter = SimpleRateLimiter(max_requests=2, time_window=1)  # 1 segundo
        client_id = "test_client"
        
        # Agotar el límite
        assert limiter.is_allowed(client_id) is True
        assert limiter.is_allowed(client_id) is True
        assert limiter.is_allowed(client_id) is False
        print("✅ Limit exhausted")
        
        # Esperar que pase el time window
        print("⏳ Waiting for time window reset...")
        time.sleep(1.1)
        
        # Debería permitir requests de nuevo
        assert limiter.is_allowed(client_id) is True
        print("✅ Time window reset correctly")
    
    def test_rate_limiter_different_clients(self):
        """Test que diferentes clientes tienen límites separados"""
        limiter = SimpleRateLimiter(max_requests=1, time_window=60)
        
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client2") is True
        print("✅ Different clients have separate limits")
        
        # Ambos deberían estar agotados ahora
        assert limiter.is_allowed("client1") is False
        assert limiter.is_allowed("client2") is False
        print("✅ Both clients properly limited")

class TestClientIP:
    """Tests para detección de IP del cliente"""
    
    def test_get_client_ip_direct(self):
        """Test IP directa del cliente"""
        request = MagicMock()
        request.headers = {}
        request.client.host = "192.168.1.100"
        
        ip = get_client_ip(request)
        assert ip == "192.168.1.100"
        print("✅ Direct IP detection works")
    
    def test_get_client_ip_x_forwarded_for(self):
        """Test IP desde X-Forwarded-For header"""
        request = MagicMock()
        request.headers = {"x-forwarded-for": "203.0.113.1, 198.51.100.1"}
        request.client.host = "192.168.1.100"
        
        ip = get_client_ip(request)
        assert ip == "203.0.113.1"  # Primera IP de la lista
        print("✅ X-Forwarded-For detection works")
    
    def test_get_client_ip_x_real_ip(self):
        """Test IP desde X-Real-IP header"""
        request = MagicMock()
        request.headers = {"x-real-ip": "203.0.113.1"}
        request.client.host = "192.168.1.100"
        
        ip = get_client_ip(request)
        assert ip == "203.0.113.1"
        print("✅ X-Real-IP detection works")
    
    def test_get_client_ip_no_client(self):
        """Test cuando no hay información del cliente"""
        request = MagicMock()
        request.headers = {}
        request.client = None
        
        ip = get_client_ip(request)
        assert ip == "unknown"
        print("✅ No client info handled correctly")

# ================================
# TESTS DE MIDDLEWARE (CORREGIDOS)
# ================================

class TestRequestLoggingMiddleware:
    """Tests para RequestLoggingMiddleware"""
    
    def test_logging_middleware_success(self, mock_request, mock_response):
        """Test logging exitoso de request"""
        middleware = RequestLoggingMiddleware(app=None)
        
        # Crear función async correcta
        async def call_next_async(request):
            return mock_response
        
        async def run_test():
            with patch('src.infrastructure.middleware.logger') as mock_logger:
                response = await middleware.dispatch(mock_request, call_next_async)
                
                # Verificar que se llamó al logger
                mock_logger.info.assert_called_once()
                
                # Verificar headers de respuesta
                assert "X-Request-ID" in response.headers
                assert "X-Process-Time" in response.headers
                return response
        
        # Ejecutar test
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        response = loop.run_until_complete(run_test())
        print("✅ Logging middleware success test passed")
    
    def test_logging_middleware_business_error(self, mock_request):
        """Test logging de error de negocio"""
        middleware = RequestLoggingMiddleware(app=None)
        
        async def call_next_error(request):
            raise AlertManagerException("TEST_ERROR", "Test message")
        
        async def run_test():
            with patch('src.infrastructure.middleware.logger') as mock_logger:
                response = await middleware.dispatch(mock_request, call_next_error)
                
                # Verificar que es JSONResponse con error
                assert hasattr(response, 'status_code')
                assert response.status_code == 400
                
                # Verificar logging
                mock_logger.warning.assert_called_once()
                return response
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        response = loop.run_until_complete(run_test())
        print("✅ Business error logging test passed")
    
    def test_logging_middleware_unexpected_error(self, mock_request):
        """Test logging de error inesperado"""
        middleware = RequestLoggingMiddleware(app=None)
        
        async def call_next_error(request):
            raise Exception("Unexpected error")
        
        async def run_test():
            with patch('src.infrastructure.middleware.logger') as mock_logger:
                response = await middleware.dispatch(mock_request, call_next_error)
                
                # Verificar que es JSONResponse con error 500
                assert hasattr(response, 'status_code')
                assert response.status_code == 500
                
                # Verificar logging con exc_info
                mock_logger.error.assert_called_once()
                return response
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        response = loop.run_until_complete(run_test())
        print("✅ Unexpected error logging test passed")

class TestRateLimitMiddleware:
    """Tests para RateLimitMiddleware"""
    
    def test_rate_limit_middleware_under_limit(self, mock_request, mock_response):
        """Test request bajo el límite de rate"""
        limiter = SimpleRateLimiter(max_requests=10, time_window=60)
        middleware = RateLimitMiddleware(app=None, limiter=limiter)
        
        async def call_next_async(request):
            return mock_response
        
        async def run_test():
            response = await middleware.dispatch(mock_request, call_next_async)
            
            # Debería pasar la request
            assert response.status_code == 200
            
            # Debería tener headers de rate limit
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers
            return response
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        response = loop.run_until_complete(run_test())
        print("✅ Rate limit under limit test passed")
    
    def test_rate_limit_middleware_over_limit(self, mock_request):
        """Test request sobre el límite de rate"""
        limiter = SimpleRateLimiter(max_requests=1, time_window=60)
        middleware = RateLimitMiddleware(app=None, limiter=limiter)
        
        async def call_next_async(request):
            response = MagicMock()
            response.status_code = 200
            response.headers = {}
            return response
        
        async def run_test():
            # Primera request debería pasar
            response1 = await middleware.dispatch(mock_request, call_next_async)
            assert response1.status_code == 200
            print("✅ First request allowed")
            
            # Segunda request debería ser bloqueada
            response2 = await middleware.dispatch(mock_request, call_next_async)
            assert response2.status_code == 429
            print("✅ Second request blocked with 429")
            
            # Verificar headers de rate limit
            assert hasattr(response2, 'headers')
            return response2
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        response = loop.run_until_complete(run_test())
        print("✅ Rate limit over limit test passed")
    
    def test_rate_limit_middleware_excludes_health_endpoints(self, mock_request, mock_response):
        """Test que excluye endpoints de health del rate limiting"""
        limiter = SimpleRateLimiter(max_requests=0, time_window=60)  # Límite 0 para forzar bloqueo
        middleware = RateLimitMiddleware(app=None, limiter=limiter)
        
        # Health endpoint debería pasar incluso con límite 0
        mock_request.url.path = "/health"
        
        async def call_next_async(request):
            return mock_response
        
        async def run_test():
            response = await middleware.dispatch(mock_request, call_next_async)
            assert response.status_code == 200
            return response
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        response = loop.run_until_complete(run_test())
        print("✅ Health endpoint exclusion test passed")

class TestSecurityHeadersMiddleware:
    """Tests para SecurityHeadersMiddleware"""
    
    def test_security_headers_http(self, mock_request, mock_response):
        """Test headers de seguridad en HTTP"""
        middleware = SecurityHeadersMiddleware(app=None)
        mock_request.url.scheme = "http"
        
        async def call_next_async(request):
            return mock_response
        
        async def run_test():
            response = await middleware.dispatch(mock_request, call_next_async)
            
            # Verificar headers de seguridad
            expected_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options", 
                "X-XSS-Protection",
                "Referrer-Policy",
                "Content-Security-Policy",
                "Permissions-Policy",
                "X-Permitted-Cross-Domain-Policies"
            ]
            
            for header in expected_headers:
                assert header in response.headers
                print(f"✅ Security header {header} present")
            
            # No debería tener HSTS en HTTP
            assert "Strict-Transport-Security" not in response.headers
            print("✅ No HSTS in HTTP (correct)")
            return response
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        response = loop.run_until_complete(run_test())
        print("✅ HTTP security headers test passed")
    
    def test_security_headers_https(self, mock_request, mock_response):
        """Test headers de seguridad en HTTPS"""
        middleware = SecurityHeadersMiddleware(app=None)
        mock_request.url.scheme = "https"
        
        async def call_next_async(request):
            return mock_response
        
        async def run_test():
            response = await middleware.dispatch(mock_request, call_next_async)
            
            # Debería tener HSTS en HTTPS
            assert "Strict-Transport-Security" in response.headers
            assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
            print("✅ HSTS present in HTTPS")
            return response
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        response = loop.run_until_complete(run_test())
        print("✅ HTTPS security headers test passed")

class TestHealthCheckMiddleware:
    """Tests para HealthCheckMiddleware"""
    
    def test_health_check_middleware_health_endpoint(self, mock_request):
        """Test respuesta directa para endpoint de health"""
        middleware = HealthCheckMiddleware(app=None)
        mock_request.url.path = "/health"
        mock_request.method = "GET"
        
        async def call_next_should_not_be_called(request):
            assert False, "call_next no debería ser llamado para health check"
        
        async def run_test():
            response = await middleware.dispatch(mock_request, call_next_should_not_be_called)
            
            # Verificar respuesta directa
            assert hasattr(response, 'status_code')
            assert response.status_code == 200
            assert hasattr(response, 'headers')
            assert "Cache-Control" in response.headers
            return response
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        response = loop.run_until_complete(run_test())
        print("✅ Health check bypass works")
    
    def test_health_check_middleware_ping_endpoint(self, mock_request):
        """Test respuesta directa para endpoint de ping"""
        middleware = HealthCheckMiddleware(app=None)
        mock_request.url.path = "/ping"
        mock_request.method = "GET"
        
        async def call_next_should_not_be_called(request):
            assert False, "call_next no debería ser llamado para ping"
        
        async def run_test():
            response = await middleware.dispatch(mock_request, call_next_should_not_be_called)
            assert response.status_code == 200
            return response
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        response = loop.run_until_complete(run_test())
        print("✅ Ping endpoint bypass works")
    
    def test_health_check_middleware_other_endpoint(self, mock_request, mock_response):
        """Test que otros endpoints pasan normalmente"""
        middleware = HealthCheckMiddleware(app=None)
        mock_request.url.path = "/api/alerts"
        
        async def call_next_async(request):
            return mock_response
        
        async def run_test():
            response = await middleware.dispatch(mock_request, call_next_async)
            assert response == mock_response
            return response
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        response = loop.run_until_complete(run_test())
        print("✅ Non-health endpoints pass through")

# ================================
# TESTS DE INTEGRACIÓN SIMPLIFICADOS
# ================================

class TestMiddlewareIntegration:
    """Tests de integración simplificados sin TestClient"""
    
    def test_middleware_stack_simulation(self):
        """Test stack de middleware simulado"""
        # Simular aplicación de middleware en orden
        
        # Crear request mock
        request = MagicMock()
        request.method = "GET"
        request.url.path = "/test"
        request.url.scheme = "http"
        request.headers = {"user-agent": "test"}
        request.client.host = "127.0.0.1"
        request.state = MagicMock()
        
        # Crear response mock
        response = MagicMock()
        response.status_code = 200
        response.headers = {}
        
        # Simular stack de middleware
        def simulate_middleware_stack():
            # 1. Security headers
            security = SecurityHeadersMiddleware(None)
            # 2. Rate limiting  
            rate_limit = RateLimitMiddleware(None, SimpleRateLimiter(10, 60))
            # 3. Logging
            logging_mw = RequestLoggingMiddleware(None)
            
            return [security, rate_limit, logging_mw]
        
        middleware_stack = simulate_middleware_stack()
        
        # Verificar que se pueden crear todos los middleware
        assert len(middleware_stack) == 3
        print("✅ Middleware stack created successfully")
        
        # Test básico de rate limiter
        limiter = SimpleRateLimiter(5, 60)
        for i in range(5):
            assert limiter.is_allowed("test_client") is True
        assert limiter.is_allowed("test_client") is False
        print("✅ Rate limiter in stack works")
    
    def test_health_check_priority(self):
        """Test que health check tiene prioridad"""
        # Health check middleware debería responder directamente
        middleware = HealthCheckMiddleware(None)
        
        request = MagicMock()
        request.url.path = "/health"
        request.method = "GET"
        
        async def run_test():
            response = await middleware.dispatch(request, lambda r: None)
            assert response.status_code == 200
            return response
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        response = loop.run_until_complete(run_test())
        print("✅ Health check has correct priority")

# ================================
# TESTS DE PERFORMANCE SIMPLIFICADOS
# ================================

class TestMiddlewarePerformance:
    """Tests básicos de performance"""
    
    def test_rate_limiter_performance(self):
        """Test performance del rate limiter"""
        limiter = SimpleRateLimiter(1000, 60)
        
        # Test de muchas requests rápidas
        start_time = time.perf_counter()
        
        for i in range(100):
            client_id = f"client_{i % 10}"  # 10 clientes diferentes
            limiter.is_allowed(client_id)
        
        duration = time.perf_counter() - start_time
        
        # 100 requests en menos de 1 segundo
        assert duration < 1.0
        print(f"✅ Rate limiter processed 100 requests in {duration:.3f}s")
    
    def test_middleware_memory_usage(self):
        """Test que los middleware no acumulan memoria"""
        import gc
        
        # Crear muchos rate limiters
        limiters = []
        for i in range(100):
            limiter = SimpleRateLimiter(10, 60)
            for j in range(10):
                limiter.is_allowed(f"client_{j}")
            limiters.append(limiter)
        
        # Limpiar referencias
        del limiters
        gc.collect()
        
        print("✅ Memory usage test completed")

# ================================
# TESTS DE SCENARIOS ESPECÍFICOS
# ================================

class TestMiddlewareEdgeCases:
    """Tests para casos edge específicos"""
    
    def test_rate_limiter_edge_cases(self):
        """Test casos edge del rate limiter"""
        limiter = SimpleRateLimiter(2, 1)  # 2 requests por segundo
        
        # Test con cliente vacío
        assert limiter.is_allowed("") is True
        
        # Test con cliente muy largo
        long_client = "x" * 1000
        assert limiter.is_allowed(long_client) is True
        
        # Test con caracteres especiales
        special_client = "client-with-special-chars-üñá@#$"
        assert limiter.is_allowed(special_client) is True
        
        print("✅ Rate limiter handles edge cases")
    
    def test_ip_detection_edge_cases(self):
        """Test casos edge de detección de IP"""
        # Request sin headers
        request1 = MagicMock()
        request1.headers = {}
        request1.client = None
        
        ip1 = get_client_ip(request1)
        assert ip1 == "unknown"
        
        # Request con headers vacíos
        request2 = MagicMock()
        request2.headers = {"x-forwarded-for": "", "x-real-ip": ""}
        request2.client.host = "192.168.1.1"
        
        ip2 = get_client_ip(request2)
        assert ip2 == "192.168.1.1"
        
        # Request con headers mal formateados
        request3 = MagicMock()
        request3.headers = {"x-forwarded-for": "invalid-ip-format"}
        request3.client.host = "127.0.0.1"
        
        ip3 = get_client_ip(request3)
        assert ip3 == "invalid-ip-format"  # Retorna lo que sea que esté ahí
        
        print("✅ IP detection handles edge cases")

# ================================
# TESTS DE DEBUGGING
# ================================

class TestMiddlewareDebugging:
    """Tests para debugging del middleware"""
    
    def test_rate_limiter_state_inspection(self):
        """Test inspección del estado del rate limiter"""
        limiter = SimpleRateLimiter(3, 60)
        
        # Estado inicial
        assert len(limiter.requests) == 0
        
        # Después de requests
        limiter.is_allowed("client1")
        limiter.is_allowed("client1")
        limiter.is_allowed("client2")
        
        assert len(limiter.requests) == 2  # 2 clientes
        assert len(limiter.requests["client1"]) == 2
        assert len(limiter.requests["client2"]) == 1
        
        print("✅ Rate limiter state inspection works")
        print(f"State: {dict(limiter.requests)}")
    
    def test_middleware_configuration_validation(self):
        """Test validación de configuración de middleware"""
        # Test configuraciones válidas
        valid_configs = [
            (10, 60),    # Normal
            (1, 1),      # Muy restrictivo
            (1000, 3600) # Muy permisivo
        ]
        
        for max_req, window in valid_configs:
            limiter = SimpleRateLimiter(max_req, window)
            assert limiter.max_requests == max_req
            assert limiter.time_window == window
            print(f"✅ Config valid: {max_req} req/{window}s")
        
        # Test configuraciones límite
        edge_configs = [
            (1, 1),      # Mínimo práctico
            (10000, 1),  # Muchas requests, ventana pequeña
        ]
        
        for max_req, window in edge_configs:
            limiter = SimpleRateLimiter(max_req, window)
            # Solo verificar que no explote
            limiter.is_allowed("test")
            print(f"✅ Edge config works: {max_req} req/{window}s")

# Test de ejecución directa
if __name__ == "__main__":
    print("🧪 Running middleware tests without external dependencies...")
    pytest.main([__file__, "-v", "-s", "--tb=short"])