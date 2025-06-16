"""
Suíte de Testes para o recurso de Pagamentos (Payments).

Testa os endpoints sob o prefixo '/payments', cobrindo o fluxo de criação
de sessão de checkout e o processamento de webhooks do Stripe.

Utiliza 'pytest-mock' para simular as chamadas à API externa do Stripe,
garantindo que os testes sejam rápidos, determinísticos e não dependam de rede.
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict
from unittest.mock import MagicMock

from sqlalchemy.orm import Session
import stripe

from src import crud
from src.schemas import UserCreate

from src.models import Order

# -------------------------------------------------------------------------- #
#                        SETUP E FIXTURES AUXILIARES                         #
# -------------------------------------------------------------------------- #


@pytest.fixture(scope="function")
def order_for_payment(
    client: TestClient, user_token_headers: Dict, superuser_token_headers: Dict
) -> Dict:
    """Fixture que cria um cenário completo (usuário, produto, pedido) para o pagamento."""
    cat_resp = client.post(
        "/categories/", headers=superuser_token_headers, json={"title": "Pagamentos"}
    )
    prod_data = {
        "name": "Produto para Pagar",
        "price": 123.45,
        "category_id": cat_resp.json()["id"],
    }
    prod_resp = client.post(
        "/products/", headers=superuser_token_headers, json=prod_data
    )
    client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": prod_resp.json()["id"], "quantity": 1},
    )
    order_response = client.post("/orders/", headers=user_token_headers)
    assert order_response.status_code == 201
    return order_response.json()


# -------------------------------------------------------------------------- #
#                   TESTES PARA 'create_checkout_session'                      #
# -------------------------------------------------------------------------- #


def test_create_checkout_session_success(
    client: TestClient, user_token_headers: Dict, order_for_payment: Dict, mocker
):
    """Testa o caminho feliz da criação de uma sessão de checkout."""
    order_id = order_for_payment["id"]
    mock_stripe_session = MagicMock(
        url="https://checkout.stripe.com/pay/cs_test_12345",
        payment_intent="pi_test_12345",
    )
    mocker.patch("stripe.checkout.Session.create", return_value=mock_stripe_session)

    response = client.post(
        f"/payments/create-checkout-session/{order_id}", headers=user_token_headers
    )
    assert response.status_code == 200
    assert response.json() == {"checkout_url": mock_stripe_session.url}
    stripe.checkout.Session.create.assert_called_once()


def test_create_checkout_for_nonexistent_order(
    client: TestClient, user_token_headers: Dict
):
    """Testa criar um checkout para um pedido que não existe (espera 404)."""
    response = client.post(
        "/payments/create-checkout-session/9999", headers=user_token_headers
    )
    assert response.status_code == 404


def test_create_checkout_for_paid_order(
    client: TestClient,
    user_token_headers: Dict,
    order_for_payment: Dict,
    db_session: Session,
):
    """Testa criar um checkout para um pedido já pago (espera 400)."""
    order_id = order_for_payment["id"]
    order_in_db = db_session.query(Order).filter(Order.id == order_id).first()
    assert order_in_db is not None
    order_in_db.status = "paid"
    db_session.commit()
    response = client.post(
        f"/payments/create-checkout-session/{order_id}", headers=user_token_headers
    )
    assert response.status_code == 400


# -------------------------------------------------------------------------- #
#                             TESTES PARA O WEBHOOK                           #
# -------------------------------------------------------------------------- #


def test_stripe_webhook_success_payment(
    client: TestClient, order_for_payment: Dict, db_session: Session, mocker
):
    """Testa o processamento bem-sucedido de um webhook de pagamento."""
    order_id = order_for_payment["id"]
    event_payload = {
        "id": "evt_12345",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_123",
                "object": "checkout.session",
                "metadata": {"order_id": str(order_id)},
                "payment_intent": "pi_test_123",
                "payment_status": "paid",
            }
        },
    }
    mocker.patch("stripe.Webhook.construct_event", return_value=event_payload)

    response = client.post(
        "/payments/webhook",
        json=event_payload,
        headers={"Stripe-Signature": "dummy_sig"},
    )
    assert response.status_code == 200
    order_in_db = db_session.query(Order).filter(Order.id == order_id).first()
    assert order_in_db is not None
    assert order_in_db.status == "paid"
    assert order_in_db.payment_intent_id == "pi_test_123"


def test_stripe_webhook_invalid_signature(client: TestClient, mocker):
    """Testa a falha do webhook quando a assinatura do Stripe é inválida."""
    from stripe import SignatureVerificationError

    mocker.patch(
        "stripe.Webhook.construct_event",
        side_effect=SignatureVerificationError("Invalid signature", "sig"),
    )
    response = client.post(
        "/payments/webhook", json={}, headers={"Stripe-Signature": "invalid_sig"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid signature"


def test_create_checkout_session_handles_stripe_error(
    client: TestClient, user_token_headers: Dict, order_for_payment: Dict, mocker
):
    """
    Testa o tratamento de um erro da API do Stripe durante a criação da sessão.
    Cobre o bloco 'except StripeError'.
    """
    order_id = order_for_payment["id"]
    mocker.patch(
        "stripe.checkout.Session.create",
        side_effect=stripe.StripeError("A comunicação com o Stripe falhou."),
    )

    response = client.post(
        f"/payments/create-checkout-session/{order_id}", headers=user_token_headers
    )

    assert response.status_code == 400
    assert "Stripe error:" in response.json()["detail"]


def test_create_checkout_session_handles_missing_url(
    client: TestClient, user_token_headers: Dict, order_for_payment: Dict, mocker
):
    """
    Testa o tratamento do caso raro em que o Stripe retorna um objeto sem URL.
    Cobre o bloco 'if not checkout_session.url'.
    """
    order_id = order_for_payment["id"]
    mock_stripe_session = MagicMock(url=None)
    mocker.patch("stripe.checkout.Session.create", return_value=mock_stripe_session)

    response = client.post(
        f"/payments/create-checkout-session/{order_id}", headers=user_token_headers
    )

    assert response.status_code == 500
    assert "did not return a checkout URL" in response.json()["detail"]


def test_stripe_webhook_handles_value_error(client: TestClient, mocker):
    """Testa o tratamento de um payload inválido que causa ValueError."""
    mocker.patch(
        "stripe.Webhook.construct_event", side_effect=ValueError("Invalid payload")
    )

    response = client.post(
        "/payments/webhook",
        content="not-a-valid-json",
        headers={"Stripe-Signature": "dummy_sig"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid payload"


def test_stripe_webhook_handles_missing_order_id(client: TestClient, mocker):
    """Testa o webhook recebendo um evento completo, mas sem order_id."""
    event_payload = {
        "type": "checkout.session.completed",
        "data": {"object": {"metadata": {}}},
    }
    mocker.patch("stripe.Webhook.construct_event", return_value=event_payload)

    response = client.post(
        "/payments/webhook",
        json=event_payload,
        headers={"Stripe-Signature": "dummy_sig"},
    )

    assert response.status_code == 200
    assert response.json()["detail"] == "Missing order_id in metadata"


def test_stripe_webhook_handles_unhandled_event_type(client: TestClient, mocker):
    """Testa o caminho do 'else', recebendo um tipo de evento não tratado."""
    event_payload = {"type": "payment_intent.created", "id": "evt_unhandled"}
    mocker.patch("stripe.Webhook.construct_event", return_value=event_payload)

    response = client.post(
        "/payments/webhook",
        json=event_payload,
        headers={"Stripe-Signature": "dummy_sig"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "success"}


# -------------------------------------------------------------------------- #
#                             TESTES DE CASOS DE BORDA                       #
# -------------------------------------------------------------------------- #


def test_stripe_webhook_handles_db_update_failure(
    client: TestClient,
    order_for_payment: Dict,
    db_session: Session,
    mocker,
):
    """
    Testa o tratamento de uma falha de banco de dados durante o processamento do webhook.

    Simula uma exceção no 'db.commit()' para garantir que o erro seja capturado
    e uma resposta 500 seja retornada. Cobre as linhas 152-154.
    """
    order_id = order_for_payment["id"]
    event_payload = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"order_id": str(order_id)},
                "payment_status": "paid",
                "payment_intent": "pi_final_test",
            }
        },
    }
    mocker.patch("stripe.Webhook.construct_event", return_value=event_payload)

    mocker.patch.object(
        db_session, "commit", side_effect=Exception("Simulated Database Commit Error")
    )

    response = client.post(
        "/payments/webhook",
        json=event_payload,
        headers={"Stripe-Signature": "dummy_sig"},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "DB update failed."
