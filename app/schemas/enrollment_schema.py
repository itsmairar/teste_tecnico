from pydantic import BaseModel, Field


class EnrollmentIn(BaseModel):
    name: str = Field(..., example="João da Silva")
    cpf: str = Field(..., example="12345678900", min_length=11, max_length=11)
    age: int = Field(..., ge=0)


class EnrollmentOut(EnrollmentIn):
    id: str


class EnrollmentMessage(BaseModel):
    name: str
    cpf: str
    age: int


class EnrollmentStatus(BaseModel):
    id: str
    name: str
    cpf: str
    age: int
    status: str = Field(..., example="processing")
