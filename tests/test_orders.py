import pytest

pytestmark = pytest.mark.asyncio


async def test_create_order_starts_unpaid(client):
    response = await client.post(
        '/api/orders/', json={'total_amount': '1000.00'}
    )

    assert response.status_code == 201
    body = response.json()
    assert body['payment_status'] == 'UNPAID'
    assert body['paid_amount'] == '0.00'


async def test_get_order(client, order):
    created = await order('250.00')

    response = await client.get(f'/api/orders/{created["id"]}')

    assert response.status_code == 200
    assert response.json()['total_amount'] == '250.00'


async def test_get_unknown_order_returns_404(client):
    response = await client.get('/api/orders/404')

    assert response.status_code == 404
    assert 'не найден' in response.json()['detail']


@pytest.mark.parametrize('total_amount', ['0.00', '-1.00'])
async def test_non_positive_total_amount_rejected(client, total_amount):
    response = await client.post(
        '/api/orders/', json={'total_amount': total_amount}
    )

    assert response.status_code >= 400
