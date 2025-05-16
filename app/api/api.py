from fastapi import APIRouter

from app.api.v1.endpoints import age_groups, enrollments

api_router = APIRouter()

api_router.include_router(
    age_groups.router, prefix="/age-groups", tags=["Grupos de Idade"]
)

api_router.include_router(
    enrollments.router, prefix="/enrollments", tags=["Matrículas"]
)
