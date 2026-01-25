from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tasks import BoardColumn,Board
from app.core.response import AppException
from sqlalchemy.future import select
from sqlalchemy import select, func
import re

def normalize_name(name: str) -> str:
    return re.sub(r'[\s\-_]+', '', name).lower()

class ColumnService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_column(self, payload, current_user):
        try:
            
            board_result = await self.db.execute(
                select(Board).where(
                    Board.id == payload.board_id,
                    Board.user_id == current_user.id
                )
            )
            board = board_result.scalar_one_or_none()
            normalized = normalize_name(payload.name)
            if not board:
                raise AppException(
                    message="Board not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            
            dup_result = await self.db.execute(
                        select(BoardColumn).where(
                            BoardColumn.board_id == payload.board_id,
                            func.replace(
                                func.replace(
                                    func.replace(func.lower(BoardColumn.name), ' ', ''),
                                    '-', ''
                                ),
                                '_', ''
                            ) == normalized))
            if dup_result.scalar_one_or_none():
                raise AppException(
                    message="Column with this name already exists in this board",
                    status_code=status.HTTP_409_CONFLICT
                )

            column = BoardColumn(
                name=payload.name.strip(),
                board_id=payload.board_id
            )

            self.db.add(column)
            await self.db.commit()
            await self.db.refresh(column)

            return {
                "success": True,
                "message": "Column created successfully",
                "data": {"column_id": column.id},
                "error": None
            }

        except AppException as e:
            await self.db.rollback()
            raise e

        except Exception as e:
            await self.db.rollback()
            raise AppException(
                message="Unexpected error occurred",
                error=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

    async def get_columns(self, board_id: int, current_user):
        board = await self.db.scalar(
            select(Board).where(
                Board.id == board_id,
                Board.user_id == current_user.id
            )
        )

        if not board:
            raise AppException(
                message="Board not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        result = await self.db.execute(
            select(BoardColumn).where(BoardColumn.board_id == board_id)
        )

        return {
            "success": True,
            "message": "Columns fetched successfully",
            "data": result.scalars().all(),
            "error": None
        }
    
    async def get_column_by_id(self, column_id: int, current_user):
        result = await self.db.execute(
            select(BoardColumn).where(
                BoardColumn.id == column_id,
                BoardColumn.board.has(user_id=current_user.id)
            )
        )
        column = result.scalar_one_or_none()

        if not column:
            raise AppException(
                message="Column not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        return {
            "success": True,
            "message": "Column fetched successfully",
            "data": column,
            "error": None
        }
    async def update_column(self, column_id: int, payload, current_user):
        result = await self.db.execute(
            select(BoardColumn).where(
                BoardColumn.id == column_id,
                BoardColumn.board.has(user_id=current_user.id)
            )
        )
        column = result.scalar_one_or_none()

        if not column:
            raise AppException(
                message="Column not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        if payload.name:
            normalized = normalize_name(payload.name)
            dup = await self.db.execute(
                select(BoardColumn).where(
                    BoardColumn.board_id == column.board_id,
                    func.replace(
                        func.replace(
                            func.replace(func.lower(BoardColumn.name), ' ', ''),
                            '-', ''
                        ),
                        '_', ''
                    ) == normalized,
                    BoardColumn.id != column_id
                )
            )
            if dup.scalar_one_or_none():
                raise AppException(
                    message="Column name already exists in this board",
                    status_code=status.HTTP_409_CONFLICT
                )

            column.name = payload.name.strip()

        await self.db.commit()
        await self.db.refresh(column)

        return {
            "success": True,
            "message": "Column updated successfully",
            "data": column,
            "error": None
        }
    async def delete_column(self, column_id: int, current_user):
        result = await self.db.execute(
            select(BoardColumn).where(
                BoardColumn.id == column_id,
                BoardColumn.board.has(user_id=current_user.id)
            )
        )
        column = result.scalar_one_or_none()

        if not column:
            raise AppException(
                message="Column not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        await self.db.delete(column)
        await self.db.commit()

        return {
            "success": True,
            "message": "Column deleted successfully",
            "data": None,
            "error": None
        }
