import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.configs import settings

security = HTTPBasic()


async def autenticar_credenciais(
    credentials: HTTPBasicCredentials = Depends(security),
):
    username_valido = secrets.compare_digest(
        credentials.username, settings.BASIC_AUTH_USERNAME
    )
    senha_valida = secrets.compare_digest(
        credentials.password, settings.BASIC_AUTH_PASSWORD
    )

    if not (username_valido and senha_valida):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return {"username": credentials.username}
