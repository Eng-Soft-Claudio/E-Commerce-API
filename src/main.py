"""
Módulo principal da aplicação FastAPI.

Este arquivo serve como o ponto de entrada principal:
1. Cria a instância da aplicação FastAPI.
2. Importa e registra todos os roteadores dos diferentes recursos.
"""

# -------------------------------------------------------------------------- #
#                         IMPORTS FUNDAMENTAIS                               #
# -------------------------------------------------------------------------- #
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import engine, Base

# -------------------------------------------------------------------------- #
#                        IMPORTS DOS MÓDULOS DE ROTAS                        #
# -------------------------------------------------------------------------- #
from .routers import auth
from .routers import cart
from .routers import categories
from .routers import dashboard
from .routers import orders
from .routers import payments
from .routers import products
from .routers import users


# -------------------------------------------------------------------------- #
#                        LIFESPAN E INICIALIZAÇÃO DO DB                      #
# -------------------------------------------------------------------------- #
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager para o ciclo de vida da aplicação.
    Garante que as tabelas do banco de dados sejam criadas na inicialização.
    """
    Base.metadata.create_all(bind=engine)
    yield


# -------------------------------------------------------------------------- #
#                  CRIAÇÃO E CONFIGURAÇÃO DA APLICAÇÃO E CORS                #
# -------------------------------------------------------------------------- #
app = FastAPI(
    title="API - Cold Metal",
    version="1.0.0",
    description="Backend para o e-commerce Cold Metal.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------------- #
#                         INCLUSÃO DOS ROTEADORES                            #
# -------------------------------------------------------------------------- #
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(users.router)


# -------------------------------------------------------------------------- #
#                                 ROOT ENDPOINT                              #
# -------------------------------------------------------------------------- #
@app.get("/", tags=["Root"])
def read_root():
    """Endpoint raiz para verificar se a API está online."""
    return {"message": "API do E-commerce Cold Metal está online."}
