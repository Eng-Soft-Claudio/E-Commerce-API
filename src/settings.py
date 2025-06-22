"""
Módulo para gerenciar configurações da aplicação a partir de variáveis de ambiente.

Esta implementação usa pathlib para construir um caminho absoluto para o arquivo .env,
resolvendo problemas de análise estática e garantindo que o arquivo seja
encontrado independentemente do diretório de trabalho atual.
"""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).parent.parent
ENV_FILE_PATH = ROOT_DIR / ".env"

print(f"--- [SETTINGS] Procurando por arquivo .env em: {ENV_FILE_PATH} ---")


class Settings(BaseSettings):
    """Carrega as configurações a partir do caminho absoluto do .env ou do ambiente."""
    
    # MODIFICAÇÃO: Usando 'Field' do Pydantic para garantir que o tipo seja 
    # exatamente uma string e sem processamentos automáticos que possam corromper o segredo.
    STRIPE_SECRET_KEY: str = Field(...)
    STRIPE_WEBHOOK_SECRET: str = Field(...)
    CLIENT_URL: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding='utf-8' # Adiciona codificação explícita
    )


try:
    settings = Settings.model_validate({})
    print("--- [SETTINGS] Configurações carregadas com sucesso! ---")
    print(f"--- [SETTINGS] Webhook Secret final (últimos 4 chars): ...{settings.STRIPE_WEBHOOK_SECRET[-4:]}")
except Exception as e:
    print(f"--- [SETTINGS] ERRO AO CARREGAR CONFIGURAÇÕES: {e} ---")
    raise e