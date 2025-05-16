import redis.asyncio as redis

from app.core.configs import settings
from app.schemas.enrollment_schema import EnrollmentMessage


class RedisProducer:
    def __init__(self):
        self.redis = redis.Redis.from_url(
            settings.REDIS_URI, decode_responses=True
        )

    async def enqueue_enrollment(self, data: EnrollmentMessage) -> None:
        await self.redis.rpush("enrollments", data.model_dump_json())
