import random

from fastapi import APIRouter, Request
from starlette.responses import JSONResponse

router = APIRouter()


@router.post("/premium/buy")
async def buy_premium_user(request: Request): ...


@router.get("/stats/overview")
async def get_overview_stats():
    """Получение общей статистики"""

    data = {
        "total_users": 0,
        "active_today": 0,
        "active_subscriptions": 0,
        "total_revenue": 0,
        "system_status": "HEALTHY",
        "system_load": f"-",
    }

    return JSONResponse(content=data)


@router.get("/analytics/activity")
async def get_activity_data():
    hours = list(range(24))
    values = [random.randint(10, 100) for _ in range(24)]

    return JSONResponse(content={"labels": hours, "values": values})


@router.get("/analytics/queues")
async def get_queue_data():
    return JSONResponse(content={"labels": [], "values": []})


@router.get("/users")
async def get_user_data():

    return JSONResponse(
        content={
            "values": [], # non-prime, prime
        }
    )


@router.put("/users/{user_id}/banned")
async def get_banned_user_data(user_id: int):
    return JSONResponse(
        content={
            "status": "banned",
            "user_id": user_id,
        }
    )


@router.get("/users/{user_id}/info")
async def get_user_info(user_id: str):

    return JSONResponse(content={})


@router.get("/payment")
async def get_payment_data():
    ...