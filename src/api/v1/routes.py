import uuid
from typing import Optional

from fastapi import APIRouter, File, UploadFile
from fastapi.params import Form
from fastapi.responses import JSONResponse
from fastapi import HTTPException

from src.api.models import GPTAssistSchema, BonusLinkSchema, ChangeUserSchema, SpamData
from src.db.orm.gpt_assistant_orm import GPTAssistantOrm
from src.db.orm.bonus_links_orm import BonusLinksOrm
from src.db.orm.user_orm import AnalyticsORM, logger
from src.config.config import ROOT_PATH
from src.scripts.spammer.service import TelegramBroadcaster

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


@router.get("/assistants")
async def get_assistants_api():
    """Получение ассистентов на фронтенд"""

    try:
        all_assistants = await GPTAssistantOrm.get_all_assistants()
        data = []

        for assist in all_assistants:
            data.append(
                {
                    "id": assist.id,
                    "title": assist.title,
                    "energy_cost": float(assist.energy_cost),
                    "free_for_premium": assist.premium_free,
                    "status": assist.disable,
                }
            )

        return JSONResponse(content={"items": data})
    except Exception as e:
        return JSONResponse(content={"status": False, "error": str(e)}, status_code=500)


@router.post("/assistants/create")
async def create_assistant(data: GPTAssistSchema):
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
async def update_assistant(assist_id: int, data: GPTAssistSchema):
    """Изменение ассистента"""

    try:
        data.id = assist_id
        await GPTAssistantOrm.update_assistant(data.model_dump())
        return JSONResponse(content={"success": True}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"status": False, "error": str(e)}, status_code=500)


@router.get("/bonuses")
async def get_all_bonuses():
    try:
        all_bonus_links = await BonusLinksOrm.get_all_bonuses()
        output_items = []
        for bonuses in all_bonus_links:
            output_items.append(
                {
                    "id": bonuses.id,
                    "link": f"{bonuses.link}",
                    "count_activate": bonuses.active_count,
                    "energy": float(bonuses.energy_bonus),
                }
            )

        return JSONResponse(content={"items": output_items}, status_code=200)
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)


@router.get("/bonuses/{id}/info")
async def get_info_bonuse(id: int):
    try:
        bonus_link = await BonusLinksOrm.get_bonus_link(link_id=id)

        return JSONResponse(
            content={
                "link": f"{bonus_link.link}",
                "count_activate": bonus_link.active_count,
                "energy": float(bonus_link.energy_bonus),
            },
            status_code=200,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/bonuses/{id}/change")
async def change_bonuse(data: BonusLinkSchema):
    try:
        change_bonuses = await BonusLinksOrm.update_bonus_link(
            data=data.model_dump(),
        )

        return JSONResponse(content={"success": True}, status_code=200)
    except:
        raise HTTPException(status_code=500)


@router.post("/bonuses/create")
async def create_bonuse(bonus_link_data: BonusLinkSchema):
    try:
        new_bonus_link = await BonusLinksOrm.create_bonus_links(
            bonus_link_data.model_dump()
        )
        return JSONResponse(content={"success": True}, status_code=201)
    except:
        raise HTTPException(status_code=500)


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


@router.post("/spam/create")
async def crete_spam(
        image: Optional[UploadFile] = File(None),
        spamText: str = Form(...),
        forPremium: bool = Form(False),
        forRegular: bool = Form(False),
):
    """Создать рассылку"""

    try:
        image_data = None
        if image:
            file_ext = image.filename.split(".")[-1]
            filename = f"{uuid.uuid4()}.{file_ext}"
            image_data = f"./tmp/spam_image/{filename}"
            with open(image_data, "wb") as buffer:
                buffer.write(await image.read())
            logger.debug(image_data)

        data = SpamData(
            spamText=spamText,
            forPremium=forPremium,
            forRegular=forRegular
        ).model_dump()

        await TelegramBroadcaster().broadcast(
            text=data["spamText"],
            photo_path=image_data,
            premium_only=data["forPremium"],
            not_premium_only=data["forRegular"],
        )

        return JSONResponse(content={"success": True}, status_code=201)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))