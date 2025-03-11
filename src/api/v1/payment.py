from fastapi import APIRouter

router = APIRouter()


@router.get("/yookassa/success")
async def get_payment_data(): ...  # добавить обработку платежки


