from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tasks import Board,BoardColumn,Task,SubTask
from app.core.response import AppException
from sqlalchemy.future import select
from sqlalchemy import select, func
import re
from app.schema.task_schema import BoardCreate
from sqlalchemy.orm import selectinload

def normalize_name(name: str) -> str:
    return re.sub(r'[\s\-_]+', '', name).lower()
class BoardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_board(self, payload: BoardCreate, current_user):
        try:
            #  Check duplicate board for user
            existing = await self.db.scalar(
                select(Board).where(
                    Board.user_id == current_user.id,
                    func.lower(Board.name) == payload.name.lower()
                )
            )

            if existing:
                raise AppException(
                    message="Board with this name already exists",
                    status_code=status.HTTP_409_CONFLICT
                )

            #  Create board
            board = Board(
                name=payload.name.strip(),
                user_id=current_user.id,
                is_active=payload.isActive
            )
            self.db.add(board)
            await self.db.flush() 

            created_columns = []

            # -------------------------
            # Create columns (optional)
            # -------------------------
            if payload.columns:
                seen = set()

                for col in payload.columns:
                    normalized = normalize_name(col.name)

                    if normalized in seen:
                        raise AppException(
                            message="Duplicate column names in request",
                            status_code=status.HTTP_409_CONFLICT
                        )

                    seen.add(normalized)

                    column = BoardColumn(
                        name=col.name.strip(),
                        board_id=board.id
                    )

                    self.db.add(column)
                    created_columns.append(column)

            # -------------------------
            # Commit
            # -------------------------
            await self.db.commit()
            await self.db.refresh(board)

            return {
                "success": True,
                "message": "Board created successfully",
                "data": {
                    "board_id": board.id,
                    "name": board.name,
                    "is_active": board.is_active,
                    "columns": [
                        {
                            "id": col.id,
                            "name": col.name
                        }
                        for col in created_columns
                    ]
                },
                "error": None
            }

        except AppException:
            await self.db.rollback()
            raise

        except Exception as e:
            await self.db.rollback()
            raise AppException(
                message="Unexpected error occurred",
                error=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    async def get_all_boards(self, current_user):
        try:
            result = await self.db.execute(
                select(Board).where(Board.user_id == current_user.id)
            )
            boards = result.scalars().all()

            return {
                "success": True,
                "message": "Boards fetched successfully",
                "data": boards,
                "error": None
            }
        except Exception as e:
            raise AppException(
                message="Failed to fetch boards",
                error=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    async def get_board_by_id(self, board_id: int, current_user):
        result = await self.db.execute(
            select(Board).where(
                Board.id == board_id,
                Board.user_id == current_user.id
            )
        )
        board = result.scalar_one_or_none()

        if not board:
            raise AppException(
                message="Board not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        return {
            "success": True,
            "message": "Board fetched successfully",
            "data": board,
            "error": None
        }



    async def update_board(self, board_id: int, payload, current_user):

        board = await self.db.scalar(
            select(Board)
            .options(selectinload(Board.columns))
            .where(
                Board.id == board_id,
                Board.user_id == current_user.id
            )
        )

        if not board:
            raise AppException(
                message="Board not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        if payload.name is not None:
            dup = await self.db.scalar(
                select(Board).where(
                    Board.user_id == current_user.id,
                    func.lower(Board.name) == payload.name.lower(),
                    Board.id != board_id
                )
            )

            if dup:
                raise AppException(
                    message="Board with this name already exists",
                    status_code=status.HTTP_409_CONFLICT
                )

            board.name = payload.name.strip()

        if payload.isActive is not None:
            board.is_active = payload.isActive

        if payload.columns is not None:
            existing_columns = {col.id: col for col in board.columns}
            incoming_ids = set()
            seen = set()

            for col in payload.columns:
                normalized = normalize_name(col.name)

                if normalized in seen:
                    raise AppException(
                        message="Duplicate column names in request",
                        status_code=status.HTTP_409_CONFLICT
                    )
                seen.add(normalized)

                if col.id:
                    column = existing_columns.get(col.id)
                    if not column:
                        raise AppException(
                            message="Column not found",
                            status_code=status.HTTP_404_NOT_FOUND
                        )
                    column.name = col.name.strip()
                    incoming_ids.add(col.id)
                else:
                    self.db.add(
                        BoardColumn(
                            name=col.name.strip(),
                            board_id=board.id
                        )
                    )

            for col_id, column in existing_columns.items():
                if col_id not in incoming_ids:
                    await self.db.delete(column)

        await self.db.commit()

        return {
            "success": True,
            "message": "Board updated successfully",
            "data": {
                "board_id": board.id,
                "name": board.name,
                "is_active": board.is_active,
                "columns": [
                    {"id": col.id, "name": col.name}
                    for col in board.columns
                ]
            },
            "error": None
        }

    async def delete_board(self, board_id: int, current_user):
        result = await self.db.execute(
            select(Board).where(
                Board.id == board_id,
                Board.user_id == current_user.id
            )
        )
        board = result.scalar_one_or_none()

        if not board:
            raise AppException(
                message="Board not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        await self.db.delete(board)
        await self.db.commit()

        return {
            "success": True,
            "message": "Board deleted successfully",
            "data": None,
            "error": None
        }
    async def get_boards_with_details(self, current_user):
        # Fetch all boards for this user
        result = await self.db.execute(
            select(Board)
            .where(Board.user_id == current_user.id)
        )
        boards = result.scalars().all()
        data = []

        for board in boards:
            board_dict = {
                "name": board.name,
                "isActive": board.is_active,
                "columns": []
            }

            # Fetch columns for this board
            columns_result = await self.db.execute(
                select(BoardColumn)
                .where(BoardColumn.board_id == board.id)
            )
            columns = columns_result.scalars().all()

            for column in columns:
                column_dict = {
                    "name": column.name,
                    "tasks": []
                }

                # Fetch tasks in this column
                tasks_result = await self.db.execute(
                    select(Task)
                    .where(Task.column_id == column.id)
                    .order_by(Task.position)
                )
                tasks = tasks_result.scalars().all()

                for task in tasks:
                    # Fetch subtasks for this task
                    subtasks_result = await self.db.execute(
                        select(SubTask)
                        .where(SubTask.task_id == task.id)
                    )
                    subtasks = subtasks_result.scalars().all()

                    task_dict = {
                        "title": task.title,
                        "description": task.description or "",
                        "status": column.name,
                        "subtasks": [
                            {
                                "title": s.title,
                                "isCompleted": s.is_completed
                            } for s in subtasks
                        ]
                    }

                    column_dict["tasks"].append(task_dict)

                board_dict["columns"].append(column_dict)

            data.append(board_dict)

        return {
            "success": True,
            "message": "Boards fetched successfully",
            "data": data,
            "error": None
        }