from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_read_main():
    """Testa o endpoint raiz do app principal."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Bem-vindo à FastAPI RESTful!"}