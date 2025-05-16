from http import HTTPStatus

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import mongo_db
from app.core.deps import get_current_user
from app.schemas.age_group_schema import AgeGroupIn, AgeGroupOut

router = APIRouter()


@router.post("/", response_model=AgeGroupOut, status_code=HTTPStatus.CREATED)
async def create_age_group(
    age_group: AgeGroupIn,
    user=Depends(get_current_user),
):
    """
    Cria um novo grupo de idade se não houver sobreposição com grupos
    existentes.

    - Valida se `min_age < max_age`.
    - Impede a criação de faixas sobrepostas.
    - Retorna os dados do grupo criado.
    """
    if age_group.min_age >= age_group.max_age:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="min_age deve ser menor que max_age",
        )

    overlapping = await mongo_db["age_groups"].find_one(
        {
            "min_age": {"$lte": age_group.max_age},
            "max_age": {"$gte": age_group.min_age},
        }
    )

    if overlapping:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail={
                "message": "Faixa etária sobreposta com grupo já existente",
                "existing_group": {
                    "id": str(overlapping["_id"]),
                    "min_age": overlapping["min_age"],
                    "max_age": overlapping["max_age"],
                },
            },
        )

    doc = age_group.dict()
    result = await mongo_db["age_groups"].insert_one(doc)
    return AgeGroupOut(id=str(result.inserted_id), **doc)


@router.get("/", response_model=list[AgeGroupOut], status_code=HTTPStatus.OK)
async def list_age_groups(user=Depends(get_current_user)):
    """
    Retorna a lista de todos os grupos de idade cadastrados.
    """
    groups = []
    cursor = mongo_db["age_groups"].find({})
    async for group in cursor:
        group_out = AgeGroupOut(
            id=str(group["_id"]),
            min_age=group["min_age"],
            max_age=group["max_age"],
        )
        groups.append(group_out)
    return groups


@router.delete("/{age_group_id}", status_code=HTTPStatus.OK)
async def delete_age_group(age_group_id: str, user=Depends(get_current_user)):
    """
    Remove um grupo de idade com base no ID fornecido.

    - Valida se o ID é válido.
    - Retorna erro 404 caso o grupo não exista.
    - Retorna sucesso caso o grupo seja removido.
    """
    try:
        oid = ObjectId(age_group_id)
    except InvalidId:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="ID inválido"
        )

    result = await mongo_db["age_groups"].delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Grupo de idade não encontrado",
        )

    return {"detail": "Grupo de idade removido com sucesso"}
