from fastapi import Depends

from app.core.auth import autenticar_credenciais


async def get_current_user(user: str = Depends(autenticar_credenciais)):
    return user
