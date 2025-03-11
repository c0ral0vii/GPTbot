from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from src.api.models.models import PaymentSchema
from src.utils.premium_script import premium_notification

router = APIRouter()


@router.post("/yookassa/success")
async def get_payment_data(data: PaymentSchema):
    """Юкасса платежка, тут вебхук как только оплачено пользователю присвается на месяц премиум"""

    payment_info = data.model_dump()

    if payment_info["event"] == "payment.succeeded":
        user_id = int(payment_info["object"]["metadata"]["user_id"])

        data = {
            "user_id": user_id,
        }

        await premium_notification(data)

        return JSONResponse({"status": "success"}, status_code=200)

    raise HTTPException(status_code=500, detail="Payment not found")
