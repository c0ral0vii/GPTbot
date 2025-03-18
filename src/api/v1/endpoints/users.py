from fastapi.responses import JSONResponse
from src.api.models import ChangeUserSchema
from src.api.v1.routes import router
from src.db.orm.user_orm import AnalyticsORM


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