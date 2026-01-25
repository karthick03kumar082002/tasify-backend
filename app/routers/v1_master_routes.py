from fastapi import APIRouter
from app.api.v1.routes import (
                                users,
                                auth_service,
                                password_routes,
                                board_routes,
                                column_routes,
                                tasks_routes,
                                sub_tasks
                    

)
master_routers = APIRouter()

master_routers.include_router(
    users.router,
    prefix="/user",  
    tags=["Users"],  
)

master_routers.include_router(
    auth_service.router,
    prefix="/auth",  
    tags=["Authentication"],  
)
master_routers.include_router(
    password_routes.router,
    prefix="/password",  
    tags=["Password"],  
)

master_routers.include_router(
    board_routes.router,
    prefix="/board",  
    tags=["Boards"],  
)
master_routers.include_router(
    board_routes.detail_router,
    prefix="/detail",  
    tags=["Boards"],  
)

master_routers.include_router(
    column_routes.router,
    prefix="/column",  
    tags=["Column"],  
)
master_routers.include_router(
    tasks_routes.router,
    prefix="/tasks",  
    tags=["tasks"],  
)
master_routers.include_router(
    tasks_routes.move_router,
    prefix="/move",  
    tags=["DragDrop"],  
)
master_routers.include_router(
    sub_tasks.router,
    prefix="/subtask",  
    tags=["subtask"],  
)