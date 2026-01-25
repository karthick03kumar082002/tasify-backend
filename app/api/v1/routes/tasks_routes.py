from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.schema.task_schema import TaskCreate,TaskUpdate,TaskMove
from app.services.task_servie import TaskService
from app.utils.jwt import get_current_user
router = APIRouter()

# ```````````````````````````create `````````````````````````````````````````````````
@router.post("/create")
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await TaskService(db).create_task(payload, current_user)
# ```````````````````````````get_all`````````````````````````````````````````````````
@router.get("/column/{column_id}")
async def get_tasks(
    column_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await TaskService(db).get_tasks(column_id, current_user)

# ```````````````````````````get_by_id `````````````````````````````````````````````````
@router.get("/{task_id}")
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await TaskService(db).get_task_by_id(task_id, current_user)

# ```````````````````````````update `````````````````````````````````````````````````
@router.put("/{task_id}")
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await TaskService(db).update_task(task_id, payload, current_user)

# ```````````````````````````delete `````````````````````````````````````````````````
@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await TaskService(db).delete_task(task_id, current_user)
# ```````````````````````````move `````````````````````````````````````````````````
move_router = APIRouter()
@move_router.put("/task")
async def move_task(
    payload: TaskMove,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await TaskService(db).move_task(payload, current_user)

