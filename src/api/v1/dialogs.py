from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/dialogs", tags=["dialogs"])


@router.get("/chat/{chat_id}")
async def get_chat(chat_id: str):
    return {"chat_id": chat_id}
