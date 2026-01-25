from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import status
from app.models.tasks import SubTask, Task, BoardColumn
from app.core.response import AppException

class SubTaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # CREATE SUBTASK
    async def create_subtask(self, payload, current_user):
        task = await self.db.scalar(
            select(Task).where(
                Task.id == payload.task_id,
                Task.column.has(
                    BoardColumn.board.has(user_id=current_user.id)
                )
            )
        )
        if not task:
            raise AppException(
                message="Task not found or not accessible",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Check duplicate subtask under same task
        dup = await self.db.scalar(
            select(SubTask).where(
                SubTask.task_id == payload.task_id,
                func.lower(SubTask.title) == payload.title.lower()
            )
        )
        if dup:
            raise AppException(
                message="Subtask with this title already exists in this task",
                status_code=status.HTTP_409_CONFLICT
            )

        subtask = SubTask(
            title=payload.title.strip(),
            task_id=payload.task_id
        )
        self.db.add(subtask)
        await self.db.commit()
        await self.db.refresh(subtask)

        return {
            "success": True,
            "message": "Subtask created successfully",
            "data": {"subtask_id": subtask.id},
            "error": None
        }

    # GET ALL SUBTASKS FOR A TASK
    async def get_subtasks_by_task(self, task_id: int, current_user):
        task = await self.db.scalar(
            select(Task).where(
                Task.id == task_id,
                Task.column.has(BoardColumn.board.has(user_id=current_user.id))
            )
        )
        if not task:
            raise AppException(
                message="Task not found or not accessible",
                status_code=status.HTTP_404_NOT_FOUND
            )

        result = await self.db.execute(
            select(SubTask).where(SubTask.task_id == task_id)
        )
        subtasks = result.scalars().all()
        total = len(subtasks)
        completed = sum(1 for s in subtasks if s.is_completed)

        data = [
            {"id": s.id, "title": s.title, "is_completed": s.is_completed}
            for s in subtasks
        ]

        return {
            "success": True,
            "message": "Subtasks fetched successfully",
            "data": {"subtasks": data, "completed_count": completed, "total_count": total},
            "error": None
        }

    # UPDATE SUBTASK
    async def update_subtask(self, subtask_id: int, payload, current_user):
        subtask = await self.db.scalar(
            select(SubTask)
            .join(Task)
            .join(Task.column)
            .where(
                SubTask.id == subtask_id,
                Task.column.has(BoardColumn.board.has(user_id=current_user.id))
            )
        )
        if not subtask:
            raise AppException(
                message="Subtask not found or not accessible",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Update title with duplicate check
        if payload.title:
            dup = await self.db.scalar(
                select(SubTask).where(
                    SubTask.task_id == subtask.task_id,
                    func.lower(SubTask.title) == payload.title.lower(),
                    SubTask.id != subtask_id
                )
            )
            if dup:
                raise AppException(
                    message="Subtask with this title already exists in this task",
                    status_code=status.HTTP_409_CONFLICT
                )
            subtask.title = payload.title.strip()

        # Update completion status
        if payload.is_completed is not None:
            subtask.is_completed = payload.is_completed

        await self.db.commit()
        await self.db.refresh(subtask)

        return {
            "success": True,
            "message": "Subtask updated successfully",
            "data": {
                "id": subtask.id,
                "title": subtask.title,
                "is_completed": subtask.is_completed
            },
            "error": None
        }

    # DELETE SUBTASK
    async def delete_subtask(self, subtask_id: int, current_user):
        subtask = await self.db.scalar(
            select(SubTask)
            .join(Task)
            .join(Task.column)
            .where(
                SubTask.id == subtask_id,
                Task.column.has(BoardColumn.board.has(user_id=current_user.id))
            )
        )
        if not subtask:
            raise AppException(
                message="Subtask not found or not accessible",
                status_code=status.HTTP_404_NOT_FOUND
            )

        await self.db.delete(subtask)
        await self.db.commit()

        return {
            "success": True,
            "message": "Subtask deleted successfully",
            "data": None,
            "error": None
        }
