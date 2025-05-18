
# Teste Técnico – API de Matrículas e Grupos de Idade

## Tecnologias

- **Linguagem**: Python 3.13  
- **Framework**: FastAPI  
- **Banco NoSQL**: MongoDB  
- **Fila**: Redis  
- **Testes**: pytest, pytest-asyncio  
- **Containers**: Docker, Docker Compose  

---

## Pré-requisitos

- Docker & Docker Compose (CLI integrada: `docker compose` ou clássico: `docker-compose`)  
- Python 3.13 (opcional, para rodar sem containers)  
- virtualenv / venv  

---

## Variáveis de Ambiente

> Copie o arquivo `.env.example` para `.env` e ajuste conforme abaixo:

```dotenv
TITLE=Teste Técnico
API_V1_STR=/api/v1

# MongoDB
MONGO_URI=mongodb://mongo:27017/testdb
MONGO_DB=test_db

# Auth Basic
BASIC_AUTH_USERNAME=admin
BASIC_AUTH_PASSWORD=123456

# Redis
REDIS_URI=redis://redis:6379/0

# Auto-reload
RELOAD=True

```


## Como Executar

### 1. Via Docker Compose

Levantando todos os serviços (Mongo, Redis, API e Worker):

`docker compose up --build` 

> Se a sua CLI ainda não reconhecer `docker compose`, substitua por `docker-compose up --build`.

-   **API** estará disponível em `http://localhost:8000`
    
-   **Swagger / OpenAPI** em `http://localhost:8000/docs`
    

Para parar e remover tudo:

`docker compose down` 

----------

### 2. Local (sem containers)

#criar e ativar virtualenv
`python3.13 -m venv .venv`
`source .venv/bin/activate`

#instalar dependências
`pip install -r requirements.txt`

#rodar a aplicação
`python main.py`


> A API sobe em `http://localhost:8000` e recarrega automaticamente quando alterar código.
----------


## Executando Testes

### 1. Usando mocks internos (sem containers)

`pytest` 

### 2. Usando containers de teste reais

`docker compose -f docker-compose.test.yml up -d`
`pytest`
`docker compose -f docker-compose.test.yml down`

----------
## Endpoints

### Grupos de Idade (`/api/v1/age-groups`)

| Método | Rota                       | Retorno                                                      |
| ------ | -------------------------- | ------------------------------------------------------------ |
| POST   | `/api/v1/age-groups/`      | `201 Created` → `{ "id": "...", "min_age": N, "max_age": M }` |
| GET    | `/api/v1/age-groups/`      | `200 OK` → lista de grupos                                   |
| DELETE | `/api/v1/age-groups/{group_id}` | `200 OK` / `404 Not Found` / `400 Bad Request`              |

---

### Matrículas (`/api/v1/enrollments`)

| Método | Rota                                  | Retorno                                                               |
| ------ | ------------------------------------- | --------------------------------------------------------------------- |
| POST   | `/api/v1/enrollments/`               | `202 Accepted` → `{ "id": "em processamento" }`                       |
| GET    | `/api/v1/enrollments/`               | `200 OK` → lista de matrículas                                        |
| GET    | `/api/v1/enrollments/{enrollment_id}` | `200 OK` → `{ "status": "pending" }` / `404 Not Found` / `500 Internal Server Error` |
