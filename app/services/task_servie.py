from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tasks import Board,BoardColumn,Task
from app.core.response import AppException
from app.services.column_service import normalize_name
from sqlalchemy import select, func,update
from app.schema.task_schema import TaskMove


class TaskService:
    def __init__(self, db):
        self.db = db

class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(self, payload, current_user):
        column = await self.db.scalar(
            select(BoardColumn).where(
                BoardColumn.id == payload.column_id,
                BoardColumn.board.has(user_id=current_user.id)
            )
        )
        if not column:
            raise AppException(
                message="Column not found",
                status_code=status.HTTP_404_NOT_FOUND
            )
        normalized = normalize_name(payload.title)
        dup = await self.db.scalar(
                select(Task).where(
                    Task.column_id == payload.column_id,
                    func.replace(
                        func.replace(
                            func.replace(func.lower(Task.title), ' ', ''),
                            '-', ''
                        ),
                        '_', ''
                    ) == normalized))
        if dup:
            raise AppException(
                message="Task with this title already exists in this column",
                status_code=status.HTTP_409_CONFLICT
            )
        last_position = await self.db.scalar(
            select(func.max(Task.position))
            .where(Task.column_id == payload.column_id)
        )
        next_position = (last_position or 0) + 1
        task = Task(
            title=payload.title.strip(),
            description=payload.description,
            column_id=payload.column_id,
            position=next_position
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return {
            "success": True,
            "message": "Task created successfully",
            "data": {
                "task_id": task.id,
                "status": column.name  
            },
            "error": None
        }


    async def get_tasks(self, column_id: int, current_user):
        column = await self.db.scalar(
            select(BoardColumn).where(
                BoardColumn.id == column_id,
                BoardColumn.board.has(user_id=current_user.id)
            )
        )

        if not column:
            raise AppException(
                message="Column not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        result = await self.db.execute(
                select(Task, BoardColumn.name)
                .join(BoardColumn, Task.column_id == BoardColumn.id)
                .where(Task.column_id == column_id)
                .order_by(Task.position)
            )
        tasks = []
        for task, column_name in result.all():
            tasks.append({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "column_id": task.column_id,
                "status": column_name,  
                "position": task.position
            })

        return {
            "success": True,
            "message": "Tasks fetched successfully",
            "data": tasks,
            "error": None
        }
    
    async def get_task_by_id(self, task_id: int, current_user):
        result = await self.db.execute(
            select(Task, BoardColumn.name)
            .join(BoardColumn, Task.column_id == BoardColumn.id)
            .where(
                Task.id == task_id,
                BoardColumn.board.has(user_id=current_user.id)
            )
        )

        row = result.first()

        if not row:
            raise AppException(
                message="Task not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        task, column_name = row

        return {
            "success": True,
            "message": "Task fetched successfully",
            "data": {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "column_id": task.column_id,
                "status": column_name,  
                "position": task.position
            },
            "error": None
        }

    
    async def update_task(self, task_id: int, payload, current_user):
        task = await self.db.scalar(
            select(Task)
            .join(BoardColumn)
            .where(
                Task.id == task_id,
                BoardColumn.board.has(user_id=current_user.id)
            )
        )

        if not task:
            raise AppException(
                message="Task not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        
        if payload.title:
            dup = await self.db.execute(
                select(Task).where(
                    Task.column_id == task.column_id,
                    func.lower(Task.title) == payload.title.lower(),
                    Task.id != task_id
                )
            )
            if dup.scalar_one_or_none():
                raise AppException(
                    message="Task title already exists in this column",
                    status_code=status.HTTP_409_CONFLICT
                )

            task.title = payload.title.strip()

        
        if payload.description is not None:
            task.description = payload.description

        
        if payload.column_id is not None:
            column = await self.db.scalar(
                select(BoardColumn).where(
                    BoardColumn.id == payload.column_id,
                    BoardColumn.board.has(user_id=current_user.id)
                )
            )

            if not column:
                raise AppException(
                    message="Target column not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            task.column_id = payload.column_id

        await self.db.commit()
        await self.db.refresh(task)

        return {
            "success": True,
            "message": "Task updated successfully",
            "data": {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "column_id": task.column_id
            },
            "error": None
        }

    async def delete_task(self, task_id: int, current_user):
        task = await self.db.scalar(
            select(Task).where(
                Task.id == task_id,
                Task.column.has(
                    BoardColumn.board.has(user_id=current_user.id)
                )
            )
        )

        if not task:
            raise AppException(
                message="Task not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        await self.db.delete(task)
        await self.db.commit()

        return {
            "success": True,
            "message": "Task deleted successfully",
            "data": None,
            "error": None
        }
    async def move_task(self, payload: TaskMove, current_user):

        task = await self.db.scalar(
            select(Task)
            .join(BoardColumn)
            .where(
                Task.id == payload.task_id,
                BoardColumn.board.has(user_id=current_user.id)
            )
        )

        if not task:
            raise AppException("Task not found", status.HTTP_404_NOT_FOUND)

        # Validate destination column
        dest_column = await self.db.scalar(
            select(BoardColumn).where(
                BoardColumn.id == payload.destination_column_id,
                BoardColumn.board.has(user_id=current_user.id)
            )
        )

        if not dest_column:
            raise AppException("Target column not found", status.HTTP_404_NOT_FOUND)

        #  Close gap in source column
        await self.db.execute(
            update(Task)
            .where(
                Task.column_id == payload.source_column_id,
                Task.position > task.position
            )
            .values(position=Task.position - 1)
        )

        #  Make space in destination column
        await self.db.execute(
            update(Task)
            .where(
                Task.column_id == payload.destination_column_id,
                Task.position >= payload.destination_position
            )
            .values(position=Task.position + 1)
        )

        #  Move task
        task.column_id = payload.destination_column_id
        task.position = payload.destination_position

        await self.db.commit()

        return {
            "success": True,
            "message": "Task moved successfully"
        }
