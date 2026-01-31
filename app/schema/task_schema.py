from pydantic import BaseModel
from typing import List, Optional


class ColumnCreate(BaseModel):
    name: str
    board_id: int
    
class ColumnCreation(BaseModel):
    name: str
    
class BoardCreate(BaseModel):
    name: str
    isActive: bool = True
    columns: Optional[List[ColumnCreation]] = None
    
    
class ColumnUpdate(BaseModel):
    id: Optional[int] = None 
    name: Optional[str] = None

class BoardUpdate(BaseModel):
    name: Optional[str]= None
    isActive: Optional[bool]= None
    columns: Optional[List[ColumnUpdate]] = None









class SubTaskCreate(BaseModel):
    title: str
    task_id: int
    
class SubTaskCreation(BaseModel):
    title: str
    
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    column_id: int
    subtasks: Optional[list[SubTaskCreation]] = None
    # subtasks: list[SubTaskCreation] 
class SubTaskUpdate(BaseModel):
    id: Optional[int] = None 
    title: Optional[str] = None
    is_completed: Optional[bool] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    column_id: Optional[int] = None 
    subtasks: Optional[List[SubTaskUpdate]] = None






class TaskMove(BaseModel):
    task_id: int
    source_column_id: int
    destination_column_id: int
    destination_position: int











































# class SubTaskCreate(BaseModel):
#     title: str
#     isCompleted: bool = False


# class TaskCreate(BaseModel):
#     title: str
#     description: Optional[str] = None
#     status: str
#     subtasks: List[SubTaskCreate]


# class ColumnCreate(BaseModel):
#     name: str
#     tasks: List[TaskCreate]


# class BoardCreate(BaseModel):
#     name: str
#     isActive: bool = True
#     columns: Optional[List[ColumnCreate]]
