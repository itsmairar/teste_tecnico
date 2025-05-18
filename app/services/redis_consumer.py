import asyncio
import json

import redis.asyncio as redis

from app.core.configs import settings
from app.core.database import mongo_db


async def process_enrollments():
    redis_client = redis.Redis.from_url(
        settings.REDIS_URI, decode_responses=True
    )

    while True:
        await asyncio.sleep(2)
        _, message = await redis_client.blpop("enrollments")
        enrollment_data = json.loads(message)

        age = enrollment_data["age"]
        matching_group = await mongo_db["age_groups"].find_one(
            {"min_age": {"$lte": age}, "max_age": {"$gte": age}}
        )

        if not matching_group:
            print(
                f"Idade {age} não corresponde a nenhum grupo de idade "
                f"cadastrado. Matrícula descartada."
            )
            continue

        await mongo_db["enrollments"].insert_one(enrollment_data)
        print(f"Matrícula salva: {enrollment_data['cpf']}")


if __name__ == "__main__":
    asyncio.run(process_enrollments())
