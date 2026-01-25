from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.schema.task_schema import SubTaskCreate,SubTaskUpdate
from app.services.sub_task_service import SubTaskService
from app.utils.jwt import get_current_user
router = APIRouter()

@router.post("/create")
async def create_subtask(
    payload: SubTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await SubTaskService(db).create_subtask(payload, current_user)

@router.get("/{task_id}")
async def get_subtasks(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await SubTaskService(db).get_subtasks_by_task(task_id, current_user)

@router.put("/{subtask_id}")
async def update_subtask(
    subtask_id: int,
    payload: SubTaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await SubTaskService(db).update_subtask(subtask_id, payload, current_user)

@router.delete("/{subtask_id}")
async def delete_subtask(
    subtask_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await SubTaskService(db).delete_subtask(subtask_id, current_user)




