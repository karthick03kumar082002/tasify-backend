# from fastapi import status, Request
# from fastapi.responses import JSONResponse
# from fastapi.exceptions import RequestValidationError
# from starlette.exceptions import HTTPException as StarletteHTTPException


# # -------------------------
# # Standard response wrapper
# # -------------------------
# def standard_response(
#     success: bool,
#     message: str,
#     data=None,
#     error: str = "",
#     status_code=status.HTTP_200_OK,
# ):
#     return JSONResponse(
#         status_code=status_code,
#         content={
#             "success": success,
#             "message": message,
#             "error": error,
#             "data": data,
#         },
#     )

# # -------------------------
# # Base AppException
# # -------------------------
# class AppException(Exception):
#     def __init__(
#         self,
#         message: str,
#         error: str = None,
#         status_code: int = status.HTTP_400_BAD_REQUEST,
#     ):
#         self.message = message
#         self.error = error or message
#         self.status_code = status_code


# # -------------------------
# # Common Exceptions
# # -------------------------
# class NotFoundException(AppException):
#     def __init__(self, message: str = "Resource not found", error: str = "Not found"):
#         super().__init__(message, error, status.HTTP_404_NOT_FOUND)


# class UnauthorizedException(AppException):
#     def __init__(self, message: str = "Unauthorized", error: str = "Unauthorized"):
#         super().__init__(message, error, status.HTTP_401_UNAUTHORIZED)


# class ForbiddenException(AppException):
#     def __init__(self, message: str = "Forbidden", error: str = "Forbidden"):
#         super().__init__(message, error, status.HTTP_403_FORBIDDEN)


# class ConflictException(AppException):
#     def __init__(self, message: str = "Conflict", error: str = "Conflict"):
#         super().__init__(message, error, status.HTTP_409_CONFLICT)


# class InternalServerError(AppException):
#     def __init__(
#         self,
#         message: str = "Unexpected error occurred",
#         error: str = "Server error",
#     ):
#         super().__init__(message, error, status.HTTP_500_INTERNAL_SERVER_ERROR)


# # -------------------------
# # Exception Handlers
# # -------------------------
# async def app_exception_handler(request: Request, exc: AppException):
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={
#             "success": False,
#             "message": exc.message,
#             "error": exc.error,
#             "data": None,
#         },
#     )


# async def validation_exception_handler(request: Request, exc: RequestValidationError):
#     errors = [
#         f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
#         for err in exc.errors()
#     ]
#     body, code = standard_response(
#         success=False,
#         message="Validation error",
#         error="; ".join(errors),
#         data=None,
#         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#     )
#     return JSONResponse(status_code=code, content=body)


# async def http_exception_handler(request: Request, exc: StarletteHTTPException):
#     body, code = standard_response(
#         success=False,
#         message=exc.detail,
#         error=str(exc.detail),
#         data=None,
#         status_code=exc.status_code,
#     )
#     return JSONResponse(status_code=code, content=body)


# async def generic_exception_handler(request: Request, exc: Exception):
#     body, code = standard_response(
#         success=False,
#         message="Internal server error",
#         error=str(exc),
#         data=None,
#         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#     )
#     return JSONResponse(status_code=code, content=body)

from fastapi import status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# -------------------------
# Standard response wrapper
# -------------------------
def standard_response(
    success: bool,
    message: str,
    data=None,
    error: str = "",
    status_code=status.HTTP_200_OK,
):
    """
    Standardized JSON response
    Returns a FastAPI JSONResponse directly
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": success,
            "message": message,
            "error": error,
            "data": data,
        },
    )


# -------------------------
# Base AppException
# -------------------------
class AppException(Exception):
    def __init__(
        self,
        message: str,
        error: str = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        data: dict | None = None,   # THIS
    ):
        self.message = message
        self.error = error or message
        self.status_code = status_code
        self.data = data

# -------------------------
# Common Exceptions
# -------------------------
class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", error: str = "Not found", data: dict | None = None):
        super().__init__(message, error, status.HTTP_404_NOT_FOUND, data)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized", error: str = "Unauthorized", data: dict | None = None):
        super().__init__(message, error, status.HTTP_401_UNAUTHORIZED, data)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Forbidden", error: str = "Forbidden", data: dict | None = None):
        super().__init__(message, error, status.HTTP_403_FORBIDDEN, data)


class ConflictException(AppException):
    def __init__(self, message: str = "Conflict", error: str = "Conflict", data: dict | None = None):
        super().__init__(message, error, status.HTTP_409_CONFLICT, data)


class InternalServerError(AppException):
    def __init__(
        self,
        message: str = "Unexpected error occurred",
        error: str = "Server error",
        data: dict | None = None,
    ):
        super().__init__(message, error, status.HTTP_500_INTERNAL_SERVER_ERROR, data)


# -------------------------
# Exception Handlers
# -------------------------
async def app_exception_handler(request: Request, exc: AppException):
    """
    Handler for custom AppExceptions
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "error": exc.error,
            "data": exc.data,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler for request validation errors
    """
    errors = [
        f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
        for err in exc.errors()
    ]
    return standard_response(
        success=False,
        message="Validation error",
        error="; ".join(errors),
        data=None,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handler for HTTP exceptions
    """
    return standard_response(
        success=False,
        message=exc.detail,
        error=str(exc.detail),
        data=None,
        status_code=exc.status_code,
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handler for all uncaught exceptions
    """
    return standard_response(
        success=False,
        message="Internal server error",
        error=str(exc),
        data=None,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
