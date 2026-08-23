import pytest

pytestmark = pytest.mark.asyncio


async def _pay(client, order_id, amount, payment_type='CASH'):
    return await client.post(
        '/api/payments/',
        json={
            'order_id': order_id,
            'amount': amount,
            'payment_type': payment_type,
        },
    )


async def test_refund_returns_money_to_the_order(client, order):
    created = await order('1000.00')
    payment = (await _pay(client, created['id'], '1000.00')).json()

    response = await client.post(f'/api/payments/{payment["id"]}/refund')

    assert response.status_code == 200
    assert response.json()['status'] == 'REFUNDED'

    body = (await client.get(f'/api/orders/{created["id"]}')).json()
    assert body['paid_amount'] == '0.00'
    assert body['payment_status'] == 'UNPAID'


async def test_partial_refund_returns_order_to_partially_paid(client, order):
    created = await order('1000.00')
    first = (await _pay(client, created['id'], '400.00')).json()
    await _pay(client, created['id'], '600.00')

    await client.post(f'/api/payments/{first["id"]}/refund')

    body = (await client.get(f'/api/orders/{created["id"]}')).json()
    assert body['paid_amount'] == '600.00'
    assert body['payment_status'] == 'PARTIALLY_PAID'


async def test_double_refund_is_rejected(client, order):
    """Регрессия: возвращённый платёж нельзя вернуть ещё раз."""

    created = await order('1000.00')
    payment = (await _pay(client, created['id'], '500.00')).json()

    await client.post(f'/api/payments/{payment["id"]}/refund')
    response = await client.post(f'/api/payments/{payment["id"]}/refund')

    assert response.status_code == 400

    body = (await client.get(f'/api/orders/{created["id"]}')).json()
    assert body['paid_amount'] == '0.00'


async def test_pending_payment_cannot_be_refunded(client, order):
    created = await order('1000.00')
    payment = (await _pay(client, created['id'], '500.00', 'ACQUIRING')).json()

    response = await client.post(f'/api/payments/{payment["id"]}/refund')

    assert response.status_code == 400


async def test_refund_of_unknown_payment_returns_404(client):
    response = await client.post('/api/payments/404/refund')

    assert response.status_code == 404


async def test_refunded_payment_frees_the_order_for_new_payments(
    client, order
):
    created = await order('1000.00')
    payment = (await _pay(client, created['id'], '1000.00')).json()
    await client.post(f'/api/payments/{payment["id"]}/refund')

    response = await _pay(client, created['id'], '1000.00')

    assert response.status_code == 201
