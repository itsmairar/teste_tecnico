import asyncio

from app.services.redis_consumer import process_enrollments

if __name__ == "__main__":
    asyncio.run(process_enrollments())
