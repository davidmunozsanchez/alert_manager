"""
Middleware sin slowapi ni loguru - Solo librerías estándar
"""
import time
import uuid
import logging
from typing import Callable, Dict
from collections import defaultdict, deque

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .logging import set_request_context, clear_request_context, get_logger
from ..domain.exceptions import AlertManagerException

# Logger para el middleware
logger = get_logger("middleware")

class SimpleRateLimiter:
    """Rate limiter simple en memoria"""
    
    def __init__(self, max_requests: int = 100, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    def is_allowed(self, client_id: str) -> bool:
        """Verificar si la request está permitida"""
        now = time.time()
        client_requests = self.requests[client_id]
        
        # Limpiar requests antiguas
        while client_requests and client_requests[0] <= now - self.time_window:
            client_requests.popleft()
        
        # Verificar límite
        if len(client_requests) >= self.max_requests:
            return False
        
        # Añadir request actual
        client_requests.append(now)
        return True
    
    def get_remaining(self, client_id: str) -> int:
        """Obtener requests restantes"""
        now = time.time()
        client_requests = self.requests[client_id]
        
        # Limpiar requests antiguas
        while client_requests and client_requests[0] <= now - self.time_window:
            client_requests.popleft()
        
        return max(0, self.max_requests - len(client_requests))

# Rate limiter global
global_limiter = SimpleRateLimiter(max_requests=100, time_window=60)

def get_client_ip(request: Request) -> str:
    """Obtener IP del cliente"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware de logging con logger estándar"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Request ID único
        request_id = str(uuid.uuid4())
        set_request_context(request_id)
        request.state.request_id = request_id
        
        # Métricas de tiempo
        start_time = time.perf_counter()
        
        # Info de la request
        client_ip = get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")
        content_length = request.headers.get("content-length", "0")
        
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log con logger estándar
            logger.info(
                f"{request.method} {request.url.path} → {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": str(request.query_params) if request.query_params else None,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 3),
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "content_length": content_length,
                    "response_size": response.headers.get("content-length", "unknown")
                }
            )
            
            # Headers de respuesta
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{duration_ms:.3f}ms"
            
            return response
            
        except AlertManagerException as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            logger.warning(
                f"Business error: {e.error_code} - {e.message}",
                extra={
                    "request_id": request_id,
                    "error_code": e.error_code,
                    "error_message": e.message,
                    "duration_ms": round(duration_ms, 3),
                    "client_ip": client_ip
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": {
                        "code": e.error_code,
                        "message": e.message,
                        "request_id": request_id,
                        "type": "business_logic_error"
                    }
                },
                headers={
                    "X-Request-ID": request_id,
                    "X-Process-Time": f"{duration_ms:.3f}ms"
                }
            )
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            logger.error(
                f"Unexpected error: {str(e)}",
                extra={
                    "request_id": request_id,
                    "error_type": type(e).__name__,
                    "duration_ms": round(duration_ms, 3),
                    "client_ip": client_ip
                },
                exc_info=True
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "Error interno del servidor",
                        "request_id": request_id,
                        "type": "internal_error"
                    }
                },
                headers={
                    "X-Request-ID": request_id,
                    "X-Process-Time": f"{duration_ms:.3f}ms"
                }
            )
        finally:
            clear_request_context()

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware nativo"""
    
    def __init__(self, app, limiter: SimpleRateLimiter = None):
        super().__init__(app)
        self.limiter = limiter or global_limiter
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Excluir algunos endpoints del rate limiting
        if request.url.path in ["/health", "/ping", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        client_ip = get_client_ip(request)
        
        if not self.limiter.is_allowed(client_ip):
            remaining = self.limiter.get_remaining(client_ip)
            
            logger.warning(
                f"Rate limit exceeded for {client_ip}",
                extra={
                    "client_ip": client_ip,
                    "path": request.url.path,
                    "remaining": remaining
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED", 
                        "message": f"Rate limit exceeded. Max {self.limiter.max_requests} requests per {self.limiter.time_window} seconds.",
                        "retry_after": self.limiter.time_window
                    }
                },
                headers={
                    "Retry-After": str(self.limiter.time_window),
                    "X-RateLimit-Limit": str(self.limiter.max_requests),
                    "X-RateLimit-Remaining": str(self.limiter.get_remaining(client_ip)),
                    "X-RateLimit-Reset": str(int(time.time()) + self.limiter.time_window)
                }
            )
        
        response = await call_next(request)
        
        # Añadir headers de rate limit a respuestas exitosas
        remaining = self.limiter.get_remaining(client_ip)
        response.headers["X-RateLimit-Limit"] = str(self.limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.limiter.time_window)
        
        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security headers modernos"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Headers de seguridad
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "X-Permitted-Cross-Domain-Policies": "none"
        }
        
        # Solo añadir HSTS en HTTPS
        if request.url.scheme == "https":
            security_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        response.headers.update(security_headers)
        return response

class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Health check rápido"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Bypass para health checks simples
        if request.url.path in ["/health", "/ping", "/status"] and request.method == "GET":
            return JSONResponse(
                content={
                    "status": "healthy",
                    "timestamp": time.time(),
                    "service": "alert_manager",
                    "version": "1.0.0"
                },
                status_code=200,
                headers={"Cache-Control": "no-cache"}
            )
        
        return await call_next(request)