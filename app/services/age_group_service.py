from http import HTTPStatus
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException

from app.core.database import mongo_db
from app.schemas.age_group_schema import AgeGroupIn


async def create_age_group(age_group: AgeGroupIn) -> str:
    """
    Cria um novo grupo de idade, validando sobreposição e min<max.
    Retorna o ID do documento inserido.
    """
    if age_group.min_age >= age_group.max_age:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="min_age deve ser menor que max_age",
        )

    overlapping = await mongo_db["age_groups"].find_one({
        "min_age": {"$lte": age_group.max_age},
        "max_age": {"$gte": age_group.min_age},
    })
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

    result = await mongo_db["age_groups"].insert_one(age_group.dict())
    return str(result.inserted_id)


async def list_age_groups() -> list[dict]:
    """
    Retorna todos os grupos de idade como lista de dicts.
    """
    cursor = mongo_db["age_groups"].find({})
    groups: list[dict] = []
    async for g in cursor:
        groups.append({
            "id": str(g["_id"]),
            "min_age": g["min_age"],
            "max_age": g["max_age"],
        })
    return groups


async def delete_age_group(age_group_id: str) -> None:
    """
    Remove um grupo de idade pelo ID.
    Lança 400 se ID inválido, 404 se não encontrado.
    """
    try:
        oid = ObjectId(age_group_id)
    except InvalidId:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="ID inválido",
        )

    result = await mongo_db["age_groups"].delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Grupo de idade não encontrado",
        )


async def check_age_in_group(age: int) -> bool:
    """
    Retorna True se existir um grupo de idade com min_age <= age <= max_age.
    (usado pelo endpoint de matrículas)
    """
    group = await mongo_db["age_groups"].find_one({
        "min_age": {"$lte": age},
        "max_age": {"$gte": age},
    })
    return bool(group)
