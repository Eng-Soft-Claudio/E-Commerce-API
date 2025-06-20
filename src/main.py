"""
Módulo principal da aplicação FastAPI.

Este arquivo serve como o ponto de entrada principal:
1. Cria a instância da aplicação FastAPI.
2. Importa e registra todos os roteadores dos diferentes recursos.

A criação das tabelas do banco de dados NÃO é mais gerenciada aqui. Ela
deve ser feita por uma ferramenta de migração (como Alembic) ou em um
script de inicialização separado, tornando a aplicação mais passiva e testável.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# -------------------------------------------------------------------------- #
#                        IMPORTS PARA REGISTRO DE MÓDULOS                    #
# -------------------------------------------------------------------------- #
from .database import engine, Base
from .routers import auth, cart, categories, orders, products, payments, dashboard


# -------------------------------------------------------------------------- #
#                        LIFESPAN E INICIALIZAÇÃO DO DB                      #
# -------------------------------------------------------------------------- #
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


# -------------------------------------------------------------------------- #
#                   CRIAÇÃO E CONFIGURAÇÃO DA APLICAÇÃO E CORS               #
# -------------------------------------------------------------------------- #
app = FastAPI(
    title="FastAPI RESTful",
    version="2.0.0",
    description="Uma API FastAPI com arquitetura em camadas e Docker.",
    lifespan=lifespan,
)
origins = [
    "http://localhost:3000",
    "http://localhost",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------------- #
#                         INCLUSÃO DOS ROTEADORES                            #
# -------------------------------------------------------------------------- #
app.include_router(dashboard.router)
app.include_router(auth.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(payments.router)


# -------------------------------------------------------------------------- #
#                                 ROOT ENDPOINT                              #
# -------------------------------------------------------------------------- #
@app.get("/", tags=["Root"])
def read_root():
    """Endpoint raiz para verificar se a API está online."""
    return {"message": "Bem-vindo à FastAPI RESTful!"}
