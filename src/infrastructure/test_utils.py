"""
Utilidades para testing del middleware
"""
import uuid
from typing import Optional
from fastapi import Request
from starlette.datastructures import Headers, QueryParams
from starlette.requests import HTTPConnection

from .logging import set_request_context, clear_request_context

class MockRequest:
    """Mock request para testing de middleware"""
    
    def __init__(
        self, 
        method: str = "GET", 
        path: str = "/", 
        headers: Optional[dict] = None,
        query_params: Optional[dict] = None,
        client_ip: str = "127.0.0.1"
    ):
        self.method = method
        self.url = MockURL(path, query_params or {})
        self.headers = Headers(headers or {})
        self.query_params = QueryParams(query_params or {})
        self.client = MockClient(client_ip)
        self.state = MockState()

class MockURL:
    """Mock URL para testing"""
    
    def __init__(self, path: str, query_params: dict):
        self.path = path
        self.query_params = query_params
    
    def __str__(self):
        if self.query_params:
            query_string = "&".join(f"{k}={v}" for k, v in self.query_params.items())
            return f"{self.path}?{query_string}"
        return self.path

class MockClient:
    """Mock client para testing"""
    
    def __init__(self, host: str):
        self.host = host

class MockState:
    """Mock state para testing"""
    
    def __init__(self):
        self._data = {}
    
    def __setattr__(self, name: str, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            self._data[name] = value
    
    def __getattr__(self, name: str):
        return self._data.get(name)

def setup_test_request_context(request_id: Optional[str] = None) -> str:
    """
    Configura contexto de request para testing
    
    Returns:
        str: El request_id generado o usado
    """
    if request_id is None:
        request_id = str(uuid.uuid4())
    
    set_request_context(request_id)
    return request_id

def cleanup_test_request_context():
    """Limpia el contexto de request después del test"""
    clear_request_context()