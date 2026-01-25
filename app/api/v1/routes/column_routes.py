from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.schema.task_schema import ColumnCreate,ColumnUpdate
from app.services.column_service import ColumnService
from app.utils.jwt import get_current_user
router = APIRouter()

# ```````````````````````````create `````````````````````````````````````````````````
@router.post("/create")
async def create_column(
    payload: ColumnCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    service = ColumnService(db)
    return await service.create_column(payload, current_user)
# ```````````````````````````get_all`````````````````````````````````````````````````
@router.get("/board/{board_id}")
async def get_columns(
    board_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    service = ColumnService(db)
    return await service.get_columns(board_id, current_user)

# ```````````````````````````get_by_id `````````````````````````````````````````````````
@router.get("/{column_id}")
async def get_column(
    column_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    service = ColumnService(db)
    return await service.get_column_by_id(column_id, current_user)

# ```````````````````````````update `````````````````````````````````````````````````
@router.put("/{column_id}")
async def update_column(
    column_id: int,
    payload: ColumnUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    service = ColumnService(db)
    return await service.update_column(column_id, payload, current_user)

# ```````````````````````````delete `````````````````````````````````````````````````
@router.delete("/{column_id}")
async def delete_column(
    column_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    service = ColumnService(db)
    return await service.delete_column(column_id, current_user)

