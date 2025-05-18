import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.core.configs import settings

security = HTTPBasic()


def autenticar_credenciais(
    credentials: HTTPBasicCredentials = Security(security),
) -> str:
    correct_user = secrets.compare_digest(
        credentials.username, settings.BASIC_AUTH_USERNAME
    )
    correct_pass = secrets.compare_digest(
        credentials.password, settings.BASIC_AUTH_PASSWORD
    )
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
