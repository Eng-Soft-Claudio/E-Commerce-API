"""
Módulo para gerenciar configurações da aplicação a partir de variáveis de ambiente.

Esta implementação usa pathlib para construir um caminho absoluto para o arquivo .env,
resolvendo problemas de análise estática e garantindo que o arquivo seja
encontrado independentemente do diretório de trabalho atual.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #
from pathlib import Path
from pydantic import Field, ValidationError, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional  # noqa: F401

# -------------------------------------------------------------------------- #
#                         CONFIGURAÇÃO DE CAMINHOS                           #
# -------------------------------------------------------------------------- #
ROOT_DIR = Path(__file__).parent.parent
ENV_FILE_PATH = ROOT_DIR / ".env"

# -------------------------------------------------------------------------- #
#                          CLASSE DE CONFIGURAÇÕES                           #
# -------------------------------------------------------------------------- #


class Settings(BaseSettings):
    """
    Carrega as configurações a partir do caminho absoluto do .env ou do ambiente.
    Valida a presença de chaves essenciais para o funcionamento da aplicação.
    """

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str

    @computed_field
    @property
    def DATABASE_URL(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    JWT_SECRET_KEY: str = Field(...)
    STRIPE_SECRET_KEY: str = Field(...)
    STRIPE_WEBHOOK_SECRET: str = Field(...)
    CLIENT_URL: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH), env_file_encoding="utf-8"
    )


# -------------------------------------------------------------------------- #
#           FUNÇÃO DE INICIALIZAÇÃO E EXPORTAÇÃO DAS CONFIGURAÇÕES           #
# -------------------------------------------------------------------------- #


def load_settings() -> Settings:
    """
    Carrega e valida as configurações. Levanta um erro em caso de falha.
    """
    try:
        return Settings.model_validate({})
    except ValidationError as e:
        raise RuntimeError(
            "Verifique se o arquivo .env existe e contém as variáveis necessárias."
        ) from e


settings = load_settings()
