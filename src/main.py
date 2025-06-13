"""
Módulo principal da aplicação FastAPI.

Define o objeto da aplicação FastAPI, a lógica de inicialização (como a criação
de tabelas do banco de dados) e inclui todos os roteadores dos recursos.
"""
from fastapi import FastAPI

from . import models
from .database import engine
from .routers import categories, products

# -------------------------------------------------------------------------- #
#                              APPLICATION SETUP                             #
# -------------------------------------------------------------------------- #

# Cria as tabelas no banco de dados com base nos modelos definidos
models.Base.metadata.create_all(bind=engine)

# Cria a instância principal da aplicação FastAPI
app = FastAPI(
    title="Minha API Escalável",
    version="2.0.0",
    description="Uma API FastAPI com arquitetura em camadas e Docker.",
)

# Inclui os roteadores dos diferentes recursos da aplicação
app.include_router(categories.router)
app.include_router(products.router)


# -------------------------------------------------------------------------- #
#                                 ROOT ENDPOINT                              #
# -------------------------------------------------------------------------- #

@app.get("/", tags=["Root"])
def read_root():
    """
    Endpoint raiz da aplicação.
    
    Retorna uma mensagem de boas-vindas para indicar que a API está online.
    """
    return {"message": "Bem-vindo à API de Categorias!"}