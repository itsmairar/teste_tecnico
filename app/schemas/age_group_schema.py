from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field, model_validator


class AgeGroupIn(BaseModel):
    min_age: int = Field(..., ge=0)
    max_age: int = Field(..., ge=0)

    @model_validator(mode="after")
    def check_age_order(self) -> "AgeGroupIn":
        if self.min_age >= self.max_age:
            raise ValueError("min_age deve ser menor que max_age.")
        return self


class AgeGroupOut(AgeGroupIn):
    id: str


class AgeGroupDB(AgeGroupIn):
    id: Optional[str]

    class Config:
        from_attributes = True
        json_encoders = {ObjectId: lambda oid: str(oid)}
