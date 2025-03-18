from fastapi.responses import JSONResponse
from src.api.v1.routes import router
from src.db.orm.gpt_assistant_orm import GPTAssistantOrm
from src.api.models import GPTAssistSchema


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

