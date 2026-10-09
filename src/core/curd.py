from pydantic import BaseModel
from tortoise.models import Model
from tortoise.expressions import Q

from typing import Any, Generic, TypeVar

ModelType = TypeVar("ModelType", bound=Model)
CreateType = TypeVar("CreateType", bound=BaseModel)
UpdateType = TypeVar("UpdateType", bound=BaseModel)

class CURDBase(Generic[ModelType, CreateType, UpdateType]):
    def __init__(self, model: type[ModelType]) -> None:
        self.model = model

    async def get(self, model_id: int) -> ModelType:
        return await self.model.get(id=model_id)

    async def list(self,
                   page: int,
                   page_size: int,
                   search : Q|None = None,
                   order: list[str]|None = None) -> tuple[int, list[ModelType]]:
        query = self.model.filter(search or Q())
        total = await query.count()
        items = (
            await query.offset((page-1) * page_size)
            .limit(page_size)
            .order_by(*(order or ["-created_at"]))
        )
        return total, items

    async def create(self, obj_in : CreateType | dict[str, Any]) -> ModelType:
        data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump()
        obj = self.model(**data)
        await obj.save()
        return obj

    async def update(self,
                     model_id: int,
                     obj_in: UpdateType | dict[str, Any]) -> ModelType:
        data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True, exclude={"id"})
        obj = await self.get(model_id)
        obj.update_from_dict(data)
        await obj.save()
        return obj

    async def delete(self, model_id : int):
        obj = await self.get(model_id)
        await obj.delete()
