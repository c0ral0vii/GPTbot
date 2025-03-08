from fastapi import APIRouter

router = APIRouter()


@router.get("/payment/yookassa/success")
async def get_payment_data(): ...  # добавить обработку платежки


@router.get("/payment/next/success")
async def get_payment_data(): ...  # добавить обработку второй платежки
