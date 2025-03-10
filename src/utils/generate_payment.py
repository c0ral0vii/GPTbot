from src.scripts.payment.service import PaymentService

payment_model = PaymentService()


async def generate_payment(user_id):
    payment_link = await payment_model.generate_yookassa_link(user_id)

    return payment_link
