from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from src.db.orm.dialog_orm import DialogORM

router = APIRouter()


@router.get("/chat/{dialog_uuid}")
async def get_dialog(dialog_uuid: str):
    """Получение диалога по UUID"""
    try:
        
        dialog_messages = await DialogORM.get_dialog_messages_by_uuid(uuid=dialog_uuid)
        
        return JSONResponse(content=dialog_messages, status_code=200)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))