from http import HTTPStatus

from fastapi import APIRouter

from app.schemas.age_group_schema import AgeGroupIn, AgeGroupOut
from app.services.age_group_service import (
    create_age_group,
    delete_age_group,
    list_age_groups,
)

router = APIRouter()


@router.post("/", response_model=AgeGroupOut, status_code=HTTPStatus.CREATED)
async def create_age_group_endpoint(age_group: AgeGroupIn):
    """
    Cria um grupo de idade — já autenticado
    """
    new_id = await create_age_group(age_group)
    return AgeGroupOut(id=new_id, **age_group.dict())


@router.get("/", response_model=list[AgeGroupOut], status_code=HTTPStatus.OK)
async def list_age_groups_endpoint():
    """
    Lista todos os grupos de idade — já autenticado
    """
    groups = await list_age_groups()
    return [AgeGroupOut(**g) for g in groups]


@router.delete("/{age_group_id}", status_code=HTTPStatus.OK)
async def delete_age_group_endpoint(age_group_id: str):
    """
    Remove um grupo de idade pelo ID — já autenticado
    """
    await delete_age_group(age_group_id)
    return {"detail": "Grupo de idade removido com sucesso"}
