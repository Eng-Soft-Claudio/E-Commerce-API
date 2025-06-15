# create_db.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "src"))
from database import engine, Base
from src import models  # noqa: F401
Base.metadata.create_all(bind=engine)
print("Banco de dados e tabelas verificados/criados com sucesso.")