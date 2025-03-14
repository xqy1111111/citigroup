from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        # 仅在访问API文档相关页面时添加自定义CSP
        if request.url.path in ["/docs", "/redoc", "/openapi.json"] or request.url.path.startswith("/docs/") or request.url.path.startswith("/redoc/"):
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net http://localhost:* https://fastapi.tiangolo.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net http://localhost:*; "
                "img-src 'self' data: https://fastapi.tiangolo.com http://localhost:*; "
                "connect-src 'self' http://localhost:*; "
                "font-src 'self' data: https://cdn.jsdelivr.net; "
                "frame-src 'self'; "
                "object-src 'none';"
            )
            response.headers["Content-Security-Policy"] = csp_policy
            
            # 添加其他安全头
            response.headers.update({
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "SAMEORIGIN",
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "Referrer-Policy": "strict-origin-when-cross-origin"
            })
        return response

def add_security_middleware(app):
    """添加安全中间件到应用"""
    app.add_middleware(SecurityMiddleware) 