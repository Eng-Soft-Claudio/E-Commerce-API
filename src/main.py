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


# -------------------------------------------------------------------------- #
#                        IMPORTS PARA REGISTRO DE MÓDULOS                    #
# -------------------------------------------------------------------------- #
from .routers import auth, cart, categories, orders, products, payments


# -------------------------------------------------------------------------- #
#                       INICIALIZAÇÃO DA APLICAÇÃO E DO DB                   #
# -------------------------------------------------------------------------- #


app = FastAPI(
    title="FastAPI RESTful",
    version="2.0.0",
    description="Uma API FastAPI com arquitetura em camadas e Docker.",
)

# -------------------------------------------------------------------------- #
#                         INCLUSÃO DOS ROTEADORES                            #
# -------------------------------------------------------------------------- #
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
