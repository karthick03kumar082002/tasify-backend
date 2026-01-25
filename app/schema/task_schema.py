from pydantic import BaseModel
from typing import List, Optional



class BoardCreate(BaseModel):
    name: str
    isActive: bool = True

class BoardUpdate(BaseModel):
    name: Optional[str]= None
    isActive: Optional[bool]= None




class ColumnCreate(BaseModel):
    name: str
    board_id: int

class ColumnUpdate(BaseModel):
    name: Optional[str] = None




class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    column_id: int

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    column_id: Optional[int] = None 


class SubTaskCreate(BaseModel):
    title: str
    task_id: int
class SubTaskUpdate(BaseModel):
    title: Optional[str] = None
    is_completed: Optional[bool] = None




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
