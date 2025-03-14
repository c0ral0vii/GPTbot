from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from src.api.models.models import PaymentSchema
from src.utils.logger import setup_logger
from src.utils.premium_script import premium_notification

router = APIRouter()
logger = setup_logger(__name__)

@router.post("/yookassa/success")
async def get_payment_data(data: PaymentSchema):
    """Юкасса платежка, тут вебхук как только оплачено пользователю присвается на месяц премиум"""

    payment_info = data.model_dump()
    logger.info(payment_info)

    if payment_info["event"] == "payment.succeeded":
        user_id = int(payment_info["object"]["metadata"]["user_id"])
        payment_method = payment_info.get("payment_method", {}).get("id", None)

        data = {
            "user_id": user_id,
            "payment_method": payment_method,
        }

        await premium_notification(data)

        return JSONResponse({"status": "success"}, status_code=200)

    raise HTTPException(status_code=500, detail="Payment not found")
