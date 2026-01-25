from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.response import AppException


async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "data": {},
            "error": exc.error,
        },
    )

async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    # Take first error (clean & simple)
    first_error = exc.errors()[0]

    field = " -> ".join(map(str, first_error["loc"]))
    message = first_error["msg"]

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": f"{field}: {message}",
            "data": {},
            "error": "VALIDATION_ERROR",
        },
    )