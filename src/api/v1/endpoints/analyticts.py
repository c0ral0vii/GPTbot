from src.api.v1.routes import router


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