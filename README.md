# API RESTful de E-commerce com FastAPI

Este projeto é uma API RESTful completa e robusta para uma aplicação de e-commerce, desenvolvida com FastAPI e Python. A aplicação segue as melhores práticas de arquitetura de software, incluindo uma estrutura em camadas, um ambiente de desenvolvimento containerizado com Docker e uma suíte de testes completa com 100% de cobertura de código.

## ✨ Funcionalidades Principais

-   **Gestão de Catálogo**: CRUD completo para `Categorias` e `Produtos`, acessível apenas por administradores.
-   **Sistema de Usuários**:
    -   Registro e login de usuários.
    -   Autenticação baseada em tokens **JWT (OAuth2)**.
    -   Sistema de autorização com dois níveis de permissão: **Administrador (superuser)** e **Cliente**.
-   **Fluxo de E-commerce**:
    -   **Carrinho de Compras (`Cart`)**: Cada cliente tem seu próprio carrinho para adicionar e remover produtos.
    -   **Pedidos (`Order`)**: Funcionalidade para converter o conteúdo do carrinho em um pedido permanente, limpando o carrinho após a conclusão.
-   **Ambiente Dockerizado**: O projeto utiliza Docker e Docker Compose para criar um ambiente de desenvolvimento consistente e facilmente reproduzível.
-   **Banco de Dados**: Integração com banco de dados relacional via **SQLAlchemy ORM**. Projetado para ser compatível com SQLite (para desenvolvimento) e PostgreSQL (para produção).
-   **Testes Automatizados**: **100% de cobertura de testes** da lógica da aplicação usando `pytest`, garantindo a robustez e a confiabilidade do código.

## 🚀 Arquitetura

A aplicação segue uma arquitetura em camadas para garantir a separação de responsabilidades e a escalabilidade:

-   **`main.py`**: Ponto de entrada da aplicação FastAPI.
-   **`models.py`**: Define os modelos de tabela do SQLAlchemy ORM.
-   **`schemas.py`**: Define os schemas de validação de dados de entrada e saída com Pydantic.
-   **`crud.py`**: Abstrai toda a lógica de acesso e manipulação do banco de dados (padrão Repository).
-   **`routers/`**: Contém os diferentes roteadores (`APIRouter`) para cada recurso (produtos, usuários, carrinho, etc.), mantendo os endpoints organizados.
-   **`database.py`**: Gerencia a conexão com o banco de dados.
-   **`auth.py`**: Centraliza toda a lógica de segurança, autenticação e autorização.

## 🛠️ Tecnologias Utilizadas

-   **Backend**: Python 3.13, FastAPI
-   **Banco de Dados**: SQLAlchemy ORM
-   **Segurança**: JWT, Passlib, OAuth2
-   **Containerização**: Docker, Docker Compose
-   **Testes**: Pytest, Pytest-Cov
-   **Servidor ASGI**: Uvicorn

## ⚙️ Como Executar o Projeto

Este projeto foi projetado para ser executado dentro de um contêiner Docker, facilitando a configuração.

### Pré-requisitos

-   [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e em execução.
-   [VSCode](https://code.visualstudio.com/) com a extensão [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers).

### Execução em Ambiente de Desenvolvimento

1.  **Clone o repositório**:
    ```bash
    git clone https://github.com/Eng-Soft-Claudio/API.git
    cd API
    ```

2.  **Abra no VSCode**:
    Abra a pasta do projeto no Visual Studio Code.

3.  **Reabrir no Contêiner**:
    O VSCode irá detectar automaticamente o arquivo `.devcontainer/devcontainer.json` e sugerirá reabrir o projeto dentro de um contêiner de desenvolvimento. Clique em **"Reopen in Container"**.

    *   Se a notificação não aparecer, abra a paleta de comandos (`Ctrl+Shift+P` ou `Cmd+Shift+P`) e procure por **"Dev Containers: Rebuild and Reopen in Container"**.

4.  **A Aplicação Iniciará Automaticamente**:
    Aguarde o VSCode construir a imagem e iniciar o contêiner. O comando `postAttachCommand` no `devcontainer.json` iniciará o servidor Uvicorn automaticamente.

5.  **Acesse a API**:
    A aplicação estará disponível em `http://localhost:8000`.
    A documentação interativa da API (Swagger UI) pode ser acessada em:
    -   **`http://localhost:8000/docs`**

## 🧪 Como Executar os Testes

Com o projeto aberto no Dev Container do VSCode:

1.  **Abra um novo terminal** no VSCode (`Ctrl+` ou `Terminal > Novo Terminal`).
2.  Execute o `pytest` para rodar a suíte de testes completa e gerar o relatório de cobertura:

    ```bash
    pytest --cov=src --cov-report=term-missing
    ```

## 👨‍💻 Autor

-   **Cláudio** - [Eng-Soft-Claudio](https://github.com/Eng-Soft-Claudio)