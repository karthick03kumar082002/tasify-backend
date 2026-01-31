from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from app.core.response import AppException,standard_response
from app.core.exception_handler import app_exception_handler,validation_exception_handler
# from fastapi.staticfiles import StaticFiles
from app.utils.jwt import jwt_middleware ,PUBLIC_URLS
from fastapi.middleware.cors import CORSMiddleware
from app.routers.v1_master_routes import master_routers
# ----------------------------
# Initialize FastAPI app
# ----------------------------
app = FastAPI(title="Project Management", version="1.0.0")



app.add_middleware(
    CORSMiddleware,
    "http://localhost:5173",   
        "http://127.0.0.1:5173",
        "https://tasify-frontend.vercel.app",  
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, etc.)
    allow_headers=["*"],  # Allow all headers
)



# # ----------------------------
# # Global JWT Middleware
# # ----------------------------
@app.middleware("http")
async def global_jwt_middleware(request: Request, call_next):
    #  Skip CORS preflight requests
    if request.method == "OPTIONS":
        response = await call_next(request)
        return response

    # Skip public URLs
    if any(request.url.path.startswith(path) for path in PUBLIC_URLS):
        return await call_next(request)

    # Apply JWT logic for protected routes
    try:
        return await jwt_middleware(request, call_next)
    except Exception as e:
        return standard_response(
            success=False,
            message="Unexpected error in middleware",
            error=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    


# app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
# ----------------------------
# Exception Handlers
# ----------------------------
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# ----------------------------
# Routers
# ----------------------------
app.include_router(master_routers, prefix="/api/v1")
# from fastapi import FastAPI

# app = FastAPI()

# @app.get("/")
# def root():
#     return {"message": "Taskify backend alive"}

