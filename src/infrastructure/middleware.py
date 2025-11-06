"""
Middleware moderno con slowapi para rate limiting
"""
import time
import uuid
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from loguru import logger

from .logging import set_request_context, clear_request_context
from ..domain.exceptions import AlertManagerException

# Rate limiter global (usando memoria por defecto)
limiter = Limiter(key_func=get_remote_address)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware de logging con Loguru
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Request ID único
        request_id = str(uuid.uuid4())
        set_request_context(request_id)
        request.state.request_id = request_id
        
        # Métricas de tiempo
        start_time = time.perf_counter()
        
        # Info de la request
        client_ip = get_remote_address(request)
        user_agent = request.headers.get("user-agent", "unknown")
        content_length = request.headers.get("content-length", "0")
        
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log con Loguru (mucho más simple)
            logger.bind(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                query_params=str(request.query_params) if request.query_params else None,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 3),
                client_ip=client_ip,
                user_agent=user_agent,
                content_length=content_length,
                response_size=response.headers.get("content-length", "unknown")
            ).info(f"{request.method} {request.url.path} → {response.status_code}")
            
            # Headers de respuesta
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{duration_ms:.3f}ms"
            
            return response
            
        except AlertManagerException as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            logger.bind(
                request_id=request_id,
                error_code=e.error_code,
                error_message=e.message,
                duration_ms=round(duration_ms, 3),
                client_ip=client_ip
            ).warning(f"Business error: {e.error_code} - {e.message}")
            
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
            
        except RateLimitExceeded as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            logger.bind(
                request_id=request_id,
                client_ip=client_ip,
                rate_limit_detail=str(e.detail),
                duration_ms=round(duration_ms, 3)
            ).warning(f"Rate limit exceeded for {client_ip}")
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": str(e.detail),
                        "request_id": request_id,
                        "type": "rate_limit_error"
                    }
                },
                headers={
                    "X-Request-ID": request_id,
                    "Retry-After": "60"
                }
            )
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            logger.bind(
                request_id=request_id,
                error_type=type(e).__name__,
                duration_ms=round(duration_ms, 3),
                client_ip=client_ip
            ).error(f"Unexpected error: {str(e)}")
            
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

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Security headers modernos (OWASP 2024)
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Headers de seguridad actualizados
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=()",
            "X-Permitted-Cross-Domain-Policies": "none",
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin"
        }
        
        # Solo añadir HSTS en HTTPS
        if request.url.scheme == "https":
            security_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        response.headers.update(security_headers)
        return response

class HealthCheckMiddleware(BaseHTTPMiddleware):
    """
    Health check rápido sin logging completo
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Bypass completo para health checks simples
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