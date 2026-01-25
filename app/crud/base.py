from typing import Generic, TypeVar, Type, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
from app.models.audit import LoginAuditLog
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
from datetime import datetime

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        Generic CRUD operations for any SQLAlchemy model.
        :param model: SQLAlchemy model class
        """
        self.model = model

    # --------------------
    # READ
    # --------------------
    async def get_by_id(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalars().first()

    async def get_all(
        self, db: AsyncSession, skip: int = 0, limit: int = 10
    ) -> List[ModelType]:
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    # --------------------
    # CREATE
    # --------------------
    async def create(self, db: AsyncSession, obj_in: CreateSchemaType) -> ModelType:
        db_obj = self.model(**obj_in.dict())
        db.add(db_obj)
        try:
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    # --------------------
    # UPDATE
    # --------------------
    async def update(
        self, db: AsyncSession, db_obj: ModelType, obj_in: UpdateSchemaType
    ) -> ModelType:
        for field, value in obj_in.dict(exclude_unset=True).items():
            setattr(db_obj, field, value)
        try:
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    # --------------------
    # DELETE
    # --------------------
    async def delete(self, db: AsyncSession, db_obj: ModelType) -> None:
        try:
            await db.delete(db_obj)
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    # --------------------
    # GET BY UNIQUE FIELD (like email)
    # --------------------
    async def get_by_field(
        self, db: AsyncSession, field_name: str, value
    ) -> Optional[ModelType]:
        field = getattr(self.model, field_name)
        result = await db.execute(select(self.model).where(field == value))
        return result.scalars().first()


    async def id_exists(self, db: AsyncSession, id: int) -> Optional[ModelType]:
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalars().first()


async def create_login_audit_log(
    db: AsyncSession,
    user_id: int = None,
    action: str = None,
    status: str = None,           # added
    ip_address: str = None,
    user_agent: str = None,
    message: str = None            #  added
):
    log_entry = LoginAuditLog(
        user_id=user_id,
        action=action,
        status=status,              #  assign status
        ip_address=ip_address,
        user_agent=user_agent,
        message=message,            #  assign message
        timestamp=datetime.utcnow()
    )
    db.add(log_entry)
    await db.commit()