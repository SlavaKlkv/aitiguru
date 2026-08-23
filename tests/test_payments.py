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


async def _order_status(client, order_id):
    response = await client.get(f'/api/orders/{order_id}')
    return response.json()['payment_status']


async def test_cash_payment_is_paid_immediately(client, order):
    created = await order('1000.00')

    response = await _pay(client, created['id'], '1000.00')

    assert response.status_code == 201
    assert response.json()['status'] == 'PAID'
    assert await _order_status(client, created['id']) == 'PAID'


async def test_partial_payment_moves_order_to_partially_paid(client, order):
    created = await order('1000.00')

    await _pay(client, created['id'], '400.00')

    assert await _order_status(client, created['id']) == 'PARTIALLY_PAID'


async def test_several_payments_close_the_order(client, order):
    created = await order('1000.00')

    await _pay(client, created['id'], '400.00')
    await _pay(client, created['id'], '600.00')

    body = (await client.get(f'/api/orders/{created["id"]}')).json()
    assert body['paid_amount'] == '1000.00'
    assert body['payment_status'] == 'PAID'


async def test_overpayment_is_rejected(client, order):
    created = await order('1000.00')

    await _pay(client, created['id'], '900.00')
    response = await _pay(client, created['id'], '200.00')

    assert response.status_code == 400
    assert await _order_status(client, created['id']) == 'PARTIALLY_PAID'


async def test_payment_for_unknown_order_returns_404(client):
    response = await _pay(client, 404, '10.00')

    assert response.status_code == 404


async def test_acquiring_payment_waits_for_the_bank(client, order):
    """Эквайринг не считается оплаченным до подтверждения банком."""

    created = await order('1000.00')

    response = await _pay(client, created['id'], '1000.00', 'ACQUIRING')

    assert response.status_code == 201
    assert response.json()['status'] == 'PENDING'
    assert response.json()['bank_payment_id']
    assert await _order_status(client, created['id']) == 'UNPAID'


async def test_bank_confirmation_closes_the_order(client, order):
    created = await order('1000.00')
    payment = (
        await _pay(client, created['id'], '1000.00', 'ACQUIRING')
    ).json()

    response = await client.post(f'/api/payments/{payment["id"]}/check')

    assert response.status_code == 200
    assert response.json()['status'] == 'PAID'
    assert await _order_status(client, created['id']) == 'PAID'


async def test_repeated_check_does_not_pay_the_order_twice(client, order):
    """Регрессия: повторная сверка не должна повторно прибавлять сумму."""

    created = await order('1000.00')
    payment = (await _pay(client, created['id'], '600.00', 'ACQUIRING')).json()

    await client.post(f'/api/payments/{payment["id"]}/check')
    await client.post(f'/api/payments/{payment["id"]}/check')

    body = (await client.get(f'/api/orders/{created["id"]}')).json()
    assert body['paid_amount'] == '600.00'
    assert body['payment_status'] == 'PARTIALLY_PAID'


async def test_pending_acquiring_blocks_overpayment(client, order):
    """Незавершённый эквайринг занимает сумму заказа."""

    created = await order('1000.00')
    await _pay(client, created['id'], '1000.00', 'ACQUIRING')

    response = await _pay(client, created['id'], '100.00')

    assert response.status_code == 400


async def test_check_on_cash_payment_is_rejected(client, order):
    created = await order('1000.00')
    payment = (await _pay(client, created['id'], '100.00')).json()

    response = await client.post(f'/api/payments/{payment["id"]}/check')

    assert response.status_code == 400


async def test_check_on_unknown_payment_returns_404(client):
    response = await client.post('/api/payments/404/check')

    assert response.status_code == 404
