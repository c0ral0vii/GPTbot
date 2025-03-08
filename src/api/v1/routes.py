import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from src.db.orm.user_orm import AnalyticsORM
from src.api.models.models import ChangeUserSchema
from src.scripts.queue.rabbit_queue import model

router = APIRouter()


@router.get("/stats/overview")
async def get_overview_stats():
    """Получение общей статистики"""

    users_data = await AnalyticsORM.get_user_for_analytics()

    data = {
        "total_users": users_data.get("total_users_count", 0),
        "active_today": users_data.get("active_users_today_count", 0),
        "active_subscriptions": users_data.get("premium_users_count", 0),
        "total_revenue": users_data.get("revenue", 0),
        "system_status": "HEALTHY",
        "system_load": f"-",
    }

    return JSONResponse(content=data)


@router.get("/analytics/activity")
async def get_activity_data():
    data = await AnalyticsORM.get_activity_users()

    return JSONResponse(
        content={"labels": data.get("labels"), "values": data.get("values")}
    )


@router.get("/analytics/queues")
async def get_queue_data():
    # analytics = await model.get_analytics_queue()
    return JSONResponse(content={})

@router.get("/analytics/users")
async def get_user_data():
    users_data = await AnalyticsORM.get_user_for_analytics()

    return JSONResponse(
        content={
            "values": [
                users_data.get("non_premium_users_count", 0),
                users_data.get("premium_users_count", 0),
            ],  # non-prime, prime
        }
    )


@router.get("/users")
async def get_all_users(
    skip: int = 0,
    limit: int = 50,
    search: str = "",
):
    users = await AnalyticsORM.get_all_users_analytics(search)

    data = {
        "items": users[skip : skip + limit] if len(users) >= limit else users,
        "total": len(users),
        "page": skip // limit + 1 if search == "" else 1,
        "total_pages": (len(users) + limit - 1) // limit,
    }

    return JSONResponse(content=data)


# @router.get("/users/{user_id}/banned")
# async def get_banned_user_data(user_id: int):
#
#     await AnalyticsORM.banned_user(user_id)
#
#     return JSONResponse(
#         content={
#             "status": "banned",
#             "user_id": user_id,
#         }
#     )


@router.get("/users/{user_id}/info")
async def get_user_info(user_id: int):
    """Получение информации о пользователе"""

    user_info = await AnalyticsORM.get_all_user_info(user_id)

    return JSONResponse(content=user_info)


@router.put("/users/{user_id}/change")
async def change_user_data(user_id: int, user_data: ChangeUserSchema):
    try:
        response = await AnalyticsORM.change_user(user_id, user_data.model_dump())

        return JSONResponse(content=response, status_code=200)
    except Exception as e:
        return JSONResponse(content={"status": False, "user_id": user_id}, status_code=500)