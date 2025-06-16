"""
Módulo para gerenciar configurações da aplicação a partir de variáveis de ambiente.

Esta implementação usa pathlib para construir um caminho absoluto para o arquivo .env,
resolvendo problemas de análise estática e garantindo que o arquivo seja
encontrado independentemente do diretório de trabalho atual.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).parent.parent
ENV_FILE_PATH = ROOT_DIR / ".env"

print(f"--- [SETTINGS] Procurando por arquivo .env em: {ENV_FILE_PATH} ---")


class Settings(BaseSettings):
    """Carrega as configurações a partir do caminho absoluto do .env ou do ambiente."""

    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    CLIENT_URL: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=str(ENV_FILE_PATH))


try:
    settings = Settings.model_validate({})
    print("--- [SETTINGS] Configurações carregadas com sucesso! ---")
except Exception as e: # pragma: no cover
    print(f"--- [SETTINGS] ERRO AO CARREGAR CONFIGURAÇÕES: {e} ---")
    raise e
