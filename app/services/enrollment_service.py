from bson import ObjectId
from pymongo.errors import PyMongoError
from fastapi import HTTPException, status

from app.core.database import mongo_db
from app.schemas.enrollment_schema import (
    EnrollmentIn,
    EnrollmentMessage,
    EnrollmentOut,
    EnrollmentStatus,
)
from app.utils.cpf_validator import is_valid_cpf
from app.services.age_group_service import check_age_in_group
from app.services.redis_producer import RedisProducer

producer = RedisProducer()


async def create_enrollment(enrollment: EnrollmentIn) -> EnrollmentOut:
    if not is_valid_cpf(enrollment.cpf):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF inválido",
        )

    if not await check_age_in_group(enrollment.age):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idade não corresponde a nenhum grupo cadastrado.",
        )

    try:
        if await mongo_db["enrollments"].find_one({"cpf": enrollment.cpf}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Já existe uma matrícula com CPF {enrollment.cpf}",
            )
    except PyMongoError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao consultar o banco de dados",
        )

    try:
        msg = EnrollmentMessage(**enrollment.model_dump())
        await producer.enqueue_enrollment(msg)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Não foi possível processar a matrícula no momento. "
                "Tente novamente mais tarde."
            ),
        )

    return EnrollmentOut(id="em processamento", **enrollment.model_dump())


async def list_enrollments() -> list[EnrollmentOut]:
    try:
        out: list[EnrollmentOut] = []
        cursor = mongo_db["enrollments"].find({})
        async for doc in cursor:
            out.append(
                EnrollmentOut(
                    id=str(doc["_id"]),
                    name=doc["name"],
                    cpf=doc["cpf"],
                    age=doc["age"],
                )
            )
        return out
    except PyMongoError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao buscar as matrículas no banco",
        )


async def get_enrollment_status(enroll_id: str) -> EnrollmentStatus:
    try:
        doc = await mongo_db["enrollments"].find_one(
            {"_id": ObjectId(enroll_id)}
        )
    except (PyMongoError, Exception):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao acessar o banco",
        )

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Matrícula não encontrada",
        )

    return EnrollmentStatus(
        id=str(doc["_id"]),
        name=doc["name"],
        cpf=doc["cpf"],
        age=doc["age"],
        status=doc.get("status", "completed"),
    )
