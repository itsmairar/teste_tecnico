from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import api_router
from app.core.auth import autenticar_credenciais
from app.core.configs import settings

app = FastAPI(
    title=settings.TITLE,
    # aqui aplicamos o HTTPBasic globalmente
    dependencies=[Depends(autenticar_credenciais)],
)

# Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas da API agrupadas (já protegidas pelo Depends acima)
app.include_router(api_router, prefix=settings.API_V1_STR)

# Se rodar diretamente:
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.RELOAD,
    )
