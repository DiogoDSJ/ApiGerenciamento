from datetime import datetime, timezone
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions import AppException


def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Captura qualquer exceção que herde de AppException."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": request.url.path,
        },
    )


def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Padroniza erros de validação automática de esquemas do Pydantic (422 -> 422 padronizado)."""
    errors_summary = []
    for err in exc.errors():
        field_path = " -> ".join(str(loc) for loc in err["loc"] if loc != "body")
        errors_summary.append(
            {
                "field": field_path or "root",
                "message": err["msg"],
                "type": err["type"],
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error_code": "VALIDATION_ERROR",
            "message": "Os dados enviados na requisição são inválidos.",
            "details": {"validation_errors": errors_summary},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": request.url.path,
        },
    )
