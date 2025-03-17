import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.api.models import GPTAssistSchema
from src.db.orm.gpt_assistant_orm import GPTAssistantOrm
from src.db.orm.user_orm import AnalyticsORM
from src.api.models.models import ChangeUserSchema, BonusLinkSchema
from src.scripts.queue.rabbit_queue import model
from src.utils.logger import setup_logger

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

        return JSONResponse(content={"success": True}, status_code=200)
    except Exception as e:
        return JSONResponse(
            content={"status": False, "error": str(e), "user_id": user_id},
            status_code=500,
        )


@router.get("/assistants")
async def get_assistants_api():
    """Получение ассистентов на фронтенд"""

    try:
        all_assistants = await GPTAssistantOrm.get_all_assistants()
        data = []

        for assist in all_assistants:
            data.append({
                "id": assist.id,
                "title": assist.title,
                "energy_cost": float(assist.energy_cost),
                "free_for_premium": assist.premium_free,
                "status": assist.disable,
            })

        return JSONResponse(content={"items": data})
    except Exception as e:
        return JSONResponse(content={"status": False, "error": str(e)}, status_code=500)


@router.post("/assistants/create")
async def create_assistant(data: GPTAssistSchema, request: Request):
    """GPTAssistSchema создание ассистента"""

    try:
        new_assis = await GPTAssistantOrm.create_new_assistant(data.model_dump())
        return JSONResponse(content={"success": True}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"status": False, "error": str(e)}, status_code=500)


@router.get("/assistants/{assist_id}/info")
async def update_assistant(assist_id: int):
    """Изменение ассистента"""

    try:
        change_assist = await GPTAssistantOrm.get_select_assistants(assist_id)
        data = {
            "title": change_assist.title,
            "assistant_id": change_assist.assistant_id,
            "comment": change_assist.comment,
            "energy_cost": float(change_assist.energy_cost),
            "premium_free": change_assist.premium_free,
            "disable": change_assist.disable,
        }

        return JSONResponse(content=data, status_code=200)
    except Exception as e:

        return JSONResponse(content={"status": False, "error": str(e)}, status_code=500)

@router.put("/assistants/{assist_id}/change")
async def update_assistant(assist_id: int, data: GPTAssistSchema, request: Request):
    """Изменение ассистента"""

    try:
        data.id = assist_id
        change_assist = await GPTAssistantOrm.update_assistant(data.model_dump())
        return JSONResponse(content={"success": True}, status_code=200)
    except Exception as e:
        logger = setup_logger(__name__)
        logger.debug(e)
        return JSONResponse(content={"status": False, "error": str(e)}, status_code=500)


@router.post("/bonus_link/add")
async def add_new_bonus_link(data: BonusLinkSchema):
    try:
        response = await AnalyticsORM.add_or_change_promo(data.model_dump())

        return JSONResponse(content=response, status_code=200)
    except Exception as e:
        return JSONResponse(content={"status": False, "error": str(e)}, status_code=500)
