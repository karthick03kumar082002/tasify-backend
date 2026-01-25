# models/board.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.db import Base


class Board(Base):
    __tablename__ = "boards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("auth_user.id"))
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    
    user = relationship(
        "AuthUser",
        back_populates="boards"
    )
    columns = relationship(
        "BoardColumn",
        back_populates="board",
        cascade="all, delete"
    )


class BoardColumn(Base):
    __tablename__ = "board_columns"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    board_id = Column(Integer, ForeignKey("boards.id"))

    board = relationship("Board", back_populates="columns")
    tasks = relationship(
        "Task",
        back_populates="column",
        cascade="all, delete"
    )


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    column_id = Column(Integer, ForeignKey("board_columns.id"))
    position = Column(Integer, nullable=False)

    column = relationship("BoardColumn", back_populates="tasks")
    subtasks = relationship(
        "SubTask",
        back_populates="task",
        cascade="all, delete-orphan"
    )

class SubTask(Base):
    __tablename__ = "subtasks"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    is_completed = Column(Boolean, default=False)

    task_id = Column(Integer, ForeignKey("tasks.id"))
    task = relationship("Task", back_populates="subtasks")
