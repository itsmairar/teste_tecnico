from fastapi import APIRouter, status

from app.schemas.enrollment_schema import (
    EnrollmentIn,
    EnrollmentOut,
    EnrollmentStatus,
)
from app.services.enrollment_service import (
    create_enrollment,
    get_enrollment_status,
    list_enrollments,
)

router = APIRouter()


@router.post(
    "/",
    response_model=EnrollmentOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_enrollment_endpoint(enrollment: EnrollmentIn):
    """
    Envia matrícula para a fila Redis, validando CPF e faixa de idade.
    """
    return await create_enrollment(enrollment)


@router.get(
    "/",
    response_model=list[EnrollmentOut],
    status_code=status.HTTP_200_OK,
)
async def list_enrollments_endpoint():
    """
    Lista todas as matrículas já concluídas no MongoDB.
    """
    return await list_enrollments()


@router.get(
    "/{enroll_id}",
    response_model=EnrollmentStatus,
    status_code=status.HTTP_200_OK,
)
async def get_enrollment_status_endpoint(enroll_id: str):
    """
    Consulta status de uma matrícula pelo seu ID.
    """
    return await get_enrollment_status(enroll_id)
