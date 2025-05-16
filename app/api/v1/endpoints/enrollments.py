from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.errors import PyMongoError

from app.core.database import mongo_db
from app.core.deps import get_current_user
from app.schemas.enrollment_schema import (
    EnrollmentIn,
    EnrollmentMessage,
    EnrollmentOut,
)
from app.services.redis_producer import RedisProducer

router = APIRouter()
producer = RedisProducer()


@router.post(
    "/", response_model=EnrollmentOut, status_code=status.HTTP_202_ACCEPTED
)
async def create_enrollment(
    enrollment: EnrollmentIn, user=Depends(get_current_user)
):
    """
    Envia matrícula para a fila Redis, desde que não exista um CPF duplicado.
    """
    try:
        existing = await mongo_db["enrollments"].find_one(
            {"cpf": enrollment.cpf}
        )
        if existing:
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
        message = EnrollmentMessage(**enrollment.model_dump())
        await producer.enqueue_enrollment(message)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Não foi possível processar a matrícula no momento. "
                "Tente novamente mais tarde."
            ),
        )

    return EnrollmentOut(id="em processamento", **enrollment.model_dump())


@router.get(
    "/", response_model=list[EnrollmentOut], status_code=status.HTTP_200_OK
)
async def list_enrollments(user=Depends(get_current_user)):
    """
    Lista todas as matrículas já salvas no MongoDB.
    """
    try:
        enrollments = []
        cursor = mongo_db["enrollments"].find({})
        async for doc in cursor:
            enrollments.append(
                EnrollmentOut(
                    id=str(doc["_id"]),
                    name=doc["name"],
                    cpf=doc["cpf"],
                    age=doc["age"],
                )
            )
        return enrollments

    except PyMongoError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao buscar as matrículas no banco",
        )
