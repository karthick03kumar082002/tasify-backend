from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.schema.task_schema import BoardCreate,BoardUpdate
from app.services.board_service import BoardService
from app.utils.jwt import get_current_user
router = APIRouter()

# ```````````````````````````create `````````````````````````````````````````````````
@router.post("/create")
async def create_board(
    payload: BoardCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    service = BoardService(db)
    return await service.create_board(payload,current_user)
# ```````````````````````````get_all`````````````````````````````````````````````````
@router.get("/all")
async def get_all_boards(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    service = BoardService(db)
    return await service.get_all_boards(current_user)
# ```````````````````````````get_by_id `````````````````````````````````````````````````
@router.get("/{board_id}")
async def get_board_by_id(
    board_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    service = BoardService(db)
    return await service.get_board_by_id(board_id, current_user)
# ```````````````````````````update `````````````````````````````````````````````````
@router.put("/{board_id}")
async def update_board(
    board_id: int,
    payload: BoardUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    service = BoardService(db)
    return await service.update_board(board_id, payload, current_user)
# ```````````````````````````delete `````````````````````````````````````````````````
@router.delete("/{board_id}")
async def delete_board(
    board_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    service = BoardService(db)
    return await service.delete_board(board_id, current_user)


# ````````````````````````````````````overall get fuction`````````````````````````````````````````````
detail_router = APIRouter()
@detail_router.get("/user")
async def get_all_boards(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    service = BoardService(db)
    return await service.get_boards_with_details(current_user)